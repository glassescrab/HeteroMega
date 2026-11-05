"""Prefill layout/algebra tests: python -m unittest discover -s npu/ffn -v."""

import unittest

import numpy as np

from reference import W4A16, bf16, pack_int4
from prefill_reference import (WEIGHT_TILE_BYTES, bf16_bits, error_metrics, pack_activations,
                               pack_output, pack_weights, projection_reference, tiled_reference,
                               unpack_activations, unpack_output, unpack_weights, validate_shape)
from run_w4a16_prefill import onehot_lane_cases


class PrefillTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(12832)

    def weight(self, n, k):
        q = self.rng.integers(0, 16, (n, k), dtype=np.uint8)
        scales = self.rng.uniform(0.002, 0.06, (n, k // 128)).astype(np.float32)
        zeros = self.rng.integers(0, 16, scales.shape, dtype=np.uint8)
        return W4A16(pack_int4(q), scales, zeros, 128)

    def test_native_activation_and_output_microtile_addresses(self):
        x = self.rng.normal(size=(32, 256)).astype(np.float32)
        packed = pack_activations(x).reshape(2, 2, 4, 16, 4, 8)
        for m, k in ((0, 0), (3, 7), (4, 8), (15, 127), (21, 169), (31, 255)):
            self.assertEqual(packed[m // 16, k // 128, m % 16 // 4, k % 128 // 8, m % 4, k % 8], bf16_bits(x)[m, k])
        np.testing.assert_array_equal(unpack_activations(packed.reshape(-1), 32, 256), bf16(x))
        y = self.rng.normal(size=(32, 96)).astype(np.float32)
        out = pack_output(y).reshape(2, 3, 4, 4, 4, 8)
        for m, n in ((0, 0), (3, 7), (4, 8), (15, 31), (21, 69), (31, 95)):
            self.assertEqual(out[m // 16, n // 32, m % 16 // 4, n % 32 // 8, m % 4, n % 8], bf16_bits(y)[m, n])
        np.testing.assert_array_equal(unpack_output(out.reshape(-1), 32, 96), bf16(y))

    def test_weight_nibble_order_group_metadata_and_no_replication(self):
        n, k = 96, 256
        q = np.fromfunction(lambda ni, ki: (ni + 3 * ki) % 16, (n, k), dtype=int).astype(np.uint8)
        scales = (1 + np.arange(n * 2).reshape(n, 2)).astype(np.float32) / 256
        zeros = np.arange(n * 2, dtype=np.uint8).reshape(n, 2) % 16
        w = W4A16(pack_int4(q), scales, zeros, 128)
        packed = pack_weights(w).reshape(3, 2, WEIGHT_TILE_BYTES)
        self.assertEqual(packed.nbytes, n * k // 2 + 3 * n * (k // 128))
        for ni, ki in ((0, 0), (7, 3), (8, 8), (31, 127), (66, 177), (95, 255)):
            offset = (((ki % 128 // 8) * 4 + ni % 32 // 8) * 8 + ki % 8) * 4 + ni % 8 // 2
            byte = int(packed[ni // 32, ki // 128, offset])
            self.assertEqual((byte >> (4 * (ni % 2))) & 15, q[ni, ki])
            self.assertEqual(packed[ni // 32, ki // 128, 2112 + ni % 32], zeros[ni, ki // 128])
            scale_bits = packed[ni // 32, ki // 128, 2048:2112].copy().view("<u2")
            self.assertEqual(scale_bits[ni % 32], bf16_bits(scales)[ni, ki // 128])
        decoded = unpack_weights(packed.reshape(-1), k, n)
        np.testing.assert_array_equal(decoded.packed, w.packed)
        np.testing.assert_array_equal(decoded.scales, bf16(w.scales))
        np.testing.assert_array_equal(decoded.zeros, w.zeros)

    def test_multi_token_k_accumulation_and_nonzero_channel_shard(self):
        x = self.rng.normal(0, 0.25, (32, 384)).astype(np.float32)
        full = self.weight(128, 384)
        shard = full.output_slice(32, 96)
        actual = unpack_output(tiled_reference(pack_activations(x), pack_weights(shard), 32, 384, 64), 32, 64)
        expected = projection_reference(x, full)[:, 32:96]
        np.testing.assert_allclose(actual, expected, rtol=0.01, atol=0.002)
        self.assertEqual(error_metrics(actual, expected)["correctness"], "passed")

    def test_nonzero_down_input_shard(self):
        x = self.rng.normal(0, 0.25, (16, 512)).astype(np.float32)
        full = self.weight(64, 512)
        shard = full.input_slice(128, 384)
        actual = unpack_output(tiled_reference(pack_activations(x[:, 128:384]), pack_weights(shard), 16, 256, 64), 16, 64)
        np.testing.assert_allclose(actual, projection_reference(x[:, 128:384], shard), rtol=0.01, atol=0.002)

    def test_zero_and_changed_inputs_do_not_reuse_results(self):
        weight = self.weight(64, 256)
        weights = pack_weights(weight)
        previous = None
        for scale in (1.0, 0.0, -0.5, 0.25):
            x = (scale * self.rng.normal(size=(32, 256))).astype(np.float32)
            actual = unpack_output(tiled_reference(pack_activations(x), weights, 32, 256, 64), 32, 64)
            np.testing.assert_allclose(actual, projection_reference(x, weight), rtol=0.01, atol=0.01)
            if scale == 0:
                np.testing.assert_array_equal(actual, np.zeros_like(actual))
            if previous is not None:
                self.assertFalse(np.array_equal(actual, previous))
            previous = actual.copy()

    def test_error_metrics_reject_corruption_and_nonfinite(self):
        ref = np.ones((16, 32), np.float32)
        self.assertEqual(error_metrics(ref + 2, ref)["correctness"], "failed")
        self.assertEqual(error_metrics(ref * np.nan, ref)["correctness"], "failed")
        self.assertEqual(error_metrics(ref * 0.0001, ref * 0)["correctness"], "failed")
        self.assertEqual(error_metrics(ref * 0, ref * 0)["correctness"], "passed")

    def test_onehot_metadata_and_quantized_lanes_match_analytic_exactly(self):
        # M=144 selects one-hot K positions across the 128-element group
        # boundary; both cases have exactly representable BF16 outputs.
        m, k, n = 144, 256, 64
        for name, x, weight, metadata in onehot_lane_cases(m, k, n):
            with self.subTest(case=name):
                self.assertEqual(metadata["comparison"], "exact")
                channels = np.arange(n)
                if name == "onehot_metadata_lanes":
                    expected = np.broadcast_to((9 - channels % 16) * np.exp2(-(channels % 4)), (m, n)).astype(np.float32)
                else:
                    expected = ((np.arange(m)[:, None] % k + 3 * channels[None, :]) % 16).astype(np.float32)
                np.testing.assert_array_equal(projection_reference(x, weight), expected)
                actual = unpack_output(tiled_reference(pack_activations(x), pack_weights(weight), m, k, n), m, n)
                np.testing.assert_array_equal(actual, expected)
                self.assertEqual(error_metrics(actual, expected, 0, 0, 0)["correctness"], "passed")
                corrupted = actual.copy()
                corrupted[:, 8:16] = corrupted[:, :8]
                self.assertEqual(error_metrics(corrupted, expected, 0, 0, 0)["correctness"], "failed")

    def test_reject_decode_and_unaligned_shapes(self):
        for args in ((1, 128, 32), (16, 64, 32), (16, 128, 8), (0, 128, 32), (16.0, 128, 32)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                validate_shape(*args)


if __name__ == "__main__":
    unittest.main()
