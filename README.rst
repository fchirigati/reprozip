========
ReproZip
========

ReproZip is a general tool for Linux distributions that simplifies the process of creating reproducible experiments from command-line executions, a frequently-used common denominator in computational science. It tracks operating system calls and creates a package that contains all the binaries, files and dependencies required to run a given command on the author's computational environment E. ReproZip also generates a workflow specification for the experiment, which can be used to help reviewers to explore and verify the experiment. A reviewer can extract the files and workflow on another environment E' (e.g., the reviewer's desktop), without interfering with any program or dependency already installed on E'.

Limitations:

* Environments E and E' need to have similar hardware architecture and Linux kernel.
* An experiment cannot be reproduced if its executables and scripts use hard-coded absolute paths.
* Repeatability of non-deterministic processes is not guaranteed.

For more information and to report bugs, contact Fernando Chirigati at fchirigati [at] nyu [dot] edu

Publications:

* SIGMOD 2013: http://vgc.poly.edu/~fchirigati/papers/SIGMOD-2013.pdf‎
* TaPP 2013: http://vgc.poly.edu/~fchirigati/papers/TaPP-2013.pdf

How To Install ReproZip
=======================

For installation instructions, please refer to INSTALL.txt.

How To Use ReproZip
===================

Packing
-------

Suppose your experiment is executed by the following command line::

    ./experiment input_file.txt -i 150 -o output_file.txt
    
First, issue the following command::

    reprozip --pack -e -c "./experiment input_file.txt -i 150 -o output_file.txt"
    
This will allow ReproZip to transparently gather all the necessary information. Argument *-e* means that the experiment should be executed prior to the creation of the package -- in case you have already executed it before with ReproZip, ReproZip may gather information stored in MongoDB rather than executing the experiment again.

This step will create a configuration file, named *rep.config*, in your working directory. Use it to exclude files that you do not want to be packed. You may also use Unix wildcards to exclude them (at the end of the configuration file, under *[exclude]*).

Next, use the following command (in the same working directory) to finally pack the experiment::

    reprozip --pack -g --name my_experiment
    
This command will create a package (*my_experiment.tar.gz*) in your working directory.

For more information about available ReproZip arguments, please use::

    reprozip --help

Unpacking
---------

Unpacking is quite simple. Just use::

    reprozip --exp my_experiment.tar.gz
    
This will unpack the experiment in a directory named *my_experiment* in the current working directory. To extract the experiment in another directory, just use the argument *--wdir* with the desired path.

Reproducing the Experiment
--------------------------

To reproduce the experiment, just use::

    ./my_experiment/rep.exec
    
Using VisTrails for Reproducibility
-----------------------------------

Alternatively, you can use the VisTrails workflow to reproduce, vary and explore the results. You can skip steps 1, 2 and 3 if you had VisTrails already installed when unpacking the experiment.

1. Download VisTrails at http://www.vistrails.org/index.php/Downloads and install it;
2. Create a directory named *CLTools* under *$HOME/.vistrails*;
3. Copy the *clt* file under *my_experiment/vistrails/cltools* to *$HOME/.vistrails/CLTools*;
4. Open VisTrails, and go to *File* -- *Import* -- *Workflow...*;
5. Choose the *xml* file under *my_experiment/vistrails*;
6. Play with the workflow!

For more information about VisTrails, please visit http://www.vistrails.org

MongoDB Considerations
======================

ReproZip uses MongoDB in the packing step to keep information about packed experiments. There is no option to use ReproZip in the packing step without MongoDB.

In case you already have MongoDB installed, you may find it useful to change the default settings of the mongod instance that ReproZip initiates at the beginning of the packing step (note that ReproZip kills this instance at the end of its execution), so that it reflects your installation. ReproZip creates its own database to include all the data, so you do not need to worry about it overriding your data.

The default settings can be found at ReproZip's configuration file (*$HOME/.reprozip/config*). The parameters are:

* *on*: indicates whether ReproZip should create its own mongod instance; set it to False in case you want to use a mongod instance that is already running;
* *port*: specifies the port for the mongod to listen for client connections;
* *dbpath*: specifies a directory for the mongod instance to store its data;
* *logpath*: specifies a path for the log file;
* *quiet*: indicates whether MongoDB should limit the amount of output; setting it to True keeps the output significantly smaller.

Acknowledgements
================

* Jesse Lingeman
* Lis Custodio
* Tiago Etiene
* Sinesio Pesco
* Claudio Silva
* VisTrails team
