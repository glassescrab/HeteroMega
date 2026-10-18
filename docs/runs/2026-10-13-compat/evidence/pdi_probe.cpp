#include "npu_matmul_func/npu_matmul_func.hpp"
#include <cstdio>
int main(){int fd=open("/dev/accel/accel0",O_RDWR);if(fd<0){perror("open");return 1;}
 uint32_t heap=0;int r=alloc_heap(fd,64*1024*1024,&heap);printf("heap result=%d handle=%u\n",r,heap);if(r)return 2;
 hwctxt ctx{};r=createHWctxt(fd,ctx,"/notebooks/HeteroMosaic-baseline/hw_bins/npu2/8192x2048x2048/bf16_int4AWQ_bf16_M/final_1024x2048x2048_64x128x64_8c_bf16_int4AWQ_bf16.pdi",32);printf("PDI context result=%d\n",r);close(fd);return r?3:0;}
