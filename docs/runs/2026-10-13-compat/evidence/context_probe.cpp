#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <cerrno>
#include "/notebooks/heteromega-baseline-logs/amdxdna-cloud.h"
int main(int argc,char**argv){
 const bool legacy=argc>1 && !strcmp(argv[1],"legacy");
 const bool aligned=argc>2 && !strcmp(argv[2],"aligned");
 const bool map=!(argc>2 && !strcmp(argv[2],"nomap"));
 const unsigned tiles=argc>3?atoi(argv[3]):32;
 const unsigned opc=argc>4?atoi(argv[4]):2048;
 const size_t size=64UL*1024*1024;
 int fd=open("/dev/accel/accel0",O_RDWR); if(fd<0){perror("open");return 1;}
 amdxdna_drm_create_bo b{}; b.size=size;b.type=AMDXDNA_BO_DEV_HEAP;
 if(ioctl(fd,DRM_IOCTL_AMDXDNA_CREATE_BO,&b)){perror("create heap");return 2;}
 amdxdna_drm_get_bo_info info{};info.handle=b.handle;
 if(ioctl(fd,DRM_IOCTL_AMDXDNA_GET_BO_INFO,&info)){perror("get heap");return 3;}
 void* reservation=nullptr; void* desired=nullptr; if(aligned){reservation=mmap(nullptr,2*size,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0); if(reservation==MAP_FAILED)return 5; desired=(void*)(((uintptr_t)reservation+size-1)&~(size-1));}
 void* p=MAP_FAILED; if(map)p=mmap(desired,size,PROT_READ|PROT_WRITE,MAP_SHARED|(aligned?MAP_FIXED:0),fd,info.map_offset);
 printf("heap handle=%u map=%p errno=%d alignment=%zu size=%zu ctxsize=%zu\n",b.handle,p,errno,(uintptr_t)p%size,size,sizeof(amdxdna_drm_create_hwctx));
 amdxdna_qos_info q{};q.user_start_col=legacy?0:USER_START_COL_NOT_REQUESTED;
 amdxdna_drm_create_hwctx c{};c.qos_p=(uint64_t)&q;c.max_opc=opc;c.num_tiles=tiles;
 int rc=ioctl(fd,DRM_IOCTL_AMDXDNA_CREATE_HWCTX,&c),e=errno;
 printf("context qos=%s mapped=%d tiles=%u opc=%u rc=%d errno=%d (%s) handle=%u\n",legacy?"legacy-zero":"current",map,tiles,opc,rc,e,strerror(e),c.handle);
 if(!rc){amdxdna_drm_destroy_hwctx d{};d.handle=c.handle;ioctl(fd,DRM_IOCTL_AMDXDNA_DESTROY_HWCTX,&d);}
 if(reservation)munmap(reservation,2*size); else if(p!=MAP_FAILED)munmap(p,size);close(fd);return rc?4:0;
}
