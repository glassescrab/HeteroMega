// Random packed W4A16 weights for the benchmarks.
#pragma once

#include "heteromega/gpu_ffn.hpp"

namespace bench {

// Packed [k, n] weights: random 4-bit values, scale 0.01, zero 8.
// Random bytes in the packed layout with valid scales, so timing matches real weights.
inline torch::Tensor random_packed(int64_t k, int64_t n, const torch::Device &dev) {
    using namespace heteromega;
    const int64_t tiles = (k / kTileK) * (n / kTileN);
    auto p = torch::randint(0, 256, {tiles, kTileBytes}, torch::TensorOptions().dtype(torch::kUInt8).device(dev));
    const auto scales = torch::full({tiles, 64}, 0.01, torch::TensorOptions().dtype(torch::kBFloat16).device(dev));
    p.slice(1, 4096, 4224).copy_(scales.view(torch::kUInt8));
    p.slice(1, 4224, kTileBytes).fill_(8);
    return p.flatten();
}

} // namespace bench
