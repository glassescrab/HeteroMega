"""Check the BFP16 kernel's compact-to-8x8 layout contract on CPU.

These tests use exact FP32 products to isolate address/metadata errors. They
do not emulate BFP16 conversion or establish AIE compilation or accuracy.
"""

import unittest

import numpy as np

from prefill_reference import (bf16_bits, bf16_from_bits, pack_activations,
                               pack_weights)
from reference import W4A16, bf16, pack_int4


def _gather_a(a, mb, kb):
    top = (2 * mb * 16 + kb) * 32
    bottom = top + 16 * 32
    return np.concatenate((a[top:top + 32], a[bottom:bottom + 32])).reshape(8, 8)


def _c_indices(mb, nb):
    top = (2 * mb * 4 + nb) * 32
    bottom = top + 4 * 32
    return np.concatenate((np.arange(top, top + 32),
                           np.arange(bottom, bottom + 32)))


def _add_128_bf16(values):
    # Model the C++ integer bit construction, without a numeric FP cast.
    return bf16_from_bits(np.uint16(0x4300) | values.astype(np.uint16))


def _dequantize_compact(payload):
    qbytes = payload[:2048].reshape(16, 4, 8, 4)
    q = np.empty((16, 4, 8, 8), dtype=np.uint8)
    q[..., 0::2], q[..., 1::2] = qbytes & 15, qbytes >> 4
    scales = bf16_from_bits(payload[2048:2112].copy().view('<u2')).reshape(4, 8)
    zeros = _add_128_bf16(payload[2112:]).reshape(4, 8)
    centered = _add_128_bf16(q) - zeros[None, :, None, :]
    return bf16(centered *
                scales[None, :, None, :])


def _accumulate_layout(a, b, c):
    # Model the C++ gather, four-accumulator grouping and scatter, with
    # ordinary FP32 multiplication in place of the device's BFP16 MMUL.
    for nb in (0, 2):
        addresses = [_c_indices(mb, column)
                     for mb, column in ((0, nb), (0, nb + 1),
                                        (1, nb), (1, nb + 1))]
        accumulators = [c[index].copy().reshape(8, 8) for index in addresses]
        for kb in range(16):
            a0, a1 = _gather_a(a, 0, kb), _gather_a(a, 1, kb)
            b0, b1 = b[kb, nb], b[kb, nb + 1]
            for acc, left, right in zip(accumulators, (a0, a0, a1, a1),
                                        (b0, b1, b0, b1)):
                acc += left @ right
        for index, acc in zip(addresses, accumulators):
            c[index] = acc.reshape(-1)


def _pack_fp32_c(values):
    return values.reshape(4, 4, 4, 8).transpose(0, 2, 1, 3).copy().reshape(-1)


class Bfp16KernelLayoutTests(unittest.TestCase):
    def test_zero_metadata_bits_and_all_quantized_differences_are_exact(self):
        values = np.arange(16, dtype=np.uint8)
        constructed = _add_128_bf16(values)
        old_numeric = bf16(np.float32(128) + values.astype(np.float32))
        np.testing.assert_array_equal(bf16_bits(constructed),
                                      bf16_bits(old_numeric))
        # Exercise all 256 q/z pairs, including negative differences and
        # cancellation to zero, against arithmetic independent of the trick.
        actual = constructed[:, None] - constructed[None, :]
        expected = values.astype(np.float32)[:, None] - values.astype(np.float32)[None, :]
        np.testing.assert_array_equal(actual.view(np.uint32),
                                      expected.view(np.uint32))

    def test_compact_dequantization_all_q_zero_pairs_and_varying_scales(self):
        # Every channel visits all q in [0,15] in each K128 group, while
        # both even/odd columns cover every zero. Shift scales by column so
        # all 256 q/z combinations see every scale and metadata lane order
        # matters. Include values that exercise BF16 metadata tie rounding.
        scale_values = np.array([2.0 ** -20, 1.0 / 300, 0.1, 1.0 / 3,
                                 1.00390625, 1.01171875, 257, 1023.5],
                                dtype=np.float32)
        groups = len(scale_values)
        channels = np.arange(32)
        q = ((np.arange(128 * groups)[None, :] + channels[:, None]) % 16).astype(np.uint8)
        zeros = np.repeat((channels // 2).astype(np.uint8)[:, None], groups, axis=1)
        scales = scale_values[(channels[:, None] + np.arange(groups)[None, :]) % groups]
        weight = W4A16(pack_int4(q), scales, zeros, 128)
        expected = weight.dequantize(True).T
        for group, payload in enumerate(pack_weights(weight).reshape(groups, 2144)):
            with self.subTest(group=group):
                actual = _dequantize_compact(payload).transpose(0, 2, 1, 3).reshape(128, 32)
                # Bitwise equality also checks the signed-zero and rounding
                # boundaries; a loose tolerance would hide metadata errors.
                np.testing.assert_array_equal(actual.view(np.uint32),
                    expected[group * 128:(group + 1) * 128].view(np.uint32))

    def test_a_gathers_preserve_all_rows_and_k_lanes(self):
        values = bf16(np.arange(16 * 128, dtype=np.float32).reshape(16, 128))
        packed = bf16_from_bits(pack_activations(values))
        for mb in range(2):
            for kb in range(16):
                np.testing.assert_array_equal(_gather_a(packed, mb, kb),
                                              values[mb * 8:(mb + 1) * 8,
                                                     kb * 8:(kb + 1) * 8])

    def test_c_scatter_covers_each_external_element_once(self):
        values = np.arange(16 * 32, dtype=np.float32).reshape(16, 32)
        packed = _pack_fp32_c(values)
        writes = np.zeros(512, dtype=np.int32)
        for mb in range(2):
            for nb in range(4):
                indices = _c_indices(mb, nb)
                np.testing.assert_array_equal(packed[indices].reshape(8, 8),
                                              values[mb * 8:(mb + 1) * 8,
                                                     nb * 8:(nb + 1) * 8])
                writes[indices] += 1
        np.testing.assert_array_equal(writes, np.ones(512, dtype=np.int32))

    def test_random_compact_weights_use_correct_per_column_metadata(self):
        rng = np.random.default_rng(20261022)
        q = rng.integers(0, 16, size=(32, 256), dtype=np.uint8)
        scales = np.exp2(rng.integers(-4, 2, size=(32, 2))).astype(np.float32)
        zeros = rng.integers(0, 16, size=(32, 2), dtype=np.uint8)
        weight = W4A16(pack_int4(q), scales, zeros, 128)
        tiles = pack_weights(weight).reshape(2, 2144)
        expected = weight.dequantize(True).T
        for kb, payload in enumerate(tiles):
            actual = _dequantize_compact(payload).transpose(0, 2, 1, 3).reshape(128, 32)
            np.testing.assert_array_equal(actual, expected[kb * 128:(kb + 1) * 128])

    def test_reuse_and_multiple_k_groups_retain_fp32_partials(self):
        rng = np.random.default_rng(20261023)
        k = 384
        q = rng.integers(0, 16, size=(32, k), dtype=np.uint8)
        scales = np.exp2(rng.integers(-4, 2, size=(32, k // 128))).astype(np.float32)
        zeros = rng.integers(0, 16, size=(32, k // 128), dtype=np.uint8)
        weight = W4A16(pack_int4(q), scales, zeros, 128)
        weights = pack_weights(weight).reshape(k // 128, 2144)
        for reuse in (1, 2, 4):
            with self.subTest(reuse=reuse):
                x = rng.integers(-4, 5, size=(reuse * 16, k)).astype(np.float32)
                a = bf16_from_bits(pack_activations(x)).reshape(reuse, k // 128, 2048)
                initial = rng.integers(-16, 17, size=(reuse * 16, 32)).astype(np.float32) / 16
                c = np.stack([_pack_fp32_c(initial[r * 16:(r + 1) * 16])
                              for r in range(reuse)])
                expected = initial.copy()
                dequantized = weight.dequantize(True).T
                for kb, payload in enumerate(weights):
                    b = _dequantize_compact(payload)
                    for r in range(reuse):
                        _accumulate_layout(a[r, kb], b, c[r])
                    expected += x[:, kb * 128:(kb + 1) * 128] @ dequantized[kb * 128:(kb + 1) * 128]
                    # Exact binary inputs avoid differences from CPU GEMM's
                    # reduction order, making any discrepancy a layout error.
                    for r in range(reuse):
                        np.testing.assert_array_equal(c[r],
                            _pack_fp32_c(expected[r * 16:(r + 1) * 16]))


if __name__ == '__main__':
    unittest.main()
