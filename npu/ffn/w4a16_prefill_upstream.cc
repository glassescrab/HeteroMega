// Copyright (C) 2025, Advanced Micro Devices, Inc.
// Copyright (C) 2025, University of Illinois Urbana-Champaign.
// Copyright (C) 2026 HeteroMega contributors.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
// W4A16 projection consuming glassescrab TileFuse weight tiles
// directly. Upstream ABI: K128/N64, 4352 bytes, corrected revision
// 121dd54abc68f84d89a7074372ebf82be2db62d5, mix_int4_ATB.cc/test.cpp.
// The graph holds one upstream payload and A[reuse,2048], then calls low
// and high with separate C[reuse,512] buffers and the same 4096-BF16 scratch.
// Thus both N32 halves reuse the original DMA object without host repacking
// or duplicate weight DMA. By default C remains FP32 across K groups; Y is
// BF16. The opt-in native8 experiment stores BF16 C at each K128 boundary.
// Native 4x8x8 four-accumulator MMUL follows AMD MLIR-AIE aie2p/mm.cc,
// Copyright 2025 AMD, Apache-2.0 WITH LLVM-exception, revision
// 7e00b57955e108fe9d8e9419f5828a0c7e650858.
// Optional BFP16-backed 8x8x8 four-accumulator MMUL follows TileFuse at
// 121dd54abc68f84d89a7074372ebf82be2db62d5 (aie2p/mix_int4_ATB.cc).
// By default internal gathers/scatters preserve the external 4x8-blocked
// A/C ABI. The opt-in native8 layout uses direct 8x8 A/C/Y blocks instead.

// Select arithmetic before AIE headers. Standalone builds default to native
// BF16; explicit 1 enables the AIE API's BFP16-backed BF16-input MMUL.
#ifndef AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
#define AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 0
#elif AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 != 0 && \
    AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 != 1
#error "Direct upstream W4A16 arithmetic flag must be 0 or 1"
#endif

// Independent ablations: defaults preserve the measured four-accumulator
// kernel and scalar zero-metadata path until device checks select a winner.
#ifndef HETEROMEGA_VECTOR_ZERO
#define HETEROMEGA_VECTOR_ZERO 0
#endif
#if HETEROMEGA_VECTOR_ZERO != 0 && HETEROMEGA_VECTOR_ZERO != 1
#error "HETEROMEGA_VECTOR_ZERO must be 0 or 1"
#endif
#ifndef HETEROMEGA_MMUL_M_REUSE
#define HETEROMEGA_MMUL_M_REUSE 1
#endif
#if HETEROMEGA_MMUL_M_REUSE != 1 && HETEROMEGA_MMUL_M_REUSE != 2
#error "HETEROMEGA_MMUL_M_REUSE must be 1 or 2"
#endif
#if AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 && HETEROMEGA_MMUL_M_REUSE != 1
#error "BFP16 MMUL requires HETEROMEGA_MMUL_M_REUSE=1"
#endif

// Opt-in paired ABI/arithmetic experiment. A/C/Y use native 8x8 blocks,
// and C is rounded to BF16 after every K128 group. The default retains
// the existing 4x8 A/Y ABI and FP32 partials exactly.
#ifndef HETEROMEGA_BFP16_NATIVE_LAYOUT
#define HETEROMEGA_BFP16_NATIVE_LAYOUT 0
#endif
#if HETEROMEGA_BFP16_NATIVE_LAYOUT != 0 && HETEROMEGA_BFP16_NATIVE_LAYOUT != 1
#error "HETEROMEGA_BFP16_NATIVE_LAYOUT must be 0 or 1"
#endif
#if HETEROMEGA_BFP16_NATIVE_LAYOUT && !AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
#error "Native 8x8 layout and BF16 partials require BFP16 arithmetic"
#endif
#ifndef HETEROMEGA_PRECONVERT_B
#define HETEROMEGA_PRECONVERT_B 0
#endif
#if HETEROMEGA_PRECONVERT_B != 0 && HETEROMEGA_PRECONVERT_B != 1
#error "HETEROMEGA_PRECONVERT_B must be 0 or 1"
#endif
#if HETEROMEGA_PRECONVERT_B && !HETEROMEGA_BFP16_NATIVE_LAYOUT
#error "Preconverted B requires native8 BFP16 arithmetic"
#endif
#ifndef HETEROMEGA_SPLIT_M32_A
#define HETEROMEGA_SPLIT_M32_A 0
#endif
#if HETEROMEGA_SPLIT_M32_A != 0 && HETEROMEGA_SPLIT_M32_A != 1
#error "HETEROMEGA_SPLIT_M32_A must be 0 or 1"
#endif
#if HETEROMEGA_SPLIT_M32_A && !HETEROMEGA_BFP16_NATIVE_LAYOUT
#error "Split M32 activation streaming requires native8 BFP16 arithmetic"
#endif
#ifndef HETEROMEGA_PRECONVERT_A
#define HETEROMEGA_PRECONVERT_A 0
#endif
#if HETEROMEGA_PRECONVERT_A != 0 && HETEROMEGA_PRECONVERT_A != 1
#error "HETEROMEGA_PRECONVERT_A must be 0 or 1"
#endif
#if HETEROMEGA_PRECONVERT_A && \
    !(HETEROMEGA_SPLIT_M32_A && HETEROMEGA_PRECONVERT_B)
#error "Preconverted A requires split M32 activation streaming and preconverted B"
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
#if HETEROMEGA_SPLIT_M32_A
static_assert(HETEROMEGA_M_REUSE == 4, "Split M32 activation streaming requires M reuse4");
#endif

namespace {
constexpr int REUSE = HETEROMEGA_M_REUSE;
constexpr int M = 16;
constexpr int K = 128;
constexpr int N = 32;
constexpr int ABI_MR = 4;
constexpr int ABI_BLOCK_ELEMENTS = ABI_MR * 8;
#if AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
constexpr int MR = 8;
#else
constexpr int MR = 4;
#endif
constexpr int KR = 8;
constexpr int NR = 8;
constexpr int MB = M / MR;
constexpr int KB = K / KR;
constexpr int NB = N / NR;
constexpr int PACKED_N = 64;
constexpr int PACKED_NB = PACKED_N / NR;
constexpr int Q_BYTES = K * PACKED_N / 2;
#if HETEROMEGA_BFP16_NATIVE_LAYOUT
using Partial = bfloat16;
#else
using Partial = float;
#endif

using MMUL = aie::mmul<MR, KR, NR, bfloat16, bfloat16, accfloat>;
#if HETEROMEGA_PRECONVERT_B
using NativeMMUL = aie::mmul<8, 8, 8, bfloat16, bfp16ebs8, accfloat>;
constexpr int BFP_TILE_BYTES = aie::block_vector<bfp16ebs8, 64>::memory_bytes();
static_assert(BFP_TILE_BYTES == 72, "BFP16 EBS8 tile must occupy 72 bytes");
constexpr int HALF_SCRATCH_ELEMENTS = KB * NB * BFP_TILE_BYTES / sizeof(bfloat16);
#else
using NativeMMUL = MMUL;
constexpr int HALF_SCRATCH_ELEMENTS = K * N;
#endif
#if HETEROMEGA_PRECONVERT_A
using PreconvertedMMUL = aie::mmul<8, 8, 8, bfp16ebs8, bfp16ebs8, accfloat>;
// Packed B halves occupy bytes [0,9216) of the split path's unchanged
// 16KiB scratch. Reuse the aligned tail for one M16 A object, [9216,11520).
// The next M16 overwrites only this tail after both N32 halves consume it.
constexpr int PACKED_A_OFFSET_BYTES = 2 * HALF_SCRATCH_ELEMENTS * sizeof(bfloat16);
constexpr int PACKED_A_BYTES = MB * KB * BFP_TILE_BYTES;
static_assert(PACKED_A_OFFSET_BYTES % 64 == 0 && KB * BFP_TILE_BYTES % 64 == 0,
              "Each packed A stream must begin at a 64-byte boundary");
static_assert(PACKED_A_OFFSET_BYTES + PACKED_A_BYTES <= 2 * K * N * sizeof(bfloat16),
              "Packed A must fit after packed B inside the full N64 scratch");
#endif
#if AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
static_assert(MMUL::size_A == 64 && MMUL::size_B == 64 &&
                  MMUL::size_C == 64,
              "BFP16 arithmetic requires an 8x8x8 MMUL");
#else
static_assert(MMUL::size_A == 32 && MMUL::size_B == 64 &&
                  MMUL::size_C == 32,
              "prefill packing requires a native 4x8x8 MMUL");
#endif
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

// The ORIGINAL W tile is independent of the selected activation layout:
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
#if !HETEROMEGA_VECTOR_ZERO
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
#endif

  for (int nb = 0; nb < NB; ++nb) {
#if HETEROMEGA_PRECONVERT_B
    // Each N8 stream starts at a 64-byte boundary (16*72=1152 bytes),
    // then reads/writes all K8 blocks sequentially. This avoids unaligned
    // block-stream seeks and fits inside the unchanged 8KiB scratch BO.
    auto *stream_base = reinterpret_cast<bfp16ebs8 *>(
        reinterpret_cast<uint8_t *>(scratch) + nb * KB * BFP_TILE_BYTES);
    aie::block_vector_output_buffer_stream<bfp16ebs8, 64> converted(stream_base);
#endif
    const auto scale = aie::load_v<NR>(scales + nb * NR)
                           .template grow_replicate<KR * NR>();
#if HETEROMEGA_VECTOR_ZERO
    // Upstream stores each N8 zero vector twice consecutively. Widen both
    // copies before setting BF16 exponent bits; repeating these 16 lanes
    // gives exactly the same eight K-row copies as the scalar reference.
    const auto zeros = aie::load_v<2 * NR>(
        zero_bytes + (Half * NB + nb) * (2 * NR));
    const auto bias = add_128_as_bf16(zeros)
                          .template grow_replicate<KR * NR>();
#else
    const auto bias = aie::load_v<NR>(zero_plus_128_bits + nb * NR)
                          .template cast_to<bfloat16>()
                          .template grow_replicate<KR * NR>();
#endif
    AIE_PREPARE_FOR_PIPELINING
    for (int kb = 0; kb < KB; ++kb) {
      const int source_tile = kb * PACKED_NB + Half * NB + nb;
      const auto q4 = aie::load_v<KR * NR>(
          reinterpret_cast<const uint4 *>(payload + source_tile * (KR * NR / 2)));
      const aie::vector<uint8, KR * NR> q8 = aie::unpack(q4);
      const auto quant_plus_128 = add_128_as_bf16(q8);
      const auto centered = aie::sub(quant_plus_128, bias);
      const auto weight = aie::mul(centered, scale).to_vector<bfloat16>();
#if HETEROMEGA_PRECONVERT_B
      // Match the BF16-input MMUL's B operand conversion exactly: preserve
      // the BF16 dequant rounding, transpose K/N, widen by multiplying by
      // BF16 one, then convert with the caller's conv_even rounding mode.
      const auto transposed = aie::transpose(weight, 8, 8);
      const aie::accum<accfloat, 64> widened = ::mul_elem_64(
          transposed, ::concat(::broadcast_one_to_v32bfloat16(),
                               ::broadcast_one_to_v32bfloat16()));
      converted << widened;
#else
      aie::store_v(scratch + (kb * NB + nb) * (KR * NR), weight);
#endif
    }
  }
}

#if AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
// Two adjacent external 4x8 row blocks form each internal 8x8 operand.
// These local vector assembly operations do not change host weight buffers,
// activation layout, FIFO element sizes or the FP32 partial-output layout.
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
#endif

#if HETEROMEGA_MMUL_M_REUSE == 2
// Pair two independent M16 lanes. Each K step shares its two B vectors
// across four A vectors and eight accumulators. Every output still sees
// the same increasing K8 MAC sequence and FP32 K128 boundary as above.
// This trades accumulator register pressure for fewer scratch loads; it
// is an experimental choice, not an assumption that the compiler avoids spills.
static inline void accumulate_dequantized_pair(
    const bfloat16 *__restrict a, const bfloat16 *__restrict b_scratch,
    float *__restrict c) {
  for (int mb = 0; mb < MB; mb += 2) {
    for (int nb = 0; nb < NB; nb += 2) {
      float *c00 = c + (mb * NB + nb) * MMUL::size_C;
      float *c01 = c00 + MMUL::size_C;
      float *c10 = c00 + NB * MMUL::size_C;
      float *c11 = c10 + MMUL::size_C;
      float *d00 = c00 + M * N;
      float *d01 = c01 + M * N;
      float *d10 = c10 + M * N;
      float *d11 = c11 + M * N;
      MMUL acc00(aie::load_v<MMUL::size_C>(c00));
      MMUL acc01(aie::load_v<MMUL::size_C>(c01));
      MMUL acc10(aie::load_v<MMUL::size_C>(c10));
      MMUL acc11(aie::load_v<MMUL::size_C>(c11));
      MMUL acc20(aie::load_v<MMUL::size_C>(d00));
      MMUL acc21(aie::load_v<MMUL::size_C>(d01));
      MMUL acc30(aie::load_v<MMUL::size_C>(d10));
      MMUL acc31(aie::load_v<MMUL::size_C>(d11));
      AIE_PREPARE_FOR_PIPELINING
      for (int kb = 0; kb < KB; ++kb) {
        const auto a0 = aie::load_v<MMUL::size_A>(
            a + (mb * KB + kb) * MMUL::size_A);
        const auto a1 = aie::load_v<MMUL::size_A>(
            a + ((mb + 1) * KB + kb) * MMUL::size_A);
        const auto a2 = aie::load_v<MMUL::size_A>(
            a + M * K + (mb * KB + kb) * MMUL::size_A);
        const auto a3 = aie::load_v<MMUL::size_A>(
            a + M * K + ((mb + 1) * KB + kb) * MMUL::size_A);
        const auto b0 = aie::load_v<MMUL::size_B>(
            b_scratch + (kb * NB + nb) * MMUL::size_B);
        const auto b1 = aie::load_v<MMUL::size_B>(
            b_scratch + (kb * NB + nb + 1) * MMUL::size_B);
        acc00.mac(a0, b0);
        acc01.mac(a0, b1);
        acc10.mac(a1, b0);
        acc11.mac(a1, b1);
        acc20.mac(a2, b0);
        acc21.mac(a2, b1);
        acc30.mac(a3, b0);
        acc31.mac(a3, b1);
      }
      aie::store_v(c00, acc00.to_vector<float>());
      aie::store_v(c01, acc01.to_vector<float>());
      aie::store_v(c10, acc10.to_vector<float>());
      aie::store_v(c11, acc11.to_vector<float>());
      aie::store_v(d00, acc20.to_vector<float>());
      aie::store_v(d01, acc21.to_vector<float>());
      aie::store_v(d10, acc30.to_vector<float>());
      aie::store_v(d11, acc31.to_vector<float>());
    }
  }
}
#endif

// Both arithmetic paths use four accumulators and preserve FP32 C across
// K groups. BFP16 changes operand arithmetic inside MMUL; the direct W4
// payload, BF16 dequantization and external A/C layout remain identical.
static inline void accumulate_dequantized(const bfloat16 *__restrict a,
                                         const bfloat16 *__restrict b_scratch,
                                         float *__restrict c) {
#if AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16
  // TileFuse's 2x2 expansion shares two A and two B vectors per K8 step.
  // The API converts BF16 inputs for the BFP16 unit, so numerical behavior
  // is not equivalent to the native BF16 control below.
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
#else
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
#endif
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
#if HETEROMEGA_MMUL_M_REUSE == 2
  for (int r = 0; r + 1 < REUSE; r += 2)
    accumulate_dequantized_pair(a + r * M * K, b_scratch, c + r * M * N);
  if (REUSE % 2)
    accumulate_dequantized(a + (REUSE - 1) * M * K, b_scratch,
                          c + (REUSE - 1) * M * N);
#else
  for (int r = 0; r < REUSE; ++r)
    accumulate_dequantized(a + r * M * K, b_scratch, c + r * M * N);
#endif
  event1();
  aie::set_rounding(saved_rounding);
}

#if HETEROMEGA_BFP16_NATIVE_LAYOUT
// Native block order A[MB=2,KB=16,8,8], C/Y[MB=2,NB=4,8,8]. This
// requires matching graph DMA transforms; it must never consume the old
// 4x8 activation layout. W and dequantized scratch retain their exact ABI.
// Four accumulators remain live, matching the selected upstream strategy;
// only K128 boundary storage changes from FP32 to nearest-even BF16.
static inline void accumulate_dequantized_native(
    const bfloat16 *__restrict a, const bfloat16 *__restrict b_scratch,
    bfloat16 *__restrict c) {
  for (int mb = 0; mb < MB; mb += 2) {
    for (int nb = 0; nb < NB; nb += 2) {
      bfloat16 *c00 = c + (mb * NB + nb) * MMUL::size_C;
      bfloat16 *c01 = c00 + MMUL::size_C;
      bfloat16 *c10 = c00 + NB * MMUL::size_C;
      bfloat16 *c11 = c10 + MMUL::size_C;
      NativeMMUL acc00(aie::load_v<MMUL::size_C>(c00));
      NativeMMUL acc01(aie::load_v<MMUL::size_C>(c01));
      NativeMMUL acc10(aie::load_v<MMUL::size_C>(c10));
      NativeMMUL acc11(aie::load_v<MMUL::size_C>(c11));
#if HETEROMEGA_PRECONVERT_B
      const auto *packed = reinterpret_cast<const uint8_t *>(b_scratch);
      aie::block_vector_input_buffer_stream<bfp16ebs8, 64> b0_stream(
          reinterpret_cast<const bfp16ebs8 *>(packed + nb * KB * BFP_TILE_BYTES));
      aie::block_vector_input_buffer_stream<bfp16ebs8, 64> b1_stream(
          reinterpret_cast<const bfp16ebs8 *>(packed + (nb + 1) * KB * BFP_TILE_BYTES));
#endif
      AIE_PREPARE_FOR_PIPELINING
      for (int kb = 0; kb < KB; ++kb) {
        const auto a0 = aie::load_v<MMUL::size_A>(
            a + (mb * KB + kb) * MMUL::size_A);
        const auto a1 = aie::load_v<MMUL::size_A>(
            a + ((mb + 1) * KB + kb) * MMUL::size_A);
#if HETEROMEGA_PRECONVERT_B
        // Public mixed MMUL requires the transpose operation modifier.
        // B is already stored as N8/K8; this selects A*B^T and passes the
        // packed parent unchanged to the hardware's 8x8T instruction.
        const auto b0 = aie::op_transpose(b0_stream.pop());
        const auto b1 = aie::op_transpose(b1_stream.pop());
#else
        const auto b0 = aie::load_v<MMUL::size_B>(
            b_scratch + (kb * NB + nb) * MMUL::size_B);
        const auto b1 = aie::load_v<MMUL::size_B>(
            b_scratch + (kb * NB + nb + 1) * MMUL::size_B);
#endif
        acc00.mac(a0, b0);
        acc01.mac(a0, b1);
        acc10.mac(a1, b0);
        acc11.mac(a1, b1);
      }
      aie::store_v(c00, acc00.to_vector<bfloat16>());
      aie::store_v(c01, acc01.to_vector<bfloat16>());
      aie::store_v(c10, acc10.to_vector<bfloat16>());
      aie::store_v(c11, acc11.to_vector<bfloat16>());
    }
  }
}

template <unsigned Half>
static inline void accumulate_half_native(const bfloat16 *__restrict a,
                                         const uint8_t *__restrict payload,
                                         bfloat16 *__restrict c,
                                         bfloat16 *__restrict b_scratch) {
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  event0();
  dequantize<Half>(payload, b_scratch);
  for (int r = 0; r < REUSE; ++r)
    accumulate_dequantized_native(a + r * M * K, b_scratch, c + r * M * N);
  event1();
  aie::set_rounding(saved_rounding);
}

#if HETEROMEGA_SPLIT_M32_A
#if HETEROMEGA_PRECONVERT_A
static inline void preconvert_a_native(const bfloat16 *__restrict a,
                                      bfp16ebs8 *__restrict packed_a) {
  for (int mb = 0; mb < MB; ++mb) {
    auto *stream_base = reinterpret_cast<bfp16ebs8 *>(
        reinterpret_cast<uint8_t *>(packed_a) + mb * KB * BFP_TILE_BYTES);
    aie::block_vector_output_buffer_stream<bfp16ebs8, 64> converted(stream_base);
    AIE_PREPARE_FOR_PIPELINING
    for (int kb = 0; kb < KB; ++kb) {
      // Exactly the mixed BF16/BFP MMUL's A conversion, with no transpose.
      const aie::accum<accfloat, 64> widened(
          aie::load_v<MMUL::size_A>(a + (mb * KB + kb) * MMUL::size_A));
      converted << widened;
    }
  }
}

static inline void accumulate_preconverted_native(
    const bfp16ebs8 *__restrict packed_a,
    const bfloat16 *__restrict b_scratch, bfloat16 *__restrict c) {
  const auto *a_bytes = reinterpret_cast<const uint8_t *>(packed_a);
  const auto *b_bytes = reinterpret_cast<const uint8_t *>(b_scratch);
  for (int nb = 0; nb < NB; nb += 2) {
    bfloat16 *c00 = c + nb * MMUL::size_C;
    bfloat16 *c01 = c00 + MMUL::size_C;
    bfloat16 *c10 = c00 + NB * MMUL::size_C;
    bfloat16 *c11 = c10 + MMUL::size_C;
    PreconvertedMMUL acc00(aie::load_v<MMUL::size_C>(c00));
    PreconvertedMMUL acc01(aie::load_v<MMUL::size_C>(c01));
    PreconvertedMMUL acc10(aie::load_v<MMUL::size_C>(c10));
    PreconvertedMMUL acc11(aie::load_v<MMUL::size_C>(c11));
    aie::block_vector_input_buffer_stream<bfp16ebs8, 64> a0_stream(packed_a);
    aie::block_vector_input_buffer_stream<bfp16ebs8, 64> a1_stream(
        reinterpret_cast<const bfp16ebs8 *>(a_bytes + KB * BFP_TILE_BYTES));
    aie::block_vector_input_buffer_stream<bfp16ebs8, 64> b0_stream(
        reinterpret_cast<const bfp16ebs8 *>(b_bytes + nb * KB * BFP_TILE_BYTES));
    aie::block_vector_input_buffer_stream<bfp16ebs8, 64> b1_stream(
        reinterpret_cast<const bfp16ebs8 *>(b_bytes + (nb + 1) * KB * BFP_TILE_BYTES));
    AIE_PREPARE_FOR_PIPELINING
    for (int kb = 0; kb < KB; ++kb) {
      const auto a0 = a0_stream.pop();
      const auto a1 = a1_stream.pop();
      const auto b0 = aie::op_transpose(b0_stream.pop());
      const auto b1 = aie::op_transpose(b1_stream.pop());
      acc00.mac(a0, b0);
      acc01.mac(a0, b1);
      acc10.mac(a1, b0);
      acc11.mac(a1, b1);
    }
    aie::store_v(c00, acc00.to_vector<bfloat16>());
    aie::store_v(c01, acc01.to_vector<bfloat16>());
    aie::store_v(c10, acc10.to_vector<bfloat16>());
    aie::store_v(c11, acc11.to_vector<bfloat16>());
  }
}
#endif

// One M32 activation FIFO object updates either rows0..31 or32..63 of
// both N32 partials. Four accumulators remain live at a time. The graph
// holds W and the full-N64 scratch until both M32 objects have completed.
template <unsigned MOffset>
static inline void accumulate_pair_m32(const bfloat16 *__restrict a,
                                      bfloat16 *__restrict c0,
                                      bfloat16 *__restrict c1,
                                      bfloat16 *__restrict b_scratch) {
  static_assert(MOffset == 0 || MOffset == 2, "M32 offset is measured in M16 lanes");
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  event0();
  for (int r = 0; r < 2; ++r) {
#if HETEROMEGA_PRECONVERT_A
    auto *packed_a = reinterpret_cast<bfp16ebs8 *>(
        reinterpret_cast<uint8_t *>(b_scratch) + PACKED_A_OFFSET_BYTES);
    preconvert_a_native(a + r * M * K, packed_a);
    accumulate_preconverted_native(packed_a, b_scratch,
                                   c0 + (MOffset + r) * M * N);
    accumulate_preconverted_native(packed_a, b_scratch + HALF_SCRATCH_ELEMENTS,
                                   c1 + (MOffset + r) * M * N);
#else
    accumulate_dequantized_native(a + r * M * K, b_scratch,
                                 c0 + (MOffset + r) * M * N);
    accumulate_dequantized_native(a + r * M * K,
                                 b_scratch + HALF_SCRATCH_ELEMENTS,
                                 c1 + (MOffset + r) * M * N);
#endif
  }
  event1();
  aie::set_rounding(saved_rounding);
}
#endif
#endif

} // namespace

extern "C" {

#if HETEROMEGA_SPLIT_M32_A
void w4a16_prefill_dequantize_pair(const uint8_t *__restrict payload,
                                  bfloat16 *__restrict b_scratch) {
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  event0();
  dequantize<0>(payload, b_scratch);
  dequantize<1>(payload, b_scratch + HALF_SCRATCH_ELEMENTS);
  event1();
  aie::set_rounding(saved_rounding);
}

void w4a16_prefill_accumulate_pair_m0(const bfloat16 *__restrict a,
                                    bfloat16 *__restrict c0,
                                    bfloat16 *__restrict c1,
                                    bfloat16 *__restrict b_scratch) {
  accumulate_pair_m32<0>(a, c0, c1, b_scratch);
}

void w4a16_prefill_accumulate_pair_m1(const bfloat16 *__restrict a,
                                    bfloat16 *__restrict c0,
                                    bfloat16 *__restrict c1,
                                    bfloat16 *__restrict b_scratch) {
  accumulate_pair_m32<2>(a, c0, c1, b_scratch);
}
#endif

// Default C/Y use [MB=4,NB=4,MR=4,NR=8] blocks; native8 uses
// [MB=2,NB=4,MR=8,NR=8].
// The graph calls init once per output tile, accumulate once per K group,
// then finish once. C stays local: FP32 by default, BF16 in native8 mode.
void w4a16_prefill_init(Partial *__restrict c) {
  const auto zeros = aie::zeros<Partial, 16>();
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < M * N; i += 16)
    aie::store_v(c + i, zeros);
}

void w4a16_prefill_finish(const Partial *__restrict c,
                         bfloat16 *__restrict output) {
#if HETEROMEGA_BFP16_NATIVE_LAYOUT
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < M * N; i += 32)
    aie::store_v(output + i, aie::load_v<32>(c + i));
#else
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < M * N; i += 16) {
    const aie::accum<accfloat, 16> value(aie::load_v<16>(c + i));
    aie::store_v(output + i, value.to_vector<bfloat16>());
  }
  aie::set_rounding(saved_rounding);
#endif
}


// Grouped ABI: A[r] is an M16/K128 tile, C[r] and Y[r] are M16/N32 tiles
// in the selected layout. Low/high select halves of the SAME original N64
// payload. K groups must still arrive in the original increasing order.
void w4a16_prefill_reuse_init(Partial *__restrict c) {
  const auto zeros = aie::zeros<Partial, 16>();
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < REUSE * M * N; i += 16)
    aie::store_v(c + i, zeros);
}

void w4a16_prefill_reuse_accumulate_low(const bfloat16 *__restrict a,
                                       const uint8_t *__restrict payload,
                                       Partial *__restrict c,
                                       bfloat16 *__restrict b_scratch) {
#if HETEROMEGA_BFP16_NATIVE_LAYOUT
  accumulate_half_native<0>(a, payload, c, b_scratch);
#else
  accumulate_half<0>(a, payload, c, b_scratch);
#endif
}

void w4a16_prefill_reuse_accumulate_high(const bfloat16 *__restrict a,
                                        const uint8_t *__restrict payload,
                                        Partial *__restrict c,
                                        bfloat16 *__restrict b_scratch) {
#if HETEROMEGA_BFP16_NATIVE_LAYOUT
  accumulate_half_native<1>(a, payload, c, b_scratch);
#else
  accumulate_half<1>(a, payload, c, b_scratch);
#endif
}

void w4a16_prefill_reuse_finish(const Partial *__restrict c,
                              bfloat16 *__restrict output) {
#if HETEROMEGA_BFP16_NATIVE_LAYOUT
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < REUSE * M * N; i += 32)
    aie::store_v(output + i, aie::load_v<32>(c + i));
#else
  const auto saved_rounding = aie::swap_rounding(aie::rounding_mode::conv_even);
  AIE_PREPARE_FOR_PIPELINING
  for (int i = 0; i < REUSE * M * N; i += 16) {
    const aie::accum<accfloat, 16> value(aie::load_v<16>(c + i));
    aie::store_v(output + i, value.to_vector<bfloat16>());
  }
  aie::set_rounding(saved_rounding);
#endif
}

} // extern "C"
