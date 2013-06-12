========
ReproZip
========

ReproZip is a general tool for Linux distributions that simplifies the process of creating reproducible experiments from command-line executions, a frequently-used common denominator in computational science. It tracks operating system calls and creates a package that contains all the binaries, files and dependencies required to run a given command on the author's computational environment E. ReproZip also generates a workflow specification for the experiment, which can be used to help reviewers to explore and verify the experiment. A reviewer can extract the files and workflow on another environment E' (e.g., the reviewer's desktop), without interfering with any program or dependency already installed on E'.

Limitations:

* Environments E and E' need to have similar hardware architecture and Linux kernel.
* An experiment cannot be reproduced if its executables and scripts use hard-coded absolute paths.
* Repeatability of non-deterministic processes is not guaranteed.

For installation instructions, please refer to INSTALL.txt.

How To Use ReproZip
===================

TODO

MongoDB considerations
======================

ReproZip uses MongoDB in the packing step to keep information about packed experiments. There is no option to use ReproZip in the packing step without MongoDB.

In case you already have MongoDB installed, you may find it useful to change the default settings of the mongod instance that ReproZip initiates at the beginning of the packing step (note that ReproZip kills this instance at the end of its execution), so that it reflects your installation. ReproZip creates its own database to include all the data, so you do not need to worry about it overriding your data.

The default settings can be found at ReproZip's configuration file ("$HOME/.reprozip.config"). The parameters are:

* "on": indicates whether ReproZip should create its own mongod instance; set it to False in case you want to use a mongod instance that is already running;
* "port": specifies the port for the mongod to listen for client connections;
* "dbpath": specifies a directory for the mongod instance to store its data;
* "logpath": specifies a path for the log file;
* "quiet": indicates whether MongoDB should limit the amount of output; setting it to True keeps the output significantly smaller.

For more information, please contact Fernando Chirigati at fchirigati@nyu.edu
