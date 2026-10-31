"""CPU-only contract tests: python -m unittest discover -s npu/ffn -v."""

import unittest

import numpy as np

from reference import FFNPartition, W4A16, bf16, ffn_partitioned, ffn_reference, pack_int4, silu_multiply, unpack_int4


class WeightTests(unittest.TestCase):
    def test_known_nibble_order_and_group_dequantization(self):
        q = np.array([[0, 15, 3, 8], [1, 2, 14, 7]], dtype=np.uint8)
        packed = pack_int4(q)
        np.testing.assert_array_equal(packed, [[0xF0, 0x83], [0x21, 0x7E]])
        np.testing.assert_array_equal(unpack_int4(packed), q)
        weight = W4A16(packed, np.array([[0.5, 2], [1, 0.25]], np.float32), np.array([[3, 8], [0, 10]]), 2)
        np.testing.assert_array_equal(weight.dequantize(), [[-1.5, 6, -10, 0], [1, 2, 1, -0.75]])

    def test_slices_preserve_group_metadata_and_views(self):
        q = np.arange(32, dtype=np.uint8).reshape(4, 8) % 16
        weight = W4A16(pack_int4(q), np.arange(1, 9, dtype=np.float32).reshape(4, 2), np.full((4, 2), 7), 4)
        for sliced, expected in [(weight.output_slice(1, 3), weight.dequantize()[1:3]), (weight.input_slice(4, 8), weight.dequantize()[:, 4:8])]:
            np.testing.assert_array_equal(sliced.dequantize(), expected)
            self.assertTrue(np.shares_memory(weight.packed, sliced.packed))
            self.assertTrue(np.shares_memory(weight.scales, sliced.scales))
        for bounds in [(2, 8), (0, 6), (-4, 4), (4, 4), (0, 12), (0.0, 4)]:
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                weight.input_slice(*bounds)

    def test_rejects_invalid_weight_formats(self):
        packed = np.zeros((4, 4), dtype=np.uint8)
        scales, zeros = np.ones((4, 2), np.float32), np.zeros((4, 2), np.int32)
        bad_args = [(packed.astype(np.int32), scales, zeros, 4), (packed, scales, zeros, 3), (packed, scales[:, :1], zeros, 4), (packed, scales, zeros + 16, 4), (packed, scales * np.nan, zeros, 4), (packed, scales * 0, zeros, 4), (packed, scales, zeros.astype(np.float32), 4), (packed, scales, zeros, 0)]
        for args in bad_args:
            with self.subTest(args=args), self.assertRaises(ValueError):
                W4A16(*args)
        for q in [np.array([[1, 16]]), np.array([[1, -1]]), np.array([[1.5, 2]]), np.array([[1, 2, 3]])]:
            with self.subTest(q=q), self.assertRaises(ValueError):
                pack_int4(q)


class FFNTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(7201)
        self.hidden, self.intermediate, self.group = 16, 32, 4
        self.x = self.rng.normal(0, 0.25, (3, self.hidden)).astype(np.float32)
        self.gate = self.weight(self.intermediate, self.hidden)
        self.up = self.weight(self.intermediate, self.hidden)
        self.down = self.weight(self.hidden, self.intermediate)

    def weight(self, n, k):
        q = self.rng.integers(0, 16, (n, k), dtype=np.uint8)
        scales = self.rng.uniform(0.01, 0.1, (n, k // self.group)).astype(np.float32)
        zeros = self.rng.integers(1, 15, (n, k // self.group), dtype=np.uint8)
        return W4A16(pack_int4(q), scales, zeros, self.group)

    def test_asymmetric_persistent_partitions_equal_dense_ffn(self):
        expected = ffn_reference(self.x, self.gate, self.up, self.down)
        for npu_channels in [0, 4, 12, 20, 28, 32]:
            with self.subTest(npu_channels=npu_channels):
                partition = FFNPartition(self.intermediate, npu_channels, self.group)
                actual, partials = ffn_partitioned(self.x, self.gate, self.up, self.down, partition)
                np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=2e-7)
                np.testing.assert_array_equal(actual, partials["npu"] + partials["gpu"])
                # Check one partial independently, catching mismatched gate/up/down slices.
                z = (self.x.astype(np.float64) @ self.gate.dequantize().astype(np.float64).T)[:, :npu_channels]
                u = (self.x.astype(np.float64) @ self.up.dequantize().astype(np.float64).T)[:, :npu_channels]
                expected_npu = (z / (1 + np.exp(-z)) * u) @ self.down.dequantize().astype(np.float64)[:, :npu_channels].T
                np.testing.assert_allclose(partials["npu"], expected_npu, rtol=1e-5, atol=2e-7)

    def test_bf16_boundaries_allow_partitioned_reduction(self):
        expected = ffn_reference(self.x, self.gate, self.up, self.down, bf16_io=True)
        actual, partials = ffn_partitioned(self.x, self.gate, self.up, self.down, FFNPartition(32, 12, 4), bf16_io=True)
        # Different FP32 summation order may straddle a BF16 rounding boundary.
        np.testing.assert_allclose(actual, expected, rtol=0.01, atol=0.0001)
        np.testing.assert_array_equal(actual, bf16(partials["npu"] + partials["gpu"]))
        np.testing.assert_array_equal(actual, bf16(actual))

    def test_ratio_rounding_and_endpoint_baselines(self):
        self.assertEqual(FFNPartition.from_ratio(14336, 0.3).npu_channels, 4352)
        self.assertEqual(FFNPartition.from_ratio(32, 0.125, 8).npu_channels, 8)
        self.assertEqual(FFNPartition.from_ratio(32, 0, 4).npu_channels, 0)
        self.assertEqual(FFNPartition.from_ratio(32, 1, 4).npu_channels, 32)
        for ratio in [-0.1, 1.1, np.nan, np.inf]:
            with self.subTest(ratio=ratio), self.assertRaises(ValueError):
                FFNPartition.from_ratio(32, ratio, 4)

    def test_rejects_misalignment_and_bad_shapes(self):
        for args in [(32, -4, 4), (32, 36, 4), (32, 6, 4), (30, 4, 4), (32, 4, 0), (32, 4.0, 4)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                FFNPartition(*args)
        for partition in [FFNPartition(32, 2, 2), FFNPartition(64, 16, 4)]:
            with self.subTest(partition=partition), self.assertRaises(ValueError):
                ffn_partitioned(self.x, self.gate, self.up, self.down, partition)
        for x, gate, up, down in [(self.x[:, :-1], self.gate, self.up, self.down), (self.x, self.gate, self.up.output_slice(0, 16), self.down), (self.x, self.gate, self.up, self.down.output_slice(0, 8)), (self.x * np.nan, self.gate, self.up, self.down)]:
            with self.subTest(), self.assertRaises(ValueError):
                ffn_reference(x, gate, up, down)


class NumericTests(unittest.TestCase):
    def test_bf16_silu_rounds_before_multiplication(self):
        # Exact BF16 input values. Expected binary fractions are independently
        # rounded exact SiLU values, multiplied by 1.25 and rounded again.
        # At -2 and -0.5, rounding only after multiplication gives a different
        # BF16 value, so this catches accidental removal of the SiLU boundary.
        gate = np.array([-4, -3, -2, -1, -0.5, 0.5, 1, 2, 3, 4], np.float32)
        up = np.full_like(gate, 1.25)
        expected = np.array([-0.08984375, -0.177734375, -0.296875, -0.3359375,
                             -0.2353515625, 0.388671875, 0.9140625, 2.203125,
                             3.578125, 4.90625], np.float32)
        actual = silu_multiply(gate, up, bf16_io=True)
        np.testing.assert_array_equal(actual, expected)
        single_round = bf16(silu_multiply(gate, up))
        self.assertNotEqual(float(single_round[2]), float(expected[2]))
        self.assertNotEqual(float(single_round[4]), float(expected[4]))

    def test_bf16_rounding_ties_and_nonfinite_values(self):
        values = np.array([1.00390625, 1.01171875, -1.00390625, np.inf, -np.inf, np.nan], np.float32)
        actual = bf16(values)
        np.testing.assert_array_equal(actual[:5], [1, 1.015625, -1, np.inf, -np.inf])
        self.assertTrue(np.isnan(actual[-1]))
        self.assertEqual(float(bf16(np.float32(1.00390625))), 1)

    def test_silu_stable_extremes_and_equal_shapes(self):
        gate = np.array([-1000, -1, 0, 1, 1000], np.float32)
        with np.errstate(over="raise", invalid="raise"):
            actual = silu_multiply(gate, np.full(5, 2, np.float32))
        np.testing.assert_allclose(actual, [0, -2 / (1 + np.exp(1)), 0, 2 / (1 + np.exp(-1)), 2000], atol=1e-7)
        with self.assertRaises(ValueError):
            silu_multiply(np.ones((1, 4)), np.ones(4))


if __name__ == "__main__":
    unittest.main()
