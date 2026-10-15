#define _GNU_SOURCE
#include <dlfcn.h>
#include <sys/ioctl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdint.h>
#include "amdxdna_accel.h"
int ioctl(int fd,unsigned long req,...){va_list ap;va_start(ap,req);void* a=va_arg(ap,void*);va_end(ap);
 if(req==DRM_IOCTL_AMDXDNA_EXEC_CMD){struct amdxdna_drm_exec_cmd*c=a;uint32_t*p=(void*)(uintptr_t)c->args;fprintf(stderr,"EXEC ctx=%u cmd=%llu argc=%u handles:",c->ctx,(unsigned long long)c->cmd_handles,c->arg_count);for(unsigned i=0;i<c->arg_count;i++)fprintf(stderr," %u",p[i]);fprintf(stderr,"\n");}
 int(*next)(int,unsigned long,...)=dlsym(RTLD_NEXT,"ioctl");return next(fd,req,a);}
