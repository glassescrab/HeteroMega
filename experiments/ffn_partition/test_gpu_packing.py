"""CPU regressions for original GPU addresses, nibble order, and metadata.

The decoder below follows addresses read by w4a16_gemm_rocwmma_packed, not
the adapter's reshape/transpose operations. This catches independently wrong
tile order, K/N orientation, quantization lanes, and slice metadata.
"""

from types import SimpleNamespace
import unittest

import numpy as np

from contract import W4A16, bf16
from gpu_backend import GPUBranch, PACKED_TILE_BYTES, pack_heteromosaic_weights
from reference import pack_int4, unpack_int4


def decode_gpu_addresses(packed, k, n):
    """Decode by the original kernel's scalar global/LDS address formulas."""
    output = np.arange(n, dtype=np.int64)
    reduction = np.arange(k, dtype=np.int64)
    nt, kt = n // 64, k // 128
    n_tile, n_local = output // 64, output % 64
    group_lengths = ((nt + 7 - np.arange(8)) // 8) * kt
    group_bases = np.r_[0, np.cumsum(group_lengths)[:-1]]
    base_z = group_bases[n_tile % 8] + (n_tile // 8) * kt
    k_tile, k_in = reduction // 128, reduction % 128
    k_sub = k_in % 32
    block_index = (k_sub[None, :] // 8) * 8 + n_local[:, None] // 8
    addresses = ((base_z[:, None] + k_tile[None, :]) * PACKED_TILE_BYTES
                 + (k_in[None, :] // 32) * 1024 + block_index * 32
                 + (k_sub[None, :] % 8) * 4 + (n_local[:, None] % 8) // 2)
    q = ((packed[addresses] >> (4 * (n_local[:, None] % 2))) & 15).astype(np.uint8)

    bases = (base_z[:, None] + np.arange(kt)[None, :]) * PACKED_TILE_BYTES
    scale_addresses = bases + 4096 + n_local[:, None] * 2
    scale_bits = (packed[scale_addresses].astype(np.uint16)
                  | (packed[scale_addresses + 1].astype(np.uint16) << 8))
    scales = (scale_bits.astype(np.uint32) << 16).view(np.float32)
    zero_addresses = bases + 4224 + (n_local[:, None] // 8) * 16 + n_local[:, None] % 8
    zeros = packed[zero_addresses]
    duplicated_zeros = packed[zero_addresses + 8]
    return q, scales, zeros, duplicated_zeros, scale_bits


def varied_weight(n, k, seed):
    rng = np.random.default_rng(seed)
    q = rng.integers(0, 16, (n, k), dtype=np.uint8)
    scales = rng.uniform(.003, .25, (n, k // 128)).astype(np.float32)
    zeros = rng.integers(0, 16, scales.shape, dtype=np.uint8)
    return W4A16(pack_int4(q), scales, zeros, 128)


class GPUPackingTests(unittest.TestCase):
    def assert_round_trip(self, weight):
        n, k = weight.shape
        packed = pack_heteromosaic_weights(weight)
        self.assertEqual(packed.dtype, np.dtype(np.uint8))
        self.assertEqual(packed.shape, (n // 64 * (k // 128) * PACKED_TILE_BYTES,))
        self.assertTrue(packed.flags.c_contiguous)
        actual_q, actual_scales, actual_zeros, duplicate, _ = decode_gpu_addresses(packed, k, n)
        np.testing.assert_array_equal(actual_q, unpack_int4(weight.packed))
        np.testing.assert_array_equal(actual_scales, bf16(weight.scales))
        np.testing.assert_array_equal(actual_zeros, weight.zeros)
        np.testing.assert_array_equal(duplicate, weight.zeros)
        dequantized = bf16((actual_q.astype(np.float32) - np.repeat(actual_zeros, 128, axis=1))
                          * np.repeat(actual_scales, 128, axis=1))
        np.testing.assert_array_equal(dequantized, weight.dequantize(True))

    def test_original_gpu_addresses_across_zigzag_groups(self):
        # Ten/eighteen N tiles force uneven modulo-eight groups and a second
        # column in several groups, where a plain N-major pack would fail.
        for n, k in ((128, 128), (640, 384), (1152, 256)):
            with self.subTest(n=n, k=k):
                self.assert_round_trip(varied_weight(n, k, n + k))

    def test_nonzero_n_and_k_slices_retain_matching_metadata(self):
        original = varied_weight(768, 512, 52)
        self.assert_round_trip(original.output_slice(128, 640))
        down_shard = original.input_slice(128, 384)
        self.assertFalse(down_shard.packed.flags.c_contiguous)
        self.assert_round_trip(down_shard)

    def test_scale_ties_round_to_even_in_both_directions(self):
        # Independent expected BF16 bit patterns around two halfway points.
        input_bits = np.array([0x3F808000, 0x3F818000, 0x3F807FFF, 0x3F808001], dtype=np.uint32)
        expected_bits = np.array([0x3F80, 0x3F82, 0x3F80, 0x3F81], dtype=np.uint16)
        scales = np.tile(input_bits.view(np.float32), 64).reshape(128, 2)
        weight = W4A16(np.full((128, 128), 0x87, dtype=np.uint8), scales,
                       np.full((128, 2), 8, dtype=np.uint8), 128)
        packed = pack_heteromosaic_weights(weight)
        *_, actual_bits = decode_gpu_addresses(packed, 256, 128)
        np.testing.assert_array_equal(actual_bits, np.tile(expected_bits, 64).reshape(128, 2))

    def test_all_unsigned_zero_points_and_negative_weights(self):
        n, k = 128, 256
        zeros = ((np.arange(n)[:, None] + np.arange(k // 128)[None, :]) % 16).astype(np.uint8)
        q = np.repeat(zeros, 128, axis=1)
        scales = np.full(zeros.shape, .125, dtype=np.float32)
        weight = W4A16(pack_int4(q), scales, zeros, 128)
        self.assert_round_trip(weight)
        np.testing.assert_array_equal(weight.dequantize(True), np.zeros((n, k), np.float32))
        # Distinguish unsigned zero=15 from a sign-extended int4 value=-1.
        negative = W4A16(np.zeros((n, k // 2), np.uint8), scales,
                         np.full_like(zeros, 15), 128)
        self.assert_round_trip(negative)
        np.testing.assert_array_equal(negative.dequantize(True), np.full((n, k), -1.875, np.float32))

    def test_rejects_invalid_kernel_shapes_and_metadata_before_torch(self):
        weight = varied_weight(128, 128, 3)
        for bad_m in (0, 1, 16, 127, 129, True, 128.0):
            with self.subTest(m=bad_m), self.assertRaises(ValueError):
                GPUBranch(weight, weight, weight, bad_m)
        for bad in (
            SimpleNamespace(shape=(64, 128), group_size=128),
            SimpleNamespace(shape=(128, 64), group_size=128),
            SimpleNamespace(shape=(128, 128), group_size=64),
        ):
            with self.assertRaises(ValueError):
                pack_heteromosaic_weights(bad)
        attributes = dict(shape=weight.shape, group_size=128, packed=weight.packed,
                          scales=weight.scales, zeros=weight.zeros)
        for change in ({"scales": np.full_like(weight.scales, np.nan)},
                       {"zeros": np.full_like(weight.zeros, 16)},
                       {"zeros": weight.zeros.astype(np.float32)},
                       {"scales": weight.scales.T},
                       {"packed": weight.packed.astype(np.int8)}):
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                pack_heteromosaic_weights(SimpleNamespace(**(attributes | change)))


if __name__ == "__main__":
    unittest.main()
