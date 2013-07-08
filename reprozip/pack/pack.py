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

from reprozip.pack.experiment.experiment import Experiment
from reprozip.pack.mongodb import Mongod
from reprozip.pack.tracer import Tracer
from reprozip.install.utils import guess_os
import reprozip.debug
import reprozip.utils
import inspect
import pickle
import argparse
import time
import sys
import os


def pack(args):
    
    # tracer information
    current_file = os.path.abspath(inspect.getfile(inspect.currentframe()))
    os_ = guess_os()

    if os_ == 'darwin':
        PASS_LITE = os.path.normpath(os.path.join(os.path.dirname(current_file),
                                                  'dtrace/pass-lite-mac.d'))
    elif os_ == 'linux':
        PASS_LITE = os.path.normpath(os.path.join(os.path.dirname(current_file),
                                                  'system_tap/pass-lite.stp'))
    else:
        msg = 'Sorry, platform %s not supported.' % os_
        reprozip.debug.error(msg)
        sys.exit(0)

    # creating an experiment
    rep_experiment = Experiment()
    
    # configuration mode
    if not (args['generate']):
        
        rep_experiment.verbose = args['verbose']
        
        rep_experiment.command_line_info = args['command']
        
        # initializing mongod instance
        reprozip.debug.verbose(args['verbose'], 'Initializing MongoDB instance...')
        mongod = Mongod()
        mongod.run()
            
        if args['execute']:
            main_tracer = Tracer(log_basedir = reprozip.utils.log_basedir(),
                                 pass_lite   = PASS_LITE)
            
            try:
                reprozip.debug.verbose(args['verbose'], 'Initializing tracer...')
                main_tracer.run_tracer()
                
                rep_experiment.execute(args['wdir'], args['env'])
                
                reprozip.debug.verbose(args['verbose'], 'Stopping tracer...')
                #main_tracer.check_tracer()
                main_tracer.stop_tracer()
                
                reprozip.debug.verbose(args['verbose'], 'Storing provenance in MongoDB...')
                main_tracer.store_process_data(port=mongod.port)
            except:
                main_tracer.stop_tracer()
                mongod.stop()
                sys.exit(1)
        else:
            # give mongod some time to begin
            time.sleep(3)
            
        # retrieving data
        try:
            reprozip.debug.verbose(args['verbose'], 'Starting retrieval of experiment data...')
            rep_experiment.retrieve_experiment_data(db_name         = reprozip.utils.mongodb_database,
                                                    collection_name = reprozip.utils.mongodb_collection,
                                                    port            = mongod.port)
        except:
            mongod.stop()
            sys.exit(1)
        
        # stopping mongod instance
        reprozip.debug.verbose(args['verbose'], 'Stopping MongoDB instance...')
        mongod.stop()
        
        # configuring
        rep_experiment.configure()
        
        # pickling object structures
        try:
            f = open(reprozip.utils.objs_path, 'w')
            pickle.dump(rep_experiment, f, pickle.HIGHEST_PROTOCOL)
            f.close()
        except:
            reprozip.debug.error('Could not serialize object structures: %s' % sys.exc_info()[1])
            sys.exit(1)
        
    # generation mode
    else:
        # de-serializing object structures
        try:
            f = open(reprozip.utils.objs_path, 'r')
            rep_experiment = pickle.load(f)
            f.close()
        except:
            reprozip.debug.error('Could not de-serialize object structures: %s' % sys.exc_info()[1])      
            sys.exit(1)
            
        rep_experiment.verbose = args['verbose']
        
        # processing configuration file
        rep_experiment.process_config_file()
    
        # generating VisTrails workflow
        rep_experiment.generate_reproducible_experiment(args['name'])
        
        # packing everything in a zip file
        rep_experiment.pack()
