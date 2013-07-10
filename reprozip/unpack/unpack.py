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
import argparse
import tarfile
import shutil
import sys
import os
import pickle
import stat

def unpack(args):
    
    package = args['exp']
    wdir = args['wdir']
    verbose = args['verbose']
    
    if not os.path.exists(package):
        reprozip.debug.error('The package "%s" does not exist.' % package)
        sys.exit(1)
    
    # directory for the experiment, already unpacked
    exp_dir = ''
    
    # if a working directory was not specified
    if not wdir:
        wdir = os.getcwd()
    
    # getting the name of the folder
    main_name = ''
    try:
        tar = tarfile.open(package)
        main_name = os.path.normpath(tar.getnames()[0])
        tar.close()
    except:
        reprozip.debug.error('Could not open package: %s' % sys.exc_info()[1])
        sys.exit(1)
            
    exp_dir = os.path.join(wdir, main_name)
        
    # found previous experiment - ask the user if it should be removed
    if os.path.exists(exp_dir):
        answer = ''
        while answer.upper() != 'Y' and answer.upper() != 'N':
            answer = raw_input('<warning> The folder "%s" already exists. Remove it before creating the new one (Y or N)? ' % os.path.basename(exp_dir))
        if answer.upper() == 'N':
            sys.exit(0)
        try:
            shutil.rmtree(exp_dir)
        except:
            reprozip.debug.error('Could not remove previous experiment: %s' % sys.exc_info()[1])
            sys.exit(1)
    
    # unpacking the file
    try:
        tar = tarfile.open(package)
        tar.extractall()
        tar.close()
    except:
        reprozip.debug.error('Could not unpack the experiment: %s' % sys.exc_info()[1])
        sys.exit(1)
        
    home = os.getenv('HOME')
    
    # replacing the directory inside the workflow, wrappers and executable
    vt_dir = os.path.join(exp_dir, os.path.basename(reprozip.utils.vistrails_dir))
    vt_files = os.listdir(vt_dir)
    vt_files.remove(os.path.basename(reprozip.utils.cltools_dir))
    
    wrapper_dir = os.path.join(vt_dir, os.path.basename(reprozip.utils.cltools_dir))
    wrappers = os.listdir(wrapper_dir)
    
    script_file = os.path.join(exp_dir, os.path.basename(reprozip.utils.exec_path))
    f = open(script_file, 'r')
    contents = f.read()
    f.close()
    
    # replacing user directory
    contents = contents.replace(reprozip.utils.user_dir_var,
                                os.path.normpath(wdir))
    
    # adding python ref
#     ref = '#!%s\n\n' %reprozip.utils.executable_in_path('python')[1]
#     contents = ref + contents
    
    f = open(script_file, 'w')
    f.write(contents)
    f.close()
    
    # making the script executable
    os.chmod(script_file, stat.S_IXUSR | stat.S_IXOTH |
             stat.S_IXGRP | stat.S_IRUSR | stat.S_IROTH |
             stat.S_IRGRP | stat.S_IWUSR | stat.S_IWOTH |
             stat.S_IWGRP)
    
    for file in vt_files:
        file_path = os.path.join(vt_dir, file)
        try:
            f = open(file_path, 'r')
            contents = f.read()
            f.close()
            
            # replacing user directory
            contents = contents.replace(reprozip.utils.user_dir_var,
                                        os.path.normpath(wdir))
            
            f = open(file_path, 'w')
            f.write(contents)
            f.close()
        except:
            reprozip.debug.error('Error while replacing the directory info: %s' % sys.exc_info()[1])
            sys.exit(1)
                
    try:
        for wrapper in wrappers:
            wrapper_file = os.path.join(wrapper_dir, wrapper)
            f = open(wrapper_file, 'r')
            contents = f.read()
            f.close()
            
            # replacing user directory
            contents = contents.replace(reprozip.utils.user_dir_var,
                                        os.path.normpath(wdir))
            
            f = open(wrapper_file, 'w')
            f.write(contents)
            f.close()
    except:
        reprozip.debug.error('Error while replacing the directory info: %s' % sys.exc_info()[1])
        sys.exit(1)
    
    # putting the CLTools wrappers in the VisTrails directory
    cltools_dir = os.path.join(home,'.vistrails/CLTools')
    if not os.path.exists(cltools_dir):
        try:
            os.mkdir(cltools_dir)
        except:
            reprozip.debug.warning('Error while creating CLTools directory for VisTrails: %s' % sys.exc_info()[1])
            reprozip.debug.warning('Wrappers are inside the package, and you may copy them manually.')

    if os.path.exists(cltools_dir):
        try:
            for wrapper in wrappers:
                wrapper_file = os.path.join(wrapper_dir, wrapper)
                n_wrapper_file = os.path.join(cltools_dir, wrapper)
                shutil.copyfile(wrapper_file, n_wrapper_file)
        except:
            reprozip.debug.warning('Error while copying wrappers to VisTrails: %s' % sys.exc_info()[1])
            reprozip.debug.warning('Wrappers are inside the package, and you may copy them manually')
        
    # copying files and dependencies, if inside the copy directory
    cp_dir = os.path.join(exp_dir, os.path.basename(reprozip.utils.cp_dir))
    
    cp_files = []
    if os.path.exists(cp_dir):
        cp_files = os.listdir(cp_dir)
        for i in range(len(cp_files)):
            cp_files[i] = os.path.join(cp_dir, cp_files[i])

    for element in cp_files:
        path = os.sep.join(os.path.basename(element).split(reprozip.utils.sep))
        
        # checking if file already exists
        if os.path.exists(path):
            answer = ''
            while (answer.lower() != 'y') and (answer.lower() != 'n'):
                answer = raw_input('<warning> File "%s" already exists; copy and replace it (Y or N)? '
                                   % path)
            if answer.lower() == 'n':
                os.remove(element)
                continue
            
        # checking if dirname exists
        if not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except:
                reprozip.debug.warning('Could not create directory "%s": %s' %(os.path.dirname(path), sys.exc_info()[1]))
                continue
        
        # copying file
        try:
            shutil.copyfile(element, path)
            shutil.copystat(element, path)
            #os.remove(element)
            print '--------> File "%s" copied with success!' % path
        except:
            reprozip.debug.warning('Could not copy file "%s": %s' %(os.path.basename(path),sys.exc_info()[1]))
            continue
        
    # configuration files
    config_files = []
    config_file = os.path.join(exp_dir, os.path.basename(reprozip.utils.config_file_path))
    if os.path.exists(config_file):
        try:
            f = open(config_file, 'r')
            config_files = pickle.load(f)
            f.close()
        except:
            reprozip.debug.error('Could not de-serialize object structures: %s' % sys.exc_info()[1])
            sys.exit(1)
            
        for config in config_files:
            config = config.replace(reprozip.utils.user_dir_var,
                                    os.path.normpath(wdir))
            
            try:
                f = open(config, 'r')
                contents = f.read()
                f.close()
                
                # replacing user directory
                contents = contents.replace(reprozip.utils.user_dir_var,
                                            os.path.normpath(wdir))
                
                f = open(config, 'w')
                f.write(contents)
                f.close()
            except:
                reprozip.debug.error('Error while replacing the directory info: %s' % sys.exc_info()[1])
                sys.exit(1)
            
        
    # symbolic links
    
    # getting the mapping
    symlink_chain = {}
    symlink_dir = {}
    mapping_file = os.path.join(exp_dir, os.path.basename(reprozip.utils.symlink_path))
    try:
        f = open(mapping_file, 'r')
        [symlink_chain, symlink_dir] = pickle.load(f)
        f.close()
    except:
        reprozip.debug.error('Could not de-serialize object structures: %s' % sys.exc_info()[1])
        sys.exit(1)
        
    # creating the symbolic links
    for _symlink in symlink_chain:
        if symlink_dir.has_key(_symlink):
            dir_chain = symlink_dir[_symlink]
            for i in range(len(dir_chain)-1, 0, -1):
                if dir_chain[i-1] and dir_chain[i]:
                    symlink = os.path.normpath(dir_chain[i-1].replace(reprozip.utils.user_dir_var, wdir))
                    target = os.path.normpath(dir_chain[i].replace(reprozip.utils.user_dir_var, wdir))
                
                    if os.path.exists(symlink):
                        os.remove(symlink)
                    if not os.path.exists(os.path.dirname(symlink)):
                        os.makedirs(os.path.dirname(symlink))
                    os.symlink(target, symlink)
                
        chain = symlink_chain[_symlink]
        for i in range(len(chain)-1, 0, -1):
            if chain[i-1] and chain[i]:
                symlink = chain[i-1].replace(reprozip.utils.user_dir_var, os.path.normpath(wdir))
                target = chain[i].replace(reprozip.utils.user_dir_var, os.path.normpath(wdir))
            
                if os.path.exists(symlink):
                    os.remove(symlink)
                if not os.path.exists(os.path.dirname(symlink)):
                    os.makedirs(os.path.dirname(symlink))
                os.symlink(target, symlink)
            
    print '** Experiment successfully unpacked in "%s" **' % exp_dir
