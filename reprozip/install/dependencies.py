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
import reprozip.install.utils
import reprozip.install.ubuntu
import reprozip.install.fedora
import reprozip.install.debian
import reprozip.debug
import platform
import sys
import os

def create_dir():
    """
    Creates the directories for logging.
    """
    
    sudo = reprozip.install.utils.guess_sudo()
    val = True
    
    def check_val(val):
        if not val:
            return False
    
    # log dir
    log_dir = reprozip.utils.log_basedir()
    if not os.path.exists(log_dir):
        cmd = 'mkdir ' + log_dir
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
    # database dir
    db_dir = reprozip.utils.mongodb_dbpath
    if not os.path.exists(db_dir):
        cmd = 'mkdir ' + db_dir
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
    return True

def install_dependencies():
    """
    Function used to install the necessary dependencies for using the packing
    features of ReproZip.
    Dependencies are SystemTap and MongoDB.
    """
    
    os_ = reprozip.install.utils.guess_os()
    
    if os_ == 'linux':
        distro = reprozip.install.utils.guess_linux_distro()
        dep = None
        
        # log directory
        rep_dir = create_dir()
        if not rep_dir:
            reprozip.debug.warning('Creation of log directory failed!')
            
        # configuration file
        config = Parser()
        config.create_config_file()
        
        # Ubuntu
        if distro == 'ubuntu':
            dep = reprozip.install.ubuntu
        
        # Fedora
        elif distro == 'fedora':
            dep = reprozip.install.fedora
            
        # Debian
        elif distro == 'debian':
            dep = reprozip.install.debian
        
        else:
            reprozip.debug.warning('%s currently not supported for automatically installing the dependencies.' %distro)
            sys.exit(0)
        
        reprozip.debug.warning(dep.msg())
        
        answer = ''
        while answer.upper() != 'Y' and answer.upper() != 'N':
            answer = raw_input('> ')
            if answer.upper() == 'N':
                sys.exit(0)
            elif answer.upper() == 'Y':
                break
        
        # SystemTap
        reprozip.debug.success('Checking / installing SystemTap...')
        stap = dep.install_stap()
        if not stap:
            reprozip.debug.warning('SystemTap is not successfully installed.')
        else:
            reprozip.debug.success('SystemTap: done!')
            
        # MongoDB
        reprozip.debug.success('Checking / installing MongoDB...')
        mongodb = dep.install_mongodb()
        if not mongodb:
            reprozip.debug.warning('MongoDB is not successfully installed.')
        else:
            reprozip.debug.success('MongoDB: done!')
            
        if not stap:
            reprozip.debug.warning('SystemTap is not successfully installed.')
        
    else:
        reprozip.debug.warning('%s currently not supported.' %os_)
    