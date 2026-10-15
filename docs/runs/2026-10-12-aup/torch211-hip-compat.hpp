#pragma once
#include <c10/hip/HIPStream.h>
#include <c10/hip/HIPGuard.h>
namespace c10::hip {
using HIPStream = c10::cuda::CUDAStream;
using HIPStreamGuard = c10::cuda::CUDAStreamGuard;
}
