import time
import json
import datetime
import os

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

# Path separator used to copy files and dependencies
sep = '_$_'

# Separators for environment variables
sep_envs = '&_&&_&'
sep_env = '&&=&&'

# Environment variables
ld_library_path = '$LD_LIBRARY_PATH$'
pythonpath = '$PYTHONPATH$'
path = '$PATH$'

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

