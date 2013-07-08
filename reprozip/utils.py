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

import time
import json
import datetime
import subprocess
import os

VERSION = '0.1.0-beta'

# Variables that represent some directories that are to be replaced later
# in the code
user_dir_var = '$USER_DIR$'
rep_dir_var = '$REP_DIR$'
#home_var = '$HOME$'

# Variables that represent some directories to be used when packing the
# experiment
exp_dir = os.path.join(rep_dir_var, 'exp')
vistrails_dir = os.path.join(rep_dir_var, 'vistrails')
cltools_dir = os.path.join(rep_dir_var, 'vistrails', 'cltools')
cp_dir = os.path.join(rep_dir_var, 'rz_cp')

exec_path = os.path.join(rep_dir_var, 'rep.exec')
config_path = os.path.join(os.getcwd(), 'rep.config')
objs_path = os.path.join(os.getcwd(), '.rep.objs')
symlink_path = os.path.join(rep_dir_var, '.symlinks')
config_file_path = os.path.join(rep_dir_var, '.config_files')

# Path separator used to copy files and dependencies
sep = '_$_'

# Separators for environment variables
sep_envs = '&_&&_&'
sep_env = '&&=&&'

# Environment variables
ld_library_path = '$LD_LIBRARY_PATH$'
pythonpath = '$PYTHONPATH$'
path = '$PATH$'

def log_basedir():
    """
    Returns the location of ReproZip log files.
    """
    
    return os.path.join(os.getenv('HOME'), '.reprozip')

# MongoDB defaults
mongodb_on = 'True'
mongodb_port = '27020'
mongodb_dbpath = os.path.join(log_basedir(), 'mongodb')
mongodb_logpath = os.path.join(mongodb_dbpath, 'mongodb.log')
mongodb_quiet = 'True'
mongodb_journaling = 'False'

# names in the database
mongodb_database = 'reprozip_db'
mongodb_collection = 'process_trace'
mongodb_session_collection = 'session_status'

def executable_in_path(executable):
    """
    Checks if executable is in PATH.
    """
    
    p = subprocess.Popen(['which', executable],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    
    if stdout == '':
        return (False, None)
    else:
        return (True, stdout.split()[0])

###############################################################################
# This part of the code came from Burrito System
# Burrito System Paper: Philip J. Guo and Margo Seltzer. Burrito: Wrapping Your
#  Lab Notebook in Computational Infrastructure. In Proceedings of the USENIX
#  Workshop on the Theory and Practice of Provenance (TaPP), June 2012.
# Many thanks to Philip Guo (http://pgbovine.net/)

def get_ms_since_epoch():
    milliseconds_since_epoch = int(time.time() * 1000)
    return milliseconds_since_epoch

def to_compact_json(obj):
    # use the most compact separators:
    return json.dumps(obj, separators=(',',':'))

def encode_datetime(t):
    return datetime.datetime.fromtimestamp(float(t) / 1000)

HOMEDIR = os.environ['HOME']
assert HOMEDIR

def prettify_filename(fn):
    # abbreviate home directory:
    if fn.startswith(HOMEDIR):
        fn = '~' + fn[len(HOMEDIR):]
    return fn

