#define _GNU_SOURCE
#include <dlfcn.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdint.h>
#include <errno.h>
#include "amdxdna_accel.h"
int ioctl(int fd,unsigned long req,...){va_list ap;va_start(ap,req);void*a=va_arg(ap,void*);va_end(ap);int(*next)(int,unsigned long,...)=dlsym(RTLD_NEXT,"ioctl");
 if(req==DRM_IOCTL_AMDXDNA_EXEC_CMD){struct amdxdna_drm_exec_cmd*c=a;struct amdxdna_drm_get_bo_info i={.handle=(uint32_t)c->cmd_handles};if(next(fd,DRM_IOCTL_AMDXDNA_GET_BO_INFO,&i))return -1;uint32_t*chain=mmap(0,4096,PROT_READ,MAP_SHARED,fd,i.map_offset);if(chain==MAP_FAILED)return -1;i=(struct amdxdna_drm_get_bo_info){.handle=chain[7]};munmap(chain,4096);if(next(fd,DRM_IOCTL_AMDXDNA_GET_BO_INFO,&i))return -1;uint32_t*ch=mmap(0,4096,PROT_READ|PROT_WRITE,MAP_SHARED,fd,i.map_offset);if(ch==MAP_FAILED)return -1;uint32_t lo=ch[4],hi=ch[5],words=ch[6],args[11];for(int k=0;k<11;k++)args[k]=ch[2+k];ch[0]=1u|(16u<<12)|(20u<<23);ch[1]=1;ch[2]=lo;ch[3]=hi;ch[4]=words*4;ch[5]=0;for(int k=0;k<11;k++)ch[6+k]=args[k];munmap(ch,4096);}
 return next(fd,req,a);}
