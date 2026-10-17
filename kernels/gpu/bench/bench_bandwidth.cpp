// GPU streaming-read bandwidth. No LibTorch.
//
// 1. Run alone to get BW_GPU_alone.
// 2. Start an NPU load (for example an NPU read benchmark), then run this again to get the GPU share of BW_both.
//
// Usage: bench_bandwidth [--mib 1024] [--seconds 10] [--host]
//   --host  read pinned host memory (hipHostMalloc) instead of device memory (hipMalloc)
// Output: one line per ~1 s window ("t_s,GBps"), then the median.
#include "bench_common.hpp"

#include <chrono>
#include <cstdio>

namespace {

__global__ void __launch_bounds__(256) read_kernel(const uint4 *__restrict__ p, size_t n, unsigned *sink) {
    unsigned acc = 0;
    for (size_t i = blockIdx.x * static_cast<size_t>(blockDim.x) + threadIdx.x; i < n; i += static_cast<size_t>(gridDim.x) * blockDim.x) {
        const uint4 v = p[i];
        acc ^= v.x ^ v.y ^ v.z ^ v.w;
    }
    if (acc == 0x9e3779b9u) {
        sink[0] = acc; // keeps the loads alive
    }
}

} // namespace

int main(int argc, char **argv) {
    const size_t mib = std::stoull(bench::arg(argc, argv, "--mib", "1024"));
    const double seconds = std::stod(bench::arg(argc, argv, "--seconds", "10"));
    const bool host = bench::flag(argc, argv, "--host");
    const size_t bytes = mib << 20;
    const size_t n = bytes / sizeof(uint4);

    void *buf = nullptr;
    if (host) {
        bench::hip_check(hipHostMalloc(&buf, bytes, hipHostMallocDefault), "hipHostMalloc");
    } else {
        bench::hip_check(hipMalloc(&buf, bytes), "hipMalloc");
    }
    bench::hip_check(hipMemset(buf, 1, bytes), "hipMemset");
    unsigned *sink = nullptr;
    bench::hip_check(hipMalloc(&sink, sizeof(unsigned)), "hipMalloc");

    hipDeviceProp_t prop;
    bench::hip_check(hipGetDeviceProperties(&prop, 0), "hipGetDeviceProperties");
    const dim3 grid(prop.multiProcessorCount * 16), block(256);
    std::fprintf(stderr, "%s, %zu MiB, %s memory, grid %u x 256\n", prop.name, mib, host ? "pinned host" : "device", grid.x);

    hipStream_t stream;
    bench::hip_check(hipStreamCreate(&stream), "hipStreamCreate");
    for (int i = 0; i < 3; ++i) {
        hipLaunchKernelGGL(read_kernel, grid, block, 0, stream, static_cast<const uint4 *>(buf), n, sink);
    }
    bench::hip_check(hipStreamSynchronize(stream), "warmup");

    std::printf("t_s,GBps\n");
    std::vector<double> windows;
    const auto start = std::chrono::steady_clock::now();
    auto win_start = start;
    size_t win_bytes = 0;
    while (true) {
        hipLaunchKernelGGL(read_kernel, grid, block, 0, stream, static_cast<const uint4 *>(buf), n, sink);
        bench::hip_check(hipStreamSynchronize(stream), "read_kernel");
        win_bytes += bytes;
        const auto now = std::chrono::steady_clock::now();
        const double win_s = std::chrono::duration<double>(now - win_start).count();
        if (win_s >= 1.0) {
            const double gbps = win_bytes / win_s / 1e9;
            windows.push_back(gbps);
            std::printf("%.1f,%.1f\n", std::chrono::duration<double>(now - start).count(), gbps);
            std::fflush(stdout);
            win_start = now;
            win_bytes = 0;
        }
        if (std::chrono::duration<double>(now - start).count() >= seconds) {
            break;
        }
    }
    std::printf("median,%.1f\n", bench::median(windows));

    (void)hipStreamDestroy(stream);
    (void)hipFree(sink);
    if (host) {
        (void)hipHostFree(buf);
    } else {
        (void)hipFree(buf);
    }
    return 0;
}
