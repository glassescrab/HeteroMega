// Candidate-only wrapper around the teammate GPU FFN implementation.
// Original GPUBranch and its extension remain unchanged.
#include "heteromega/gpu_ffn.hpp"
#include <torch/extension.h>
#include <pybind11/stl.h>
#include <cstdint>
#include <tuple>

namespace {
std::tuple<torch::Tensor, torch::Tensor> prepare(
    const torch::Tensor &gate, const torch::Tensor &up,
    const torch::Tensor &down, int64_t hidden, int64_t intermediate,
    int64_t begin, int64_t end) {
    auto w = heteromega::slice_packed_ffn(
        gate, up, down, hidden, intermediate, begin, end,
        heteromega::GateUpLayout::kInterleaved);
    return {w.gate_up, w.down};
}

void forward(torch::Tensor output, const torch::Tensor &input,
             const torch::Tensor &gate_up_weights,
             const torch::Tensor &down_weights, torch::Tensor gate_up,
             torch::Tensor act, torch::Tensor x_pad, int64_t hidden,
             int64_t channels, uint64_t stream_handle) {
    TORCH_CHECK(hidden > 0 && channels > 0 && hidden % 128 == 0 && channels % 128 == 0,
                "teammate FFN requires H and channels divisible by 128");
    TORCH_CHECK(input.dim() == 2 && input.size(0) > 0 && input.size(0) % 128 == 0 &&
                input.size(1) == hidden, "teammate prefill requires [M,H], M divisible by 128");
    const torch::Tensor *activations[] = {&output, &input, &gate_up, &act, &x_pad};
    for (const auto *t : activations) {
        TORCH_CHECK(t->is_cuda() && t->device() == input.device() &&
                    t->scalar_type() == torch::kBFloat16 && t->is_contiguous(),
                    "teammate FFN activations must be contiguous BF16 on the same GPU");
    }
    for (const auto *t : {&gate_up_weights, &down_weights}) {
        TORCH_CHECK(t->is_cuda() && t->device() == input.device() &&
                    t->scalar_type() == torch::kUInt8 && t->dim() == 1 && t->is_contiguous(),
                    "teammate FFN weights must be contiguous uint8 on the same GPU");
    }
    heteromega::FfnSliceWeights weights;
    weights.gate_up = gate_up_weights;
    weights.down = down_weights;
    weights.begin = 0;
    weights.end = channels;
    weights.hidden = hidden;
    weights.layout = heteromega::GateUpLayout::kInterleaved;
    heteromega::GpuFfnBuffers buffers{gate_up, act, x_pad};
    heteromega::gpu_ffn_slice_forward(
        weights, input, buffers, output,
        reinterpret_cast<hipStream_t>(static_cast<uintptr_t>(stream_handle)));
}

torch::Tensor linear(torch::Tensor out, const torch::Tensor &in,
                     const torch::Tensor &packed, int64_t k, int64_t n,
                     int64_t packed_k, int64_t packed_n, uint64_t stream_handle,
                     bool fuse_activation) {
    heteromega::LinearOptions opt;
    opt.packed_k = packed_k;
    opt.packed_n = packed_n;
    opt.fuse_activation = fuse_activation;
    heteromega::packed_linear(out, in, packed, k, n,
                              reinterpret_cast<hipStream_t>(static_cast<uintptr_t>(stream_handle)), opt);
    return out;
}

torch::Tensor silu_mul(torch::Tensor gate_up, torch::Tensor act, int64_t layout,
                       uint64_t stream_handle) {
    heteromega::silu_mul(gate_up, act,
                         reinterpret_cast<hipStream_t>(static_cast<uintptr_t>(stream_handle)),
                         static_cast<heteromega::GateUpLayout>(layout));
    return act;
}
} // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("prepare", &prepare, pybind11::call_guard<pybind11::gil_scoped_release>(),
          "Gather original packed tiles into the teammate interleaved GPU FFN slice");
    m.def("forward", &forward, pybind11::call_guard<pybind11::gil_scoped_release>(),
          "Enqueue teammate merged gate/up, fused SiLU*up and down projection");
    m.def("linear", &linear, pybind11::call_guard<pybind11::gil_scoped_release>(),
          pybind11::arg("out"), pybind11::arg("in"), pybind11::arg("packed"),
          pybind11::arg("k"), pybind11::arg("n"), pybind11::arg("packed_k"),
          pybind11::arg("packed_n"), pybind11::arg("stream_handle"),
          pybind11::arg("fuse_activation") = false,
          "Enqueue one packed W4A16 linear projection");
    m.def("silu_mul", &silu_mul, pybind11::call_guard<pybind11::gil_scoped_release>(),
          "Enqueue fused SiLU*up for an interleaved gate/up buffer");
}
