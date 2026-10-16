// Latency of the GPU slice of one FFN sublayer for a grid of (M, s).
// Weights are random bytes in the packed layout with valid scales, so timing matches real weights.
//
// Usage: bench_gpu_ffn_slice [--m 1,128,512,2048,4096] [--s 1024,2048,...,14336] [--iters 50] [--warmup 10]
// Output: CSV on stdout. s = 14336 is the GPU-only run of the same kernels (ablation A1).
#include "bench_common.hpp"
#include "heteromega/gpu_ffn.hpp"

#include <c10/hip/HIPStream.h>

#include <cstdio>

using namespace heteromega;

namespace {

constexpr int64_t kHidden = 4096;
constexpr int64_t kInter = 14336;

// Packed [k, n] weights: random 4-bit values, scale 0.01, zero 8.
torch::Tensor random_packed(int64_t k, int64_t n, const torch::Device &dev) {
    const int64_t tiles = (k / kTileK) * (n / kTileN);
    auto p = torch::randint(0, 256, {tiles, kTileBytes}, torch::TensorOptions().dtype(torch::kUInt8).device(dev));
    const auto scales = torch::full({tiles, 64}, 0.01, torch::TensorOptions().dtype(torch::kBFloat16).device(dev));
    p.slice(1, 4096, 4224).copy_(scales.view(torch::kUInt8));
    p.slice(1, 4224, kTileBytes).fill_(8);
    return p.flatten();
}

std::string default_splits() {
    std::string s;
    for (int64_t v = 1024; v <= 13312; v += 1024) {
        s += std::to_string(v) + ",";
    }
    return s + std::to_string(kInter);
}

} // namespace

int main(int argc, char **argv) {
    const auto ms = bench::parse_list(bench::arg(argc, argv, "--m", "1,128,512,2048,4096"));
    const auto splits = bench::parse_list(bench::arg(argc, argv, "--s", default_splits()));
    const int iters = std::stoi(bench::arg(argc, argv, "--iters", "50"));
    const int warmup = std::stoi(bench::arg(argc, argv, "--warmup", "10"));

    const torch::Device dev(torch::kCUDA, 0);
    const hipStream_t stream = c10::hip::getCurrentHIPStream().stream();
    const int64_t max_m = *std::max_element(ms.begin(), ms.end());

    std::printf("M,s,gpu_fraction,gate_up_ms,silu_mul_ms,down_ms,total_ms,weight_GBps\n");
    for (int64_t s : splits) {
        if (s <= 0 || s > kInter || s % 512 != 0) {
            std::fprintf(stderr, "skip s=%lld: must be a multiple of 512 in (0, %lld]\n", static_cast<long long>(s),
                         static_cast<long long>(kInter));
            continue;
        }
        FfnSliceWeights w;
        w.gate_up = random_packed(kHidden, 2 * s, dev);
        w.down = random_packed(s, kHidden, dev);
        w.begin = 0, w.end = s, w.hidden = kHidden;
        auto buf = GpuFfnBuffers::allocate(max_m, s, kHidden, dev);
        const double weight_bytes = static_cast<double>(w.gate_up.numel() + w.down.numel());

        for (int64_t m : ms) {
            // The GEMM reads whole 128-row tiles, so x gets padded storage (see padded_rows()).
            const auto x = (torch::randn({padded_rows(m), kHidden}, torch::TensorOptions().device(dev)) * 0.5)
                               .to(torch::kBFloat16)
                               .narrow(0, 0, m);
            auto y = torch::empty({m, kHidden}, x.options());
            auto gate_up = buf.gate_up.narrow(0, 0, m);
            auto act = buf.act.narrow(0, 0, m);
            const auto run = [&](bench::EventTimer &t, int it) {
                t.mark(4 * it);
                packed_linear(gate_up, x, w.gate_up, kHidden, 2 * s, stream);
                t.mark(4 * it + 1);
                silu_mul(gate_up, act, stream);
                t.mark(4 * it + 2);
                packed_linear(y, act, w.down, s, kHidden, stream);
                t.mark(4 * it + 3);
            };

            bench::EventTimer warm(stream, 4 * warmup);
            for (int it = 0; it < warmup; ++it) {
                run(warm, it);
            }
            bench::hip_check(hipStreamSynchronize(stream), "hipStreamSynchronize");
            // Enqueue all iterations back to back, then read the events.
            bench::EventTimer t(stream, 4 * iters);
            for (int it = 0; it < iters; ++it) {
                run(t, it);
            }
            std::vector<double> t_gu, t_act, t_down, t_total;
            for (int it = 0; it < iters; ++it) {
                const int b = 4 * it;
                t_gu.push_back(t.ms(b, b + 1));
                t_act.push_back(t.ms(b + 1, b + 2));
                t_down.push_back(t.ms(b + 2, b + 3));
                t_total.push_back(t.ms(b, b + 3));
            }
            const double gu = bench::median(t_gu), a = bench::median(t_act), d = bench::median(t_down), tot = bench::median(t_total);
            std::printf("%lld,%lld,%.4f,%.4f,%.4f,%.4f,%.4f,%.1f\n", static_cast<long long>(m), static_cast<long long>(s),
                        static_cast<double>(s) / kInter, gu, a, d, tot, weight_bytes / ((gu + d) * 1e6));
            std::fflush(stdout);
        }
    }
    return 0;
}
