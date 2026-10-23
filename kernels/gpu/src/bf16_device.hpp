// bf16 helpers for HIP device code. bf16 values are handled as raw uint16_t bits.
#pragma once

#include <hip/hip_runtime.h>

#include <cstdint>
#include <stdexcept>
#include <string>

namespace heteromega {

__device__ __forceinline__ float bf16_to_float(uint16_t b) { return __uint_as_float(static_cast<uint32_t>(b) << 16); }

// Round to nearest even. NaN stays NaN.
__device__ __forceinline__ uint16_t float_to_bf16(float f) {
    uint32_t u = __float_as_uint(f);
    if ((u & 0x7fffffffu) > 0x7f800000u) {
        return static_cast<uint16_t>((u >> 16) | 0x40u);
    }
    u += 0x7fffu + ((u >> 16) & 1u);
    return static_cast<uint16_t>(u >> 16);
}

__device__ __forceinline__ void load8(const uint16_t *p, float out[8]) {
    const uint4 v = *reinterpret_cast<const uint4 *>(p);
    const auto *h = reinterpret_cast<const uint16_t *>(&v);
#pragma unroll
    for (int k = 0; k < 8; ++k) {
        out[k] = bf16_to_float(h[k]);
    }
}

__device__ __forceinline__ void load8(const float *p, float out[8]) {
    const float4 a = reinterpret_cast<const float4 *>(p)[0];
    const float4 b = reinterpret_cast<const float4 *>(p)[1];
    out[0] = a.x, out[1] = a.y, out[2] = a.z, out[3] = a.w;
    out[4] = b.x, out[5] = b.y, out[6] = b.z, out[7] = b.w;
}

__device__ __forceinline__ void store8(uint16_t *p, const float in[8]) {
    uint4 v;
    auto *h = reinterpret_cast<uint16_t *>(&v);
#pragma unroll
    for (int k = 0; k < 8; ++k) {
        h[k] = float_to_bf16(in[k]);
    }
    *reinterpret_cast<uint4 *>(p) = v;
}

inline void check_launch(const char *what) {
    const hipError_t err = hipGetLastError();
    if (err != hipSuccess) {
        throw std::runtime_error(std::string(what) + ": " + hipGetErrorString(err));
    }
}

// Grid for a grid-stride loop over `work` items with 256 threads per block.
inline dim3 grid_for(int64_t work) {
    constexpr int64_t kMaxBlocks = 8192;
    const int64_t blocks = (work + 255) / 256;
    return dim3(static_cast<unsigned>(blocks < kMaxBlocks ? blocks : kMaxBlocks));
}

} // namespace heteromega
