// Copyright (C) 2026 HeteroMega contributors.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Correctness-first single-token, single-core W4A16 projection.
// Deliberately scalar: this is a source-level bring-up kernel, not an optimized
// replacement for HeteroMosaic's shipped matrix multiplication kernels.

#include <aie_api/aie.hpp>
#include <stdint.h>

#ifndef HETEROMEGA_K
#define HETEROMEGA_K 128
#endif
#ifndef HETEROMEGA_N
#define HETEROMEGA_N 64
#endif

static_assert(HETEROMEGA_K > 0 && HETEROMEGA_K % 128 == 0,
              "K must be a positive multiple of the 128-element group size");
static_assert(HETEROMEGA_N > 0 && HETEROMEGA_N % 64 == 0,
              "N must be a positive multiple of 64");

// Payload has three contiguous output-major regions:
//   uint8 q[N][K/2], low nibble = even K, high nibble = odd K;
//   bfloat16 scales[N][K/128]; uint8 zeros[N][K/128].
// Projection dimensions are compile-time constants. The host slices weights
// before packing; there is no implicit global channel offset in this kernel.
extern "C" void w4a16_linear_bf16(const bfloat16 *__restrict x,
                                  const uint8_t *__restrict payload,
                                  bfloat16 *__restrict y) {
  constexpr int K = HETEROMEGA_K;
  constexpr int N = HETEROMEGA_N;
  constexpr int groups = K / 128;
  constexpr int quant_bytes = N * K / 2;
  const bfloat16 *scales =
      reinterpret_cast<const bfloat16 *>(payload + quant_bytes);
  const uint8_t *zeros = payload + quant_bytes + N * groups * 2;
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);

  for (int n = 0; n < N; ++n) {
    float sum = 0.0f;
    for (int k = 0; k < K; ++k) {
      const uint8_t byte = payload[n * (K / 2) + k / 2];
      const int q = (byte >> ((k & 1) * 4)) & 15;
      const int group = n * groups + k / 128;
      // Match the BF16 dequantized-weight boundary of the portable oracle.
      const bfloat16 w = bfloat16(float(q - int(zeros[group])) *
                                  float(scales[group]));
      sum += float(x[k]) * float(w);
    }
    y[n] = bfloat16(sum);
  }
  aie::set_rounding(saved_rounding);
}
