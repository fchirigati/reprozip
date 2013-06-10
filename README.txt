========
ReproZip
========

ReproZip is a general tool for Linux distributions that simplifies the process of creating reproducible experiments from command-line executions, a frequently-used common denominator in computational science. It tracks operating system calls and creates a package that contains all the binaries, files and dependencies required to run a given command on the author's computational environment E. ReproZip also generates a workflow specification for the experiment, which can be used to help reviewers to explore and verify the experiment. A reviewer can extract the files and workflow on another environment E' (e.g., the reviewer's desktop), without interfering with any program or dependency already installed on E'.

Limitations:

* An experiment cannot be reproduced if its executables and scripts use hard-coded absolute paths.
* Repeatability of non-deterministic processes is not guaranteed.

For more information, please contact Fernando Chirigati at fchirigati@nyu.edu
