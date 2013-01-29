/*
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
*/

/*int reads[pid_t, int64_t];
int writes[pid_t, int64_t];*/

#pragma D option quiet

/* ==== */
/* Open */
/* ==== */

syscall::open:entry
{
	self->filename = copyinstr(arg0);
}

syscall::open:return
/self->filename != "."/
{
	self->fd = arg0;
	self->rw_flags = fds[arg0].fi_oflags & 0x3;
}

/* Assuming for now that self->filename is already an absolute path */
syscall::open:return
/arg1 >= 0 && self->filename != "."/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("OPEN_ABSPATH||%s\n", self->filename);
}

/* O_RDWR */
syscall::open:return
/errno == 0 && self->rw_flags == 0x2 && self->filename != "."/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("OPEN_READWRITE||%s||%d\n", self->filename, self->fd);

	/*delete reads[pid, self->fd];
	delete writes[pid, self->fd];*/
}

/* O_WRONLY */
syscall::open:return
/errno == 0 && self->rw_flags == 0x1 && self->filename != "."/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("OPEN_WRITE||%s||%d\n", self->filename, self->fd);

	/*delete reads[pid, self->fd];
	delete writes[pid, self->fd];*/
}

/* O_RDONLY */
syscall::open:return
/errno == 0 && self->rw_flags == 0x0 && self->filename != "."/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("OPEN_READ||%s||%d\n", self->filename, self->fd);

	/*delete reads[pid, self->fd];
	delete writes[pid, self->fd];*/
}

/* ============ */
/* Read / Write */
/* ============ */

syscall::read:entry,
syscall::write:entry
{
	self->fd = arg0;
}

syscall::read:return
/*errno == 0 && !reads[pid, self->fd]*/
/errno == 0/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("READ||%d\n", self->fd);
	
	reads[pid, self->fd] = 1;
}

syscall::write:return
/*errno == 0 && !writes[pid, self->fd]*/
/errno == 0/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("WRITE||%d\n", self->fd);
	
	writes[pid, self->fd] = 1;
}

/* ==== */
/* Mmap */
/* ==== */

syscall::mmap:entry
{
	self->fd = arg4;
	self->rw_prot = arg2 & 0x3;
}

/* PROT_READ */
syscall::mmap:return
/errno == 0 && self->rw_prot == 0x1/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("MMAP_READ||%d\n", self->fd);
}

/* PROT_WRITE */
syscall::mmap:return
/errno == 0 && self->rw_prot == 0x2/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("MMAP_WRITE||%d\n", self->fd);
}

/* PROT_READWRITE */
syscall::mmap:return
/errno == 0 && self->rw_prot == 0x0/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("MMAP_READWRITE||%d\n", self->fd);
}

/* ===== */
/* Close */
/* ===== */

syscall::close:entry
{
	self->fd = arg0;
}

syscall::close:return
/errno == 0/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("CLOSE||%d\n", self->fd);

	/*delete reads[pid, self->fd];
	delete writes[pid, self->fd];*/
}

/* ==== */
/* Pipe */
/* ==== */

/*syscall::pipe:entry
{
	size = sizeof(int64_t);

	self->pipe0 = copyin(arg0, size);
	self->pipe1 = copyin(arg0 + size, size);
}*/

syscall::pipe:return
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	/*printf("PIPE||%d||%d\n", *(int64_t*)self->pipe0, *(int64_t*)self->pipe1);*/
	printf("PIPE||%d||%d\n", arg0, uthread->uu_rval[1]);
}

/* === */
/* Dup */
/* === */

syscall::dup:entry
{
	self->fd = arg0;
}

syscall::dup:return
/errno == 0/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("DUP||%d||%d\n", self->fd, arg0)
}

/* ==== */
/* Dup2 */
/* ==== */

syscall::dup2:entry
{
	self->oldfd = arg0;
	self->newfd = arg1;
}

syscall::dup2:return
/errno == 0/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("DUP2||%d||%d||%d\n", self->oldfd, self->newfd, arg0)

        /*delete reads[pid(), self->newfd]
    	delete writes[pid(), self->newfd]*/
}

/* ==== */
/* Fork */
/* ==== */

syscall::fork:return
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("FORK||%d\n", arg0);
}

/* ====== */
/* Execve */
/* ====== */

syscall::execve:entry
{
	/* Trying to get the absolute path for cwd (but it did not work) */
	/*printf("PWD: %s\n", stringof(curproc->p_fd->fd_cdir->v_name));*/

	self->filename = copyinstr(arg0);
	self->argc = curproc->p_argc;
	/*printf("ARGC: %d\n", self->argc);*/
	/*self->argv = (uint64_t)copyin(curproc->p_dtrace_argv, sizeof(uint64_t) * self->argc);*/

	/*printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("EXECVE||%s||%s\n", cwd, self->filename)*/
	/*printf("EXECVE||%s||%s||%s\n", cwd, self->filename, args)*/
	/* Note: cwd is not in absolute path! */
}

/*syscall::execve:return
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("EXECVE_RETURN||%d\n", arg0);
}*/

/* Some code adapted from https://gist.github.com/1242279                                */
/* Using proc, since syscall::execve:entry did not work well for Mac                     */
/* Note that the program must have at most 9 arguments                                   */
/* Here, we consider only successful executions - and we are interesting in those anyway */ 

proc:::exec
{
	self->filename = args[0];
}

proc:::exec-success
{
	/* Not checking if architecture is x64 - but it is eventually necessary */
	self->isx64 = (curproc->p_flag & P_LP64) != 0;

	self->ptrsize = sizeof(uint64_t);
	self->argc = curproc->p_argc;
	self->argc = (self->argc < 0) ? 0 : self->argc;
	self->argv = (uint64_t)copyin(curproc->p_dtrace_argv, self->ptrsize * self->argc);

	/* Args */
	self->args = "";
	self->args = (0 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*0)), "\" "))) : self->args;
	self->args = (1 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*1)), "\" "))) : self->args;
	self->args = (2 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*2)), "\" "))) : self->args;
	self->args = (3 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*3)), "\" "))) : self->args;
	self->args = (4 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*4)), "\" "))) : self->args;
	self->args = (5 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*5)), "\" "))) : self->args;
	self->args = (6 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*6)), "\" "))) : self->args;
	self->args = (7 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*7)), "\" "))) : self->args;
	self->args = (8 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*8)), "\" "))) : self->args;
	self->args = (9 < self->argc) ? strjoin(self->args, strjoin("\"", strjoin(copyinstr((user_addr_t)*(uint64_t*)((self->argv) + sizeof(uint64_t)*9)), "\" "))) : self->args;

	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("EXECVE||%s||%s||%s\n", cwd, self->filename, self->args);

	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("EXECVE_RETURN||%d\n", 0);
}

/*proc:::exec-failure
{
}*/

/*proc:::exit
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("EXECVE_RETURN||%d\n", args[0]);
}*/

/* ==== */
/* Exit */
/* ==== */

syscall::exit:entry
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("EXIT_GROUP||%d\n", arg0);
}

/* ====== */
/* Rename */
/* ====== */

syscall::rename:entry
/errno == 0/
{
	printf("%d||%d||%d||%d||%s||", (uint64_t) (walltimestamp / 1000000), pid, ppid, uid, execname);
	printf("RENAME||%s||%s\n", copyinstr(arg0), copyinstr(arg1));
}
