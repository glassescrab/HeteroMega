// Copyright (C) 2025, Advanced Micro Devices, Inc.
// Copyright (C) 2025, University of Illinois Urbana-Champaign.
// Copyright (C) 2026, HeteroMega contributors.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
// W4A16 prefill using TileFuse's BFP16-backed 8x8x8 MMUL strategy, adapted
// from glassescrab/mlir-aie at 121dd54abc68f84d89a7074372ebf82be2db62d5:
//   aie_kernels/aie2p/mix_int4_ATB.cc
//   programming_examples/tilefuse/gemm_w4a16/makefile-common
//
// The upstream full 64x128x64, DIV=2 array schedule is NOT copied here.
// HeteroMega retains M16/K128/N32 compact tensors and explicit REUSE=1/2/4
// state. This avoids the upstream hidden g_counter and keeps FP32 partials
// resident across K groups rather than rounding each group to BF16.
//
// External A/C layout remains 4x8-blocked; vector gathers/scatters below
// bridge to the internal 8x8 layout. W stays 2144 bytes: 2048 packed q bytes,
// 64 BF16 scale bytes and 32 zero-point bytes. Bscratch stays 8192 bytes.
// Dequantization retains HeteroMega's hardware-validated compact metadata
// loads; its per-column (q-z)*scale is equivalent to the corrected upstream
// row-major dequantization. Upstream's duplicated zero-point bytes are not
// present in this ABI. The native-BF16 source remains a separate control.
// Hardware compilation, numerical deviation and speedup require measurement.

// The AIE API implements BF16-input 8x8x8 MMUL via the BFP16 unit only
// when this flag is enabled before its headers. A caller cannot silently
// switch this source back to the native BF16 arithmetic implementation.
#ifndef AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
#define AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 1
#elif AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 != 1
#error "The BFP16 FFN kernel requires BFP16 MMUL emulation enabled"
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
constexpr int MR = 8;
constexpr int ABI_MR = 4;
constexpr int ABI_BLOCK_ELEMENTS = ABI_MR * 8;
constexpr int KR = 8;
constexpr int NR = 8;
constexpr int MB = M / MR;
constexpr int KB = K / KR;
constexpr int NB = N / NR;
constexpr int Q_BYTES = K * N / 2;

using MMUL = aie::mmul<MR, KR, NR, bfloat16, bfloat16, accfloat>;
static_assert(MMUL::size_A == 64 && MMUL::size_B == 64 &&
                  MMUL::size_C == 64,
              "BFP16 arithmetic requires an 8x8x8 MMUL");
static_assert(M % (2 * MR) == 0 && N % (2 * NR) == 0,
              "the four-accumulator expansion requires two M and N blocks");
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
  // For validated W4 zero points z in [0,15], BF16(128+z) has exact bits
  // 0x4300|z. Build those bits directly: a scalar integer-to-bfloat16 cast
  // otherwise lowers to 32 software __floatunsisf calls per packed tile.
  // Retain scalar lane addressing because earlier vectorized metadata
  // widening exposed incorrect varying-zero lanes on hardware. Loading as
  // uint16 and casting the vector bits avoids type-punning the local array.
  // Eight-element loads require only 16-byte metadata alignment.
  alignas(aie::vector_decl_align) uint16_t zero_plus_128_bits[N];
  for (int n = 0; n < N; ++n)
    zero_plus_128_bits[n] = uint16_t(0x4300u | unsigned(zero_bytes[n]));

  for (int nb = 0; nb < NB; ++nb) {
    const auto scale = aie::load_v<NR>(scales + nb * NR)
                           .template grow_replicate<KR * NR>();
    const auto bias = aie::load_v<NR>(zero_plus_128_bits + nb * NR)
                          .template cast_to<bfloat16>()
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

// The external ABI keeps 4x8 A/C microtiles so the existing DMA schedule,
// compact host packers, adjacent SwiGLU FIFOs and output drains are unchanged.
// Internally combine two adjacent row blocks into each row-major 8x8 vector.
// aie::concat / vector::extract are the AIE API vector assembly operations.
static inline aie::vector<bfloat16, 64>
load_a_8x8(const bfloat16 *__restrict a, int mb, int kb) {
  const int top = (2 * mb * KB + kb) * ABI_BLOCK_ELEMENTS;
  const int bottom = top + KB * ABI_BLOCK_ELEMENTS;
  return aie::concat(aie::load_v<32>(a + top), aie::load_v<32>(a + bottom));
}

static inline aie::vector<float, 64>
load_c_8x8(const float *__restrict c, int mb, int nb) {
  const int top = (2 * mb * NB + nb) * ABI_BLOCK_ELEMENTS;
  const int bottom = top + NB * ABI_BLOCK_ELEMENTS;
  return aie::concat(aie::load_v<32>(c + top), aie::load_v<32>(c + bottom));
}

static inline void store_c_8x8(float *__restrict c, int mb, int nb,
                               const aie::vector<float, 64> &value) {
  const int top = (2 * mb * NB + nb) * ABI_BLOCK_ELEMENTS;
  const int bottom = top + NB * ABI_BLOCK_ELEMENTS;
  aie::store_v(c + top, value.extract<32>(0));
  aie::store_v(c + bottom, value.extract<32>(1));
}

// TileFuse's 2x2 expansion: each K8 step reuses two A and two B vectors in
// four 8x8 MMUL accumulators. The API converts the BF16 operands to BFP16;
// C is FP32, including between K128 groups, and is narrowed only in finish.
// This is not numerically equivalent to the native BF16 multiplication path.
static inline void accumulate_dequantized(const bfloat16 *__restrict a,
                                         const bfloat16 *__restrict b_scratch,
                                         float *__restrict c) {
  for (int mb = 0; mb < MB; mb += 2) {
    for (int nb = 0; nb < NB; nb += 2) {
      MMUL acc00(load_c_8x8(c, mb, nb));
      MMUL acc01(load_c_8x8(c, mb, nb + 1));
      MMUL acc10(load_c_8x8(c, mb + 1, nb));
      MMUL acc11(load_c_8x8(c, mb + 1, nb + 1));

      AIE_PREPARE_FOR_PIPELINING
      for (int kb = 0; kb < KB; ++kb) {
        const auto a0 = load_a_8x8(a, mb, kb);
        const auto a1 = load_a_8x8(a, mb + 1, kb);
        const auto b0 = aie::load_v<MMUL::size_B>(
            b_scratch + (kb * NB + nb) * MMUL::size_B);
        const auto b1 = aie::load_v<MMUL::size_B>(
            b_scratch + (kb * NB + nb + 1) * MMUL::size_B);
        acc00.mac(a0, b0);
        acc01.mac(a0, b1);
        acc10.mac(a1, b0);
        acc11.mac(a1, b1);
      }
      store_c_8x8(c, mb, nb, acc00.to_vector<float>());
      store_c_8x8(c, mb, nb + 1, acc01.to_vector<float>());
      store_c_8x8(c, mb + 1, nb, acc10.to_vector<float>());
      store_c_8x8(c, mb + 1, nb + 1, acc11.to_vector<float>());
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
