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

import reprozip.install.utils
import reprozip.utils
import subprocess
import platform
import inspect
import os

lsb_release = platform.linux_distribution()[2]
ddebs = ['deb http://ddebs.ubuntu.com ' + lsb_release + ' main restricted universe multiverse',
         'deb http://ddebs.ubuntu.com ' + lsb_release + '-updates main restricted universe multiverse',
         'deb http://ddebs.ubuntu.com ' + lsb_release + '-security main restricted universe multiverse',
         'deb http://ddebs.ubuntu.com ' + lsb_release + '-proposed main restricted universe multiverse']

ten_gen = ['deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen']

def msg():
    """
    Returns message about installation.
    """
    
    msg = 'The following packages will be installed:\n'
    msg += '  1) systemtap\n'
    msg += '  2) pkg-create-dbgsym\n'
    msg += '  3) linux-headers-generic\n'
    msg += '  4) gcc\n'
    msg += '  5) libcap-dev\n'
    msg += '  6) linux-image-' + platform.uname()[2] + '-dbgsym\n'
    msg += '  7) elfutils\n'
    msg += '  8) mongodb-10gen\n'
    
    msg += 'Packages 3, 5 and 6 may be upgraded in case they are already installed.\n'
    msg += 'Do you wish to continue? (Y/N)'
    
    return msg

def test_stap():
    """
    Function used to test SystemTap.
    """
    
    sudo = reprozip.install.utils.guess_sudo()
    
    p = subprocess.Popen([sudo,'stap','-ve','probe begin { log("hello world") exit () }'])
    returncode = p.wait()
    
    if (returncode != 0):
        return False
    
    p = subprocess.Popen([sudo,'stap','-v', '-e','probe vfs.read {printf(\"read performed\\n\"); exit()}'])
    returncode = p.wait()
    
    if (returncode != 0):
        return False
    
    return True

def install_stap():
    """
    Function used to install SystemTap.
    """
    
    sudo = reprozip.install.utils.guess_sudo()
    val = True
    
    def check_val(val):
        if not val:
            return False
    
    (in_path, filename) = reprozip.utils.executable_in_path('stap')
    if not in_path:
        
        # installing SystemTap
        stap_cmd = sudo + ' apt-get install systemtap'
        val = reprozip.install.utils.execute_install_cmd(stap_cmd)
        check_val(val)
        
    (in_path, filename) = reprozip.utils.executable_in_path('pkg_create_dbgsym')
    if not in_path:
        
        # kernel support
        cmd = sudo + ' apt-get install pkg-create-dbgsym'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
    # devel environment
    cmd = sudo + ' apt-get install linux-headers-generic libcap-dev'
    val = reprozip.install.utils.execute_install_cmd(cmd)
    check_val(val)
    
    (in_path, filename) = reprozip.utils.executable_in_path('gcc')
    if not in_path:
        
        # installing gcc
        cmd = sudo + ' apt-get install gcc'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
    # including ddebs repositories
    ddebs_file = '/etc/apt/sources.list.d/ddebs.list'
    if not os.path.exists(ddebs_file):
        temp_file = os.path.join(reprozip.utils.log_basedir(), '.ddebs.list')
        t = open(temp_file, 'w')
        t.write('\n'.join(ddebs))
        t.close()
        cmd = sudo + ' cp ' + temp_file + ' ' + ddebs_file
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
        # importing the debug symbol archive GPG key
        cmd = sudo + ' apt-key adv --keyserver keyserver.ubuntu.com --recv-keys ECDCAD72428D7C01'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
            
        # updating repository
        cmd = sudo + ' apt-get update'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
    # installing debug package
    uname = platform.uname()[2]
    cmd = sudo + ' apt-get install linux-image-' + uname + '-dbgsym'
    val = reprozip.install.utils.execute_install_cmd(cmd)
    check_val(val)
    
    (in_path, filename) = reprozip.utils.executable_in_path('eu-readelf')
    if not in_path:
        
        # installing elfutils
        cmd = sudo + ' apt-get install elfutils'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
    # running eu-readelf script
    print "Running eu-readelf script..."
    dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    script = os.path.join(dir, 'eu-readelf.script')
    cmd = sudo + ' ' + script
    val = reprozip.install.utils.execute_install_cmd(cmd)
    check_val(val)
    print "Done!"
        
    return test_stap()

def install_mongodb():
    """
    Function used to install MongoDB.
    """
    
    sudo = reprozip.install.utils.guess_sudo()
    val = True
    
    def check_val(val):
        if not val:
            return False
        
    (in_path, filename) = reprozip.utils.executable_in_path('mongod')
    if not in_path:
        
        # including 10gen repository
        f = '/etc/apt/sources.list.d/10gen.list'
        if not os.path.exists(f):
            temp_file = os.path.join(reprozip.utils.log_basedir(), '.10gen.list')
            t = open(temp_file, 'w')
            t.write('\n'.join(ten_gen))
            t.close()
            cmd = sudo + ' cp ' + temp_file + ' ' + f
            val = reprozip.install.utils.execute_install_cmd(cmd)
            check_val(val)
        
        # importing the 10gen GPG key
        cmd = sudo + ' apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
        # updating repository
        cmd = sudo + ' apt-get update'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
        # installing MongoDB
        cmd = sudo + ' apt-get install mongodb-10gen=2.4.4'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
    return True

    
