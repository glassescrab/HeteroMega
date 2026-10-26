"""Host checks for native BF16 metadata and MMUL-loop ablations.

The MMUL test compiles the actual C++ address/loop bodies against a scalar
host model. It checks mapping and K order, not AIE instruction semantics or
performance. Actual native-BF16 equivalence still requires device checks.
"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import numpy as np

from prefill_reference import bf16_bits, bf16_from_bits
from reference import bf16


SOURCE = Path(__file__).with_name('w4a16_prefill_upstream.cc')


def _function(source, name):
    start = source.index(f'static inline void {name}(')
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class UpstreamKernelOptimizationTests(unittest.TestCase):
    def test_native_and_ablation_macro_guards(self):
        compiler = shutil.which('c++') or shutil.which('clang++')
        if compiler is None:
            self.skipTest('host C++ compiler is unavailable')
        prefix = SOURCE.read_text().split('#include <aie_api/aie.hpp>', 1)[0]
        for vector_zero in (0, 1, 2):
            for mmul_reuse in (0, 1, 2, 3):
                result = subprocess.run([compiler, '-E', '-dM', '-x', 'c++', '-',
                    f'-DHETEROMEGA_VECTOR_ZERO={vector_zero}',
                    f'-DHETEROMEGA_MMUL_M_REUSE={mmul_reuse}'], input=prefix,
                    text=True, capture_output=True, check=False)
                with self.subTest(vector_zero=vector_zero, mmul_reuse=mmul_reuse):
                    self.assertEqual(result.returncode == 0,
                                     vector_zero in (0, 1) and mmul_reuse in (1, 2))
                    if result.returncode == 0:
                        self.assertIn('#define AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16 0',
                                      result.stdout)

    def test_vector_metadata_preserves_all_zero_values_and_both_halves(self):
        # Every N8 block varies by lane, block and seed. The independent
        # logical oracle uses z directly; the candidate reads the original
        # duplicated byte payload and repeats its full16-lane vector.
        q = np.arange(16, dtype=np.uint16)[:, None, None]
        scales = bf16(np.array([0.0, 1 / 1024, 3 / 128, 0.75, 1.0, 3.5, -0.5, -2.0],
                               dtype=np.float32))
        for seed in range(16):
            zero = ((np.arange(64).reshape(8, 8) * 3 + np.arange(8)[:, None] + seed) % 16
                    ).astype(np.uint8)
            payload = np.repeat(zero[:, None, :], 2, axis=1).reshape(-1)
            for half in range(2):
                for nb in range(4):
                    logical = zero[half * 4 + nb]
                    offset = (half * 4 + nb) * 16
                    loaded = payload[offset:offset + 16].astype(np.uint16)
                    vector_bias = bf16_from_bits(np.tile(loaded | np.uint16(0x4300), 4)).reshape(8, 8)
                    expected_bias = np.broadcast_to(logical.astype(np.float32) + 128, (8, 8))
                    np.testing.assert_array_equal(vector_bias, expected_bias)
                    shifted_q = bf16_from_bits(q | np.uint16(0x4300))
                    actual = bf16((shifted_q - vector_bias) * scales)
                    expected = np.broadcast_to(bf16((q.astype(np.float32) - logical) * scales),
                                               actual.shape)
                    np.testing.assert_array_equal(bf16_bits(actual), bf16_bits(expected))

    def test_actual_mmul_address_bodies_pair_lanes_without_changing_reduction(self):
        compiler = shutil.which('c++') or shutil.which('clang++')
        if compiler is None:
            self.skipTest('host C++ compiler is unavailable')
        source = SOURCE.read_text()
        base = _function(source, 'accumulate_dequantized')
        pair = _function(source, 'accumulate_dequantized_pair')
        dispatch = 'template <unsigned Half>\n' + _function(source, 'accumulate_half')
        prefix = r'''
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>
using bfloat16 = float; // Address/ordering model only; not an AIE/BF16 simulator.
#define AIE_PREPARE_FOR_PIPELINING
void event0() {}
void event1() {}
namespace aie {
template <typename T, unsigned N> using vector = std::array<T, N>;
template <unsigned N, typename T> vector<T, N> load_v(const T *p) {
  vector<T, N> result;
  for (unsigned i = 0; i < N; ++i) result[i] = p[i];
  return result;
}
template <typename T, std::size_t N> void store_v(T *p, const std::array<T, N> &v) {
  for (unsigned i = 0; i < N; ++i) p[i] = v[i];
}
enum class rounding_mode { conv_even };
int swap_rounding(rounding_mode) { return 0; }
void set_rounding(int) {}
}
struct MMUL {
  static constexpr unsigned size_A = 32, size_B = 64, size_C = 32;
  aie::vector<float, size_C> values;
  explicit MMUL(aie::vector<float, size_C> initial) : values(initial) {}
  void mac(aie::vector<float, size_A> a, aie::vector<float, size_B> b) {
    for (unsigned row = 0; row < 4; ++row)
      for (unsigned col = 0; col < 8; ++col)
        for (unsigned k = 0; k < 8; ++k)
          values[row * 8 + col] += a[row * 8 + k] * b[k * 8 + col];
  }
  template <typename T> aie::vector<T, size_C> to_vector() const { return values; }
};
template <unsigned Half> void dequantize(const uint8_t *, bfloat16 *) {}
'''
        pieces = [prefix]
        for reuse in (1, 2, 4):
            for mode in (1, 2):
                pieces.append(f'''
namespace r{reuse}_mode{mode} {{
constexpr int REUSE={reuse}, M=16, K=128, N=32, MB=4, KB=16, NB=4;
{base}
{pair}
#undef HETEROMEGA_MMUL_M_REUSE
#define HETEROMEGA_MMUL_M_REUSE {mode}
{dispatch}
}}
''')
        pieces.append(r'''
int main() {
  constexpr float guard = -1234567.0f;
  std::vector<float> a(4 * 2048), b(4096), initial(4 * 512 + 32, guard);
  for (unsigned i = 0; i < a.size(); ++i) a[i] = float(int((i * 17 + i / 2048 * 7) % 43) - 21) / 16;
  for (unsigned i = 0; i < b.size(); ++i) b[i] = float(int((i * 11 + i / 64) % 37) - 18) / 32;
  for (unsigned i = 0; i < 4 * 512; ++i) initial[i] = float(int(i % 19) - 9) / 8;
''')
        for reuse in (1, 2, 4):
            pieces.append(f'''
  {{
    std::vector<float> c(initial.begin(), initial.begin() + {reuse} * 512);
    c.resize({reuse} * 512 + 32, guard);
    auto d = c;
    for (unsigned kg = 0; kg < 3; ++kg) {{
      r{reuse}_mode1::accumulate_half<0>(a.data(), nullptr, c.data(), b.data());
      r{reuse}_mode2::accumulate_half<0>(a.data(), nullptr, d.data(), b.data());
      if (std::memcmp(c.data(), d.data(), c.size() * sizeof(float))) return 10 + {reuse};
      for (unsigned i = {reuse} * 512; i < c.size(); ++i)
        if (c[i] != guard || d[i] != guard) return 20 + {reuse};
    }}
  }}
''')
        pieces.append('return 0;\n}\n')
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'check.cpp'
            executable = Path(temporary) / 'check'
            path.write_text(''.join(pieces))
            built = subprocess.run([compiler, '-std=c++17', '-O1', '-ffp-contract=off',
                str(path), '-o', str(executable)], text=True, capture_output=True, check=False)
            self.assertEqual(built.returncode, 0, built.stderr)
            checked = subprocess.run([str(executable)], text=True, capture_output=True, check=False)
            self.assertEqual(checked.returncode, 0, checked.stderr)


if __name__ == '__main__':
    unittest.main()
