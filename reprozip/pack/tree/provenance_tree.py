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

import reprozip.debug
import reprozip.utils
import subprocess
import sys
import os

class Node:
    """
    This class represents a node in the provenance tree.
    
    A node contains all the information related to the execution of a program,
    i.e., a command line. Information such as process id, files read, files
    written, input and output files, and the command line are stored in a node.
    """
    
    def __init__(self, parent_node):
        """
        Init method for Node.
        
        --> parent_node: id of the parent node
        """
        
        # provenance information
        self.__pid = None
        self.__execve_argv = None
        self.__execve_pwd = None
        self.__execve_env = {}
        self.__files_read = []
        self.__files_written = []
        self.__dirs = []
        
        # tree information
        self.__id = None
        self.__parent_node = parent_node
        
        # argv_dict is a list that stores information about the command line
        # argv_dict[i] --> for the index i, returns a dictionary containing five
        # keys: 'value', which contains the value of the argument i; 'input file', a
        # boolean that indicates if the argument is an input file; 'output file', a
        # boolean that indicates if the argument is an output file; 'dir', a
        # boolean that indicates if the argument is a directory; 'flag',
        # which contains the flag associated with the argument, if any; and
        # 'prefix', which contains the prefix for the argument, if any
        self.__argv_dict = []
        
        # program
        self.__program = None
        
        # input files
        self.__input_files = []
        
        # output files
        self.__output_files = []
        
        # dependencies
        self.__dependencies = []
        
        # mapping from symbolic links to target
        self.__symlink_to_target = {}

    def get_dirs(self):
        return self.__dirs


    def get_execve_env(self):
        return self.__execve_env


    def set_execve_env(self, value):
        if value != 'None':
            envs = value.split(reprozip.utils.sep_envs)
            for env in envs:
                if env != '':
                    env_var = env.split(reprozip.utils.sep_env)
                    env_name = env_var[0]
                    env_value = env_var[1]
                    self.__execve_env[env_name] = env_value


    def get_dependencies(self):
        return self.__dependencies


    def get_argv_dict(self):
        return self.__argv_dict


    def get_program(self):
        return self.__program


    def get_input_files(self):
        return self.__input_files


    def get_output_files(self):
        return self.__output_files
        

    def get_pid(self):
        return self.__pid


    def get_execve_argv(self):
        return self.__execve_argv


    def get_execve_pwd(self):
        return self.__execve_pwd


    def get_files_read(self):
        return self.__files_read


    def get_files_written(self):
        return self.__files_written


    def get_id(self):
        return self.__id


    def get_parent_node(self):
        return self.__parent_node


    def get_symlink_to_target(self):
        return self.__symlink_to_target


    def set_symlink_to_target(self, value):
        for symlink_dict in value:
            self.__symlink_to_target[symlink_dict['symlink']] = symlink_dict['target']
            

    def set_pid(self, value):
        self.__pid = value


    def set_execve_argv(self, value):
        if value != 'None':
            self.__execve_argv = value
            argv = self.__execve_argv.split()
            for i in range(len(argv)):
                value = argv[i]
                prefix = None
                if '=' in argv[i]:
                    prefix = argv[i][:argv[i].index('=') + 1]
                    value = argv[i][argv[i].index('=') + 1:] 
                elif argv[i][0] == '-':
                    continue
                suffix = os.path.splitext(value)[1]
                if suffix == '':
                    suffix = None
                self.__argv_dict.append({'value': value,
                                         'input file': False,
                                         'output file': False,
                                         'dir': False,
                                         'flag': None,
                                         'prefix': prefix,
                                         'suffix': suffix})
                # getting the flag, if any
                if (argv[i-1][0] == '-') and ('=' not in argv[i-1]):
                    self.__argv_dict[-1]['flag'] = argv[i-1]
                    
            self.__program = self.__argv_dict[0]['value']
            
            # here, we check if the program is called using an absolute path
            # absolute paths may indicate hard-coded paths, and that may cause problems when
            # trying to reproduce the experiment
            # then, if the program is being called using a relative path, we try
            # to get the absolute path by looking at the current working directory
            # finally, we check if the program is in PATH
            if os.path.isabs(self.__program):
                if self.__parent_node:
    #                print '<warning> The program "%s" might be being called using a hard-coded absolute path.' % os.path.basename(self.__program)
    #                print '          Hard-coded absolute paths make it difficult to reproduce the experiment.'
                    pass
            else:
                path = os.path.normpath(os.path.join(self.__execve_pwd,
                                        self.__program))
                if os.path.exists(path):
                    self.__program = path
                    self.__argv_dict[0]['value'] = path
                else:
                    # program is in PATH
                    # need to find where it is located
                    (in_path, filename) = reprozip.utils.executable_in_path(self.__program)
                    if in_path:
                        self.__program = filename
                        self.__argv_dict[0]['value'] = self.__program
                        
            # checking if program is a symbolic link
            if os.path.islink(self.__program):
                target = os.path.realpath(self.__program)
                if not os.path.isabs(target):
                    target = os.path.normpath(os.path.join(os.path.dirname(self.__program), target))
                self.__symlink_to_target[self.__program] = target


    def set_execve_pwd(self, value):
        if value != 'None':
            self.__execve_pwd = os.path.normpath(value)


    def set_files_read(self, value):
        for i in range(len(value)):
            filename = os.path.normpath(str(value[i]['filename']))
            if not filename.startswith('PIPE'):
                self.__files_read.append(filename)
            
        # input files
        self.retrieve_input()
        
        # dependencies
        self.retrieve_dependencies()


    def set_files_written(self, value):
        for i in range(len(value)):
            filename = os.path.normpath(str(value[i]['filename']))
            if not filename.startswith('PIPE'):
                self.__files_written.append(filename)
            
        # output files
        self.retrieve_output()
        
    
    def set_dirs(self, value):
        for i in range(len(value)):
            filename = os.path.normpath(str(value[i]['dirname']))
            self.__dirs.append(filename)


    def set_id(self, value):
        self.__id = value
        
        
    def retrieve_input(self):
        """
        Method used to store information about input files and directories.
        It is assumed that input files are files present in the command line
        and also recorded as "files read" by the process; input directories
        are also present in the command line, and they match the directory name
        of at least one input file.
        If in the command line, name of input file is not complete - for instance,
        if it does not include extension ('/home/aneurism') - it will not be
        considered an input file, since the comparison will not be true - for
        instance, '/home/aneurism' with '/home/aneurism.txt'.
        Since there is no way to know how the experiment process it, it is better
        to consider it as an input string, than as an input file.
        """
        
        self.__input_files = []
        
        for i in range(1, len(self.__argv_dict)):
            is_input_file = False
            
            input = None
            if os.path.isabs(self.__argv_dict[i]['value']):
                input = os.path.normpath(self.__argv_dict[i]['value'])
            else:
                input = os.path.normpath(os.path.join(self.__execve_pwd,
                                                      self.__argv_dict[i]['value']))
            for filename in self.__files_read:
#                if self.__parent_node and os.path.isabs(input):
#                    print '<warning> The file "%s" might be being called using a hard-coded absolute path.' % os.path.basename(input)
#                    print '          Hard-coded absolute paths make it difficult to reproduce the experiment.'
                
                # if input file
                if (os.path.normpath(filename) == input):
                    self.__argv_dict[i]['value'] = filename
                    self.__argv_dict[i]['input file'] = True
                    self.__input_files.append(filename)
                    is_input_file = True
                    
                    break
                
            # if not input file, check if it is a directory
            if not is_input_file:
                if (os.path.isabs(self.__argv_dict[i]['value'])) and\
                (os.path.splitext(self.__argv_dict[i]['value'])[1] == ''):
                    self.__argv_dict[i]['dir'] = True
            
            
    def retrieve_output(self):
        """
        Method used to store information about output files and directories.
        It is assumed that output files are files written by the process that
        are present in the command line; output directories are also present
        in the command line, and they match the directory name of at least
        one output file.
        If in the command line, name of output file is not complete - for instance,
        if it does not include extension ('/home/aneurism') - it will not be
        considered an output file, since the comparison will not be true - for
        instance, '/home/aneurism' with '/home/aneurism.out' or '/home/aneurism_2.out'.
        Since there is no way to know how the experiment process it, it is better
        to consider it as an input string, than as an output file.
        """
        
        self.__output_files = []
        
        for i in range(1, len(self.__argv_dict)):
            
            if (not self.__argv_dict[i]['dir']) and (not self.__argv_dict[i]['input file']):
                is_output_file = False
                
                output = None
                if os.path.isabs(self.__argv_dict[i]['value']):
                    output = os.path.normpath(self.__argv_dict[i]['value'])
                else:
                    output = os.path.normpath(os.path.join(self.__execve_pwd,
                                                          self.__argv_dict[i]['value']))
                
                for filename in self.__files_written:
                    # if output file
                    if (os.path.normpath(filename) == output):
                        self.__argv_dict[i]['value'] = filename
                        self.__argv_dict[i]['output file'] = True
                        self.__output_files.append(filename)
                        is_output_file = True
                        
                        break
            
            
    def retrieve_dependencies(self):
        """
        Method used to store all the dependencies.
        Dependencies, in this case, are all the files read by the process but the
        ones considered input files.
        """
        
        self.__dependencies = list(set(self.__files_read) - set(self.__input_files))
        
        
    def add_files_read(self, files):
        """
        Method used to add more files that were read.
        Use this method with caution, since it calls retrieve_input().
        The input of this method must be a list of files.
        """
        
        self.__files_read += files
        self.__files_read = list(set(self.__files_read))
        
        self.retrieve_input()
        self.retrieve_dependencies()
        
        
    def add_files_written(self, files):
        """
        Method used to add more files that were written.
        Use this method with caution, since it calls retrieve_output().
        The input of this method must be a list of files.
        """
        
        self.__files_written += files
        self.__files_written = list(set(self.__files_written))
        
        self.retrieve_output()
        
        
    def add_targets(self, symlink_to_target):
        """
        Method used to add more targets and symbolic links.
        The input is a mapping between symbolic links and targets.
        """
        
        for symlink in symlink_to_target:
            self.__symlink_to_target[symlink] = symlink_to_target[symlink]
            
            
    def add_dirs(self, dirs):
        """
        Method used to add more directories.
        """
        
        self.__dirs += dirs
        self.__dirs = list(set(self.__dirs))
            
            
    def add_env(self, env_dict):
        """
        Method used to add additional environment variables not captured
        by main process.
        """
        
        for env in env_dict:
            if not self.__execve_env.has_key(env):
                self.__execve_env[env] = env_dict[env]
                    

    pid = property(get_pid, set_pid, None, None)
    execve_argv = property(get_execve_argv, None, None, None)
    execve_pwd = property(get_execve_pwd, set_execve_pwd, None, None)
    files_read = property(get_files_read, None, None, None)
    files_written = property(get_files_written, None, None, None)
    id = property(get_id, set_id, None, None)
    parent_node = property(get_parent_node, None, None, None)
    argv_dict = property(get_argv_dict, None, None, None)
    program = property(get_program, None, None, None)
    input_files = property(get_input_files, None, None, None)
    output_files = property(get_output_files, None, None, None)
    dependencies = property(get_dependencies, None, None, None)
    symlink_to_target = property(get_symlink_to_target, set_symlink_to_target, None, None)
    execve_env = property(get_execve_env, set_execve_env, None, None)
    dirs = property(get_dirs, set_dirs, None, None)


class ProvenanceTree:
    """
    This class represents a provenance tree related to the execution of a program
    or script.
    """
    
    def __init__(self):
        """
        Init method for ProvenanceTree.
        """
        
        # information about the tree
        self.__root = None
        self.__tree = {}
        self.__height = -1
        
        # information about nodes
        self.__current_id = 0
        self.__nodes = {}


    def get_tree(self):
        return self.__tree


    def get_nodes(self):
        return self.__nodes


    def get_root(self):
        return self.__nodes.get(0)


    def get_height(self):
        return self.__height


    def set_root(self, root):
        root.id = self.__current_id
        
        self.__tree[root.id] = []
        self.__nodes[root.id] = root
        self.__height = 0
        
        # incrementing id
        self.__current_id += 1


    def set_height(self, value):
        self.__height = value
        
        
    def add_node(self, node):
        """
        Method used to add a node in the provenance tree.
        The node must contain a parent node.
        """
        
        if not self.__nodes.get(0):
            reprozip.debug.error('There is not a root in the provenance tree.')
            sys.exit(1)
            
        nodes = self.__nodes.keys()
        if node.parent_node not in nodes:
            reprozip.debug.error('The provenance tree does not contain the parent node.')
            sys.exit(1)
    
        # information about the node
        node.id = self.__current_id
        self.__tree[node.id] = []
        self.__nodes[node.id] = node
        
        # information about the parent node
        self.__tree[node.parent_node].append(node.id)
        
        # incrementing id
        self.__current_id += 1
        
        return node.id
    
    
    def update_root_information(self):
        """
        Method used to update the information in the root.
        Basically, this method adds files read and written by all the nodes
        to the root, since the root might have input and output files not
        captured before. All the dependencies are automatically passed to
        the root. Additionally, symbolic links and their corresponding targets,
        and environment variables are also passed.
        """
        
        files_read = []
        files_written = []
        dirs = []
        symlink_to_target = {}
        execve_env = {}
        for id in self.__nodes:
            if id != 0:                
                files_read += self.__nodes[id].files_read
                files_written += self.__nodes[id].files_written
                dirs += self.__nodes[id].dirs
                
                node_execve_env = self.__nodes[id].execve_env
                for env in node_execve_env:
                    if not execve_env.has_key(env):
                        execve_env[env] = node_execve_env[env]
                
                node_symlink_to_target = self.__nodes[id].symlink_to_target
                for symlink in node_symlink_to_target:
                    symlink_to_target[symlink] = node_symlink_to_target[symlink]
        
        self.__nodes[0].add_files_read(list(set(files_read)))
        self.__nodes[0].add_files_written(list(set(files_written)))
        self.__nodes[0].add_targets(symlink_to_target)
        self.__nodes[0].add_dirs(dirs)
        self.__nodes[0].add_env(execve_env)


    root = property(get_root, None, None, None)
    height = property(get_height, set_height, None, None)
    tree = property(get_tree, None, None, None)
    nodes = property(get_nodes, None, None, None)
        
