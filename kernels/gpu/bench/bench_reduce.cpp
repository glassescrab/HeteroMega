// R-GPU vs R-CPU reducer latency: x += y_g + y_n with x, y of shape [M, 4096].
// The CPU version runs on pinned host tensors. Neither number includes the join wait.
//
// Usage: bench_reduce [--m 1,128,512,2048,4096] [--iters 200] [--warmup 20]
// Output: CSV on stdout.
#include "bench_common.hpp"
#include "heteromega/gpu_ffn.hpp"

#include <c10/hip/HIPStream.h>

#include <chrono>
#include <cstdio>

using namespace heteromega;

int main(int argc, char **argv) {
    const auto ms = bench::parse_list(bench::arg(argc, argv, "--m", "1,128,512,2048,4096"));
    const int iters = std::stoi(bench::arg(argc, argv, "--iters", "200"));
    const int warmup = std::stoi(bench::arg(argc, argv, "--warmup", "20"));
    constexpr int64_t kHidden = 4096;

    const torch::Device dev(torch::kCUDA, 0);
    const hipStream_t stream = c10::hip::getCurrentHIPStream().stream();

    std::printf("M,partial_dtype,gpu_ms,cpu_ms\n");
    for (int64_t m : ms) {
        for (auto pdt : {torch::kBFloat16, torch::kFloat32}) {
            const auto gpu = torch::TensorOptions().device(dev);
            auto x = torch::randn({m, kHidden}, gpu).to(torch::kBFloat16);
            const auto yg = torch::randn({m, kHidden}, gpu).to(torch::kBFloat16);
            const auto yn = torch::randn({m, kHidden}, gpu).to(pdt);

            const auto pinned = torch::TensorOptions().pinned_memory(true);
            auto xc = torch::empty({m, kHidden}, pinned.dtype(torch::kBFloat16)).copy_(x);
            const auto ygc = torch::empty({m, kHidden}, pinned.dtype(torch::kBFloat16)).copy_(yg);
            const auto ync = torch::empty({m, kHidden}, pinned.dtype(pdt)).copy_(yn);

            // GPU: enqueue all iterations back to back, then read the events.
            for (int it = 0; it < warmup; ++it) {
                residual_add2(x, yg, yn, stream);
            }
            bench::hip_check(hipStreamSynchronize(stream), "hipStreamSynchronize");
            bench::EventTimer t(stream, 2 * iters);
            for (int it = 0; it < iters; ++it) {
                t.mark(2 * it);
                residual_add2(x, yg, yn, stream);
                t.mark(2 * it + 1);
            }
            std::vector<double> t_gpu, t_cpu;
            for (int it = 0; it < iters; ++it) {
                t_gpu.push_back(t.ms(2 * it, 2 * it + 1));
            }

            for (int it = 0; it < warmup + iters; ++it) {
                const auto c0 = std::chrono::steady_clock::now();
                residual_add2_cpu(xc, ygc, ync);
                const auto c1 = std::chrono::steady_clock::now();
                if (it >= warmup) {
                    t_cpu.push_back(std::chrono::duration<double, std::milli>(c1 - c0).count());
                }
            }
            std::printf("%lld,%s,%.4f,%.4f\n", static_cast<long long>(m), pdt == torch::kFloat32 ? "fp32" : "bf16",
                        bench::median(t_gpu), bench::median(t_cpu));
            std::fflush(stdout);
        }
    }
    return 0;
}
