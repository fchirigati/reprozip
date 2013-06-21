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

from reprozip.pack.config_parser import Parser
from reprozip.install.utils import guess_sudo
import reprozip.debug
import subprocess
import sys
import os

class Mongod:
    """
    Class that represents an access to a mongod instance.
    It handles the execution and end of such instance.
    """
    
    def __init__(self):
        """
        Init method.
        """
        
        self.__mongodb = None
        
        self.__on = None
        self.__port = None
        self.__dbpath = None
        self.__logpath = None
        self.__quiet = None
        self.__journaling = None
        
        parser = Parser()
        t = parser.read_mongodb_config()
        (self.__on, self.__port, self.__dbpath, self.__logpath, self.__quiet, self.__journaling) = t

    def get_port(self):
        return self.__port

    def run(self):
        """
        Runs a mongod instance.
        """
        
        if not self.__on:
            return
        
        quiet = ' --quiet'
        if not self.__quiet:
            quiet = ''
            
        journaling = ' --nojournal'
        if self.__journaling:
            journaling = ''
            
        cmd = guess_sudo() + ' mongod --fork' + quiet +  ' --port '
        cmd += self.__port + ' --dbpath ' + self.__dbpath + ' --logpath '
        cmd += self.__logpath + ' --logappend' + journaling
        
        try:
            self.__mongodb = subprocess.Popen(cmd.split(),
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE)
        except:
            reprozip.debug.error('Could not run mongod: %s' %sys.exc_info()[1]) 
            sys.exit(1)
            
        self.__mongodb.wait()
            
    def stop(self):
        """
        Tries to stop the mongod instance.
        """
        
        if not self.__on:
            return
        
        if (self.__mongodb == None):
            pass
        else:
            cmd = guess_sudo() + ' mongod --shutdown --dbpath ' + self.__dbpath
            try:
                p = subprocess.Popen(cmd.split(),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            except:
                msg = 'Could not stop mongod: %s. ' %sys.exc_info()[1]
                msg += 'You may want to try stopping it by running "%s"' %cmd
                reprozip.debug.warning(msg)
                
            self.__mongodb = None
    
    port = property(get_port, None, None, None)
                
    