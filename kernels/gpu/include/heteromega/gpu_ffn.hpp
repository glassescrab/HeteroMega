// GPU side of the HeteroMega FFN split. See kernels/gpu/README.md.
//
// One device owns intermediate channels [begin, end) of an FFN layer and computes
//   Y = (SiLU(X W_gate[:, begin:end]) * (X W_up[:, begin:end])) W_down[begin:end, :]
// The partial outputs of the GPU and the NPU are added by residual_add2().
#pragma once

#include <hip/hip_runtime.h>
#include <torch/torch.h>

#include <cstdint>

namespace heteromega {

constexpr int64_t kTileK = 128;      // rows per packed tile; also the quantization group size
constexpr int64_t kTileN = 64;       // columns per packed tile
constexpr int64_t kTileBytes = 4352; // 4096 weight bytes + 64 bf16 scales + 128 zero bytes

// HeteroMosaic's GEMM reads whole 128-row tiles of its input (only the output writes are guarded).
// For M > 1, input storage must therefore hold padded_rows(M) rows.
inline int64_t padded_rows(int64_t m) { return (m + kTileK - 1) / kTileK * kTileK; }

// ---- Weight packing (CPU) --------------------------------------------------

// Packs a [K, N] W4A16 matrix into the HeteroMosaic tile layout. Both
// hipkernels::w4a16_{gemm,gemv}_fused_packed and the NPU binaries read this layout.
//   qweight: [K, N] uint8, values 0..15
//   scales:  [K / 128, N] bfloat16
//   zeros:   [K / 128, N] int8
// K must be a multiple of 128 and N a multiple of 64. Returns a flat uint8 CPU tensor.
torch::Tensor pack_w4a16(const torch::Tensor &qweight, const torch::Tensor &scales, const torch::Tensor &zeros);

// AWQ tensors of one FFN layer in [in_features, out_features] order, as returned by
// HeteroMosaic _unpack_awq_qweight / _unpack_awq_qzeros. H = hidden, I = intermediate.
struct FfnLayerQuant {
    torch::Tensor gate_q, gate_s, gate_z; // [H, I], [H/128, I], [H/128, I]
    torch::Tensor up_q, up_s, up_z;       // [H, I], [H/128, I], [H/128, I]
    torch::Tensor down_q, down_s, down_z; // [I, H], [I/128, H], [I/128, H]
};

// One device's packed share of an FFN layer: intermediate channels [begin, end).
struct FfnSliceWeights {
    torch::Tensor gate_up; // packed [H, 2n]: columns [0, n) are gate, [n, 2n) are up
    torch::Tensor down;    // packed [n, H]
    int64_t begin = 0;
    int64_t end = 0;
    int64_t hidden = 0;

    int64_t channels() const { return end - begin; }
    FfnSliceWeights to(const torch::Device &device) const;
};

// Packs channels [begin, end). begin and end must be multiples of 128.
// Split points that are multiples of 512 (8 tile columns) keep each slice a tile subset of the full packed buffer.
FfnSliceWeights pack_ffn_slice(const FfnLayerQuant &layer, int64_t begin, int64_t end);

// ---- GPU kernels -------------------------------------------------------------

// act[m, j] = SiLU(gate_up[m, j]) * gate_up[m, n + j] for j < n.
// bf16 in and out, fp32 math, one rounding. n must be a multiple of 8.
void silu_mul(const torch::Tensor &gate_up, torch::Tensor &act, hipStream_t stream);

// Reducer R-GPU: x += y_g + y_n. x is bf16 [M, H]. y_g and y_n are bf16 or fp32 [M, H].
void residual_add2(torch::Tensor &x, const torch::Tensor &y_g, const torch::Tensor &y_n, hipStream_t stream);

// Reducer R-CPU: the same math on CPU tensors (for example pinned host memory).
// The caller must make sure that both devices have finished writing y_g and y_n.
void residual_add2_cpu(torch::Tensor &x, const torch::Tensor &y_g, const torch::Tensor &y_n);

// ---- GPU slice forward -------------------------------------------------------

// Scratch buffers for gpu_ffn_slice_forward(). Allocate once for the largest M.
// Rows are padded to a multiple of 128 (see padded_rows()).
struct GpuFfnBuffers {
    torch::Tensor gate_up; // [rows, 2n] bf16
    torch::Tensor act;     // [rows, n] bf16
    torch::Tensor x_pad;   // [rows, H] bf16: copy of x_norm when its storage is not padded

    static GpuFfnBuffers allocate(int64_t max_m, int64_t channels, int64_t hidden, const torch::Device &device);
};

// GPU share of one FFN sublayer. Enqueues 3 kernels on `stream` and does not synchronize.
// If M > 1 and x_norm's storage is not padded to 128 rows, it first copies x_norm into buf.x_pad.
//   x_norm: [M, H] bf16, contiguous (the RMSNorm output)
//   y:      [M, H] bf16, contiguous (the partial output Y_G)
// M == 1 uses the HeteroMosaic GEMV kernel. M > 1 uses the GEMM kernel.
void gpu_ffn_slice_forward(const FfnSliceWeights &w, const torch::Tensor &x_norm, GpuFfnBuffers &buf, torch::Tensor &y,
                           hipStream_t stream);

// Packed matmul: out[M, n] = in[M, k] @ W[k, n]. GEMV for M == 1, GEMM otherwise.
// For M > 1, in's storage must hold padded_rows(M) rows; the extra rows can hold any values.
void packed_linear(torch::Tensor &out, const torch::Tensor &in, const torch::Tensor &packed, int64_t k, int64_t n,
                   hipStream_t stream);

} // namespace heteromega
