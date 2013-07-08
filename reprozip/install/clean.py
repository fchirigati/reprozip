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

from reprozip.pack.mongodb import Mongod
import reprozip.install.utils
import reprozip.utils
import reprozip.debug
import pymongo
import time
import sys
import os

def clean_stap():
    """
    Removes old directories of SystemTap files.
    """
    
    reprozip.debug.success('Removing old directories of SystemTap...')
    
    try:
        user = os.getenv('USER')
        l = os.listdir(reprozip.utils.log_basedir())
        dirs = []
        for path in l:
            if user in path:
                dirs.append(path)
                
        # removing previous and current session
        dirs.sort()
        dirs.reverse()
        dirs = dirs[2:]
        
        base_dir = reprozip.utils.log_basedir()
        sudo = reprozip.install.utils.guess_sudo()
        for dir in dirs:
            cmd = sudo + ' rm -r ' + os.path.join(base_dir, dir)
            reprozip.install.utils.execute_install_cmd(cmd)
            
    except:
        reprozip.debug.error(sys.exc_info()[1])
        sys.exit(1)
    
    reprozip.debug.success('Done!')

def clean_mongodb():
    """
    Drops ReproZip collections from the database.
    """
    
    reprozip.debug.success('Cleaning ReproZip database in MongoDB...')
    
    mongod = Mongod()
    mongod.run()
    
    # give mongod some time to begin
    time.sleep(3)
    
    # connecting to MongoDB
    try:
        conn = pymongo.MongoClient(port=int(mongod.port))
    except:
        reprozip.debug.error('Could not connect to MongoDB: %s' %sys.exc_info()[1])
        mongod.stop()
        sys.exit(1)

    # accessing the database
    try:
        db = conn[reprozip.utils.mongodb_database]
    except:
        reprozip.debug.error('Could not open the database: %s' %sys.exc_info()[1])
        conn.close()
        mongod.stop()
        sys.exit(1)

    # dropping ReproZip collections
    try:
        db.drop_collection(reprozip.utils.mongodb_collection)
        db.drop_collection(reprozip.utils.mongodb_session_collection)
    except:
        reprozip.debug.error('Error while dropping collections: %s' %sys.exc_info()[1])
        conn.close()
        mongod.stop()
        sys.exit(1)
        
    conn.close()
    mongod.stop()
    
    reprozip.debug.success('Done!')
    