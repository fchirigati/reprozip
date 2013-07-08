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

# This code stores process information in a centralized MongoDB database

'''
Collections within MongoDB reprozip_db:

reprozip_db.process_trace
  - contains the cleaned output from pass-lite.out.*
  - _id is a concatenation of creation timestamp and PID
  - most_recent_event_timestamp is the most recent time that this
    process entry was updated

reprozip_db.session_status
  - _id:               unique session tag
  - last_updated_time: timestamp of last update to this session
'''

import os
import sys
import datetime

from reprozip.pack.system_tap import Process, parse_raw_pass_lite_line
from reprozip.utils import *
import reprozip.debug

from pymongo import MongoClient, ASCENDING

class Provenance:
    """
    The class Provenance deals with integrating data from the process
    trace to a MongoDB collection.
    """
    
    def __init__(self):
        """
        Init method for Provenance.
        """
          
        # prefix of the process trace file
        self.file = 'pass-lite.out'

        # Dict mapping PIDs to active processes (i.e., haven't yet exited)
        # Key: PID
        # Value: Process object
        self.pid_to_active_processes = {}

        # the PARENT pids of all exited processes
        self.exited_process_ppids = set()
        
        # tag for current session
        self.session_tag = None
        
        # current directory for storing log
        self.logdir = None
        
        self.session_status_col = None
        self.proc_col = None


    def save_tagged_db_entry(self, col, json_entry):
        json_entry['session_tag'] = self.session_tag
        col.save(json_entry) # does an insert (if not-exist) or update (if exists)


    def gen_entries_from_multifile_log(self):
        """
        Parses the log file one line at a time.
        """
        
        fullpath = os.path.join(self.logdir, self.file)
    
        if not os.path.isfile(fullpath):
            reprozip.debug.error('Could not find file %s' %fullpath)
            raise Exception
    
        # opening trace file
        f = open(fullpath)
        for (line_no, line) in enumerate(f):
            try:
                entry = parse_raw_pass_lite_line(line.rstrip())      
                yield entry
            except:
                reprozip.debug.error('Could not parse the log file: %s' %sys.exc_info()[1])
                f.close()
                raise Exception


    def exit_handler(self):
        
        cur_time = get_ms_since_epoch()
        self.session_status_col.save({'_id': self.session_tag,
                                      'last_updated_time': datetime.datetime.now()})
        
        # now make all active processes into exited processes since our
        # session has ended!
        # TODO: is this really necessary!?
        for p in self.pid_to_active_processes.values():
            p.mark_exit(cur_time, -1) # use a -1 exit code to mark that it was "rudely" killed
            self.handle_process_exit_event(p)


    ### pass-lite logs ###
    
    def handle_process_exit_event(self, p):
        assert p.exited
        
        del self.pid_to_active_processes[p.pid]
        self.proc_col.remove({'_id': p.unique_id()}) # remove and later (maybe) re-insert
        
        skip_me = False
        
        # Optimization: if this process is 'empty' (i.e., has no phases)
        # and isn't the parent of any previously-exited process or
        # currently-active process, then there is NO POINT in storing it
        # into the database.
#        if (not p.phases):
#            active_process_ppids = set()
#            for p in self.pid_to_active_processes.itervalues():
#                active_process_ppids.add(p.ppid)
#            if (p.pid not in self.exited_process_ppids) and (p.pid not in active_process_ppids):
#                skip_me = True
        
        if not skip_me:
            self.save_tagged_db_entry(self.proc_col, p.serialize())
            self.exited_process_ppids.add(p.ppid)


    def index_pass_lite_logs(self):
    
        entries = self.gen_entries_from_multifile_log()
        
        try:
            for pl_entry in entries:
                if pl_entry.pid not in self.pid_to_active_processes:
                    # remember, creating a new process adds it to
                    # the pid_to_active_processes dictionary
                    p = Process(pl_entry.pid, pl_entry.ppid, pl_entry.uid,
                                pl_entry.timestamp, self.pid_to_active_processes)
                    assert self.pid_to_active_processes[pl_entry.pid] == p # sanity check
                else:
                    p = self.pid_to_active_processes[pl_entry.pid]
                
                is_exited = p.add_entry(pl_entry)
                if is_exited:
                    self.handle_process_exit_event(p)
            
            for p in self.pid_to_active_processes.itervalues():
                self.save_tagged_db_entry(self.proc_col, p.serialize())
        except:
            reprozip.debug.error('Error while parsing entries: %s' %sys.exc_info()[1])
            raise Exception


    def do_index(self):
        
        self.index_pass_lite_logs()
        
        self.session_status_col.save({'_id': self.session_tag,
                                      'last_updated_time': encode_datetime(get_ms_since_epoch())})
    
    
    def store(self, logdir, session_tag, port):
        """
        Main method that stores the provenance data in MongoDB.
        """
        
        self.logdir = logdir
        self.session_tag = session_tag
    
        # connecting to mongodb
        try:
            c = MongoClient(port=int(port))
            db = c.reprozip_db
        except:
            reprozip.debug.error('Could not connect to MongoDB: %s' %sys.exc_info()[1])
            raise Exception
        
        self.proc_col = db.process_trace
        self.session_status_col = db.session_status
        
        self.proc_col.remove({"session_tag": self.session_tag})
        self.session_status_col.remove({"_id": self.session_tag})
        
        # Creating indices
        # TODO: create indices every time?
        self.proc_col.ensure_index('pid')
        self.proc_col.ensure_index('exited')
        self.proc_col.ensure_index('most_recent_event_timestamp')
        self.proc_col.ensure_index('session_tag')
        
        # For time range searches!  This multi-key index ensures fast
        # searches for creation_time alone too!
        self.proc_col.ensure_index([('creation_time', ASCENDING), ('exit_time', ASCENDING)])
        
        self.proc_col.ensure_index('phases.name')
        self.proc_col.ensure_index('phases.start_time')
        self.proc_col.ensure_index('phases.files_read.timestamp')
        self.proc_col.ensure_index('phases.files_written.timestamp')
        self.proc_col.ensure_index('phases.files_renamed.timestamp')
        
        # storing everything
        try:
            self.do_index()
        except:
            raise Exception
        
        # exiting
        self.exit_handler()
