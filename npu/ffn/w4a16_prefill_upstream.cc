// Copyright (C) 2026 HeteroMega contributors.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
// Native BF16 W4A16 projection consuming glassescrab TileFuse weight tiles
// directly. Upstream ABI: K128/N64, 4352 bytes, corrected revision
// 121dd54abc68f84d89a7074372ebf82be2db62d5, mix_int4_ATB.cc/test.cpp.
// The graph holds one upstream payload and A[reuse,2048], then calls low
// and high with separate C[reuse,512] buffers and the same 4096-BF16 scratch.
// Thus both N32 halves reuse the original DMA object without host repacking
// or duplicate weight DMA. C remains FP32 across K groups; Y is BF16.
// Native 4x8x8 four-accumulator MMUL follows AMD MLIR-AIE aie2p/mm.cc,
// Copyright 2025 AMD, Apache-2.0 WITH LLVM-exception, revision
// 7e00b57955e108fe9d8e9419f5828a0c7e650858.

// Select native BF16 before AIE headers, including standalone compilations.
#ifndef AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
#define AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 0
#elif AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 != 0
#error "Direct upstream W4A16 requires native BF16 MMUL"
#endif

#include <aie_api/aie.hpp>
#include <stdint.h>
#include "aie_kernel_utils.h"

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
constexpr int PACKED_N = 64;
constexpr int PACKED_NB = PACKED_N / NR;
constexpr int Q_BYTES = K * PACKED_N / 2;

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

// A uses native [MB=4, KB=16, MR=4, KR=8] blocks. The ORIGINAL W tile:
//   bytes [0,4096): q[KB=16,NB=8,KR=8,NR/2=4], low-even/high-odd;
//   bytes [4096,4224): BF16 scales[64];
//   bytes [4224,4352): zeros[NB=8,repeat=2,NR=8].
// The duplicate zero vectors are per N8 block, not two copies of all N64.
// Scratch remains BF16 [KB=16, NB=4, KR=8, NR=8] for one selected half.
// Keeping Half static gives the compiler constant payload offsets.
template <unsigned Half>
static inline void dequantize(const uint8_t *__restrict payload,
                             bfloat16 *__restrict scratch) {
  static_assert(Half < 2, "an upstream N64 tile has two N32 halves");
  const auto *scales =
      reinterpret_cast<const bfloat16 *>(payload + Q_BYTES) + Half * N;
  const auto *zero_bytes = payload + Q_BYTES + PACKED_N * 2;
  // Build exact BF16(128+z) bits for validated W4 zero points in [0,15].
  // Scalar lane addressing preserves the varying-zero hardware fix while
  // avoiding software integer-to-float conversion calls.
  alignas(aie::vector_decl_align) uint16_t zero_plus_128_bits[N];
  for (int n = 0; n < N; ++n) {
    const int upstream_n = Half * N + n;
    const int zero_offset = (upstream_n / NR) * (2 * NR) + upstream_n % NR;
    zero_plus_128_bits[n] =
        uint16_t(0x4300u | unsigned(zero_bytes[zero_offset]));
  }

  for (int nb = 0; nb < NB; ++nb) {
    const auto scale = aie::load_v<NR>(scales + nb * NR)
                           .template grow_replicate<KR * NR>();
    const auto bias = aie::load_v<NR>(zero_plus_128_bits + nb * NR)
                          .template cast_to<bfloat16>()
                          .template grow_replicate<KR * NR>();
    AIE_PREPARE_FOR_PIPELINING
    for (int kb = 0; kb < KB; ++kb) {
      const int source_tile = kb * PACKED_NB + Half * NB + nb;
      const auto q4 = aie::load_v<KR * NR>(
          reinterpret_cast<const uint4 *>(payload + source_tile * (KR * NR / 2)));
      const aie::vector<uint8, KR * NR> q8 = aie::unpack(q4);
      const auto quant_plus_128 = add_128_as_bf16(q8);
      const auto centered = aie::sub(quant_plus_128, bias);
      const auto weight = aie::mul(centered, scale).to_vector<bfloat16>();
      aie::store_v(scratch + (kb * NB + nb) * (KR * NR), weight);
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

// Reuse the same dequantized half across every M tile. The caller keeps
// the full upstream FIFO object acquired until both low/high calls finish.
template <unsigned Half>
static inline void accumulate_half(const bfloat16 *__restrict a,
                                   const uint8_t *__restrict payload,
                                   float *__restrict c,
                                   bfloat16 *__restrict b_scratch) {
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  event0();
  dequantize<Half>(payload, b_scratch);
  for (int r = 0; r < REUSE; ++r)
    accumulate_dequantized(a + r * M * K, b_scratch, c + r * M * N);
  event1();
  aie::set_rounding(saved_rounding);
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
// baseline M16/N32 tile. Low/high select halves of the SAME original N64
// payload. K groups must still arrive in the original increasing order.
void w4a16_prefill_reuse_init(float *__restrict c) {
  const auto zeros = aie::zeros<float, 16>();
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < REUSE * M * N; i += 16)
    aie::store_v(c + i, zeros);
}

void w4a16_prefill_reuse_accumulate_low(const bfloat16 *__restrict a,
                                       const uint8_t *__restrict payload,
                                       float *__restrict c,
                                       bfloat16 *__restrict b_scratch) {
  accumulate_half<0>(a, payload, c, b_scratch);
}

void w4a16_prefill_reuse_accumulate_high(const bfloat16 *__restrict a,
                                        const uint8_t *__restrict payload,
                                        float *__restrict c,
                                        bfloat16 *__restrict b_scratch) {
  accumulate_half<1>(a, payload, c, b_scratch);
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
