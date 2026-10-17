#include "bf16_device.hpp"
#include "heteromega/gpu_ffn.hpp"

namespace heteromega {
namespace {

// x += y_g + y_n. The two partials are added first, then the residual. One bf16 rounding.
template <typename PG, typename PN>
__global__ void __launch_bounds__(256)
    residual_add2_kernel(uint16_t *__restrict__ x, const PG *__restrict__ yg, const PN *__restrict__ yn, int64_t rows, int64_t cols,
                         int64_t ld_x, int64_t ld_g, int64_t ld_n) {
    const int64_t vec_per_row = cols / 8;
    const int64_t total = rows * vec_per_row;
    for (int64_t i = blockIdx.x * static_cast<int64_t>(blockDim.x) + threadIdx.x; i < total;
         i += static_cast<int64_t>(gridDim.x) * blockDim.x) {
        const int64_t r = i / vec_per_row;
        const int64_t c = (i - r * vec_per_row) * 8;
        float xv[8], gv[8], nv[8];
        load8(x + r * ld_x + c, xv);
        load8(yg + r * ld_g + c, gv);
        load8(yn + r * ld_n + c, nv);
#pragma unroll
        for (int k = 0; k < 8; ++k) {
            xv[k] += gv[k] + nv[k];
        }
        store8(x + r * ld_x + c, xv);
    }
}

template <typename PG, typename PN>
void launch(torch::Tensor &x, const torch::Tensor &y_g, const torch::Tensor &y_n, hipStream_t stream) {
    const int64_t rows = x.size(0);
    const int64_t cols = x.size(1);
    const int64_t work = rows * (cols / 8);
    if (work == 0) {
        return;
    }
    hipLaunchKernelGGL((residual_add2_kernel<PG, PN>), grid_for(work), dim3(256), 0, stream, reinterpret_cast<uint16_t *>(x.data_ptr()),
                       reinterpret_cast<const PG *>(y_g.data_ptr()), reinterpret_cast<const PN *>(y_n.data_ptr()), rows, cols, x.stride(0),
                       y_g.stride(0), y_n.stride(0));
    check_launch("residual_add2");
}

void check_operand(const torch::Tensor &t, const torch::Tensor &x, const char *name) {
    TORCH_CHECK(t.dim() == 2 && t.size(0) == x.size(0) && t.size(1) == x.size(1), "residual_add2: ", name, " must match x");
    TORCH_CHECK(t.is_cuda() || t.is_pinned(), "residual_add2: ", name, " must be GPU or pinned host memory");
    TORCH_CHECK(t.scalar_type() == torch::kBFloat16 || t.scalar_type() == torch::kFloat32, "residual_add2: ", name,
                " must be bf16 or fp32");
    TORCH_CHECK(t.stride(1) == 1 && t.stride(0) % 8 == 0, "residual_add2: ", name, " needs a contiguous last dim, row stride % 8 == 0");
    TORCH_CHECK(reinterpret_cast<uintptr_t>(t.data_ptr()) % 16 == 0, "residual_add2: ", name, " must be 16-byte aligned");
}

} // namespace

void residual_add2(torch::Tensor &x, const torch::Tensor &y_g, const torch::Tensor &y_n, hipStream_t stream) {
    TORCH_CHECK(x.dim() == 2 && x.scalar_type() == torch::kBFloat16, "residual_add2: x must be bf16 [M, H]");
    TORCH_CHECK(x.size(1) % 8 == 0, "residual_add2: H must be a multiple of 8");
    check_operand(x, x, "x");
    check_operand(y_g, x, "y_g");
    check_operand(y_n, x, "y_n");

    const bool g32 = y_g.scalar_type() == torch::kFloat32;
    const bool n32 = y_n.scalar_type() == torch::kFloat32;
    if (!g32 && !n32) {
        launch<uint16_t, uint16_t>(x, y_g, y_n, stream);
    } else if (!g32 && n32) {
        launch<uint16_t, float>(x, y_g, y_n, stream);
    } else if (g32 && !n32) {
        launch<float, uint16_t>(x, y_g, y_n, stream);
    } else {
        launch<float, float>(x, y_g, y_n, stream);
    }
}

} // namespace heteromega
