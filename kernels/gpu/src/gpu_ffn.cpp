#include "heteromega/gpu_ffn.hpp"

#include "hipkernels/w4a16_gemm_packed.hpp"

namespace heteromega {
namespace {

// True if t's storage holds `rows` rows starting at t's first element.
bool storage_has_rows(const torch::Tensor &t, int64_t rows) {
    const int64_t needed = (t.storage_offset() + rows * t.stride(0)) * t.element_size();
    return static_cast<int64_t>(t.storage().nbytes()) >= needed;
}

} // namespace

void packed_linear(torch::Tensor &out, const torch::Tensor &in, const torch::Tensor &packed, int64_t k, int64_t n,
                   hipStream_t stream) {
    TORCH_CHECK(in.dim() == 2 && in.size(1) == k && in.is_contiguous(), "packed_linear: input must be contiguous [M, ", k, "]");
    const int64_t m = in.size(0);
    TORCH_CHECK(m > 0, "packed_linear: M must be > 0");
    TORCH_CHECK(k % kTileK == 0 && n % kTileN == 0, "packed_linear: k must be a multiple of 128 and n of 64");
    TORCH_CHECK(m == 1 || k <= 1024 || n % 128 == 0, "packed_linear: the GEMM needs n % 128 == 0 when k > 1024");
    TORCH_CHECK(out.dim() == 2 && out.size(0) == in.size(0) && out.size(1) == n && out.is_contiguous(),
                "packed_linear: output must be contiguous [M, ", n, "]");
    TORCH_CHECK(in.scalar_type() == torch::kBFloat16 && out.scalar_type() == torch::kBFloat16, "packed_linear: expected bf16");
    TORCH_CHECK(packed.numel() == (k / kTileK) * (n / kTileN) * kTileBytes, "packed_linear: packed size does not match ", k, "x", n);
    TORCH_CHECK(packed.device() == in.device() && out.device() == in.device(), "packed_linear: all tensors must be on one device");

    if (m == 1) {
        hipkernels::w4a16_gemv_fused_packed(out, in, packed, k, n, -1, 0, stream);
    } else {
        TORCH_CHECK(storage_has_rows(in, padded_rows(m)), "packed_linear: input storage must hold ", padded_rows(m),
                    " rows for M = ", m, " (the GEMM reads whole 128-row tiles)");
        hipkernels::w4a16_gemm_fused_packed(out, in, packed, k, n, stream);
    }
}

GpuFfnBuffers GpuFfnBuffers::allocate(int64_t max_m, int64_t channels, int64_t hidden, const torch::Device &device) {
    const auto opt = torch::TensorOptions().dtype(torch::kBFloat16).device(device);
    const int64_t rows = padded_rows(max_m);
    return {torch::empty({rows, 2 * channels}, opt), torch::empty({rows, channels}, opt), torch::empty({rows, hidden}, opt)};
}

void gpu_ffn_slice_forward(const FfnSliceWeights &w, const torch::Tensor &x_norm, GpuFfnBuffers &buf, torch::Tensor &y,
                           hipStream_t stream) {
    const int64_t n = w.channels();
    const int64_t h = w.hidden;
    const int64_t m = x_norm.size(0);
    TORCH_CHECK(buf.gate_up.size(0) >= padded_rows(m) && buf.gate_up.size(1) == 2 * n && buf.act.size(1) == n &&
                    buf.x_pad.size(1) == h,
                "gpu_ffn_slice_forward: buffers do not fit M = ", m, ", ", n, " channels, H = ", h);
    TORCH_CHECK(x_norm.dim() == 2 && x_norm.size(1) == h && x_norm.is_contiguous(), "gpu_ffn_slice_forward: x_norm must be contiguous [M, H]");

    torch::Tensor x = x_norm;
    if (m > 1 && !storage_has_rows(x_norm, padded_rows(m))) {
        x = buf.x_pad.narrow(0, 0, m);
        const hipError_t err = hipMemcpyAsync(x.data_ptr(), x_norm.data_ptr(), x_norm.nbytes(), hipMemcpyDefault, stream);
        TORCH_CHECK(err == hipSuccess, "gpu_ffn_slice_forward: copy to x_pad failed: ", hipGetErrorString(err));
    }

    auto gate_up = buf.gate_up.narrow(0, 0, m);
    auto act = buf.act.narrow(0, 0, m);
    packed_linear(gate_up, x, w.gate_up, h, 2 * n, stream);
    silu_mul(gate_up, act, stream);
    packed_linear(y, act, w.down, n, h, stream);
}

} // namespace heteromega
