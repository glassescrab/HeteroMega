#define _GNU_SOURCE
#include <stdint.h>
#include <stdarg.h>
#include <string.h>
#include <dlfcn.h>
#include <sys/ioctl.h>
#include <stdio.h>
#include "amdxdna_accel.h"
struct cloud_qos { uint32_t fields[6]; uint32_t user_start_col; uint32_t reserved; };
int ioctl(int fd, unsigned long request, ...) {
 va_list ap; va_start(ap,request); void* arg=va_arg(ap,void*); va_end(ap);
 int (*real_ioctl)(int,unsigned long,...)=dlsym(RTLD_NEXT,"ioctl");
 if(request==DRM_IOCTL_AMDXDNA_CREATE_CTX && arg) {
  struct amdxdna_drm_create_ctx* old=arg;
  if(old->qos_p) {
   struct cloud_qos q={0}; memcpy(q.fields,(void*)(uintptr_t)old->qos_p,sizeof(q.fields)); q.user_start_col=0xff;
   struct amdxdna_drm_create_ctx c=*old; uint64_t oldp=c.qos_p; c.qos_p=(uint64_t)(uintptr_t)&q;
   int r=real_ioctl(fd,request,&c); c.qos_p=oldp; *old=c;
   fprintf(stderr,"XDNA QoS compatibility translation: context result %d\n",r); return r;
  }
 }
 return real_ioctl(fd,request,arg);
}
