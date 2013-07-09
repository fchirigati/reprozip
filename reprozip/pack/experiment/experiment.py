###############################################################################
##
## Copyright (C) 2012-2013, NYU-Poly. 
## All rights reserved.
## Contact: fchirigati@nyu.edu
##
## This file is part of ReproZip.
##
## "Redistribution and use in source and binary forms, with or without 
## modification, are permitted provided that the following conditions are met:
##
##  - Redistributions of source code must retain the above copyright notice, 
##    this list of conditions and the following disclaimer.
##  - Redistributions in binary form must reproduce the above copyright 
##    notice, this list of conditions and the following disclaimer in the 
##    documentation and/or other materials provided with the distribution.
##  - Neither the name of NYU-Poly nor the names of its 
##    contributors may be used to endorse or promote products derived from 
##    this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
## AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
## THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; 
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
###############################################################################

from reprozip.pack.vt_workflow.workflow import VTWorkflow
from reprozip.pack.vt_workflow.cltools_wrapper import Wrapper
from reprozip.pack.tree.provenance_tree import Node, ProvenanceTree
from reprozip.install.utils import guess_sudo
import reprozip.debug
import reprozip.utils
import reprozip.install
import shutil
import stat
import pickle
import fnmatch
import platform
import subprocess
import time
import pymongo
import sys
import os
import tarfile

class Experiment:
    """
    The class Experiment represents an experiment to be reproducible.
    Note: information about the experiment is retrieved in a MongoDB collection.
    """
    
    def __init__(self):
        """
        Init method for Experiment.
        """
        
        # dependencies
        self.__dependencies = {} # 'key' is original file, and 'value' is the new file
        self.__exclude_dependencies = []
        
        # input files
        self.__input_files = {} # 'key' is original file, and 'value' is the new file
        self.__child_input_files = {} # 'key' is original file, and 'value' is the new file
        self.__exclude_input_files = []
        self.__exclude_child_input_files = []
        
        # output files
        self.__output_files = []
        
        # directories
        self.__dirs = {}
        
        # configuration files
        self.__config_files = {}
        
        # symbolic links
        self.__symlink_to_target = {}
        self.__symlink_chain = {} # 'key' is the first symbolic link, and 'value' is a list containing the chain
        self.__symlink_dir = {} # 'key' is a symbolic link, and 'value' is a chain of directory symbolic links necessary for the 'key'
        self.__targets = {} # 'key' is original file, and 'value' is the new file
        
        # programs
        self.__main_program = {}
        self.__child_programs = {}
        self.__exclude_main_program = []
        self.__exclude_child_programs = []
        
        # start time of the experiment
        self.__start_time = None
        
        # environment variables
        self.__env = {}
        
        # provenance tree
        self.__prov_tree = ProvenanceTree()
        
        # last modified time of configuration file
        self.__config_mtime = None
        
        # information about the experiment, used to retrieve experiment data
        self.__command_line_info = None
        
        # directory for the reproducible experiment
        self.__rep_dir = None
        
        # directory for the reproducible experiment in the reproducer's machine
        self.__user_dir = None
        
        # verbose option
        self.__verbose = False


    def get_verbose(self):
        return self.__verbose


    def set_verbose(self, value):
        self.__verbose = value


    def get_command_line_info(self):
        return self.__command_line_info


    def set_command_line_info(self, value):
        self.__command_line_info = value
    
    
    command_line_info = property(get_command_line_info, set_command_line_info,
                                 None, None)
    verbose = property(get_verbose, set_verbose, None, None)
    
    
#    def verbose_(self, args):
#        """
#        Verbose method.
#        """
#        if self.verbose:
#            for arg in args:
#                print arg
#        else:
#            pass
    
    
    def execute(self, working_dir, env):
        """
        Method used to execute the experiment. It also records the data for
        the experiment.
        """
            
        args = self.command_line_info.split()

        print 'Executing the program...\n'
        print '################################################################'

        try:
            p = subprocess.Popen(args, env=env,
                                 cwd=working_dir)
        except:
            reprozip.debug.error('Could not execute the command line of the program: %s' %sys.exc_info()[1])
            raise Exception
        
        returncode = p.wait()
        
        print '################################################################\n'
        
        if (returncode != 0):
            reprozip.debug.error('Error while executing the command line.')
            raise Exception
        
    
    def retrieve_experiment_data(self, db_name, collection_name, port):
        """
        Method used to retrieve the information about the experiment.
        This information is obtained in a MongoDB collection.
        """
        
        # connecting to Mongo
        reprozip.debug.verbose(self.verbose, 'Connecting to MongoDB...')
        try:
            conn = pymongo.MongoClient(port=int(port))
        except:
            reprozip.debug.error('Could not connect to MongoDB: %s' %sys.exc_info()[1])
            raise Exception
    
        # accessing the database
        reprozip.debug.verbose(self.verbose, 'Accessing the database...')
        try:
            db = conn[db_name]
        except:
            reprozip.debug.error('Could not open the database: %s' %sys.exc_info()[1])
            conn.close()
            raise Exception
    
        # accessing the collection
        reprozip.debug.verbose(self.verbose, 'Accessing the collection...')
        try:
            collection = db[collection_name]
        except:
            reprozip.debug.error('Could not access the collection: %s' %sys.exc_info()[1])
            conn.close()
            raise Exception
            
        reprozip.debug.verbose(self.verbose, 'Querying the collection...')
        l_args = self.command_line_info.split()
        for i in range(len(l_args)):
            l_args[i] = '\"' + l_args[i] + '\"'
        n_argument = ' '.join(l_args)
        n_argument = n_argument[:-1]
        cursor = collection.find({'phases.execve_argv':
                                  {'$regex': n_argument + '.*' }})
            
        # sorting the results
        cursor = cursor.sort('creation_time', pymongo.DESCENDING)
        
        # getting one record (assuming that the most recent record is the valid one)
        # also, if there was an error with the execution, the record is discarded
        len_cursor = cursor.count()
        if (len_cursor == 0):
            print '** No results found **'
            conn.close()
            raise Exception
        
        exec_wf = cursor[0]
            
        # getting information from the main program
        pid = int(exec_wf['pid'])
        self.__start_time = exec_wf['creation_time']
        
        # if main process has more than one phase, we need to know the 'main'
        # phase
        reprozip.debug.verbose(self.verbose, 'Getting information of main process...')
        
        execve_argv = ''
        main_phase_index = None
        for i in range(len(exec_wf['phases'])):
            execve_argv = str(exec_wf['phases'][i]['execve_argv'])
            execve_argv = execve_argv.replace('\"','')
            
            execve_argv = ' '.join(execve_argv.split())
            command_line = ' '.join(self.command_line_info.split())            
            
            if execve_argv == command_line:
                main_phase_index = i
                break
            
        if main_phase_index == None:
            reprozip.debug.error('No phases found. This should not happen...')
            conn.close()
            raise Exception
        
        execve_pwd = str(exec_wf['phases'][main_phase_index]['execve_pwd'])
        
        execve_env = str(exec_wf['phases'][main_phase_index]['execve_env'])
        
        dirs = exec_wf['phases'][main_phase_index]['directories'] or [] # list of dictionaries
        
        files_read = exec_wf['phases'][main_phase_index]['files_read'] or [] # list of dictionaries
        
        files_written = exec_wf['phases'][main_phase_index]['files_written'] or [] # list of dictionaries
        
        symlinks = exec_wf['phases'][main_phase_index]['symlinks'] or [] # list of dictionaries
        
        # creating root node and adding it to the provenance tree
        root_node = Node(None)
        root_node.pid = pid
        root_node.set_execve_pwd(execve_pwd)
        root_node.set_execve_argv(execve_argv)
        root_node.set_execve_env(execve_env)
        root_node.set_files_read(files_read)
        root_node.set_files_written(files_written)
        root_node.set_dirs(dirs)
        root_node.set_symlink_to_target(symlinks)
        
#        self.verbose_(['main execve_argv: %s' %root_node.execve_argv,
#                       'main execve_pwd: %s' %root_node.execve_pwd,
#                       'main execve_env: %s' %str(root_node.execve_env),
#                       'main files_read: %s' %str(root_node.files_read),
#                       'main files_written: %s' %str(root_node.files_written),
#                       'main symlinks: %s\n' %str(root_node.symlink_to_target)])
        
        # setting the root node
        self.__prov_tree.set_root(root_node)
        
        # other phases of main process are included as child nodes of the root
        # node
        # ideally, this is not the perfect solution, but it works
        reprozip.debug.verbose(self.verbose, 'Getting additional information of main process...')
        
        phase_added = False
        for i in range(len(exec_wf['phases'])):
            if i != main_phase_index:
                execve_argv = str(exec_wf['phases'][i]['execve_argv'])
                execve_argv = execve_argv.replace('\"','')
                
                execve_pwd = str(exec_wf['phases'][i]['execve_pwd'])
                
                execve_env = str(exec_wf['phases'][i]['execve_env'])
                
                files_read = exec_wf['phases'][i]['files_read'] or []
                
                files_written = exec_wf['phases'][i]['files_written'] or []
                
                dirs = exec_wf['phases'][i]['directories'] or []
                
                symlinks = exec_wf['phases'][i]['symlinks'] or []
                
                if execve_argv == 'None':
                    continue
                
                phase_added = True
                
                node = Node(0)
                node.pid = pid
                node.set_execve_pwd(execve_pwd)
                node.set_execve_argv(execve_argv)
                node.set_execve_env(execve_env)
                node.set_files_read(files_read)
                node.set_files_written(files_written)
                node.set_dirs(dirs)
                node.set_symlink_to_target(symlinks)
                
                self.__prov_tree.add_node(node)
        
        # finding child processes
        reprozip.debug.verbose(self.verbose, 'Getting information of child processes...')
        try:
            height = self.__get_child_processes(0, collection)
        except:
            reprozip.debug.error('Error while getting information of child processes: %s' %sys.exc_info()[1])
            raise Exception
        
        if (height == 0) and phase_added:
            height = 1
        
        # updating height of the tree
        self.__prov_tree.height = height
                
        conn.close()
        
        # updating root information
        reprozip.debug.verbose(self.verbose, 'Updating and traversing provenance tree...')
        if self.__prov_tree.height > 0:
            self.__prov_tree.update_root_information()
            
#        for node in self.__prov_tree.nodes:
#            print self.__prov_tree.nodes[node].execve_argv
#        print len(self.__prov_tree.nodes)

        # environment variables
        self.__env = self.__prov_tree.root.execve_env
        
        # main program
        self.__main_program[self.__prov_tree.root.program] = None
        
        # input files from main program
        self.__input_files = dict((input_file, None) for input_file in self.__prov_tree.root.input_files)
        
        # output files from main program
        self.__output_files = dict((output_file, None) for output_file in self.__prov_tree.root.output_files)
        
        # directories
        self.__dirs = dict((dir, None) for dir in self.__prov_tree.root.dirs)
        
        # mapping from symbolic links to target files
        self.__symlink_to_target = self.__prov_tree.root.symlink_to_target
        
        # child programs
        # also getting their input files
        child_input_files = []
        child_programs = []
        for id in self.__prov_tree.nodes:
            if id != 0:
                node = self.__prov_tree.nodes[id]
                input_files = node.input_files
                child_input_files += input_files
                if node.program:
                    child_programs.append(node.program)
                
        # assuring no intersection between child input files and main input files
        child_input_files = list(set(child_input_files) -
                                 set(self.__input_files.keys()))
        
        # assuring no intersection between dependencies and child input files
        dependencies = list(set(self.__prov_tree.root.dependencies) -
                            set(child_input_files))
        self.__dependencies = dict((dependency, None) for dependency in dependencies)
        
        # child programs and input files
        self.__child_input_files = dict((input_file, None) for input_file in child_input_files)
        self.__child_programs = dict((program, None) for program in child_programs)
        
        # function to remove duplicates of a list
#         def remove_duplicates(l):
#            no_duplicates = []
#            for e in l:
#                if e not in no_duplicates:
#                    no_duplicates.append(e)
#            return no_duplicates
        
        # assuring the symbolic links are really symbolic links (sanity check)
        # also getting long chains of symbolic links
        reprozip.debug.verbose(self.verbose, 'Identifying symbolic links...')
        exclude_symlink = []
        try:
            for symlink in self.__symlink_to_target:
                if not os.path.islink(symlink):
                    exclude_symlink.append(symlink)
                    continue
                target = self.__symlink_to_target[symlink]
                path = symlink
                chain = [symlink]
                dir_chain = []
                while (os.path.realpath(path) != os.path.normpath(path)):
                    if not os.path.islink(path):
                        # we have a directory that is a symbolic link!
                        common_prefix = os.path.commonprefix([path, os.path.realpath(path)])
                        sub_dirs = path.replace(common_prefix, '').split(os.sep)
                        dir_link = common_prefix
                        while sub_dirs != []:
                            dir_link = os.path.normpath(os.path.join(dir_link, sub_dirs[0]))
                            sub_dirs.pop(0)
                            if os.path.islink(dir_link):
                                if dir_chain == []:
                                    dir_chain.append(dir_link)
                                elif dir_chain[-1] != dir_link:
                                    dir_chain.append(None)
                                    dir_chain.append(dir_link)
                                next_target = os.readlink(dir_link)
                                if not os.path.isabs(next_target):
                                    next_target = os.path.normpath(os.path.join(os.path.dirname(dir_link), next_target))
                                dir_chain.append(next_target)
                                path = os.path.normpath(os.path.join(next_target, os.sep.join(sub_dirs)))
                                chain.append(None)
                                chain.append(path)
                                break
                        if sub_dirs == []:
                            reprozip.debug.error("Something is wrong...")
                            break
                    else:
                        next_target = os.readlink(path)
                        if not os.path.isabs(next_target):
                            next_target = os.path.normpath(os.path.join(os.path.dirname(path), next_target))
                        chain.append(next_target)
                        path = next_target
                if len(chain) < 3:
                    continue
                if (path != target):
                    reprozip.debug.error("Something is wrong...")
                    
                self.__symlink_chain[symlink] = chain
                if dir_chain != []:
                    self.__symlink_dir[symlink] = dir_chain
        except:
            reprozip.debug.error('Problem while retrieving symbolic link information: %s' %sys.exc_info()[1])
            raise Exception
        
        for symlink in exclude_symlink:
            self.__symlink_to_target.pop(symlink)
            
    
    def configure(self):
        """
        Method to configure the experiment to be packed.
        """
        
        # working directory of main program
        # this directory will be used to find a common directory structure
        # between programs and files
        wdir = self.__prov_tree.root.execve_pwd
        
        ########################################################################
        
        # function that takes care of including the necessary files in the
        # reproducible package
        def add_rep_file(file, file_dict):
            """
            file      -> file to be added
            file_dict -> dictionary containing the file
            """
            
            file_ = file
            if file_.startswith(os.sep):
                file_ = file_[1:]
            file_dict[file] = os.path.join(reprozip.utils.exp_dir, file_)
               
            # symbolic links
            if self.__symlink_to_target.has_key(file):
                target = self.__symlink_to_target[file]
                self.__targets[target] = None
                add_rep_file(target, self.__targets)
                        
        ########################################################################
        
        # child programs
        reprozip.debug.verbose(self.verbose, 'Configuring child programs...')
        for program in self.__child_programs:
            add_rep_file(program, self.__child_programs)
                    
        # main program
        reprozip.debug.verbose(self.verbose, 'Configuring main program...')
        add_rep_file(self.__main_program.keys()[0], self.__main_program)
        
        # main input files
        reprozip.debug.verbose(self.verbose, 'Configuring main input files...')
        for input_file in self.__input_files:
            add_rep_file(input_file, self.__input_files)
                        
        # child input files
        reprozip.debug.verbose(self.verbose, 'Configuring child input files...')
        for input_file in self.__child_input_files:
            add_rep_file(input_file, self.__child_input_files)
            
        # directories
        reprozip.debug.verbose(self.verbose, 'Configuring directories...')
        for dir in self.__dirs:
            add_rep_file(dir, self.__dirs)
                    
        # trying to identify implicit input files among dependencies
        # a dependency is considered an implicit input file if it is
        # located together with other input files (considering the working
        # directory of the main program as the common structure) 
        # implicit input files are put together with child input files
        reprozip.debug.verbose(self.verbose, 'Configuring dependencies...')
        
        rm_dependencies = []
        for dependency in self.__dependencies:
            l = [dependency, wdir]
            common_prefix = os.path.normpath(os.path.commonprefix(l))
            if not os.path.exists(common_prefix):
                common_prefix = os.path.dirname(common_prefix)
            
            # if there is no common_prefix
            if (common_prefix == '') or (common_prefix == os.sep):
                continue
            
            # if there is a common prefix
            else:
                self.__child_input_files[dependency] = None
                rm_dependencies.append(dependency)
                
                add_rep_file(dependency, self.__child_input_files)
                
        for rm_dependency in rm_dependencies:
            self.__dependencies.pop(rm_dependency)

        # dependencies
        # dependencies are libraries and possible include files
        for dependency in self.__dependencies:
            add_rep_file(dependency, self.__dependencies)
            
#        self.verbose_(['input files: %s' %str(self.__input_files),
#                       'output files: %s' %str(self.__output_files),
#                       'main program: %s' %str(self.__main_program),
#                       'child programs: %s' %str(self.__child_programs),
#                       'child input files: %s' %str(self.__child_input_files),
#                       'dependencies: %s' %str(self.__dependencies)])

        # generate configuration file
        reprozip.debug.verbose(self.verbose, 'Writing configuration file...')
        self.__gen_config_file()
        
        
    def process_config_file(self):
        """
        Method to read and process the configuration file.
        """
        
        reprozip.debug.verbose(self.verbose, 'Reading configuration file...')
        
        if not os.path.exists(reprozip.utils.config_path):
            reprozip.debug.error('Configuration file not found in %s' % os.path.dirname(reprozip.utils.config_path))
            reprozip.debug.error('Make sure you are in the right directory.')
            sys.exit(1)
            
        # if configuration file was not modified, do not need to process it
        if os.path.getmtime(reprozip.utils.config_path) == self.__config_mtime:
            return
        
        # opening file
        f = open(reprozip.utils.config_path, 'r')
        config_info = f.read().splitlines()
        f.close()
        
        # stripping lines
        for i in range(len(config_info)):
            config_info[i] = config_info[i].strip()
            
        # identifying info
        try:
            main_program_index = config_info.index('[main program]')
        except:
            main_program_index = None
        
        try:
            child_programs_index = config_info.index('[other programs]')
        except:
            child_programs_index = None
            
        try:
            main_input_files_index = config_info.index('[main input files]')
        except:
            main_input_files_index = None
        
        try:
            child_input_files_index = config_info.index('[other input files]')
        except:
            child_input_files_index = None
        
        try:
            dependencies_index = config_info.index('[dependencies]')
        except:
            dependencies_index = None
            
        try:
            exclude_index = config_info.index('[exclude]')
        except:
            exclude_index = None
        
        categories = ['[main program]',
                      '[other programs]',
                      '[main input files]',
                      '[other input files]',
                      '[dependencies]',
                      '[exclude]']
        
        # exclude patterns
        exclude_patterns = []
        if exclude_index != None:
            for i in range(exclude_index + 1, len(config_info), 1):
                if (config_info[i] != '') and (config_info[i][0] != '#'):
                    if config_info[i].lower() in categories:
                        break
                    
                    # getting pattern and annotating files to be excluded
                    pattern = config_info[i].split()[0]
                    exclude_patterns.append(pattern)
                    
        ########################################################################
        
        # function used to update file information taking into account
        # the configuration file
        def update_file_info(index, file_dict, config, categories, exclude):
            """
            'index'      -> index of section
            'file_dict'  -> the dictionary related to the section
            'config'     -> configuration 
            'categories' -> categories of files
            'exclude'    -> list of file patterns that must not be considered
            """
            
            exclude_files = []
            for pattern in exclude:
                matches = fnmatch.filter(file_dict.keys(), pattern)
                for match in matches:
                    exclude_files.append(match)
            
            if index != None:
                for i in range(index + 1, len(config), 1):
                    if (config[i] != '') and (config[i][0] != '#'):
                        if config[i].lower() in categories:
                            break
                            
                        element = config[i].split()
                    
                        # checking first if file was found by the exclude pattern
                        if element[0] in exclude_files:
                            file_dict.pop(element[0])
                            if self.__symlink_to_target.has_key(element[0]):
                                target = self.__symlink_to_target[element[0]]
                                self.__symlink_to_target.pop(element[0])
                                self.__targets.pop(target)
                            continue
                        
                        # include or not
                        if (element[2].lower() != 'y') and (element[2].lower() != 'n'):
                            reprozip.debug.error('Bad configuration file: value "%s" unrecognized' % element[2])
                            sys.exit(1)
                            
                        # configuration files
#                        if (element[3].lower() != 'y') and (element[3].lower() != 'n'):
#                            reprozip.debug.error('Bad configuration file: value "%s" unrecognized' % element[3])
#                            sys.exit(1)
                            
                        include = True
                        if element[2].lower() == 'n':
                            include = False
                            
                        config_file = False
#                        if element[3].lower() == 'y':
#                            config_file = True
                            
                        if not file_dict.has_key(element[0]):
                            # maybe file is a target?
                            if self.__targets.has_key(element[0]):
                                if not include:
                                    self.__targets.pop(element[0])
                                    for symlink in self.__symlink_to_target:
                                        if self.__symlink_to_target[symlink] == element[0]:
                                            self.__symlink_to_target.pop(symlink)
                                elif config_file:
                                    self.__config_files[element[0]] = self.__targets[element[0]]
                                #else:
                                #    self.__targets[element[0]] = element[3]
                                continue
                            reprozip.debug.error('Bad configuration file: file "%s" not found' % element[0])
                            sys.exit(1)
                            
                        if not include:
                            file_dict.pop(element[0])
                            if self.__symlink_to_target.has_key(element[0]):
                                target = self.__symlink_to_target[element[0]]
                                self.__symlink_to_target.pop(element[0])
                                self.__targets.pop(target)
                        elif config_file:
                            if self.__symlink_to_target.has_key(element[0]):
                                target = self.__symlink_to_target[element[0]]
                                self.__config_files[target] = self.__targets[target]
                            else:
                                self.__config_files[element[0]] = file_dict[element[0]]
                        #else:
                        #    file_dict[element[0]] = element[3]
                                
        ########################################################################
        
        reprozip.debug.verbose(self.verbose, 'Processing configuration file...')
        
        # main program
        update_file_info(main_program_index, self.__main_program, config_info,
                         categories, exclude_patterns)
        
        # child programs
        update_file_info(child_programs_index, self.__child_programs, config_info,
                         categories, exclude_patterns)
        
        # main input files
        update_file_info(main_input_files_index, self.__input_files, config_info,
                         categories, exclude_patterns)
        
        # child input files
        update_file_info(child_input_files_index, self.__child_input_files, config_info,
                         categories, exclude_patterns)
        
        # dependencies
        update_file_info(dependencies_index, self.__dependencies, config_info,
                         categories, exclude_patterns)
            
        
    def generate_reproducible_experiment(self, name):
        """
        Method to generate a reproducible package for the experiment.
        """
        
        # name of the module / workflow
        if name:
            main_name = name
        else:
            sep = self.command_line_info.split()
            basename = os.path.basename(sep[0])
            main_name = 'rep-' + basename
            
        self.__user_dir = os.path.join(reprozip.utils.user_dir_var, main_name)
        self.__user_exp_dir = reprozip.utils.exp_dir.replace(reprozip.utils.rep_dir_var, self.__user_dir)
        
        # creating folder for the reproducible experiment
        self.__rep_dir = os.path.join(os.getcwd(), main_name)
        self.__rep_exp_dir = reprozip.utils.exp_dir.replace(reprozip.utils.rep_dir_var, self.__rep_dir)
        if os.path.exists(self.__rep_dir):
            answer = ''
            while answer.upper() != 'Y' and answer.upper() != 'N':
                answer = raw_input('<warning> The folder "%s" already exists. Remove it before creating the new one (Y or N)? ' % self.__rep_dir)
            if answer.upper() == 'N':
                sys.exit(0)
            try:
                shutil.rmtree(self.__rep_dir)
            except:
                reprozip.debug.error('Could not remove previous reproducible folder: %s' %sys.exc_info()[1])
                sys.exit(1)
                
        try:
            os.mkdir(self.__rep_dir)
        except:
            reprozip.debug.error('Could not create reproducible folder: %s' %sys.exc_info()[1])
            sys.exit(1)
            
        argv_dict = self.__prov_tree.root.argv_dict
        
        ########################################################################
                
        def include_file(original_file, rep_file, program=False):
            in_cp_dir = False
            
            # if file does not exist (tmp file), just ignore it
            if not os.path.exists(original_file):
                return (None, in_cp_dir)

            if reprozip.utils.rep_dir_var not in rep_file:
                in_cp_dir = True
                basename = reprozip.utils.sep.join(rep_file.split(os.sep))
                rep_file = os.path.join(reprozip.utils.cp_dir, basename)
            rep_file = os.path.normpath(rep_file.replace(reprozip.utils.rep_dir_var,
                                                         self.__rep_dir))
            try:
                if not os.path.exists(os.path.dirname(rep_file)):
                    os.makedirs(os.path.dirname(rep_file))
                
#                # configuration files
#                if (self.__config_files[original_file]) and (not program):
#                    file_ = self.__config_files[original_file]
#                    f = open(original_file, 'r')
#                    config = f.read()
#                    f.close()
#                    
#                    # this is a very bad approach - change it later
#                    for child_program in self.__child_programs:
#                        config = config.replace(child_program,
#                                                self.__child_programs[child_program].replace(reprozip.utils.rep_dir_var, self.__user_dir))
#                        
#                    for input_file in self.__input_files:
#                        config = config.replace(input_file,
#                                                self.__input_files[input_file].replace(reprozip.utils.rep_dir_var, self.__user_dir))
#                        
#                    for child_input_file in self.__child_input_files:
#                        config = config.replace(child_input_file,
#                                                self.__child_input_files[child_input_file].replace(reprozip.utils.rep_dir_var, self.__user_dir))
#                        
#                    for dep in self.__dependencies:
#                        config = config.replace(dep,
#                                                self.__dependencies[dep].replace(reprozip.utils.rep_dir_var, self.__user_dir))
#                        
#                    f = open(rep_file, 'w')
#                    f.write(config)
#                    f.close()
#                    
#                    self.__config_files[original_file] = file_.replace(reprozip.utils.rep_dir_var, self.__user_dir)
#                    
#                # other files
#                else:
                
                if os.path.isdir(original_file):
                    if os.path.exists(rep_file):
                        return (rep_file, in_cp_dir)
                    os.makedirs(rep_file)
                else:
                    if os.path.exists(rep_file):
                        os.remove(rep_file)
                    shutil.copyfile(original_file, rep_file)
                    
                st = os.stat(original_file)
                os.chmod(rep_file, st.st_mode)
                    
                if program:
#                     shutil.copystat(original_file, rep_file)
                    os.chmod(rep_file, stat.S_IXUSR | stat.S_IXOTH |
                             stat.S_IXGRP | stat.S_IRUSR | stat.S_IROTH |
                             stat.S_IRGRP | stat.S_IWUSR | stat.S_IWOTH |
                             stat.S_IWGRP)
#                     st = os.stat(original_file)
#                     os.chmod(rep_file, st.st_mode | stat.S_IEXEC)
            except:
                reprozip.debug.warning('Could not copy "%s": %s' % (original_file, sys.exc_info()[1]))
                reprozip.debug.warning('Reproducible package will not contain this file.')
                return (None, in_cp_dir)
            
            # symbolic links
            if self.__symlink_to_target.has_key(original_file):
                symlink = original_file
                rep_symlink = rep_file
                target = self.__symlink_to_target[symlink]
                rep_target, target_in_cp_dir = include_file(target, self.__targets[target], program)
                
                if rep_target:
                    if in_cp_dir:
                        rep_symlink = os.sep.join(os.path.basename(rep_symlink).split(reprozip.utils.sep))
                    else:
                        rep_symlink = os.path.join(self.__user_dir, os.path.relpath(rep_symlink, self.__rep_dir))
                    
                    if target_in_cp_dir:
                        rep_target = os.sep.join(os.path.basename(rep_target).split(reprozip.utils.sep))
                    else:
                        rep_target = os.path.join(self.__user_dir, os.path.relpath(rep_target, self.__rep_dir))
                    
                    # chain of symbolic links
                    # not the best place to handle that, but ok...
                    if self.__symlink_chain.has_key(original_file):
                        chain = self.__symlink_chain[original_file]
                        self.__symlink_chain.pop(original_file)
                        
                        # first symbolic link
                        chain[0] = rep_symlink
                        # target
                        chain[-1] = rep_target
                        
                        for i in range(1, len(chain)-1):
                            if chain[i]:
                                chain[i] = os.path.join(self.__user_exp_dir, chain[i][1:])
                            
                        self.__symlink_chain[rep_symlink] = chain
                    else:
                        self.__symlink_chain[rep_symlink] = [rep_symlink, rep_target]
                    
                    # symbolic links between directories
                    if self.__symlink_dir.has_key(original_file):
                        chain = self.__symlink_dir[original_file]
                        self.__symlink_dir.pop(original_file)
                        
                        for i in range(len(chain)):
                            if chain[i]:
                                chain[i] = os.path.join(self.__user_exp_dir, chain[i][1:])
                            
                        self.__symlink_dir[rep_symlink] = chain
            
            return (rep_file, in_cp_dir)
        
        ########################################################################
        
        print "\n- Copying files to package... Be patient! This may take a while...\n"
            
        reprozip.debug.verbose(self.verbose, 'Including main program in package...')
            
        # main program
        if len(self.__main_program) == 1:
            main_program = self.__main_program.keys()[0]
            program, in_cp_dir = include_file(main_program,
                                              self.__main_program[main_program],
                                              True)
            
            if program:
                # updating information
                if in_cp_dir:
                    argv_dict[0]['value'] = os.sep.join(os.path.basename(program).split(reprozip.utils.sep))
                    
                else:
                    argv_dict[0]['value'] = os.path.join(self.__user_dir,
                                                         os.path.relpath(program, self.__rep_dir))
            else:
                # if an error occurred
                self.__main_program = {}
        else:
            argv_dict[0]['value'] = os.path.join(self.__user_exp_dir,
                                                 argv_dict[0]['value'][1:])
                
        reprozip.debug.verbose(self.verbose, 'Including child programs in package...')
                
        # child programs
        for program in self.__child_programs:
            rep_program, in_cp_dir = include_file(program, self.__child_programs[program], True)
            
        reprozip.debug.verbose(self.verbose, 'Including main input files in package...')
            
        # input and output files and directories
        for i in range(len(argv_dict)):
            if argv_dict[i]['input file']:
                file_ = argv_dict[i]['value']
                if self.__input_files.has_key(file_): # file not excluded by user
                    input_file, in_cp_dir = include_file(file_, self.__input_files[file_])
                    
                    if input_file:
                        # updating information
                        if in_cp_dir:
                            argv_dict[i]['value'] = os.sep.join(os.path.basename(input_file).split(reprozip.utils.sep))
                        else:
                            argv_dict[i]['value'] = os.path.join(self.__user_dir,
                                                                 os.path.relpath(input_file, self.__rep_dir))
                else: # file excluded by user -- assume data will be there when reproducing experiment
                    argv_dict[i]['value'] = os.path.join(self.__user_exp_dir,
                                                         file_[1:])
            elif argv_dict[i]['output file']:
                output_ = os.path.join(self.__rep_exp_dir,
                                       os.path.dirname(argv_dict[i]['value'])[1:])
                if not os.path.exists(output_):
                    os.makedirs(output_)
                argv_dict[i]['value'] = os.path.join(self.__user_dir,
                                                     os.path.relpath(output_, self.__rep_dir),
                                                     os.path.basename(argv_dict[i]['value']))
            elif argv_dict[i]['dir']:
                output_ = argv_dict[i]['value']
                if not os.path.exists(output_):
                    output_ = os.path.dirname(output_)
                output_ = os.path.join(self.__rep_exp_dir,
                                       output_[1:])
                if not os.path.exists(output_):
                    os.makedirs(output_)
                argv_dict[i]['value'] = os.path.join(self.__user_exp_dir,
                                                     argv_dict[i]['value'][1:])
                
        reprozip.debug.verbose(self.verbose, 'Including child input files in package...')
                
        # child input files
        for file_ in self.__child_input_files:
            rep_file, in_cp_dir = include_file(file_, self.__child_input_files[file_])
            
        reprozip.debug.verbose(self.verbose, 'Including dependencies in package...')
                
        # dependencies
        for dependency in self.__dependencies:
            rep_dependency, in_cp_dir = include_file(dependency, self.__dependencies[dependency])
            
        reprozip.debug.verbose(self.verbose, 'Making sure the required directories were created in package...')
            
        # directories - making sure they exist
        for dir in self.__dirs:
            rep_dir = self.__dirs[dir]
            rep_dir = os.path.normpath(rep_dir.replace(reprozip.utils.rep_dir_var,
                                                       self.__rep_dir))
            if not os.path.exists(rep_dir):
                os.makedirs(rep_dir)
                
                st = os.stat(dir)
                os.chmod(rep_dir, st.st_mode)
            
        # saving configuration file inside package
        try:
            shutil.copyfile(reprozip.utils.config_path, os.path.join(self.__rep_dir,
                                                            os.path.basename(reprozip.utils.config_path)))
        except:
            reprozip.debug.warning('Could not copy configuration file: %s' % sys.exc_info()[1])
            reprozip.debug.warning('Reproducible package will not contain this file.')
            
        # storing chains of symbolic links in the reproducible directory
        # these chains will be used in the unpacking step
        symlink_file = reprozip.utils.symlink_path.replace(reprozip.utils.rep_dir_var, self.__rep_dir)
        try:
            f = open(symlink_file, 'w')
            pickle.dump([self.__symlink_chain, self.__symlink_dir],
                        f, pickle.HIGHEST_PROTOCOL)
            f.close()
        except:
            reprozip.debug.error('Could not serialize object structures: %s' % sys.exc_info()[1])
            sys.exit(1)
            
        # storing configuration files
        if self.__config_files:
            config_file = reprozip.utils.config_file_path.replace(reprozip.utils.rep_dir_var, self.__rep_dir)
            try:
                f = open(config_file, 'w')
                pickle.dump(self.__config_files.values(),
                            f, pickle.HIGHEST_PROTOCOL)
                f.close()
            except:
                reprozip.debug.error('Could not serialize object structures: %s' % sys.exc_info()[1])
                sys.exit(1)
        
        reprozip.debug.verbose(self.verbose, 'Getting environment variables...')
        
        # environment variables
        env_var = {}

        ld_library_path = ''
        
        # in order to find out the paths to be included in LD_LIBRARY_PATH,
        # ldconfig is executed
        # TODO: is there a better way to do this?
        try:
            p = subprocess.Popen([guess_sudo(), 'ldconfig', '-v'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            (stdout, stderr) = p.communicate()
            
            l_stdout = stdout.split('\n')
            paths = []
            for i in range(len(l_stdout)):
                if l_stdout[i].startswith('\t'):
                    continue
                if l_stdout[i] == '':
                    continue
                
                lib_path = l_stdout[i][:l_stdout[i].index(':')]
                if lib_path.startswith(os.sep):
                    lib_path = lib_path[1:]
                dep_path = os.path.join(self.__rep_exp_dir, lib_path)
                
                # only including if path exists
                if os.path.exists(dep_path):
                    paths.append(os.path.join(self.__user_exp_dir, lib_path))
                        
            # now checking LD_LIBRARY_PATH in case we need to include something
            # from there
            #env_paths = os.getenv('LD_LIBRARY_PATH', '').split(':')
            env_paths = self.__env.get('LD_LIBRARY_PATH', '').split(':')
            for path in env_paths:
                if path == '':
                    continue
            
                if path.startswith(os.sep):
                    path = path[1:]
                dep_path = os.path.join(self.__rep_exp_dir, path)
                
                # only including if path exists
                if os.path.exists(dep_path):
                    paths.append(os.path.join(self.__user_exp_dir, path))
                        
            paths = list(set(paths))
            ld_library_path = ':'.join(paths)
            
        except:
            reprozip.debug.warning('Could not execute and use ldconfig command: %s' % sys.exc_info()[1])
            reprozip.debug.warning('LD_LIBRARY_PATH will not be set.')
            
        if ld_library_path != '':
            env_var['LD_LIBRARY_PATH'] = ld_library_path
            
        pythonpath = ''
            
        # in order to find out the paths to be included in PYTHONPATH,
        # sys.path is used
        # PYTHONPATH is only set if python is used in the experiment
        python = False
        programs = self.__main_program.keys() + self.__child_programs.keys()
        for program in programs:
            if 'python' in program:
                python = True
                break
        if python:
            paths = []
            for path in sys.path:
                if path == '':
                    continue
                
                if path.startswith(os.sep):
                    path = path[1:]
                dep_path = os.path.join(self.__rep_exp_dir, path)
                
                # only including if path exists
                if os.path.exists(dep_path):
                    paths.append(os.path.join(self.__user_exp_dir, path))
            
            # also verifying the PYTHONPATH environment variable, if already defined
            # this variable may be only defined for the execution, and in this case,
            # the directories will not be in sys.path
            env_paths = self.__env.get('PYTHONPATH', '').split(':')
            for path in env_paths:
                if path == '':
                    continue
            
                if path.startswith(os.sep):
                    path = path[1:]
                dep_path = os.path.join(self.__rep_exp_dir, path)
                
                # only including if path exists
                if os.path.exists(dep_path):
                    paths.append(os.path.join(self.__user_exp_dir, path))
                        
            paths = list(set(paths))  
            pythonpath = ':'.join(paths)
            
            if pythonpath != '':
                env_var['PYTHONPATH'] = pythonpath
                
        # HOME environment variable
        home_dir = os.path.join(self.__rep_exp_dir, os.getenv('HOME')[1:])
        homepath = None
        if os.path.exists(home_dir):
            homepath = os.path.join(self.__user_exp_dir, os.getenv('HOME')[1:])
            env_var['HOME'] = homepath
            
        # taking care of other environment variables
        # here, we need to be careful because an environment variable may
        # not be a directory
        # we also need to remove environment variables we do not need to deal with
        # TODO: better way to remove unnecessary environment variables?
        rm = ['LD_LIBRARY_PATH',
              'PYTHONPATH',
              'HOME',
              'PWD',
              'GNOME_DESKTOP_SESSION_ID',
              'GNOME_KEYRING_CONTROL',
              'GNOME_KEYRING_PID',
              '_',
              '.xcf',
              '01;31:*.zip',
              '35:*.mpeg',
              '00;36:*.spx',
              '01;31:*.7z',
              'LESSOPEN',
              'LESSCLOSE',
              'LOGNAME',
              'USER',
              'DISPLAY',
              'SSH_AGENT_PID',
              'LANG',
              'TERM',
              'SHELL',
              'SESSION_MANAGER',
              'DISPLAY',
              'ORBIT_SOCKETDIR',
              'XAUTHORITY',
              'XDG_SESSION_PATH',
              'XDG_SESSION_COOKIE',
              'XDG_CONFIG_DIRS',
              'XDG_DATA_DIRS',
              'XDG_SEAT_PATH',
              'XDG_CURRENT_DESKTOP',
              'SESSION_MANAGER',
              'SHLVL',
              'MANDATORY_PATH',
              'WINDOWID',
              'GPG_AGENT_INFO',
              'SSH_AUTH_SOCK',
              'GDMSESSION',
              'DBUS_SESSION_BUS_ADDRESS',
              'DESKTOP_SESSION',
              'DEFAULTS_PATH',
              'UBUNTU_MENUPROXY',
              'COLORTERM',
              'LS_COLORS']
        
        for env in rm:
            self.__env.pop(env, None)
        
        for var in self.__env:
            values = []
            env_values = self.__env.get(var, '').split(':')
            for value in env_values:
                if value == '':
                    continue
            
                n_value = value
                if value.startswith(os.sep):
                    n_value = value[1:]
                dep_path = os.path.join(self.__rep_exp_dir, n_value)
                
                # 'value' can be either a directory or another type of variable
                if os.path.exists(dep_path):
                    values.append(os.path.join(self.__user_exp_dir, n_value))
                else:
                    if (not os.path.isabs(value)):
                        values.append(value)
            
            env_values = ':'.join(values)
            if env_values != '':
                env_var[var] = '\'%s\'' %env_values.replace('\'','\"')
        
        # pwd        
        pwd = os.path.join(self.__user_exp_dir, self.__prov_tree.root.execve_pwd[1:])
            
        # generating executable script
        reprozip.debug.verbose(self.verbose, 'Writing executable script...')
        self.generate_exec_script(argv_dict, env_var, pwd)
        
        # generating VisTrails workflow
        reprozip.debug.verbose(self.verbose, 'Writing workflow...')
        self.generate_vt_workflow(main_name, argv_dict, env_var, pwd)
        
    def generate_exec_script(self, argv_dict, env_var, pwd):
        """
        Method that generates an executable script for the execution of
        the experiment.
        """
        
#         script = ''
#          
#         script += 'import os\n'
#         script += 'import subprocess\n\n'
#          
#         script += 'pwd = os.getcwd()\n'
#         script += 'os.chdir(\'%s\')\n\n' %pwd
#              
#         cmd = ''
#         for i in range(0, len(argv_dict), 1):
#             if argv_dict[i]['flag']:
#                 cmd += '%s ' %argv_dict[i]['flag']
#             if argv_dict[i]['prefix']:
#                 cmd += '%s' %argv_dict[i]['prefix']
#             cmd += '%s ' %argv_dict[i]['value']
#              
#         script += 'cmd = \"%s\".split()\n' %cmd
#         script += 'env = %s\n' %str(env_var)
#         script += 'p = subprocess.Popen(cmd, env=env)\n'
#         script += 'r = p.wait()\n\n'
#              
#         script += 'os.chdir(pwd)'
        
        script = ''
         
        script += 'pushd %s\n(' %pwd
        for var in env_var:
            script += 'export %s=%s; ' %(var, env_var[var])
             
        for i in range(0, len(argv_dict), 1):
            if argv_dict[i]['flag']:
                script += '%s ' %argv_dict[i]['flag']
            if argv_dict[i]['prefix']:
                script += '%s' %argv_dict[i]['prefix']
            script += '%s ' %argv_dict[i]['value']
             
        script += ')\npopd'
            
        script_file = reprozip.utils.exec_path.replace(reprozip.utils.rep_dir_var,
                                                       self.__rep_dir)
        try:
            f = open(script_file, 'w')
            f.write(script)
            f.close()
        except:
            reprozip.debug.error('Could not create executable script: %s' % sys.exc_info()[1])
            sys.exit(1)
            
    def generate_vt_workflow(self, name, argv_dict, env_var, pwd):
        """
        Method that generates a VisTrails workflow for the experiment.
        """
        
        # creating CLTools wrapper
        # assuming that the first argument is the main command
        command = argv_dict[0]['value']
        num_args = len(argv_dict) - 1
        
        main_name = name
        
        wrapper = Wrapper()
        
        ## arguments
        input_id = 0
        output_id = 0
        if (num_args != 0):
            for i in range(1, len(argv_dict), 1):
                if argv_dict[i]['output file']:
                    output_id += 1
                    wrapper.add_arg(type     = 'Output',
                                    name     = 'output%d' % output_id,
                                    _class   = "File",
                                    flag     = argv_dict[i]['flag'],
                                    prefix   = argv_dict[i]['prefix'],
                                    suffix   = argv_dict[i]['suffix'],
                                    required = True)
                elif argv_dict[i]['input file']:
                    input_id += 1
                    wrapper.add_arg(type     = 'Input',
                                    name     = 'input%d' % input_id,
                                    _class   = "File",
                                    flag     = argv_dict[i]['flag'],
                                    prefix   = argv_dict[i]['prefix'],
                                    suffix   = None,
                                    required = True)
                else:
                    input_id += 1
                    wrapper.add_arg(type     = 'Input',
                                    name     = 'input%d' % input_id,
                                    _class   = "String",
                                    flag     = argv_dict[i]['flag'],
                                    prefix   = argv_dict[i]['prefix'],
                                    suffix   = None,
                                    required = True)
                    
        #  main command
        wrapper.set_command(command)
        
        # setting environment variables
        for env in env_var:
            wrapper.set_env(env, env_var[env])
            
        # pwd
        wrapper.set_working_dir(pwd)
        
        # stderr
        wrapper.add_stderr(name     = 'stderr',
                           _class   = 'String',
                           required = True)
    
        #  stdout
        wrapper.add_stdout(name     = 'stdout',
                           _class   = 'String',
                           required = True)
        
        # saving wrapper
        wrapper_dir = reprozip.utils.cltools_dir.replace(reprozip.utils.rep_dir_var,
                                                self.__rep_dir)
        try:
            os.makedirs(wrapper_dir)
        except:
            reprozip.debug.warning('Could not create CLTools directory: %s' % sys.exc_info()[1])
            reprozip.debug.warning('ReproZip will not create the VisTrails workflow.')
            return False
            
        wrapper_file = os.path.join(wrapper_dir, main_name + '.clt')
        try:
            f = open(wrapper_file, 'w')
            f.write(wrapper.get_str())
            f.close()
        except:
            reprozip.debug.warning('Could not create CLTools wrapper: %s' % sys.exc_info()[1])
            reprozip.debug.warning('ReproZip will not create the VisTrails workflow.')
            return False
            
        # VisTrails workflow
        wf = VTWorkflow('1.0.2')
        
        # main module
        exec_module = wf.add_module(cache      = '1',
                                    name       = main_name,
                                    namespace  = '',
                                    package    = 'edu.utah.sci.vistrails.cltools',
                                    version    = '0.1.1',
                                    return_obj = True)
        
        wf.add_location(module     = exec_module,
                        x          = '-57.847804463',
                        y          = '-14.4016938993',
                        return_obj = False)
        
        # StandardOutput (stdout)
        stdout_module = wf.add_module(cache      = '1',
                                      name       = 'StandardOutput',
                                      namespace  = '',
                                      package    = 'edu.utah.sci.vistrails.basic',
                                      version    = '1.6',
                                      return_obj = True)
        
        wf.add_location(module     = stdout_module,
                        x          = '-2.05448946096',
                        y          = '-118.766234237',
                        return_obj = False)
        
        wf.add_annotation(wf_object  = stdout_module,
                          key        = '__desc__',
                          value      = 'stdout',
                          return_obj = False)
        
        # StandardOutput (stderr)
        stderr_module = wf.add_module(cache      = '1',
                                      name       = 'StandardOutput',
                                      namespace  = '',
                                      package    = 'edu.utah.sci.vistrails.basic',
                                      version    = '1.6',
                                      return_obj = True)
        
        wf.add_location(module     = stderr_module,
                        x          = '-205.465652427',
                        y          = '-119.307819009',
                        return_obj = False)
        
        wf.add_annotation(wf_object  = stderr_module,
                          key        = '__desc__',
                          value      = 'stderr',
                          return_obj = False)
        
        # module_map[i] stores the corresponding modules for argument i
        # if the argument is an input file, it stores a 'persistent_module'
        # if the argument is an output file, it stores a 'filesink_module' and
        # a 'persistent_module'; otherwise, it stores a 'string_module'
        module_map = [{}]
        
        input_id = 0
        output_id = 0
        for i in range(1, len(argv_dict), 1):
            
            # input file
            if argv_dict[i]['input file']:
                input_id += 1
                
                # PersistentInputFile
                persistent_module = wf.add_module(cache      = '1',
                                                  name       = 'PersistentInputFile',
                                                  namespace  = '',
                                                  package    = 'edu.utah.sci.vistrails.persistence',
                                                  version    = '0.2.3',
                                                  return_obj = True)
                
                wf.add_location(module     = persistent_module,
                                x          = '-222.703296661',
                                y          = '218.125704396',
                                return_obj = False)
                
                wf.add_annotation(wf_object  = persistent_module,
                                  key        = '__desc__',
                                  value      = 'input%s' % str(input_id),
                                  return_obj = False)
                
                module_map.append({'persistent_module': persistent_module})
        
                # port value
                function = wf.add_function(module     = persistent_module,
                                           name       = 'value',
                                           pos        = '0',
                                           return_obj = True)
        
                wf.add_parameter(function   = function,
                                 alias      = '',
                                 name       = '&lt;no description&gt;',
                                 pos        = '0',
                                 type       = 'edu.utah.sci.vistrails.basic:File',
                                 value      = argv_dict[i]['value'],
                                 return_obj = False)
        
                # port localPath
                function = wf.add_function(module     = persistent_module,
                                           name       = 'localPath',
                                           pos        = '0',
                                           return_obj = True)
        
                wf.add_parameter(function   = function,
                                 alias      = '',
                                 name       = '&lt;no description&gt;',
                                 pos        = '0',
                                 type       = 'edu.utah.sci.vistrails.basic:File',
                                 value      = argv_dict[i]['value'],
                                 return_obj = False)
        
                # port readLocal
                function = wf.add_function(module     = persistent_module,
                                           name       = 'readLocal',
                                           pos        = '0',
                                           return_obj = True)
        
                wf.add_parameter(function   = function,
                                 alias      = '',
                                 name       = '&lt;no description&gt;',
                                 pos        = '0',
                                 type       = 'edu.utah.sci.vistrails.basic:Boolean',
                                 value      = 'True',
                                 return_obj = False)
     
                # port writeLocal
                function = wf.add_function(module     = persistent_module,
                                           name       = 'writeLocal',
                                           pos        = '0',
                                           return_obj = True)
        
                wf.add_parameter(function   = function,
                                 alias      = '',
                                 name       = '&lt;no description&gt;',
                                 pos        = '0',
                                 type       = 'edu.utah.sci.vistrails.basic:Boolean',
                                 value      = 'False',
                                 return_obj = False)
                
            # output file
            elif argv_dict[i]['output file']:
                output_id += 1
                
                # FileSink
                filesink_module = wf.add_module(cache      = '1',
                                                name       = 'FileSink',
                                                namespace  = '',
                                                package    = 'edu.utah.sci.vistrails.basic',
                                                version    = '1.6',
                                                return_obj = True)
                
                wf.add_location(module     = filesink_module,
                                x          = '-5.28184598779',
                                y          = '219.104703112',
                                return_obj = False)
                
                wf.add_annotation(wf_object  = filesink_module,
                                  key        = '__desc__',
                                  value      = 'output%s' % str(output_id),
                                  return_obj = False)
                
                # port outputPath
                function = wf.add_function(module     = filesink_module,
                                           name       = 'outputPath',
                                           pos        = '0',
                                           return_obj = True)
        
                wf.add_parameter(function   = function,
                                 alias      = '',
                                 name       = '&lt;no description&gt;',
                                 pos        = '0',
                                 type       = 'edu.utah.sci.vistrails.basic:OutputPath',
                                 value      = argv_dict[i]['value'],
                                 return_obj = False)
                
                # port overwrite
                function = wf.add_function(module     = filesink_module,
                                           name       = 'overwrite',
                                           pos        = '0',
                                           return_obj = True)
        
                wf.add_parameter(function   = function,
                                 alias      = '',
                                 name       = '&lt;no description&gt;',
                                 pos        = '0',
                                 type       = 'edu.utah.sci.vistrails.basic:Boolean',
                                 value      = 'True',
                                 return_obj = False)
                
                # PersistentOutputFile
                persistent_module = wf.add_module(cache      = '1',
                                                  name       = 'PersistentOutputFile',
                                                  namespace  = '',
                                                  package    = 'edu.utah.sci.vistrails.persistence',
                                                  version    = '0.2.3',
                                                  return_obj = True)
                
                wf.add_location(module     = persistent_module,
                                x          = '168.177621563',
                                y          = '-21.4722468575',
                                return_obj = False)
                
                wf.add_annotation(wf_object  = persistent_module,
                                  key        = '__desc__',
                                  value      = 'output%s' % str(output_id),
                                  return_obj = False)
                
                
                module_map.append({'persistent_module': persistent_module,
                                   'filesink_module': filesink_module})
                
            # not an input / output file
            else:
                input_id += 1
                
                # String
                string_module = wf.add_module(cache      = '1',
                                              name       = 'String',
                                              namespace  = '',
                                              package    = 'edu.utah.sci.vistrails.basic',
                                              version    = '1.6',
                                              return_obj = True)
                
                wf.add_location(module     = string_module,
                                x          = '81.2817793353',
                                y          = '96.6952535799',
                                return_obj = False)
                
                wf.add_annotation(wf_object  = string_module,
                                  key        = '__desc__',
                                  value      = 'input%s' % str(input_id),
                                  return_obj = False)
                
                module_map.append({'string_module': string_module})
                
                # port value
                function = wf.add_function(module     = string_module,
                                           name       = 'value',
                                           pos        = '0',
                                           return_obj = True)
        
                wf.add_parameter(function   = function,
                                 alias      = '',
                                 name       = '&lt;no description&gt;',
                                 pos        = '0',
                                 type       = 'edu.utah.sci.vistrails.basic:String',
                                 value      = argv_dict[i]['value'],
                                 return_obj = False)
        
        # connections
        
        # stdout --> StandardOutput
        source_port = wf.create_port(module    = exec_module,
                                     name      = 'stdout',
                                     signature = '(edu.utah.sci.vistrails.basic:String)')
    
        dst_port = wf.create_port(module    = stdout_module,
                                  name      = 'value',
                                  signature = '(edu.utah.sci.vistrails.basic:Module)')
        
        wf.add_connection(source_port, dst_port, False)
        
        # stderr --> StandardOutput
        source_port = wf.create_port(module    = exec_module,
                                     name      = 'stderr',
                                     signature = '(edu.utah.sci.vistrails.basic:String)')
    
        dst_port = wf.create_port(module    = stderr_module,
                                  name      = 'value',
                                  signature = '(edu.utah.sci.vistrails.basic:Module)')
        
        wf.add_connection(source_port, dst_port, False)
        
    
        input_id = 0
        output_id = 0
        for i in range(1, len(argv_dict), 1):
            
            # input file
            if argv_dict[i]['input file']:
                input_id += 1
                
                # PersistentInputFile --> main module
                source_port = wf.create_port(module    = module_map[i]['persistent_module'],
                                             name      = 'value',
                                             signature = '(edu.utah.sci.vistrails.basic:File)')
            
                dst_port = wf.create_port(module    = exec_module,
                                          name      = 'input%s' % str(input_id),
                                          signature = '(edu.utah.sci.vistrails.basic:File)')
                
                wf.add_connection(source_port, dst_port, False)
                
            # output file
            elif argv_dict[i]['output file']:
                output_id += 1
                
                # main module --> FileSink
                source_port = wf.create_port(module    = exec_module,
                                             name      = 'output%s' % str(output_id),
                                             signature = '(edu.utah.sci.vistrails.basic:File)')
            
                dst_port = wf.create_port(module    = module_map[i]['filesink_module'],
                                          name      = 'file',
                                          signature = '(edu.utah.sci.vistrails.basic:File)')
                
                wf.add_connection(source_port, dst_port, False)
        
                
                # main module --> PersistentOutputFile
                source_port = wf.create_port(module    = exec_module,
                                             name      = 'output%s' % str(output_id),
                                             signature = '(edu.utah.sci.vistrails.basic:File)')
            
                dst_port = wf.create_port(module    = module_map[i]['persistent_module'],
                                          name      = 'value',
                                          signature = '(edu.utah.sci.vistrails.basic:File)')
                
                wf.add_connection(source_port, dst_port, False)
        
            # not an input / output file
            else:
                input_id += 1
                
                # String --> main module
                source_port = wf.create_port(module    = module_map[i]['string_module'],
                                             name      = 'value',
                                             signature = '(edu.utah.sci.vistrails.basic:String)')
            
                dst_port = wf.create_port(module    = exec_module,
                                          name      = 'input%s' % str(input_id),
                                          signature = '(edu.utah.sci.vistrails.basic:String)')
                
                wf.add_connection(source_port, dst_port, False)
        
        # saving workflow
        wf_filename = os.path.join(reprozip.utils.vistrails_dir.replace(reprozip.utils.rep_dir_var, self.__rep_dir),
                                   main_name + '.xml')
        
        try:
            f = open(wf_filename, 'w')
            f.write(wf.get_str_repr())
            f.close()
        except:
            reprozip.debug.warning('Could not create VisTrails workflow: %s' % sys.exc_info()[1])
            reprozip.debug.warning('ReproZip will not create the VisTrails workflow.')
            return False
        
        return True
            
    def pack(self):
        """
        Method to pack the experiment in a tar.gz file.
        """
        
        package = '%s.tar.gz' %(os.path.basename(self.__rep_dir))
        
        if os.path.exists(package):
            answer = ''
            while answer.upper() != 'Y' and answer.upper() != 'N':
                answer = raw_input('<warning> The package "%s" already exists. Remove it before creating the new one (Y or N)? ' % package)
            if answer.upper() == 'N':
                sys.exit(0)
        try:
            tar = tarfile.open(package, 'w:gz')
            tar.add(os.path.basename(self.__rep_dir))
            tar.close()
        except:
            reprozip.debug.error('Error while packing the files: %s' % sys.exc_info()[1])
            sys.exit(1)
            
        shutil.rmtree(self.__rep_dir)
            
        print '** Experiment packed in %s with success **' % (package)

    def __gen_config_file(self):
        """
        Method to generate a configuration file of the packing process.
        """
        
        config_file = '# Platform: %s\n' % platform.platform(aliased=True)
        config_file += '# Processor: %s\n' % platform.processor()
        
        try:
            config_file += '# Number of CPUs: %s\n' % os.sysconf('SC_NPROCESSORS_ONLN')
            #config_file += '# Size of word: %s bits\n' % os.sysconf('SC_WORD_BIT')
        except:
            pass
        
        config_file += '\n\n'
        
        # original file
        first_column = ['* Original File *', '']
        
        # size of original file
        second_column = ['* Size (KB) *', '']
        
        # include or not
        third_column = ['* Include? *', '']
        
        # configuration file
        #fourth_column = ['* Config File? *', '']
        
        # file in the reproducible folder
        #fifth_column = ['* Package File *', '']
        
        ########################################################################
        
        # function used to include information inside the configuration file
        def include_in_config(title, file_dict):
            """
            'title'         -> class of file (main program, ...)
            'file_dict'     -> dictionary with files
            
            Returns lists for first, second, third and fourth columns of
            configuration file.
            """
            first_column = []
            second_column = []
            third_column = []
            #fourth_column = []
            #fifth_column = []
            
            first_column.append('[%s]' %title)
            second_column.append('')
            third_column.append('')
            #fourth_column.append('')
            #fifth_column.append('')
            
            for file_ in file_dict:
                size = ''
                try:
                    size = '%0.2f' %(os.path.getsize(file_)/1024.0)
                except:
                    size = 'N/A'
                
                first_column.append(file_)
                second_column.append(size)
                third_column.append('Y')
                #fourth_column.append('N')
                #fifth_column.append(file_dict[file_])
                
                if self.__symlink_to_target.has_key(file_):
                    size = ''
                    try:
                        size = '%0.2f' %(os.path.getsize(self.__symlink_to_target[file_])/1024.0)
                    except:
                        size = 'N/A'
                        
                    first_column.append(self.__symlink_to_target[file_])
                    second_column.append(size)
                    third_column.append('Y')
                    #fourth_column.append('N')
                    #fifth_column.append(self.__targets[self.__symlink_to_target[file_]])
                
            first_column.append('')
            second_column.append('')
            third_column.append('')
            #fourth_column.append('')
            #fifth_column.append('')
            
            return (first_column, second_column, third_column)
            #return (first_column, second_column, third_column, fourth_column)
        
        ########################################################################
        
        # main program
        if len(self.__main_program) == 1:
            (first, second, third) = include_in_config('main program',
                                                       self.__main_program)
            first_column += first
            second_column += second
            third_column += third
            #fourth_column += fourth
        
        # child programs
        if len(self.__child_programs) > 0:
            (first, second, third) = include_in_config('other programs',
                                                       self.__child_programs)
            first_column += first
            second_column += second
            third_column += third
            #fourth_column += fourth
                
        # main input files
        if len(self.__input_files) > 0:
            (first, second, third) = include_in_config('main input files',
                                                       self.__input_files)
            first_column += first
            second_column += second
            third_column += third
            #fourth_column += fourth
                
        # child input files
        if len(self.__child_input_files) > 0:
            (first, second, third) = include_in_config('other input files',
                                                       self.__child_input_files)
            first_column += first
            second_column += second
            third_column += third
            #fourth_column += fourth
        
        # dependencies
        if len(self.__dependencies) > 0:
            (first, second, third) = include_in_config('dependencies',
                                                       self.__dependencies)
            first_column += first
            second_column += second
            third_column += third
            #fourth_column += fourth
            
        # exclude patterns
        # these patterns should be written using Unix shell-style wildcards,
        # otherwise it will not work
        first_column.append('[exclude]')
        second_column.append('')
        third_column.append('')
        #fourth_column.append('')
        
        # maximum lengths, for the purpose of formatting
        max_first = str(len(max(first_column, key=len)))
        max_second = str(len(max(second_column, key=len)))
        max_third = str(len(max(third_column, key=len)))
        #max_fourth = str(len(max(fourth_column, key=len)))
        
        format = '{:<%s}\t{:^%s}\t{:^%s}\n' % (max_first, max_second, max_third)
        for i in range(len(first_column)):
            config_file += format.format(first_column[i],
                                         second_column[i],
                                         third_column[i])
            
        try:
            f = open(reprozip.utils.config_path, 'w')
            f.write(config_file)
            f.close()
        except:
            reprozip.debug.error('Could not save configuration file: %s' %sys.exc_info()[1])
            sys.exit(1)
            
        self.__config_mtime = os.path.getmtime(reprozip.utils.config_path)
            
        print '** Configuration file created in "%s" **' % reprozip.utils.config_path
                        

    def __get_child_processes(self, id, db_collection, depth=1):
        """
        Recursive method to get all the child processes.
        It returns the depth of the recursion.
        """
        
        current_ppid = self.__prov_tree.nodes[id].pid    
        cursor = db_collection.find({'$and': [
                                              {'ppid': current_ppid},
                                              {'creation_time': {'$gte': self.__start_time}}
                                              ]})
        
        # checking if cursor is empty
        len_cursor = cursor.count()
        if len_cursor == 0:
            return (depth - 1)
            
        depths = []
        for i in range(len_cursor):
            exec_wf = cursor[i]
            
            c_pid = int(exec_wf['pid'])
            
            # a process may have more than one phase
            # when this happens, it morphs from one executable to another
            # for this reason, we need to consider all the phases
            # here, phases from same process are stored as separate nodes
            # TODO: should store phases inside same node?
            main_id = None
            
            for i in range(len(exec_wf['phases'])):
                
                execve_argv = str(exec_wf['phases'][i]['execve_argv'])
                execve_argv = execve_argv.replace('\"','')
                
                execve_pwd = str(exec_wf['phases'][i]['execve_pwd'])
                
                execve_env = str(exec_wf['phases'][i]['execve_env'])
                
                files_read = exec_wf['phases'][i]['files_read'] or [] # list of dictionaries
                
                files_written = exec_wf['phases'][i]['files_written'] or [] # list of dictionaries
                
                dirs = exec_wf['phases'][i]['directories'] or [] # list of dictionaries
                
                symlinks = exec_wf['phases'][i]['symlinks'] or [] # list of dictionaries
    
#                if execve_argv == 'None':
#                    continue
                
                # creating node and adding it to the provenance tree
                node = Node(id)
                node.pid = c_pid
                node.set_execve_pwd(execve_pwd)
                node.set_execve_argv(execve_argv)
                node.set_execve_env(execve_env)
                node.set_files_read(files_read)
                node.set_files_written(files_written)
                node.set_dirs(dirs)
                node.set_symlink_to_target(symlinks)
                
                # child processes are connected to the first phase
                if i == 0:
                    main_id = self.__prov_tree.add_node(node)
                else:
                    c_id = self.__prov_tree.add_node(node)
                
            # a process may not have phases, but it is still important to
            # consider it, since the experiment may need executions
            # from its child processes
            if len(exec_wf['phases']) == 0:
                
                # creating node and adding it to the provenance tree
                node = Node(id)
                node.pid = c_pid
                
                main_id = self.__prov_tree.add_node(node)
            
            if not main_id:
                continue
            
            depths.append(self.__get_child_processes(main_id, db_collection,
                                                     depth + 1))
        
        if not depths:
            depths.append(0)
        return max(depths)
