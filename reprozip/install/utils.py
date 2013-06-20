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
import reprozip.debug
import platform
import subprocess
import os
import sys

def architecture():
    """
    Returns architecture of machine.
    """
    
    arch_dict = {'AMD64': 64, 'x86_64': 64, 'i386': 32, 'i686': 32, 'x86': 32}
    
    machine = platform.machine()
    return arch_dict.get(machine, None)

def execute_install_cmd(cmd):
    """
    Execute a command line for installation.
    """
    
    try:
        p = subprocess.Popen(cmd.split())
    except:
        reprozip.debug.error('Could not execute "%s": %s' %(cmd,sys.exc_info()[1]))
        return False
    
    returncode = p.wait()
    if (returncode != 0):
        reprozip.debug.error('Error while executing "%s".' %cmd)
        return False
    
    return True

def guess_os():
    """
    Returns the OS.
    """
    
    if 'darwin' in platform.system().lower():
        return 'darwin'
    elif 'linux' in platform.system().lower():
        return 'linux'
    elif 'windows' in platform.system().lower():
        return 'windows'
    else:
        return platform.system().lower()

def guess_linux_distro():
    """
    Returns the linux distro.
    """
    
    return platform.linux_distribution()[0].lower()
        
def guess_sudo():
    """
    Tries to guess what to call to run a shell with elevated privileges.
    """
    
    return 'sudo'
    
#    if reprozip.utils.executable_is_in_path('kdesu'):
#        return 'kdesu -c'
#    elif reprozip.utils.executable_is_in_path('gksu'):
#        return 'gksu'
#    elif reprozip.utils.executable_is_in_path('sudo'):
#        return 'sudo'
#    elif (reprozip.utils.executable_is_in_path('sudo') and
#          reprozip.utils.executable_is_in_path('zenity')):
#        return ('((echo "" | sudo -v -S -p "") || ' +
#                '(zenity --entry --title "sudo password prompt" --text "Please enter your password '
#                'to give the system install authorization." --hide-text="" | sudo -v -S -p "")); sudo -S -p ""')
#    else:
#        reprozip.debug.warning("Could not find a graphical su-like command.")
#        reprozip.debug.warning("Will use regular su.")
#        return 'su -c'
    
