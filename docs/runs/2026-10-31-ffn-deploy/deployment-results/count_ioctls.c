#define _GNU_SOURCE
#include <dlfcn.h>
#include <sys/ioctl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdint.h>
#include <errno.h>
#include "amdxdna_accel.h"
static unsigned long ctx_ok,exec_ok,exec_fail,legacy_ok,legacy_fail,timeline_ok,timeline_fail;
int ioctl(int fd,unsigned long req,...) {
 va_list ap;va_start(ap,req);void *a=va_arg(ap,void*);va_end(ap);
 int (*real_ioctl)(int,unsigned long,...)=dlsym(RTLD_NEXT,"ioctl");
 int ret=real_ioctl(fd,req,a);int e=errno;
 if(req==DRM_IOCTL_AMDXDNA_CREATE_CTX && ret==0)__sync_fetch_and_add(&ctx_ok,1);
 if(req==DRM_IOCTL_AMDXDNA_EXEC_CMD)__sync_fetch_and_add(ret==0?&exec_ok:&exec_fail,1);
 if(req==DRM_IOCTL_AMDXDNA_WAIT_CMD)__sync_fetch_and_add(ret==0?&legacy_ok:&legacy_fail,1);
 if(req==DRM_IOCTL_SYNCOBJ_TIMELINE_WAIT)__sync_fetch_and_add(ret==0?&timeline_ok:&timeline_fail,1);
 errno=e;return ret;
}
__attribute__((destructor)) static void report(void) {fprintf(stderr,"IOCTL_COUNTS ctx_ok=%lu exec_ok=%lu exec_fail=%lu legacy_ok=%lu legacy_fail=%lu timeline_ok=%lu timeline_fail=%lu\n",ctx_ok,exec_ok,exec_fail,legacy_ok,legacy_fail,timeline_ok,timeline_fail);}
