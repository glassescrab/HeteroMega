// Copyright (C) 2026 HeteroMega contributors.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
// Batched-M W4A16 GEMM tiles for AIE2P / NPU2.
// Reuse one dequantized K128/N32 weight tile across 1, 2 or 4 M16 tiles.
// Existing single-tile exported functions retain their original ABI.
// New grouped functions use A[reuse,2048], C[reuse,512], Y[reuse,512],
// with identical native microtile order inside each M16 tile.
// Weight payload remains 2144 bytes; Bscratch remains 4096 BF16 elements.
// Set -DHETEROMEGA_M_REUSE=1/2/4 and include reuse in the compiled object name.
// The blocked 2x2 MMUL expansion follows AMD MLIR-AIE's aie2p/mm.cc
// (Copyright 2025 AMD, Apache-2.0 WITH LLVM-exception), pinned at
// 7e00b57955e108fe9d8e9419f5828a0c7e650858.
// This is native BF16 multiplication with FP32 accumulation, not BFP16.

#include <aie_api/aie.hpp>
#include <stdint.h>
#include "aie_kernel_utils.h"

#if defined(AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16) && \
    AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
#error "W4A16 prefill requires native BF16 MMUL; disable BFP16 emulation"
#endif

#ifndef HETEROMEGA_M_REUSE
#define HETEROMEGA_M_REUSE 2
#endif
static_assert(HETEROMEGA_M_REUSE == 1 || HETEROMEGA_M_REUSE == 2 ||
                  HETEROMEGA_M_REUSE == 4,
              "M reuse must be 1, 2 or 4 native M16 tiles");

namespace {
constexpr int REUSE = HETEROMEGA_M_REUSE;
constexpr int M = 16;
constexpr int K = 128;
constexpr int N = 32;
constexpr int MR = 4;
constexpr int KR = 8;
constexpr int NR = 8;
constexpr int MB = M / MR;
constexpr int KB = K / KR;
constexpr int NB = N / NR;
constexpr int Q_BYTES = K * N / 2;

using MMUL = aie::mmul<MR, KR, NR, bfloat16, bfloat16, accfloat>;
static_assert(MMUL::size_A == 32 && MMUL::size_B == 64 &&
                  MMUL::size_C == 32,
              "prefill packing requires a native 4x8x8 MMUL");
static_assert(sizeof(uint4) == 1,
              "uint4 pointer arithmetic must step bytes");

// BF16 bits 0x4300 | q represent BF16(128 + q) exactly for q in [0,127].
// Widen before setting the exponent bits, keeping this conversion
// independent of byte interleave shuffles.
template <unsigned Lanes>
static inline aie::vector<bfloat16, Lanes>
add_128_as_bf16(aie::vector<uint8, Lanes> q) {
  const aie::vector<uint16, Lanes> wide = aie::unpack(q);
  return aie::bit_or(uint16(0x4300), wide).template cast_to<bfloat16>();
}

// A is packed [MB=4, KB=16, MR=4, KR=8]. Each 4x8 block is row-major.
// W payload is:
//   q bytes [KB=16, NB=4, KR=8, NR/2=4], low nibble is even local N;
//   BF16 scales[N=32], then unsigned uint8 zero_points[N=32].
// One K=128 tile is exactly one quantization group. Total payload: 2144 B.
// Bscratch receives BF16 [KB=16, NB=4, KR=8, NR=8] (8192 bytes).
static inline void dequantize(const uint8_t *__restrict payload,
                             bfloat16 *__restrict scratch) {
  const auto *scales =
      reinterpret_cast<const bfloat16 *>(payload + Q_BYTES);
  const auto *zero_bytes = payload + Q_BYTES + N * 2;
  // Convert only the 32 per-channel metadata values scalarly. Hardware
  // diagnostics exposed incorrect varying-zero lanes in the vectorized
  // metadata path; the packed 4096 weights and all MACs remain vectorized.
  // Eight-element loads also require only 16-byte metadata alignment.
  alignas(aie::vector_decl_align) bfloat16 zero_plus_128[N];
  for (int n = 0; n < N; ++n)
    zero_plus_128[n] = bfloat16(128 + unsigned(zero_bytes[n]));

  for (int nb = 0; nb < NB; ++nb) {
    const auto scale = aie::load_v<NR>(scales + nb * NR)
                           .template grow_replicate<KR * NR>();
    const auto bias = aie::load_v<NR>(zero_plus_128 + nb * NR)
                          .template grow_replicate<KR * NR>();
    AIE_PREPARE_FOR_PIPELINING
    for (int kb = 0; kb < KB; ++kb) {
      const int tile = kb * NB + nb;
      const auto q4 = aie::load_v<KR * NR>(
          reinterpret_cast<const uint4 *>(payload + tile * (KR * NR / 2)));
      const aie::vector<uint8, KR * NR> q8 = aie::unpack(q4);
      const auto quant_plus_128 = add_128_as_bf16(q8);
      // The subtraction is exact: integer q-z is in [-15,15]. Perform
      // the scale product in FP32 and round once to the BF16 weight.
      const auto centered = aie::sub(quant_plus_128, bias);
      const auto weight = aie::mul(centered, scale).to_vector<bfloat16>();
      aie::store_v(scratch + tile * (KR * NR), weight);
    }
  }
}

// Keep the baseline four-accumulator microkernel. Reuse targets weight
// transfer/dequantization, without speculatively multiplying accumulator
// register pressure by REUSE. Each call preserves FP32 C across K groups.
static inline void accumulate_dequantized(const bfloat16 *__restrict a,
                                         const bfloat16 *__restrict b_scratch,
                                         float *__restrict c) {
  // Four independent 4x8 accumulators reuse two A and two B vectors each
  // K step. All arithmetic in the K reduction is aie::mmul::mac.
  for (int mb = 0; mb < MB; mb += 2) {
    for (int nb = 0; nb < NB; nb += 2) {
      float *c00 = c + (mb * NB + nb) * MMUL::size_C;
      float *c01 = c00 + MMUL::size_C;
      float *c10 = c00 + NB * MMUL::size_C;
      float *c11 = c10 + MMUL::size_C;
      MMUL acc00(aie::load_v<MMUL::size_C>(c00));
      MMUL acc01(aie::load_v<MMUL::size_C>(c01));
      MMUL acc10(aie::load_v<MMUL::size_C>(c10));
      MMUL acc11(aie::load_v<MMUL::size_C>(c11));

      AIE_PREPARE_FOR_PIPELINING
      for (int kb = 0; kb < KB; ++kb) {
        const auto a0 = aie::load_v<MMUL::size_A>(
            a + (mb * KB + kb) * MMUL::size_A);
        const auto a1 = aie::load_v<MMUL::size_A>(
            a + ((mb + 1) * KB + kb) * MMUL::size_A);
        const auto b0 = aie::load_v<MMUL::size_B>(
            b_scratch + (kb * NB + nb) * MMUL::size_B);
        const auto b1 = aie::load_v<MMUL::size_B>(
            b_scratch + (kb * NB + nb + 1) * MMUL::size_B);
        acc00.mac(a0, b0);
        acc01.mac(a0, b1);
        acc10.mac(a1, b0);
        acc11.mac(a1, b1);
      }
      aie::store_v(c00, acc00.to_vector<float>());
      aie::store_v(c01, acc01.to_vector<float>());
      aie::store_v(c10, acc10.to_vector<float>());
      aie::store_v(c11, acc11.to_vector<float>());
    }
  }
}

} // namespace

extern "C" {

// C and Y use [MB=4, NB=4, MR=4, NR=8] block-major layout.
// The graph calls init once per output tile, accumulate once per K group,
// then finish once. C remains local FP32 across all K groups.
void w4a16_prefill_init(float *__restrict c) {
  const auto zeros = aie::zeros<float, 16>();
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < M * N; i += 16)
    aie::store_v(c + i, zeros);
}

void w4a16_prefill_accumulate(const bfloat16 *__restrict a,
                             const uint8_t *__restrict payload,
                             float *__restrict c,
                             bfloat16 *__restrict b_scratch) {
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  event0();
  dequantize(payload, b_scratch);

  accumulate_dequantized(a, b_scratch, c);
  event1();
  aie::set_rounding(saved_rounding);
}

void w4a16_prefill_finish(const float *__restrict c,
                         bfloat16 *__restrict output) {
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < M * N; i += 16) {
    const aie::accum<accfloat, 16> value(aie::load_v<16>(c + i));
    aie::store_v(output + i, value.to_vector<bfloat16>());
  }
  aie::set_rounding(saved_rounding);
}


// Grouped ABI: A[r] is the baseline M16/K128 tile, C[r] and Y[r] are the
// baseline M16/N32 tile. The graph supplies the SAME N32/K128 weight tile for
// every r. K groups must still arrive in the original increasing order.
void w4a16_prefill_reuse_init(float *__restrict c) {
  const auto zeros = aie::zeros<float, 16>();
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < REUSE * M * N; i += 16)
    aie::store_v(c + i, zeros);
}

void w4a16_prefill_reuse_accumulate(const bfloat16 *__restrict a,
                                   const uint8_t *__restrict payload,
                                   float *__restrict c,
                                   bfloat16 *__restrict b_scratch) {
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  event0();
  // This is intentionally outside the M-reuse loop. The new graph also
  // streams this packed payload once for the entire group, reducing both
  // dequantization count and logical weight DMA bytes by REUSE.
  dequantize(payload, b_scratch);
  for (int r = 0; r < REUSE; ++r)
    accumulate_dequantized(a + r * M * K, b_scratch, c + r * M * N);
  event1();
  aie::set_rounding(saved_rounding);
}

void w4a16_prefill_reuse_finish(const float *__restrict c,
                              bfloat16 *__restrict output) {
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < REUSE * M * N; i += 16) {
    const aie::accum<accfloat, 16> value(aie::load_v<16>(c + i));
    aie::store_v(output + i, value.to_vector<bfloat16>());
  }
  aie::set_rounding(saved_rounding);
}

} // extern "C"
