// Correctness tests for the GPU side of the FFN split.
//   Level 1: each kernel against an fp32 reference (random signed inputs, nonuniform weights, scales and zeros).
//   Level 2: Y_G + Y_N of two channel slices against the unsplit fp32 FFN.
// Run on the AUP cloud in the environment of docs/cloud-baseline.md:
//   ./test_gpu_ffn          (full: M in {1, 37, 128, 512, 2048}, s in {512, 7168, 10240, 13824})
//   ./test_gpu_ffn --quick  (M in {1, 37, 128}, s = 7168)
// Exit code 0 means every check passed.
#include "heteromega/gpu_ffn.hpp"

#include <c10/hip/HIPStream.h>

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

using namespace heteromega;

namespace {

constexpr int64_t kHidden = 4096;
constexpr int64_t kInter = 14336;
int g_failures = 0;

struct Tol {
    double max_rel;
    double rel_l2;
    double cos;
};
constexpr Tol kExact{1e-2, 5e-3, 0.99999}; // one bf16 rounding
constexpr Tol kLevel{1e-2, 1e-2, 0.9999};  // levels 1 and 2

// max_rel = max |got - ref| / max |ref|.
void check(const std::string &name, const torch::Tensor &got, const torch::Tensor &ref, Tol tol) {
    const auto g = got.to(torch::kCPU, torch::kFloat64).flatten();
    const auto r = ref.to(torch::kCPU, torch::kFloat64).flatten();
    const double max_rel = (g - r).abs().max().item<double>() / (r.abs().max().item<double>() + 1e-30);
    const double rel_l2 = ((g - r).norm() / (r.norm() + 1e-30)).item<double>();
    const double cos = (torch::dot(g, r) / (g.norm() * r.norm() + 1e-30)).item<double>();
    const bool ok = max_rel <= tol.max_rel && rel_l2 <= tol.rel_l2 && cos >= tol.cos;
    std::printf("%-52s %s  max_rel=%.2e  rel_l2=%.2e  cos=%.7f\n", name.c_str(), ok ? "PASS" : "FAIL", max_rel, rel_l2, cos);
    if (!ok) {
        ++g_failures;
    }
}

struct Quant {
    torch::Tensor q, s, z;
};

// AWQ-like random weights: q in [0, 15], zeros in [6, 9], scales in [0.002, 0.02].
Quant random_quant(int64_t k, int64_t n) {
    const auto cpu = torch::TensorOptions().device(torch::kCPU);
    Quant t;
    t.q = torch::randint(0, 16, {k, n}, cpu.dtype(torch::kUInt8));
    t.s = (torch::rand({k / kTileK, n}, cpu.dtype(torch::kFloat32)) * 0.018 + 0.002).to(torch::kBFloat16);
    t.z = torch::randint(6, 10, {k / kTileK, n}, cpu.dtype(torch::kInt8));
    return t;
}

// fp32 [k, n] weight: (q - zero) * scale, one scale and zero per 128-row group.
torch::Tensor dequant(const Quant &t, const torch::Device &dev) {
    const auto z = t.z.to(dev, torch::kFloat32).repeat_interleave(kTileK, 0);
    const auto s = t.s.to(dev, torch::kFloat32).repeat_interleave(kTileK, 0);
    return (t.q.to(dev, torch::kFloat32) - z) * s;
}

torch::Tensor bf16(const torch::Tensor &t) { return t.to(torch::kBFloat16).contiguous(); }

// Random bf16 [m, k] input whose storage holds padded_rows(m) rows, as packed_linear() requires.
torch::Tensor padded_input(int64_t m, int64_t k, const torch::Device &dev) {
    return bf16(torch::randn({padded_rows(m), k}, torch::TensorOptions().device(dev)) * 0.5).narrow(0, 0, m);
}

void sync() { (void)hipDeviceSynchronize(); }

// Level 1: packer + HeteroMosaic GEMM/GEMV on full matrices and on the slices that HeteroMega uses.
void test_packed_linear(const torch::Device &dev, hipStream_t stream, const std::vector<int64_t> &ms) {
    struct Case {
        const char *name;
        int64_t k, n;
    };
    const Case cases[] = {{"gate_up slice [4096 x 2*7168]", kHidden, 2 * 7168},
                          {"gate_up slice [4096 x 2*512]", kHidden, 2 * 512},
                          {"gate_up slice [4096 x 2*10240]", kHidden, 2 * 10240},
                          {"down slice [7168 x 4096]", 7168, kHidden},
                          {"down slice [10240 x 4096]", 10240, kHidden},
                          {"down slice [512 x 4096]", 512, kHidden}};
    for (const auto &c : cases) {
        const Quant t = random_quant(c.k, c.n);
        const auto w = dequant(t, dev);
        const auto packed = pack_w4a16(t.q, t.s, t.z).to(dev);
        for (int64_t m : ms) {
            const auto x = padded_input(m, c.k, dev);
            auto y = torch::empty({m, c.n}, x.options());
            packed_linear(y, x, packed, c.k, c.n, stream);
            sync();
            check(std::string("L1 linear ") + c.name + " M=" + std::to_string(m), y, x.to(torch::kFloat32).matmul(w), kLevel);
        }
    }
}

// Level 1: SiLU-and-multiply.
void test_silu_mul(const torch::Device &dev, hipStream_t stream) {
    for (int64_t m : {1L, 37L, 2048L}) {
        const int64_t n = 7168;
        const auto gu = bf16(torch::randn({m, 2 * n}, torch::TensorOptions().device(dev)) * 4.0);
        auto act = torch::empty({m, n}, gu.options());
        silu_mul(gu, act, stream);
        sync();
        const auto g = gu.narrow(1, 0, n).to(torch::kFloat32);
        const auto u = gu.narrow(1, n, n).to(torch::kFloat32);
        check("L1 silu_mul M=" + std::to_string(m), act, torch::silu(g) * u, kExact);
    }
}

// Level 1: reducers R-GPU and R-CPU, bf16 and fp32 partials.
void test_residual_add2(const torch::Device &dev, hipStream_t stream) {
    for (int64_t m : {1L, 2048L}) {
        for (auto pdt : {torch::kBFloat16, torch::kFloat32}) {
            const auto opt = torch::TensorOptions().device(dev);
            const auto x0 = bf16(torch::randn({m, kHidden}, opt));
            const auto yg = bf16(torch::randn({m, kHidden}, opt) * 0.3);
            const auto yn = (torch::randn({m, kHidden}, opt) * 0.3).to(pdt).contiguous();
            const auto ref = x0.to(torch::kFloat32) + (yg.to(torch::kFloat32) + yn.to(torch::kFloat32));
            const std::string tag = std::string(" M=") + std::to_string(m) + (pdt == torch::kFloat32 ? " y_n=fp32" : " y_n=bf16");

            auto xg = x0.clone();
            residual_add2(xg, yg, yn, stream);
            sync();
            check("L1 residual_add2 GPU" + tag, xg, ref, kExact);

            auto xc = x0.cpu();
            residual_add2_cpu(xc, yg.cpu(), yn.cpu());
            check("L1 residual_add2 CPU" + tag, xc, ref, kExact);
        }
    }
}

// Level 2: Y_G + Y_N == full FFN. The NPU slice runs on the GPU here as a stand-in.
// x is not padded, so M = 37 also tests the copy into GpuFfnBuffers::x_pad.
void test_ffn_split(const torch::Device &dev, hipStream_t stream, const std::vector<int64_t> &ms,
                    const std::vector<int64_t> &splits) {
    FfnLayerQuant layer;
    const Quant g = random_quant(kHidden, kInter), u = random_quant(kHidden, kInter), d = random_quant(kInter, kHidden);
    layer.gate_q = g.q, layer.gate_s = g.s, layer.gate_z = g.z;
    layer.up_q = u.q, layer.up_s = u.s, layer.up_z = u.z;
    layer.down_q = d.q, layer.down_s = d.s, layer.down_z = d.z;
    const auto wg = dequant(g, dev), wu = dequant(u, dev), wd = dequant(d, dev);

    const int64_t max_m = *std::max_element(ms.begin(), ms.end());
    const auto full = pack_ffn_slice(layer, 0, kInter).to(dev);
    auto full_buf = GpuFfnBuffers::allocate(max_m, kInter, kHidden, dev);

    for (int64_t s : splits) {
        const auto gpu_part = pack_ffn_slice(layer, 0, s).to(dev);
        const auto npu_part = pack_ffn_slice(layer, s, kInter).to(dev);
        auto gpu_buf = GpuFfnBuffers::allocate(max_m, s, kHidden, dev);
        auto npu_buf = GpuFfnBuffers::allocate(max_m, kInter - s, kHidden, dev);

        for (int64_t m : ms) {
            const auto x = bf16(torch::randn({m, kHidden}, torch::TensorOptions().device(dev)) * 0.5);
            const auto xf = x.to(torch::kFloat32);
            const auto ref = (torch::silu(xf.matmul(wg)) * xf.matmul(wu)).matmul(wd);

            auto y_g = torch::empty({m, kHidden}, x.options());
            auto y_n = torch::empty({m, kHidden}, x.options());
            auto y_full = torch::empty({m, kHidden}, x.options());
            gpu_ffn_slice_forward(gpu_part, x, gpu_buf, y_g, stream);
            gpu_ffn_slice_forward(npu_part, x, npu_buf, y_n, stream);
            gpu_ffn_slice_forward(full, x, full_buf, y_full, stream);

            // Reducer path: zero residual, so x_out == Y_G + Y_N.
            auto x_out = torch::zeros({m, kHidden}, x.options());
            residual_add2(x_out, y_g, y_n, stream);
            sync();

            const std::string tag = " s=" + std::to_string(s) + " M=" + std::to_string(m);
            check("L2 split Y_G + Y_N vs fp32 FFN" + tag, x_out, ref, kLevel);
            check("L2 unsplit GPU FFN vs fp32 FFN" + tag, y_full, ref, kLevel);
        }
    }
}

} // namespace

int main(int argc, char **argv) {
    const bool quick = argc > 1 && std::strcmp(argv[1], "--quick") == 0;
    torch::manual_seed(0);
    const torch::Device dev(torch::kCUDA, 0);
    const hipStream_t stream = c10::hip::getCurrentHIPStream().stream();

    // On an APU, "device memory" can be a small BIOS carve-out. The full test needs about 2 GiB.
    hipDeviceProp_t prop;
    size_t free_bytes = 0, total_bytes = 0;
    if (hipGetDeviceProperties(&prop, 0) == hipSuccess && hipMemGetInfo(&free_bytes, &total_bytes) == hipSuccess) {
        std::printf("Device: %s (%s), %.1f GiB free of %.1f GiB\n", prop.name, prop.gcnArchName, free_bytes / 1073741824.0,
                    total_bytes / 1073741824.0);
    }

    const std::vector<int64_t> ms = quick ? std::vector<int64_t>{1, 37, 128} : std::vector<int64_t>{1, 37, 128, 512, 2048};
    const std::vector<int64_t> splits = quick ? std::vector<int64_t>{7168} : std::vector<int64_t>{512, 7168, 10240, 13824};

    test_packed_linear(dev, stream, ms);
    test_silu_mul(dev, stream);
    test_residual_add2(dev, stream);
    test_ffn_split(dev, stream, ms, splits);

    std::printf("%s (%d failed)\n", g_failures == 0 ? "ALL PASS" : "FAILURES", g_failures);
    return g_failures == 0 ? 0 : 1;
}
