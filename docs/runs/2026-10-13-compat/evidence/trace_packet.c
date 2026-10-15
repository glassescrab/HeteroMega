#define _GNU_SOURCE
#include <dlfcn.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdint.h>
#include <errno.h>
#include "amdxdna_accel.h"
static volatile uint32_t *chain,*child;static int n;
int ioctl(int fd,unsigned long req,...){va_list ap;va_start(ap,req);void*a=va_arg(ap,void*);va_end(ap);int(*next)(int,unsigned long,...)=dlsym(RTLD_NEXT,"ioctl");
 if(req==DRM_IOCTL_AMDXDNA_EXEC_CMD && n++<2){struct amdxdna_drm_exec_cmd*c=a;uint32_t*args=(void*)(uintptr_t)c->args;struct amdxdna_drm_get_bo_info i={.handle=(uint32_t)c->cmd_handles};next(fd,DRM_IOCTL_AMDXDNA_GET_BO_INFO,&i);chain=mmap(0,4096,PROT_READ,MAP_SHARED,fd,i.map_offset);i=(struct amdxdna_drm_get_bo_info){.handle=chain[7]};next(fd,DRM_IOCTL_AMDXDNA_GET_BO_INFO,&i);child=mmap(0,4096,PROT_READ,MAP_SHARED,fd,i.map_offset);i=(struct amdxdna_drm_get_bo_info){.handle=args[0]};next(fd,DRM_IOCTL_AMDXDNA_GET_BO_INFO,&i);fprintf(stderr,"PACKET inst_bo_addr=%llx encoded=%08x:%08x childhdr=%08x chainhdr=%08x\n",(unsigned long long)i.xdna_addr,child[5],child[4],child[0],chain[0]);}
 int r=next(fd,req,a),e=errno;if(req==DRM_IOCTL_SYNCOBJ_TIMELINE_WAIT&&n<=2&&child)fprintf(stderr,"AFTER_WAIT rc=%d chain_state=%u child_state=%u submit_idx=%u error_idx=%u\n",r,chain[0]&15,child[0]&15,chain[2],chain[3]);errno=e;return r;}
