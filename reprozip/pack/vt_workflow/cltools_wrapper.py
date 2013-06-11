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
import json
import sys
import os

class Wrapper:
    """
    Wrapper represents a CLTools wrapper for a VisTrails workflow.
    """
    
    def __init__(self):
        """
        Init method for Wrapper.
        """
        
        self.__wrapper = {'args': []}
        
    def add_arg(self, type, name, _class, flag, prefix, required, suffix):
        """
        Method that adds an argument.
        """
        
        optional_dict = {}
        if required:
            optional_dict['required'] = ''
        if flag:
            optional_dict['flag'] = flag
        if prefix:
            optional_dict['prefix'] = prefix
        if suffix:
            optional_dict['suffix'] = suffix
        
        self.__wrapper['args'].append([type, name, _class, optional_dict])
        
    def set_env(self, name, value):
        """
        Method that sets an environment variable for the execution of the main
        command.
        """
        
        if not self.__wrapper.has_key('options'):
            self.__wrapper['options'] = {'env': '%s=%s' % (name, value)}
        else:
            self.__wrapper['options']['env'] += ';%s=%s' % (name, value)
        
    def add_stdout(self, name, _class, required):
        """
        Method that adds an output port for stdout.
        """
        
        optional_dict = {}
        if required:
            optional_dict['required'] = ''
        
        self.__wrapper['stdout'] = [name, _class, optional_dict]
        
    def add_stderr(self, name, _class, required):
        """
        Method that adds an output port for stderr.
        """
        
        optional_dict = {}
        if required:
            optional_dict['required'] = ''
        
        self.__wrapper['stderr'] = [name, _class, optional_dict]
        
    def set_command(self, command):
        """
        Method that sets the main command of the wrapper.
        """
        
        self.__wrapper['command'] = command
        
    def set_working_dir(self, dir):
        """
        Method that sets the working directory.
        """
        
        self.__wrapper['dir'] = dir
        
    def get_str(self):
        """
        Method that returns the string representation of the wrapper.
        """
        
        return json.dumps(self.__wrapper)
        
    def save_wrapper(self, name):
        """
        Method that saves the wrapper in the CLTools directory.
        """
        
        cltools_dir = os.path.join(os.environ['HOME'],'.vistrails/CLTools')
        if not os.path.exists(cltools_dir):
            try:
                os.mkdir(cltools_dir)
            except:
                reprozip.debug.error('Could not create CLTools folder: %s' %sys.exc_info()[0])
                sys.exit(1)
        
        wrapper = os.path.join(cltools_dir, name + '.clt')
        try:
            f = open(wrapper, 'w')
            f.write(json.dumps(self.__wrapper))
            f.close()
        except:
            reprozip.debug.error('Could not create CLTools wrapper: %s' %sys.exc_info()[0])
            sys.exit(1)
