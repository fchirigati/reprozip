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

from reprozip.utils import get_ms_since_epoch
from reprozip.pack.store_data import Provenance
from reprozip.install.utils import guess_sudo, guess_os
import reprozip.debug
import subprocess
import time
import sys
import os

class Tracer:
    """
    The class Tracer represents a tracer to get process information and store
    it in a MongoDB.
    """
    
    def __init__(self, log_basedir, pass_lite):
        """
        Init method for Tracer.
        
        -> log_basedir is the path to the log files
        -> pass_lite is the script executed by SystemTap / DTrace to get process
           information
        -> integrator is the complete path to the python script that stores all
           the information in a MongoDB
        """
        
        self.__log_basedir = log_basedir
        self.__pass_lite = pass_lite
        self.__session_name = None
        self.__session_name_path = None
        self.__provenance = Provenance()
        
        self.__p_tracer = None
        
        self.__session_name = '%s-%d' % (os.getenv('USER'), get_ms_since_epoch())
        self.__session_name_path = os.path.join(self.__log_basedir,
                                                self.__session_name)
        os.mkdir(self.__session_name_path)
        
        # rename the existing current-session/ symlink and add a new link to SESSION_NAME
        cs = os.path.join(self.__log_basedir, 'current-session')
        if os.path.exists(cs):
            os.rename(cs, os.path.join(self.__log_basedir, 'previous-session'))
        os.symlink(self.__session_name, cs)
        
        
    def store_process_data(self, port):
        """
        Method that stores data in MongoDB.
        """
        self.__provenance.store(self.__session_name_path,
                                self.__session_name,
                                port)

        
    def run_tracer(self):
        """
        Method that executes the tracer.
        """
        
        command_line = ''
        
        if guess_os() == 'linux':
            command_line = guess_sudo() + ' killall stap'
            
            try:
                p = subprocess.Popen(command_line.split(),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            except:
                reprozip.debug.error('Could not kill previous processes: %s' %sys.exc_info()[1])  
                raise Exception
            
            (stdout, stderr) = p.communicate()

            command_line = guess_sudo() + ' stap -o %s/pass-lite.out %s' % (self.__session_name_path,
                                                                            self.__pass_lite)
            
            try:
                self.__p_tracer = subprocess.Popen(command_line.split(),
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)
            except:
                reprozip.debug.error('Could not run stap: %s' %sys.exc_info()[1])
                self.__p_tracer = None
                raise Exception
                
        elif guess_os() == 'darwin':
            command_line = guess_sudo() + ' killall dtrace'
            
            try:
                p = subprocess.Popen(command_line.split(),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            except:
                reprozip.debug.error('Could not kill previous processes: %s' %sys.exc_info()[1])
                raise Exception
            
            (stdout, stderr) = p.communicate()

            command_line = guess_sudo() + ' dtrace -b 10m -o %s/pass-lite.out.0 -s %s' % (self.__session_name_path,
                                                                                          self.__pass_lite)
            
            try:
                self.__p_tracer = subprocess.Popen(command_line.split(),
                                                   stdout=subprocess.PIPE,
                                                   stderr=subprocess.PIPE)
            except:
                reprozip.debug.error('Could not run dtrace: %s' %sys.exc_info()[1])
                self.__p_tracer = None
                raise Exception
        
        # give it some time to begin
        time.sleep(10)
        
    def check_tracer(self):
        """
        Method that checks if there was any problem with the tracer.
        """
        
        if self.__p_tracer.returncode == None:
            # tracer has terminated - an error has probably occured
            stderr = self.__p_tracer.stderr.read()
            reprozip.debug.error('Error while tracing system calls: \"%s\"' %stderr)
            raise Exception
                
    def stop_tracer(self):
        """
        Method that stops the tracer.
        """
        
        # give it some time to finalize
        time.sleep(5)
        
        if (self.__p_tracer == None):
            pass
        else:
            cmd = guess_sudo() + ' kill %d' %self.__p_tracer.pid
            try:
                p = subprocess.Popen(cmd.split(),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            except:
                msg = 'Could not stop stap: %s. ' %sys.exc_info()[1]
                msg += 'You may want to try stopping it by running "%s"' %cmd
                reprozip.debug.warning(msg)
            
            self.__p_tracer = None
