###############################################################################
##
## This file was modified from the Burrito System code.
## Burrito System Paper:
##  - Philip J. Guo and Margo Seltzer. Burrito: Wrapping Your Lab Notebook in
##    Computational Infrastructure. In Proceedings of the USENIX Workshop on
##    the Theory and Practice of Provenance (TaPP), June 2012.
## Developer: Philip Guo (http://pgbovine.net/)
##
## This file is part of ReproZip.
##
###############################################################################

import os
import sys
from copy import deepcopy
import posix

import reprozip.debug
from reprozip.utils import *

from pymongo import Connection, ASCENDING

IGNORE_DIRS = ['/dev/', '/proc/', '/sys/', '/tmp/']

# the double-pipe delimeter isn't perfect, but it'll do for now
FIELD_DELIMITER = '||'

OPEN_VARIANTS = ('OPEN_READ', 'OPEN_WRITE', 'OPEN_READWRITE')
OPEN_AT_VARIANTS = ('OPEN_AT_READ', 'OPEN_AT_WRITE', 'OPEN_AT_READWRITE')
RW_VARIANTS   = ('READ', 'WRITE', 'MMAP_READ', 'MMAP_WRITE', 'MMAP_READWRITE')

# if multiple file read/write entries occur within this amount of time,
# only keep the earlier one
FILE_ACCESS_COALESCE_MS = 200


# sub-classes simply add new fields depending on syscall_name
class RawPassLiteLogEntry:
    def __init__(self, syscall_name, timestamp, pid, ppid, uid, proc_name):
        self.syscall_name = syscall_name
        self.timestamp = timestamp
        self.pid = pid
        self.ppid = ppid
        self.uid = uid
        self.proc_name = proc_name

    def __str__(self):
        return "%d %s %d %d %s" % (self.timestamp, self.syscall_name, self.pid,
                                   self.uid, self.proc_name)


def parse_raw_pass_lite_line(line):
    """
    Function that parses according to the format outputted by pass-lite.stp.
    """
  
    toks = line.split(FIELD_DELIMITER)
    
    # fields that all lines should have in common
    timestamp = int(toks[0])
    pid = int(toks[1])
    ppid = int(toks[2])
    uid = int(toks[3])
    proc_name = toks[4]
    syscall_name = toks[5]
    rest = toks[6:]
    
    entry = RawPassLiteLogEntry(syscall_name, timestamp, pid, ppid, uid, proc_name)
    
    if syscall_name in OPEN_VARIANTS:
        assert len(rest) == 2
        entry.filename = rest[0]
        entry.fd = int(rest[1])
        
    elif syscall_name in OPEN_AT_VARIANTS:
        assert len(rest) == 3
        entry.filename = rest[0]
        entry.d_filename = rest[1]
        entry.fd = int(rest[2])
    
    elif syscall_name == 'OPEN_ABSPATH':
        assert len(rest) == 1
        entry.filename_abspath = rest[0]
        assert entry.filename_abspath[0] == os.sep # absolute path check
        
    elif syscall_name in ('STAT', 'ACCESS', 'TRUNCATE'):
        assert len(rest) == 1
        entry.filename = rest[0]
        
    elif syscall_name in ('STAT_AT','ACCESS_AT'):
        assert len(rest) == 2
        entry.filename = rest[0]
        entry.d_filename = rest[1]
    
    elif syscall_name in RW_VARIANTS or syscall_name == 'CLOSE':
        assert len(rest) == 1
        entry.fd = int(rest[0])
        
    elif syscall_name == 'SYMLINK':
        assert len(rest) == 3
        entry.symlink = rest[0]
        entry.target = rest[1]
        entry.pwd = rest[2]
        
    elif syscall_name == 'SYMLINK_AT':
        assert len(rest) == 3
        entry.symlink = rest[0]
        entry.d_filename = rest[1]
        entry.target = rest[2]
    
    elif syscall_name == 'PIPE':
        assert len(rest) == 2
        entry.pipe_read_fd = int(rest[0])
        entry.pipe_write_fd = int(rest[1])
    
    elif syscall_name == 'DUP':
        assert len(rest) == 2
        entry.src_fd = int(rest[0])
        entry.dst_fd = int(rest[1])
    
    elif syscall_name == 'DUP2':
        assert len(rest) == 3
        entry.src_fd = int(rest[0])
        entry.dst_fd = int(rest[1])
        # sanity check
        assert int(rest[2]) == entry.dst_fd
    
    elif syscall_name == 'FORK':
        assert len(rest) == 1
        entry.child_pid = int(rest[0])
    
    elif syscall_name == 'EXECVE':
        # it's possible for the command line (argv) itself to contain
        # FIELD_DELIMITER, so .join() everything after rest[0]
        assert len(rest) >= 3
        entry.pwd = rest[0]
        entry.exec_filename = rest[1]
        entry.env = rest[2]
        entry.argv = FIELD_DELIMITER.join(rest[3:])
        
    elif syscall_name == 'CHDIR':
        assert len(rest) == 1
        entry.path = rest[0]
    
    elif syscall_name == 'EXECVE_RETURN':
        assert len(rest) == 1
        entry.return_code = int(rest[0])
    
    elif syscall_name == 'EXIT_GROUP':
        assert len(rest) == 1
        entry.exit_code = int(rest[0])
    
    elif syscall_name == 'RENAME':
        assert len(rest) == 2
        entry.old_filename = rest[0]
        entry.new_filename = rest[1]
        assert entry.old_filename[0] == os.sep # absolute path check
        assert entry.new_filename[0] == os.sep # absolute path check
    
    else:
        assert False, line
    
    return entry


class ProcessPhase:
    """
    A process has 1 or more 'phases', where during each phase it has some
    set name.  A process changes from one phase to the next when an EXECVE
    system call is made, so that it morphs into another executable.
    """
    
    def __init__(self, start_time, execve_filename=None, execve_pwd=None, execve_argv=None, execve_env=None):
        self.start_time = start_time
        
        self.process_name = None # to be filled in by _set_or_confirm_name()
        
        # note that these might be 'None' if the ProcessPhase wasn't created
        # by an execve call (i.e., it's the first phase in the process)
        self.execve_filename = execve_filename
        self.execve_pwd = execve_pwd
        self.execve_argv = execve_argv
        self.execve_env = execve_env
        
        # Each entry is a dict mapping from filename to a SORTED LIST of
        # timestamps
        #
        # Apply filters using IGNORE_DIRS to prevent weird pseudo-files from
        # being added to these sets
        self.files_read = {}
        self.files_written = {}
        
        # directories accessed
        self.dirs = {}
        
        # mapping from symbolic link to target
        # symlinks[symlink] = target
        self.symlinks = {}
        
        # Each entry is a tuple of (timestamp, old_filename, new_filename)
        self.files_renamed = set()


    def is_empty(self):
        if self.process_name == None:
            # sanity checks
            assert not self.files_read
            assert not self.files_written
            assert not self.files_renamed
            assert not self.dirs
            assert not self.symlinks
            return True
        else:
            return False


    def _insert_coalesced_time(self, lst, timestamp):
        # lst must be a list
        if not lst:
            lst.append(timestamp)
        else:
            # weird out-of-order case
            if timestamp < lst[-1]:
                print >> sys.stderr, "WARNING: Inserting out-of-order timestamp", timestamp, "where the latest entry is", lst[-1]
                
                lst.append(timestamp)
                lst.sort() # keep things in order
                # TODO: maybe do coalescing here
            else:
                # coalescing optimization
                if (lst[-1] + FILE_ACCESS_COALESCE_MS) < timestamp:
                    lst.append(timestamp)


    def add_file_read(self, proc_name, timestamp, filename):
        self._set_or_confirm_name(proc_name)
        
        if filename not in self.files_read:
            self.files_read[filename] = []
        self._insert_coalesced_time(self.files_read[filename], timestamp)
    
    
    def add_file_write(self, proc_name, timestamp, filename):
        self._set_or_confirm_name(proc_name)
        if filename not in self.files_written:
            self.files_written[filename] = []
        self._insert_coalesced_time(self.files_written[filename], timestamp)
        
    
    def add_dir(self, proc_name, timestamp, filename):
        self._set_or_confirm_name(proc_name)
        if filename not in self.dirs:
            self.dirs[filename] = []
        self._insert_coalesced_time(self.dirs[filename], timestamp)
        
    
    def add_file_rename(self, proc_name, timestamp, old_filename, new_filename):
        self._set_or_confirm_name(proc_name)
        self.files_renamed.add((timestamp, old_filename, new_filename))
        
        
    def add_symlink(self, proc_name, symlink, target):
        self._set_or_confirm_name(proc_name)
        self.symlinks[symlink] = target


    def _set_or_confirm_name(self, proc_name):
        if self.process_name:
            # make an exception for a process named 'exe', since programs like
            # Chrome do an execve on '/proc/self/exe' to re-execute "itself",
            # so the process name is temporarily 'exe' before it reverts back to
            # its original name ... weird, I know!!!
            #
            # other weird observed cases include 'mono' (for C# apps, I presume?)
            #
            # so for now, just issue a warning ...
            #
            # TODO: perhaps a better solution is to acknowledge that a phase
            # can have multiple names and keep track of ALL names for a phase
            # rather than just one name
            if self.process_name != proc_name:
                print >> sys.stderr, "WARNING: Process phase name changed from '%s' to '%s'" % (self.process_name, proc_name)
        
        self.process_name = proc_name # always override it!


    def get_latest_timestamp(self):
        max_time = self.start_time
        for times in self.files_read.values() + self.files_written.values():
            for t in times:
                max_time = max(t, max_time)
        for (t, _, _) in self.files_renamed:
            max_time = max(t, max_time)
        return max_time


    def printMe(self):
        print "  Phase start:", self.start_time, self.process_name
        if self.execve_filename:
            print "    execve:", self.execve_filename
            print "      argv:", self.execve_argv
            print "       pwd:", self.execve_pwd
            print "       env:", self.execve_env
        print "     Files: %d read, %d written, %d renamed" % (len(self.files_read), len(self.files_written), len(self.files_renamed))


    def serialize(self):
        """
        Method that serializes the process phase for MongoDB.
        """
        ret = dict(name=self.process_name,
                   start_time=encode_datetime(self.start_time),
                   execve_filename=self.execve_filename,
                   execve_pwd=self.execve_pwd,
                   execve_argv=self.execve_argv,
                   execve_env=self.execve_env)
        
        # Flatten these dicts into lists, since MongoDB doesn't like
        # filenames being used as dict keys (because they might contain DOT
        # characters, which are apparently not legal in BSON/MongoDB keys).
        #
        # Also, since most files have ONE access time, make the values into
        # an integer rather than a single-element list.  However, when there
        # is more than one access time, keep the list:
        
        serialized_files_read = []
        for (k,v) in self.files_read.iteritems():
            if len(v) > 1:
                serialized_files_read.append(dict(filename=k, timestamp=[encode_datetime(e) for e in v]))
            else:
                assert len(v) == 1
                serialized_files_read.append(dict(filename=k, timestamp=encode_datetime(v[0])))
        
        serialized_files_written = []
        for (k,v) in self.files_written.iteritems():
            if len(v) > 1:
                serialized_files_written.append(dict(filename=k, timestamp=[encode_datetime(e) for e in v]))
            else:
                assert len(v) == 1
                serialized_files_written.append(dict(filename=k, timestamp=encode_datetime(v[0])))
                
        serialized_dirs = []
        for (k,v) in self.dirs.iteritems():
            if len(v) > 1:
                serialized_dirs.append(dict(dirname=k, timestamp=[encode_datetime(e) for e in v]))
            else:
                assert len(v) == 1
                serialized_dirs.append(dict(dirname=k, timestamp=encode_datetime(v[0])))
        
        serialized_renames = []
        for (t, old, new) in sorted(self.files_renamed):
            serialized_renames.append(dict(timestamp=encode_datetime(t), old_filename=old, new_filename=new))
            
        serialized_symlinks = []
        for key in self.symlinks:
            serialized_symlinks.append(dict(symlink=key, target=self.symlinks[key]))
        
        # turn empty collections into None for simplicity
        if not serialized_files_read:
            serialized_files_read = None
        if not serialized_files_written:
            serialized_files_written = None
        if not serialized_renames:
            serialized_renames = None
        if not serialized_symlinks:
            serialized_symlinks = None
        if not serialized_dirs:
            serialized_dirs = None
        
        ret['files_read'] = serialized_files_read
        ret['files_written'] = serialized_files_written
        ret['files_renamed'] = serialized_renames
        ret['directories'] = serialized_dirs
        ret['symlinks'] = serialized_symlinks
        
        return ret  
 

class Process:
    """
    Class that represents a process.
    """
    
    def __init__(self, pid, ppid, uid, creation_time, active_processes_dict):
        self.pid = pid
        self.ppid = ppid
        
        self.uid = uid         # the initial UID at process creation time
        self.other_uids = None # for setuid executables, create a list to store other UIDs
        
        self.creation_time = creation_time
        
        # Open file descriptors (inherit from parent on fork)
        # Key: fd (int)
        # Value: (filename, mode) where mode can be: {'r', 'w', 'rw'}
        self.opened_files = {}
        
        # Some files, for some reason, are opened and not effectively read or
        # written, so they are not stored
        # however, when reproducing the experiment, these files may be
        # needed, so we need to keep track of that
        # Key: fd (int)
        # Value: bool
        #self.processed_files = {}
        
        # TODO: DON'T do the following pre-seeding, since some programs
        # (e.g., kernel-controlled daemons) don't reserve fd's 0, 1, 2
        # so those fd's can be used for regular files.
        #
        # Pre-seed with stdin/stdout/stderr
        # (even though STDIN is read-only, some weirdos try to write to
        # stdin as well, so don't croak on this)
        #self.opened_files = {0: ('STDIN', 'rw'), 1: ('STDOUT', 'w'), 2: ('STDERR', 'w')}
        
        # Open pipes (inherit from parent on fork)
        # Each element is a triple of (creator pid, read fd, write fd)
        self.opened_pipes = set()
        
        self.phases = [ProcessPhase(self.creation_time)]
        
        # Once the process exits, it's "locked" and shouldn't be modified anymore
        self.exited = False
        self.exit_code = None
        self.exit_time = None
        
        # for symbolic links, we need to keep track of working directory
        self.wdir = None
        
        self.prev_entry = None # sometimes we want to refer back to the PREVIOUS entry
        
        # Optimization for incremental indexing ... always update this with
        # the timestamp of the most recent event, so that we can know when
        # this Process instance was last updated
        self.most_recent_event_timestamp = creation_time
        
        # This is pretty gross, but all Process objects should keep a
        # reference to the same dict which maps PIDs to Process objects that
        # are active (i.e., haven't yet exited)
        self.active_processes_dict = active_processes_dict
        
        # Now ADD YOURSELF to active_processes_dict:
        self.active_processes_dict[self.pid] = self
    
    
    def unique_id(self):
        # put creation_time first, so that we can alphabetically sort
        return '%d-%d' % (self.creation_time, self.pid)
    
    
    def _finalize(self):
        # filter out empty phases
        self.phases = [e for e in self.phases if not e.is_empty()]
        
        # do some sanity checks
        assert self.exit_time
        assert self.creation_time <= self.exit_time
        for p in self.phases:
            p_latest_timestamp = p.get_latest_timestamp()
            # relax this assertion since sometimes SystemTap produces
            # timestamps that are SLIGHTLY out of order
            # (hopefully < 1000 microseconds)
            #assert p.get_latest_timestamp() <= self.exit_time
            if p_latest_timestamp > self.exit_time:
                assert p_latest_timestamp <= (self.exit_time + 1000) # fudge factor
                print >> sys.stderr, 'WARNING: p_latest_timestamp[%d] > exit_time[%d] for PID %d ... patching with %d' % (p_latest_timestamp, self.exit_time, self.pid, p_latest_timestamp)
                self.exit_time = p_latest_timestamp
    
    
    def printMe(self):
        print "%d [ppid: %d, uid: %d]" % (self.pid, self.ppid, self.uid),
        if self.other_uids:
            print "| other uids:", self.other_uids
        else:
            print
        
        print "Created:", self.creation_time,
        if self.exited:
            print "| Exited:", self.exit_time, "with code", self.exit_code
        else:
            print
        
        print "  Last updated:", encode_datetime(self.most_recent_event_timestamp)
        
        for p in self.phases:
            p.printMe()
    
    
    def serialize(self):
        """
        Method that serializes process for MongoDB.
        """
        ret = dict(_id=self.unique_id(), # unique ID for MongoDB
                   pid=self.pid,
                   ppid=self.ppid,
                   uid=self.uid,
                   other_uids=self.other_uids,
                   creation_time=encode_datetime(self.creation_time),
                   most_recent_event_timestamp=encode_datetime(self.most_recent_event_timestamp),
                   exited=self.exited,
                   exit_code=self.exit_code,
                   phases=[e.serialize() for e in self.phases])
        
        # ugh ...
        if self.exit_time:
            ret['exit_time'] = encode_datetime(self.exit_time)
        else:
            ret['exit_time'] = None
        
        return ret
    
    
    def mark_exit(self, exit_time, exit_code):
        self.exited = True
        self.exit_time = exit_time
        self.exit_code = exit_code
        
        assert self.creation_time
        
        if (self.exit_time < self.creation_time):
            # OMG there are KRAZY weird situations where timestamps are f***ed
            # up and not in order, so if the exit time appears to be smaller
            # than the creation_time, then loop through all the timestamps
            # in this entry and pick the LARGEST one and just use that as
            # the exit time (since that's the best info we have)
            
            max_time = self.creation_time
            for p in self.phases:
                max_time = max(p.get_latest_timestamp(), max_time)
            
            max_time += 1 # bump it up by 1 so that it doesn't overlap :)
            
            print >> sys.stderr, 'WARNING: exit_time[%d] < creation_time[%d] for PID %d ... patching with %d' % (self.exit_time, self.creation_time, self.pid, max_time)
            self.exit_time = max_time
        
        self._finalize() # finalize and freeze this entry!!!
    
    
    def _mark_changed(self, entry):
        """
        This method should only be called when there has been a VISIBLE change
        to self!
        """
        self.most_recent_event_timestamp = entry.timestamp # VERY important!
    
    
    def add_entry(self, entry):
        """
        Returns True if entry.syscall_name == 'EXIT_GROUP'
        """
        assert entry.pid == self.pid # sanity check
        
        # for setuid executables ...
        if entry.uid != self.uid:
            if self.other_uids:
                if entry.uid not in self.other_uids:
                    self.other_uids.append(entry.uid)
                    self._mark_changed(entry)
            else:
                self.other_uids = [entry.uid]
                self._mark_changed(entry)
        
        assert not self.exited # don't allow ANY more entries after you've exited
        
        
        if (entry.syscall_name in OPEN_VARIANTS):
            # OPEN_ABSPATH always preceeds another OPEN_* entry,
            # or something is wrong ...
            assert self.prev_entry.syscall_name == 'OPEN_ABSPATH'
            # use the ABSOLUTE PATH filename from prev_entry
            filename_abspath = os.path.normpath(self.prev_entry.filename_abspath)
            
            # ok this check is a bit too harsh ... issue a WARNING if it fails
            # rather than dying.  sometimes 'close' system calls get LOST, so
            # just assume that the previous file has been closed if this new
            # one is opened with the same fd
            #assert entry.fd not in self.opened_files
            if entry.fd in self.opened_files:
                print >> sys.stderr, "WARNING: On OPEN, fd", entry.fd, "is already being used by", self.opened_files[entry.fd]
            
            # Resolving symbolic links
            
            symlink = False
            filename = os.path.normpath(entry.filename)
            if self.wdir:
                if not os.path.isabs(filename):
                    filename = os.path.normpath(os.path.join(self.wdir, filename))
                if (filename != filename_abspath):
                    # we have a symlink!
                    symlink = True
            
            # Files are being added here!
            # For the reproducibility tool, the timestamp does not matter,
            # but it is important to know that the timestamp being added
            # here is WRONG!
            
            ignore = False
            for d in IGNORE_DIRS:
                if filename_abspath.startswith(d):
                    ignore = True
                    break
                
            args = (entry.proc_name, entry.timestamp, filename)
            args_symlink = (entry.proc_name, filename, filename_abspath)
            
            if entry.syscall_name == 'OPEN_READ':
                self.opened_files[entry.fd] = (filename_abspath, 'r')
                if not ignore:
                    self.phases[-1].add_file_read(*args)
                    if symlink:
                        self.phases[-1].add_symlink(*args_symlink)
            elif entry.syscall_name == 'OPEN_WRITE':
                self.opened_files[entry.fd] = (filename_abspath, 'w')
                if not ignore:
                    self.phases[-1].add_file_write(*args)
                    if symlink:
                        self.phases[-1].add_symlink(*args_symlink)
            elif entry.syscall_name == 'OPEN_READWRITE':
                self.opened_files[entry.fd] = (filename_abspath, 'rw')
                if not ignore:
                    self.phases[-1].add_file_read(*args)
                    self.phases[-1].add_file_write(*args)
                    if symlink:
                        self.phases[-1].add_symlink(*args_symlink)
            else:
                assert False
                
        elif (entry.syscall_name in OPEN_AT_VARIANTS):
            assert self.prev_entry.syscall_name == 'OPEN_ABSPATH'
            filename_abspath = os.path.normpath(self.prev_entry.filename_abspath)
            
            if entry.fd in self.opened_files:
                print >> sys.stderr, "WARNING: On OPEN, fd", entry.fd, "is already being used by", self.opened_files[entry.fd]
            
            # Resolving symbolic links
            symlink = False
            filename = os.path.normpath(entry.filename)
            if not os.path.isabs(filename):
                d_filename = os.path.normpath(entry.d_filename)
                if not os.path.isabs(d_filename):
                    return False
                filename = os.path.normpath(os.path.join(d_filename, filename))
            if (filename != filename_abspath):
                # we have a symlink!
                symlink = True
            
            ignore = False
            for d in IGNORE_DIRS:
                if filename_abspath.startswith(d):
                    ignore = True
                    break
                
            args = (entry.proc_name, entry.timestamp, filename)
            args_symlink = (entry.proc_name, filename, filename_abspath)
            
            if entry.syscall_name == 'OPEN_AT_READ':
                self.opened_files[entry.fd] = (filename_abspath, 'r')
                if not ignore:
                    self.phases[-1].add_file_read(*args)
                    if symlink:
                        self.phases[-1].add_symlink(*args_symlink)
            elif entry.syscall_name == 'OPEN_AT_WRITE':
                self.opened_files[entry.fd] = (filename_abspath, 'w')
                if not ignore:
                    self.phases[-1].add_file_write(*args)
                    if symlink:
                        self.phases[-1].add_symlink(*args_symlink)
            elif entry.syscall_name == 'OPEN_AT_READWRITE':
                self.opened_files[entry.fd] = (filename_abspath, 'rw')
                if not ignore:
                    self.phases[-1].add_file_read(*args)
                    self.phases[-1].add_file_write(*args)
                    if symlink:
                        self.phases[-1].add_symlink(*args_symlink)
            else:
                assert False
                
        elif entry.syscall_name == 'SYMLINK':
            symlink = os.path.normpath(entry.symlink)
            target = os.path.normpath(entry.target)
            pwd = os.path.normpath(entry.pwd)
            
            if not os.path.isabs(symlink):
                if not os.path.isabs(pwd):
                    return False
                symlink = os.path.join(pwd, symlink)
                if not os.path.exists(symlink):
                    return False
            
            for d in IGNORE_DIRS:
                if symlink.startswith(d):
                    return False 
            
            args = (entry.proc_name, entry.timestamp, symlink)
            # file
            if not os.path.isdir(symlink):
                self.phases[-1].add_file_read(*args)
                if not os.path.isabs(target):
                    target = os.path.realpath(symlink)
                args_symlink = (entry.proc_name, symlink, target)
                self.phases[-1].add_symlink(*args_symlink)
            # dir
            else:
                self.phases[-1].add_dir(*args)
                    
        elif entry.syscall_name == 'SYMLINK_AT':
            symlink = os.path.normpath(entry.symlink)
            target = os.path.normpath(entry.target)
            if not os.path.isabs(symlink):
                d_filename = os.path.normpath(entry.d_filename)
                if not os.path.isabs(d_filename):
                    return False
                symlink = os.path.normpath(os.path.join(d_filename, symlink))
                if not os.path.exists(symlink):
                    return False
                
            for d in IGNORE_DIRS:
                if symlink.startswith(d):
                    return False 
                
            args = (entry.proc_name, entry.timestamp, symlink)
            # file
            if not os.path.isdir(symlink):
                self.phases[-1].add_file_read(*args)
                if not os.path.isabs(target):
                    target = os.path.realpath(symlink)
                args_symlink = (entry.proc_name, symlink, target)
                self.phases[-1].add_symlink(*args_symlink)
            # dir
            else:
                self.phases[-1].add_dir(*args)
                
        elif entry.syscall_name in ('STAT', 'ACCESS', 'TRUNCATE'):
            filename = os.path.normpath(entry.filename)
            if os.path.isabs(filename) and os.path.exists(filename):
                
                for d in IGNORE_DIRS:
                    if filename.startswith(d):
                        return False 
                
                args = (entry.proc_name, entry.timestamp, filename)
                # file
                if not os.path.isdir(filename):
                    self.phases[-1].add_file_read(*args)
                    if os.path.islink(filename):
                        args_symlink = (entry.proc_name, filename, os.path.realpath(filename))
                        self.phases[-1].add_symlink(*args_symlink)
                # dir
                else:
                    self.phases[-1].add_dir(*args)
                    
        elif entry.syscall_name in ('STAT_AT', 'ACCESS_AT'):
            filename = os.path.normpath(entry.filename)
            if not os.path.isabs(filename):
                d_filename = os.path.normpath(entry.d_filename)
                if not os.path.isabs(d_filename):
                    return False
                filename = os.path.normpath(os.path.join(d_filename, filename))
                
            for d in IGNORE_DIRS:
                if filename.startswith(d):
                    return False 
                
            args = (entry.proc_name, entry.timestamp, filename)
            # file
            if not os.path.isdir(filename):
                self.phases[-1].add_file_read(*args)
                if os.path.islink(filename):
                    args_symlink = (entry.proc_name, filename, os.path.realpath(filename))
                    self.phases[-1].add_symlink(*args_symlink)
            # dir
            else:
                self.phases[-1].add_dir(*args)
        
        elif entry.syscall_name == 'DUP' or entry.syscall_name == 'DUP2':
            # 'close' dst_fd if necessary
            if entry.dst_fd in self.opened_files:
                del self.opened_files[entry.dst_fd]
            
            # do the fd duplication!
            if entry.src_fd in self.opened_files:
                self.opened_files[entry.dst_fd] = self.opened_files[entry.src_fd]
        
        elif entry.syscall_name == 'CLOSE':
            # ignore CLOSE calls that don't match a corresponding OPEN
            if entry.fd in self.opened_files:
#                # file was processed before (read, written, ...)
#                if entry.fd in self.processed_files:
#                    del self.processed_files[entry.fd]
#                # file was not processed before
#                # include this file anyway (for purposes of reproducibility)
#                else:
#                    (fn, mode) = self.opened_files[entry.fd]
#                    
#                    # ignoring dirs
#                    ignore = False
#                    for d in IGNORE_DIRS:
#                        if fn.startswith(d):
#                            ignore = True
#                            break
#                            
#                    if not ignore:
#                        args = (entry.proc_name, entry.timestamp, fn)
#                        
#                        if mode == 'r':
#                            self.phases[-1].add_file_read(*args)
#                        elif mode == 'w':
#                            self.phases[-1].add_file_write(*args)
#                        else: # rw
#                            self.phases[-1].add_file_read(*args)
#                            self.phases[-1].add_file_write(*args)
#                    
                del self.opened_files[entry.fd]
            else:
                #print >> sys.stderr, 'WARNING: orphan', entry.syscall_name, entry.pid, entry.proc_name, entry.fd
                pass
        
        elif entry.syscall_name in RW_VARIANTS:
            try:
                (fn, mode) = self.opened_files[entry.fd]
                
                skip_me = False
                # ignore reads to filenames that start with IGNORE_DIRS
                for d in IGNORE_DIRS:
                    if fn.startswith(d):
                        skip_me = True
                        break
                
                if not skip_me:
                    args = (entry.proc_name, entry.timestamp, fn)
                    
                    if entry.syscall_name in ('READ', 'MMAP_READ'):
                        assert mode == 'r' or mode == 'rw'
                        self.phases[-1].add_file_read(*args)
                        #self.processed_files[entry.fd] = True
                    elif entry.syscall_name in ('WRITE', 'MMAP_WRITE'):
                        assert mode == 'w' or mode == 'rw', entry
                        self.phases[-1].add_file_write(*args)
                        #self.processed_files[entry.fd] = True
                    elif entry.syscall_name == 'MMAP_READWRITE':
                        self.phases[-1].add_file_read(*args)
                        # sometimes there are weird MMAP_READWRITE calls when the file
                        # is opened in 'r' mode, so only do add_file_write() if the
                        # file was actually opened in 'w' or 'rw' mode
                        if mode == 'w' or mode == 'rw':
                            self.phases[-1].add_file_write(*args)
                        #self.processed_files[entry.fd] = True
                    
                    self._mark_changed(entry)
            except KeyError:
                # ignore READ/WRITE calls where the fd isn't found!
                #print >> sys.stderr, 'WARNING: orphan', entry.syscall_name, entry.pid, entry.proc_name, entry.fd
                pass
        
        elif entry.syscall_name == 'RENAME':
            self.phases[-1].add_file_rename(entry.proc_name, entry.timestamp, entry.old_filename, entry.new_filename)
            self._mark_changed(entry)
        
        elif entry.syscall_name == 'EXIT_GROUP':
            self.mark_exit(entry.timestamp, entry.exit_code)
            self._mark_changed(entry)
            return True
        
        elif entry.syscall_name == 'EXECVE':
            # Optimization: REMOVE previous phase if it was empty:
            if self.phases and self.phases[-1].is_empty():
                self.phases.pop()
        
            n = ProcessPhase(entry.timestamp, entry.exec_filename, entry.pwd, entry.argv, entry.env)
            self.phases.append(n)
            self._mark_changed(entry)
            
            # working directory
            self.wdir = entry.pwd
            
        elif entry.syscall_name == 'CHDIR':
            # updating working directory
            if os.path.isabs(entry.path):
                self.wdir = os.path.normpath(entry.path)
            else:
                if self.wdir:
                    self.wdir = os.path.normpath(os.path.join(self.wdir, entry.path))
        
        elif entry.syscall_name == 'PIPE':
            assert entry.pipe_read_fd not in self.opened_files # sanity check
            assert entry.pipe_write_fd not in self.opened_files # sanity check
            # PIPE creates two new file descriptors ...
            # (encode the pid and fd in the pseudo-filename of the pipe)
            self.opened_files[entry.pipe_read_fd] =  ('PIPE-%d-%d' % (self.pid, entry.pipe_read_fd), 'r')
            self.opened_files[entry.pipe_write_fd] = ('PIPE-%d-%d' % (self.pid, entry.pipe_write_fd), 'w')
            
#            self.processed_files[entry.pipe_read_fd] = True
#            self.processed_files[entry.pipe_read_fd] = True
            
            self.opened_pipes.add((self.pid, entry.pipe_read_fd, entry.pipe_write_fd))
        
        elif entry.syscall_name == 'FORK':
            # add a Process object for your offspring ...
            if entry.child_pid not in self.active_processes_dict:
                child_proc = Process(entry.child_pid, self.pid, entry.uid, entry.timestamp, self.active_processes_dict)
                
                # child inherits fd's and pipes from parent ... make a deepcopy!
                child_proc.opened_files = deepcopy(self.opened_files)
                child_proc.opened_pipes = deepcopy(self.opened_pipes)
            else:
                # This shouldn't happen if the SystemTap logs were perfect, but
                # in reality, some entries come in slightly OUT OF ORDER, so if
                # entry.child_pid is already in self.active_processes_dict, then
                # just trust that entry!
                #print >> sys.stderr, "WARNING: fork() child PID", entry.child_pid, "already exists!"
                pass
        
        self.prev_entry = entry # set previous entry for reference
        return False
    