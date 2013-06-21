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

import reprozip.utils
import ConfigParser
import os

class Parser:
    """
    Class used to handle ReproZip configuration file.
    Note: this is not the configuration file of a reproducible package.
    """
    
    def __init__(self):
        """
        Init method.
        """
        
        self.__file = os.path.join(reprozip.utils.log_basedir(), 'config')
        
    def create_config_file(self):
        """
        Method that creates the configuration file.
        """
        
        config = ConfigParser.RawConfigParser()
        
        config.add_section('mongodb')
        config.set('mongodb', 'journaling', reprozip.utils.mongodb_journaling)
        config.set('mongodb', 'quiet', reprozip.utils.mongodb_quiet)
        config.set('mongodb', 'logpath', reprozip.utils.mongodb_logpath)
        config.set('mongodb', 'dbpath', reprozip.utils.mongodb_dbpath)
        config.set('mongodb', 'port', reprozip.utils.mongodb_port)
        config.set('mongodb', 'on', reprozip.utils.mongodb_on)
        
        with open(self.__file, 'wb') as configfile:
            config.write(configfile)
            
    def read_mongodb_config(self):
        """
        Reads MongoDB section in the configuration file, returning its parameters in a tuple.
        """
        
        config = ConfigParser.RawConfigParser()
        config.read(self.__file)
        
        on = config.getboolean('mongodb', 'on')
        port = config.get('mongodb', 'port')
        dbpath = config.get('mongodb', 'dbpath')
        logpath = config.get('mongodb', 'logpath')
        quiet = config.getboolean('mongodb', 'quiet')
        journaling = config.getboolean('mongodb', 'journaling')
        
        return (on, port, dbpath, logpath, quiet, journaling)
        