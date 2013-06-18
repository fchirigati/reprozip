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
import reprozip.install.ubuntu
import reprozip.utils
import platform
import os

ten_gen_64 = ['[10gen]',
              'name=10gen Repository',
              'baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64',
              'gpgcheck=0',
              'enabled=1']

ten_gen_32 = ['[10gen]',
              'name=10gen Repository',
              'baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/i686',
              'gpgcheck=0',
              'enabled=1']

def msg():
    """
    Returns message about installation.
    """
    
    msg = 'The following packages will be installed:\n'
    msg += '  1) systemtap\n'
    msg += '  2) systemtap-runtime\n'
    msg += '  3) kernel-devel\n'
    msg += '  4) kernel-debuginfo\n'
    msg += '  5) kernel-debuginfo-common\n'
    
    msg += 'Do you wish to continue? (Y/N)'
    
    return msg

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
        cmd = sudo + ' yum install systemtap systemtap-runtime'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
        
    # installing kernel debug symbols
    cmd = sudo + ' yum install kernel-devel'
    val = reprozip.install.utils.execute_install_cmd(cmd)
    check_val(val)
    
    cmd = sudo + ' debuginfo-install kernel'
    val = reprozip.install.utils.execute_install_cmd(cmd)
    check_val(val)
        
    return reprozip.install.ubuntu.test_stap()

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
        
        # configuring yum
        f = '/etc/yum.repos.d/10gen.repo'
        if not os.path.exists(f):
            temp_file = os.path.join(reprozip.utils.log_basedir(), '.10gen.repo')
            t = open(temp_file, 'w')
            if reprozip.install.utils.architecture() == 64:
                t.write('\n'.join(ten_gen_64))
            elif reprozip.install.utils.architecture() == 32:
                t.write('\n'.join(ten_gen_32))
            else:
                return False
            t.close()
            cmd = sudo + ' cp ' + temp_file + ' ' + f
            val = reprozip.install.utils.execute_install_cmd(cmd)
            check_val(val)
            
        # installing MongoDB
        cmd = sudo + ' yum install mongo-10gen-2.4.4 mongo-10gen-server-2.4.4'
        val = reprozip.install.utils.execute_install_cmd(cmd)
        check_val(val)
    
    return True
