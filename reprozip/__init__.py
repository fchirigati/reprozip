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

def run():
    
    description = 'a tool to make reproducible experiments'
    
    pack_help = 'indicates the packing phase of ReproZip'
    
    execute_help = 'indicates that the command line should be executed prior to '
    execute_help += 'the creation of the package'
    
    command_help = 'the command line of the experiment'
    
    wdir_help = 'for the packing phase, it represents the working directory for the execution of the command line; '
    wdir_help += 'for the unpacking phase, it represents the working directory where the experiment should be extracted '
    wdir_help += '(if different from the current one)'
    
    env_help = 'a mapping that defines the environment variables for the execution '
    env_help += 'of the program'
    
    generate_help = 'indicates that the experiment is already configured; '
    generate_help += 'the experiment MUST be configured before the creation of '
    generate_help += 'the package'
    
    name_help = 'name of the package - by default, the name of the package contains '
    name_help += 'either the name of the input or the beginning of its command line'
    
    exp_help = 'the experiment to be unpacked (a tar.gz file) - the whole path '
    exp_help += 'should be specified'
    
    verbose_help = 'verbose option'
    
#    def boolean(string):
#        if (string.title().lower() == 'true') or (string.title().lower() == 'false'):
#            return eval(string.title())
#        else:
#            msg = '%r is not a boolean value' % string
#            raise argparse.ArgumentTypeError(msg)
 
    parser = argparse.ArgumentParser(prog        = 'reprozip',
                                     description = description)
    parser.add_argument('--version', '-v', action='version', version='%(prog)s 0.1.0-beta')
    parser.add_argument('--verbose', action='store_true', help=verbose_help)
    
    # packing / unpacking
    parser.add_argument('--pack', '-p', action='store_true', help=pack_help)
    
    # packing
    parser.add_argument('--command', '-c', help=command_help)
    parser.add_argument('--execute', '-e', action='store_true', help=execute_help)
    parser.add_argument('--wdir', '-w', help=wdir_help)
    parser.add_argument('--env', help=env_help)
    parser.add_argument('--generate', '-g', action='store_true', help=generate_help)
    parser.add_argument('--name', '-n', help=name_help)
    
    # unpacking
    parser.add_argument('--exp', help=exp_help)
    
    namespace = parser.parse_args()
    args = vars(namespace)
    
    if args['pack']:
        from reprozip.pack import pack
        pack.pack(args)
    else:
        from reprozip.unpack import unpack
        unpack.unpack(args)