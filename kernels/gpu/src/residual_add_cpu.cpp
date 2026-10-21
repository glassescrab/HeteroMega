// Reducer R-CPU: x += y_g + y_n on host memory. AVX-512 when the CPU has it (Zen 5 does), scalar otherwise.
#include "heteromega/gpu_ffn.hpp"

#include <cstring>

#if defined(__x86_64__)
#include <immintrin.h>
#endif

namespace heteromega {
namespace {

inline float load1(uint16_t v) {
    const uint32_t u = static_cast<uint32_t>(v) << 16;
    float f;
    std::memcpy(&f, &u, sizeof(f));
    return f;
}

inline float load1(float v) { return v; }

inline uint16_t to_bf16(float f) {
    uint32_t u;
    std::memcpy(&u, &f, sizeof(u));
    if ((u & 0x7fffffffu) > 0x7f800000u) {
        return static_cast<uint16_t>((u >> 16) | 0x40u);
    }
    u += 0x7fffu + ((u >> 16) & 1u);
    return static_cast<uint16_t>(u >> 16);
}

template <typename PG, typename PN>
void row_scalar(uint16_t *x, const PG *g, const PN *n, int64_t begin, int64_t end) {
    for (int64_t c = begin; c < end; ++c) {
        x[c] = to_bf16(load1(x[c]) + (load1(g[c]) + load1(n[c])));
    }
}

#if defined(__x86_64__)
__attribute__((target("avx512f"))) inline __m512 load16(const uint16_t *p) {
    const __m256i h = _mm256_loadu_si256(reinterpret_cast<const __m256i *>(p));
    return _mm512_castsi512_ps(_mm512_slli_epi32(_mm512_cvtepu16_epi32(h), 16));
}

__attribute__((target("avx512f"))) inline __m512 load16(const float *p) { return _mm512_loadu_ps(p); }

// Round to nearest even, same as to_bf16().
__attribute__((target("avx512f"))) inline void store16(uint16_t *p, __m512 v) {
    const __m512i u = _mm512_castps_si512(v);
    const __m512i lsb = _mm512_and_si512(_mm512_srli_epi32(u, 16), _mm512_set1_epi32(1));
    __m512i r = _mm512_add_epi32(u, _mm512_add_epi32(_mm512_set1_epi32(0x7fff), lsb));
    const __mmask16 nan = _mm512_cmp_ps_mask(v, v, _CMP_UNORD_Q);
    r = _mm512_mask_mov_epi32(r, nan, _mm512_or_si512(u, _mm512_set1_epi32(0x400000)));
    _mm256_storeu_si256(reinterpret_cast<__m256i *>(p), _mm512_cvtepi32_epi16(_mm512_srli_epi32(r, 16)));
}

template <typename PG, typename PN>
__attribute__((target("avx512f"))) void row_avx512(uint16_t *x, const PG *g, const PN *n, int64_t cols) {
    int64_t c = 0;
    for (; c + 16 <= cols; c += 16) {
        const __m512 partial = _mm512_add_ps(load16(g + c), load16(n + c));
        store16(x + c, _mm512_add_ps(load16(x + c), partial));
    }
    row_scalar(x, g, n, c, cols);
}

bool cpu_has_avx512() {
    static const bool has = __builtin_cpu_supports("avx512f");
    return has;
}
#endif

template <typename PG, typename PN>
void run(torch::Tensor &x, const torch::Tensor &y_g, const torch::Tensor &y_n) {
    const int64_t rows = x.size(0);
    const int64_t cols = x.size(1);
    auto *xp = reinterpret_cast<uint16_t *>(x.data_ptr());
    const auto *gp = reinterpret_cast<const PG *>(y_g.data_ptr());
    const auto *np = reinterpret_cast<const PN *>(y_n.data_ptr());
    const int64_t lx = x.stride(0), lg = y_g.stride(0), ln = y_n.stride(0);

#pragma omp parallel for schedule(static) if (rows * cols >= (1 << 16))
    for (int64_t r = 0; r < rows; ++r) {
#if defined(__x86_64__)
        if (cpu_has_avx512()) {
            row_avx512(xp + r * lx, gp + r * lg, np + r * ln, cols);
            continue;
        }
#endif
        row_scalar(xp + r * lx, gp + r * lg, np + r * ln, 0, cols);
    }
}

void check_cpu_operand(const torch::Tensor &t, const torch::Tensor &x, const char *name) {
    TORCH_CHECK(t.device().is_cpu(), "residual_add2_cpu: ", name, " must be a CPU tensor");
    TORCH_CHECK(t.dim() == 2 && t.size(0) == x.size(0) && t.size(1) == x.size(1), "residual_add2_cpu: ", name, " must match x");
    TORCH_CHECK(t.scalar_type() == torch::kBFloat16 || t.scalar_type() == torch::kFloat32, "residual_add2_cpu: ", name,
                " must be bf16 or fp32");
    TORCH_CHECK(t.stride(1) == 1, "residual_add2_cpu: ", name, " needs a contiguous last dimension");
}

} // namespace

void residual_add2_cpu(torch::Tensor &x, const torch::Tensor &y_g, const torch::Tensor &y_n) {
    TORCH_CHECK(x.dim() == 2 && x.scalar_type() == torch::kBFloat16, "residual_add2_cpu: x must be bf16 [M, H]");
    check_cpu_operand(x, x, "x");
    check_cpu_operand(y_g, x, "y_g");
    check_cpu_operand(y_n, x, "y_n");

    const bool g32 = y_g.scalar_type() == torch::kFloat32;
    const bool n32 = y_n.scalar_type() == torch::kFloat32;
    if (!g32 && !n32) {
        run<uint16_t, uint16_t>(x, y_g, y_n);
    } else if (!g32 && n32) {
        run<uint16_t, float>(x, y_g, y_n);
    } else if (g32 && !n32) {
        run<float, uint16_t>(x, y_g, y_n);
    } else {
        run<float, float>(x, y_g, y_n);
    }
}

} // namespace heteromega
