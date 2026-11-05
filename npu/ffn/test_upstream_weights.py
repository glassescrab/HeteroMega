"""Independent upstream packer checks for direct-buffer native BF16 input.

The producer below follows glassescrab's test.cpp, rather than HeteroMega's
compact packer. These CPU checks establish addressing/dequantization only;
they do not emulate or claim execution of an AIE kernel.
"""

import hashlib
import unittest

import numpy as np

from prefill_reference import bf16_bits, bf16_from_bits
from reference import bf16
from upstream_weights import (UpstreamWeightBuffer, WEIGHT_TILE_BYTES,
                              upstream_weight_bytes, weight_tile_offset)


def _upstream_producer(q, scales, zeros):
    """Test-only implementation of upstream's N64/K128 packing loops."""
    k, n = q.shape
    payloads = []
    for col_mod in range(8):
        for nt in range(col_mod, n // 64, 8):
            for kg in range(k // 128):
                payload = np.empty(4352, dtype=np.uint8)
                for kr in range(16):
                    for nr in range(8):
                        block = q[kg * 128 + kr * 8:kg * 128 + kr * 8 + 8,
                                  nt * 64 + nr * 8:nt * 64 + nr * 8 + 8]
                        offset = (kr * 8 + nr) * 32
                        payload[offset:offset + 32] = (
                            block[:, 0::2] | (block[:, 1::2] << 4)).reshape(-1)
                ns = slice(nt * 64, (nt + 1) * 64)
                payload[4096:4224] = bf16_bits(scales[kg, ns]).view(np.uint8)
                for group in range(8):
                    for repeat in range(2):
                        offset = 4224 + group * 16 + repeat * 8
                        payload[offset:offset + 8] = zeros[
                            kg, nt * 64 + group * 8:nt * 64 + group * 8 + 8]
                payloads.append(payload)
    return np.concatenate(payloads)


def _kernel_half(payload, half):
    """Address model of native kernel's selected N32 dequantization."""
    result = np.empty((128, 32), np.float32)
    for nb in range(4):
        ni = half * 32 + nb * 8
        scales = bf16_from_bits(payload[4096 + ni * 2:4096 + ni * 2 + 16]
                                .view('<u2'))
        zero_offset = 4224 + (half * 4 + nb) * 16
        zeros = payload[zero_offset:zero_offset + 8]
        bias = bf16_from_bits(np.uint16(0x4300) | zeros.astype(np.uint16))
        for kb in range(16):
            offset = (kb * 8 + half * 4 + nb) * 32
            packed = payload[offset:offset + 32].reshape(8, 4)
            q = np.empty((8, 8), np.uint8)
            q[:, 0::2], q[:, 1::2] = packed & 15, packed >> 4
            shifted = bf16_from_bits(np.uint16(0x4300) | q.astype(np.uint16))
            result[kb * 8:kb * 8 + 8, nb * 8:nb * 8 + 8] = bf16(
                (shifted - bias) * scales)
    return result


class UpstreamWeightTests(unittest.TestCase):
    def test_offsets_cover_original_striped_order_including_ragged_stripes(self):
        for tiles in (1, 7, 8, 9, 17, 40, 224):
            with self.subTest(n64_tiles=tiles):
                observed = []
                for stripe in range(8):
                    for nt in range(stripe, tiles, 8):
                        for kg in range(3):
                            observed.append(weight_tile_offset(384, tiles * 64, kg, nt))
                self.assertEqual(observed, list(range(0, tiles * 3 * 4352, 4352)))
                self.assertEqual(upstream_weight_bytes(384, tiles * 64), len(observed) * 4352)

    def test_both_halves_preserve_weights_and_varying_metadata(self):
        k, n = 384, 1088  # 17 N64 tiles: unequal lengths across eight stripes.
        ki, ni = np.arange(k)[:, None], np.arange(n)[None, :]
        q = ((7 * ki + 3 * ni + ki // 128 + ni // 64) % 16).astype(np.uint8)
        kg, nc = np.arange(k // 128)[:, None], np.arange(n)[None, :]
        scales = bf16(((nc % 13 + 1) * (kg + 1) / 256).astype(np.float32))
        zeros = ((nc + 5 * kg + nc // 8) % 16).astype(np.uint8)
        data = _upstream_producer(q, scales, zeros)
        digest = hashlib.sha256(data).hexdigest()
        weights = UpstreamWeightBuffer(data, k, n)
        self.assertIs(weights.data, data)
        for nt in range(n // 64):
            for group in range(k // 128):
                offset = weights.tile_offset(group, nt)
                payload = weights.data[offset:offset + WEIGHT_TILE_BYTES]
                self.assertTrue(np.shares_memory(payload, data))
                for half in range(2):
                    ns = slice(nt * 64 + half * 32, nt * 64 + (half + 1) * 32)
                    ks = slice(group * 128, (group + 1) * 128)
                    expected = bf16((q[ks, ns].astype(np.float32) - zeros[group, ns])
                                    * scales[group, ns])
                    np.testing.assert_array_equal(_kernel_half(payload, half), expected)
                for nb in range(8):
                    z = payload[4224 + nb * 16:4224 + (nb + 1) * 16]
                    np.testing.assert_array_equal(z[:8], z[8:])
        self.assertEqual(hashlib.sha256(data).hexdigest(), digest)

    def test_partition_selection_retains_full_source_offsets(self):
        k, n = 512, 1088
        data = np.arange(upstream_weight_bytes(k, n), dtype=np.uint8)
        data.flags.writeable = False
        weights = UpstreamWeightBuffer(data, k, n)
        before = hashlib.sha256(data).hexdigest()
        weights.validate_slice(128, 96, 256, 736)
        # Half of N64 tile1 at K group1 must reference its FULL source ordinal.
        tile = weights.tile_offset(1, 1)
        expected_tiles_before_stripe1 = 3  # N64 indices0,8,16.
        self.assertEqual(tile, (expected_tiles_before_stripe1 * 4 + 1) * 4352)
        self.assertIs(weights.data, data)
        self.assertEqual(weights.nbytes, data.nbytes)
        self.assertFalse(weights.data.flags.writeable)
        self.assertEqual(hashlib.sha256(data).hexdigest(), before)

    def test_rejects_storage_conversion_and_wrong_sizes(self):
        size = upstream_weight_bytes(128, 64)
        invalid = ([0] * size, np.zeros(size, np.uint16),
                   np.zeros((1, size), np.uint8), np.zeros(size - 1, np.uint8),
                   np.zeros(size * 2, np.uint8)[::2])
        for data in invalid:
            with self.assertRaises(ValueError):
                UpstreamWeightBuffer(data, 128, 64)

    def test_shape_offsets_and_slice_bounds(self):
        for shape in ((0, 64), (128, 0), (129, 64), (128, 32),
                      (True, 64), (128, 64.0), (-128, 64)):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                upstream_weight_bytes(*shape)
        for kg, nt in ((-1, 0), (0, -1), (2, 0), (0, 16), (True, 0), (0, 1.0)):
            with self.subTest(tile=(kg, nt)), self.assertRaises(ValueError):
                weight_tile_offset(256, 1024, kg, nt)
        weights = UpstreamWeightBuffer(np.zeros(upstream_weight_bytes(256, 1024), np.uint8),
                                       256, 1024)
        for args in ((1, 0, 128, 64), (0, 1, 128, 64), (0, 0, 64, 64),
                     (0, 0, 128, 16), (128, 0, 256, 64), (0, 992, 128, 64),
                     (0, 0, 0, 64), (-128, 0, 128, 64), (False, 0, 128, 64)):
            with self.subTest(slice=args), self.assertRaises(ValueError):
                weights.validate_slice(*args)
        weights.validate_slice(128, 992, 128, 32)


if __name__ == '__main__':
    unittest.main()
