"""CPU checks for shared weights, BF16 stage boundaries, and native reordering."""

import unittest

import numpy as np

from contract import (FFNWeights, W4A16, benchmark_stats, bf16, error_metrics,
                      packed_output_to_activation, random_weights, reference_full,
                      reference_partitioned, split_weights, validate_shape)
from prefill_reference import pack_activations, pack_output
from reference import pack_int4, unpack_int4


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weights = random_weights(128, 384, seed=77)
        cls.x = np.random.default_rng(78).normal(0, 0.25, (128, 128)).astype(np.float32)

    def test_shape_and_projection_validation(self):
        validate_shape(128, 128, 384, 0)
        validate_shape(512, 4096, 14336, 2048)
        validate_shape(128, 128, 384, 384)
        for shape in ((1, 128, 384, 128), (128, 64, 384, 128),
                      (128, 128, 384, 64), (128, 128, 384, 512),
                      (True, 128, 384, 128), (128, 128, 384, 128.0)):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                validate_shape(*shape)
        with self.assertRaises(ValueError):
            FFNWeights(self.weights.gate, self.weights.up, self.weights.gate)
        with self.assertRaises(ValueError):
            reference_full(np.full_like(self.x, np.nan), self.weights)

    def test_deterministic_canonical_weights(self):
        other = random_weights(128, 384, seed=77)
        different = random_weights(128, 384, seed=78)
        for name in ("gate", "up", "down"):
            first, second = getattr(self.weights, name), getattr(other, name)
            np.testing.assert_array_equal(first.packed, second.packed)
            np.testing.assert_array_equal(first.scales, second.scales)
            np.testing.assert_array_equal(first.zeros, second.zeros)
            np.testing.assert_array_equal(first.scales, bf16(first.scales))
            self.assertFalse(np.array_equal(first.packed, getattr(different, name).packed))
            self.assertGreater(np.unique(first.zeros).size, 1)
            self.assertTrue(np.all(np.isfinite(first.dequantize(True))))

    def test_asymmetric_slices_preserve_weights_and_metadata(self):
        branches = split_weights(self.weights, 128)
        self.assertEqual(branches["npu"].intermediate, 128)
        self.assertEqual(branches["gpu"].intermediate, 256)
        for name in ("gate", "up"):
            np.testing.assert_array_equal(
                np.concatenate([getattr(branches[d], name).packed for d in ("npu", "gpu")]),
                getattr(self.weights, name).packed)
        for field in ("packed", "scales", "zeros"):
            np.testing.assert_array_equal(
                np.concatenate([getattr(branches[d].down, field) for d in ("npu", "gpu")], axis=1),
                getattr(self.weights.down, field))
            self.assertTrue(np.shares_memory(getattr(branches["gpu"].down, field),
                                             getattr(self.weights.down, field)))

    def test_asymmetric_ffn_rounds_partials_before_reduction(self):
        output, partials = reference_partitioned(self.x, self.weights, 128)
        branches = split_weights(self.weights, 128)
        for name in ("npu", "gpu"):
            np.testing.assert_array_equal(partials[name], reference_full(self.x, branches[name]))
            np.testing.assert_array_equal(partials[name], bf16(partials[name]))
        np.testing.assert_array_equal(output, bf16(partials["npu"] + partials["gpu"]))
        self.assertTrue(error_metrics(output, reference_full(self.x, self.weights))["passed"])

    def test_single_device_endpoints_match_full_ffn(self):
        expected = reference_full(self.x, self.weights)
        for npu_channels, empty in ((0, "npu"), (384, "gpu")):
            output, partials = reference_partitioned(self.x, self.weights, npu_channels)
            np.testing.assert_array_equal(output, expected)
            np.testing.assert_array_equal(partials[empty], np.zeros_like(self.x))
            self.assertIsNone(split_weights(self.weights, npu_channels)[empty])

    def test_zeros_and_alternating_inputs(self):
        first, _ = reference_partitioned(self.x, self.weights, 128)
        changed, _ = reference_partitioned(-self.x, self.weights, 128)
        zero, _ = reference_partitioned(np.zeros_like(self.x), self.weights, 128)
        repeated, _ = reference_partitioned(self.x, self.weights, 128)
        self.assertFalse(np.array_equal(first, changed))
        np.testing.assert_array_equal(repeated, first)
        np.testing.assert_array_equal(zero, np.zeros_like(zero))
        w = self.weights.gate
        zero_gate = W4A16(pack_int4(np.repeat(w.zeros, 128, axis=1)), w.scales.copy(), w.zeros.copy(), 128)
        zero_weights = FFNWeights(zero_gate, self.weights.up, self.weights.down)
        np.testing.assert_array_equal(reference_full(self.x, zero_weights), np.zeros_like(self.x))

    def test_packed_conversion_matches_independent_logical_pack(self):
        # Vary both row and channel axes across several M16 and N32 tiles.
        logical = np.arange(128 * 384, dtype=np.float32).reshape(128, 384) / 128
        packed = pack_output(logical)
        actual = packed_output_to_activation(packed, 128, 384)
        np.testing.assert_array_equal(actual, pack_activations(logical))
        self.assertFalse(np.array_equal(packed, actual))
        self.assertFalse(np.shares_memory(actual, packed))

    def test_packed_conversion_preserves_every_bit_pattern(self):
        # Includes signed zero, infinities and NaN payloads; float conversion
        # would destroy some of these bit patterns.
        logical_bits = np.arange(128 * 512, dtype=np.uint16).reshape(128, 512)
        c = np.empty(128 * 512, dtype=np.uint16)
        expected = np.empty_like(c)
        for m in range(128):
            for n in range(512):
                c_index = (((((m // 16) * 16 + n // 32) * 4 + (m % 16) // 4) * 4
                             + (n % 32) // 8) * 4 + m % 4) * 8 + n % 8
                a_index = (((((m // 16) * 4 + n // 128) * 4 + (m % 16) // 4) * 16
                             + (n % 128) // 8) * 4 + m % 4) * 8 + n % 8
                c[c_index] = logical_bits[m, n]
                expected[a_index] = logical_bits[m, n]
        np.testing.assert_array_equal(packed_output_to_activation(c, 128, 512), expected)
        with self.assertRaises(ValueError):
            packed_output_to_activation(c.view(np.int16), 128, 512)

    def test_lane_corruption_is_detected(self):
        w = self.weights.gate
        q = unpack_int4(w.packed)
        # Corrupt a nonzero channel slice and vary metadata lanes independently.
        q[128:256] = 15 - q[128:256]
        zeros = w.zeros.copy()
        zeros[128:256] = 15 - zeros[128:256]
        scales = w.scales.copy()
        scales[128:256] *= 2
        corrupted = FFNWeights(W4A16(pack_int4(q), scales, zeros, 128),
                               self.weights.up, self.weights.down)
        expected = reference_full(self.x, self.weights)
        self.assertFalse(error_metrics(reference_full(self.x, corrupted), expected)["passed"])

    def test_error_checks_and_measured_statistics(self):
        expected = np.ones((128, 128), np.float32)
        self.assertTrue(error_metrics(expected, expected)["passed"])
        self.assertFalse(error_metrics(expected * 1.1, expected)["passed"])
        corrupted = expected.copy()
        corrupted[0, 17] = 2
        self.assertFalse(error_metrics(corrupted, expected)["passed"])
        corrupted[0, 17] = np.nan
        self.assertFalse(error_metrics(corrupted, expected)["finite"])
        self.assertFalse(error_metrics(np.full_like(expected, 1e-9), np.zeros_like(expected))["passed"])
        with self.assertRaises(ValueError):
            error_metrics(expected, expected, l2_limit=np.inf)
        stats = benchmark_stats([10, 20, 30, 40, 50])
        self.assertEqual(stats, {"count": 5, "median_us": 30.0, "p10_us": 14.0,
                                 "p90_us": 46.0, "min_us": 10.0, "max_us": 50.0})
        for invalid in ([], [0], [-1], [np.nan], [np.inf], [[1, 2]]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                benchmark_stats(invalid)


if __name__ == "__main__":
    unittest.main()
