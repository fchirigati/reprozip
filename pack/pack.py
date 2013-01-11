from experiment.experiment import Experiment
from tracer import Tracer
import inspect
import utils
import pickle
import argparse
import sys
import os


if __name__ == '__main__':
    
    # Tracer information
    
    # TODO: change log dir to /opt/log
    LOG_BASEDIR = os.path.join(os.getenv('HOME'), 'log')

    current_file = os.path.abspath(inspect.getfile(inspect.currentframe()))

    if sys.platform.startswith('darwin'):
        PASS_LITE = os.path.normpath(os.path.join(os.path.dirname(current_file),
                                                  'DTrace/pass-lite-mac.d'))
    elif sys.platform.startswith('linux'):
        PASS_LITE = os.path.normpath(os.path.join(os.path.dirname(current_file),
                                                  'SystemTap/pass-lite.stp'))
    else:
        print '<error> Sorry, platform %s not supported.' % sys.platform
        sys.exit(0)
    
    ####################
    
    description = 'Makes the experiment reproducible by creating a package for it. '
    description += 'A VisTrails workflow is created for the experiment inside the package.'
    
    execute_help = 'indicates that the command line should be executed prior to '
    execute_help += 'the creation of the package'
    
    command_help = 'the command line of the experiment'
    
    wdir_help = 'the working directory for the execution of the command line'
    
    env_help = 'a mapping that defines the environment variables for the execution '
    env_help += 'of the program'
    
    generate_help = 'indicates that the experiment is already configured; '
    generate_help += 'the experiment MUST be configured before the creation of '
    generate_help += 'the package'
    
    name_help = 'name of the package - by default, the name of the package contains '
    name_help += 'either the name of the input or the beginning of its command line'
    
    verbose_help = 'verbose option'
    
#    def boolean(string):
#        if (string.title() == 'True') or (string.title() == 'False'):
#            return eval(string.title())
#        else:
#            msg = '%r is not a boolean value' % string
#            raise argparse.ArgumentTypeError(msg)
 
    parser = argparse.ArgumentParser(prog        = 'pack',
                                     description = description)

    parser.add_argument('--command', '-c', help=command_help)
    parser.add_argument('--version', '-v', action='version', version='%(prog)s 0.1')
    parser.add_argument('--execute', '-e', action='store_true', help=execute_help)
    parser.add_argument('--wdir', '-w', help=wdir_help)
    parser.add_argument('--env', help=env_help)
    parser.add_argument('--generate', '-g', action='store_true', help=generate_help)
    parser.add_argument('--name', '-n', help=name_help)
    parser.add_argument('--verbose', action='store_true', help=verbose_help)
    
    namespace = parser.parse_args()
    args = vars(namespace)
    
    # creating an experiment
    rep_experiment = Experiment()
    
    # configuration mode
    if not (args['generate']):
        
        rep_experiment.verbose = args['verbose']
        
        rep_experiment.command_line_info = args['command']
            
        if args['execute']:
            main_tracer = Tracer(log_basedir = LOG_BASEDIR,
                                 pass_lite   = PASS_LITE)
            
            main_tracer.run_tracer()
            rep_experiment.execute(args['wdir'], args['env'])
            main_tracer.stop_tracer()
            
            main_tracer.store_process_data()
            
        # retrieving data
        rep_experiment.retrieve_experiment_data(db_name         = 'reprozip_db',
                                                collection_name = 'process_trace')
        
        # configuring
        rep_experiment.configure()
        
        # pickling object structures
        try:
            f = open(utils.objs_path, 'w')
            pickle.dump(rep_experiment, f, pickle.HIGHEST_PROTOCOL)
            f.close()
        except:
            print '<error> Could not serialize object structures.'
            print '        %s' % sys.exc_info()[1]
            sys.exit(1)
        
    # generation mode
    else:
        # de-serializing object structures
        try:
            f = open(utils.objs_path, 'r')
            rep_experiment = pickle.load(f)
            f.close()
        except:
            print '<error> Could not de-serialize object structures'
            print '        %s' % sys.exc_info()[1]
            sys.exit(1)
            
        rep_experiment.verbose = args['verbose']
        
        # processing configuration file
        rep_experiment.process_config_file()
    
        # generating VisTrails workflow
        rep_experiment.generate_reproducible_experiment(args['name'])
        
        # packing everything in a zip file
        rep_experiment.pack()
