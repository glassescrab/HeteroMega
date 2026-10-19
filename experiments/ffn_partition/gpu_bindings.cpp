// A deliberately thin adapter to the unchanged HeteroMosaic GPU GEMM.
// The Python caller supplies a HIP stream handle so this adapter does not
// depend on version-specific c10 HIP/CUDA stream aliases.
#include "hipkernels/w4a16_gemm_packed.hpp"
#include <cstdint>
#include <torch/extension.h>

namespace {
void gemm(torch::Tensor output, const torch::Tensor &input,
          const torch::Tensor &packed, int64_t k, int64_t n,
          uint64_t stream_handle) {
    TORCH_CHECK(k > 0 && n > 0 && k % 128 == 0 && n % 128 == 0,
                "GPU GEMM requires positive K and N divisible by 128");
    TORCH_CHECK(input.dim() == 2 && input.size(1) == k &&
                    input.size(0) > 0 && input.size(0) % 128 == 0,
                "GPU GEMM requires input [M,K], positive M divisible by 128");
    TORCH_CHECK(output.dim() == 2 && output.size(0) == input.size(0) &&
                    output.size(1) == n,
                "GPU GEMM output must have shape [M,N]");
    TORCH_CHECK(input.is_cuda() && output.is_cuda() && packed.is_cuda(),
                "GPU GEMM tensors must be on the ROCm GPU");
    TORCH_CHECK(input.device() == output.device() &&
                    input.device() == packed.device(),
                "GPU GEMM tensors must share a device");
    TORCH_CHECK(input.scalar_type() == torch::kBFloat16 &&
                    output.scalar_type() == torch::kBFloat16 &&
                    packed.scalar_type() == torch::kUInt8,
                "GPU GEMM expects BF16 input/output and uint8 weights");
    TORCH_CHECK(input.is_contiguous() && output.is_contiguous() &&
                    packed.is_contiguous(),
                "GPU GEMM requires contiguous compact buffers");
    TORCH_CHECK(packed.dim() == 1 &&
                    packed.numel() == (k / 128) * (n / 64) * 4352,
                "GPU GEMM packed weight buffer has the wrong size");
    hipkernels::w4a16_gemm_fused_packed(
        output, input, packed, k, n,
        reinterpret_cast<hipStream_t>(static_cast<uintptr_t>(stream_handle)));
}
} // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("gemm", &gemm, pybind11::call_guard<pybind11::gil_scoped_release>(),
          "Enqueue original HeteroMosaic packed BF16 W4A16 GEMM");
}
