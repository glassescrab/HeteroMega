#pragma once
#include "heteromega/merged_ffn_contract.hpp"
#include <hip/hip_runtime.h>
#include <memory>
#include <torch/torch.h>

namespace heteromega {
struct MergedFfnResult {
    // Partials are borrowed per-stream scratch; consume before the next call on that stream.
    torch::Tensor output, gpu_partial, npu_partial;
};

// Fixed-artifact, host-staged deployment. No graph compiler or Python harness dependency.
// Separate HIP streams have separate scratch; NPU submit/wait shares the native runtime mutex.
class MergedFfn {
  public:
    explicit MergedFfn(const std::string &config_path);
    ~MergedFfn();
    MergedFfn(const MergedFfn &) = delete;
    MergedFfn &operator=(const MergedFfn &) = delete;
    const MergedFfnConfig &config() const;
    bool supports(int64_t rows, int64_t hidden, int64_t intermediate) const;
    void add_layer(const torch::Tensor &gate, const torch::Tensor &up, const torch::Tensor &down);
    // Sets up every layer now, with a GPU copy of all channels in the order [P, I) ++ [0, P), and frees the original weights that
    // add_layer received. Prefill uses the first I - P channels of that copy, forward_gpu_all all of them.
    void prepare_all(const torch::Device &device, hipStream_t stream);
    bool has_full_gpu_copy() const;
    // y = the whole FFN of `layer` on the GPU, for any rows (decode, and chunks that the artifact does not take). After prepare_all only.
    void forward_gpu_all(int64_t layer, const torch::Tensor &normalized, torch::Tensor &y, hipStream_t current_stream);
    // With sum = false, output stays unwritten and the caller adds the partials on current_stream.
    MergedFfnResult forward(int64_t layer, const torch::Tensor &normalized, torch::Tensor output,
                            hipStream_t current_stream, bool serial = false, bool sum = true);
    uint64_t completed_dispatches() const;

  private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
} // namespace heteromega
