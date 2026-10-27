"""CPU fixture/oracle tests; these do not establish native hardware behavior."""

import json
import unittest

import numpy as np

from experiments.ffn_partition.contract import bf16
from experiments.ffn_partition.diagnose_native_projection import (
    CASES, fixture_hashes, make_fixture, projection_reference, representative_k_indices)


class NativeProjectionDiagnosticTests(unittest.TestCase):
    def test_basis_covers_all_k_groups_and_microtile_edges(self):
        indices = representative_k_indices()
        self.assertEqual(indices.shape, (256,))
        self.assertEqual(len(set(indices)), 256)
        np.testing.assert_array_equal(np.unique(indices // 128), np.arange(32))
        for group in range(32):
            np.testing.assert_array_equal(indices[group * 8:(group + 1) * 8] % 128,
                                          [0, 1, 7, 8, 63, 64, 126, 127])

    def test_onehot_oracle_matches_dense_independent_product(self):
        for name in ("onehot_qzeros", "onehot_scales"):
            with self.subTest(name=name):
                weights, x, indices = make_fixture(name, seed=7, hidden=256, intermediate=384)
                np.testing.assert_array_equal(x[:16], x[16:])
                np.testing.assert_array_equal(np.count_nonzero(x, axis=1), 1)
                for weight in (weights.gate, weights.up):
                    ref = projection_reference(name, x, weight, indices)
                    np.testing.assert_array_equal(ref, bf16(x @ weight.dequantize(True).T))
                np.testing.assert_array_equal(weights.down.dequantize(True), 0)

    def test_constant_exact_fixture_has_analytical_value_and_equal_halves(self):
        weights, x, indices = make_fixture("constant_exact", hidden=256, intermediate=128)
        np.testing.assert_array_equal(x, 1 / 16)
        for weight in (weights.gate, weights.up):
            ref = projection_reference("constant_exact", x, weight, indices)
            np.testing.assert_array_equal(ref, 256 / 256)
            np.testing.assert_array_equal(ref, bf16(x @ weight.dequantize(True).T))

    def test_signed_constant_fixture_keeps_negative_and_positive_inputs(self):
        weights, x, indices = make_fixture("constant_signed", seed=9, hidden=256, intermediate=128)
        self.assertTrue(np.any(x < 0))
        self.assertTrue(np.any(x > 0))
        np.testing.assert_array_equal(x[:16], x[16:])
        ref = projection_reference("constant_signed", x, weights.gate, indices)
        np.testing.assert_array_equal(ref, bf16(x @ weights.gate.dequantize(True).T))

    def test_random_fixture_and_hashes_are_reproducible_and_reportable(self):
        for name in CASES:
            with self.subTest(name=name):
                weights, x, indices = make_fixture(name, seed=10, hidden=128, intermediate=128)
                again, x2, _ = make_fixture(name, seed=10, hidden=128, intermediate=128)
                self.assertEqual(fixture_hashes(weights, x), fixture_hashes(again, x2))
                json.dumps(fixture_hashes(weights, x), allow_nan=False)
                ref = projection_reference(name, x, weights.up, indices)
                self.assertEqual(ref.shape, (16, 128))
                self.assertTrue(np.all(np.isfinite(ref)))

    def test_invalid_case_and_k_alignment_rejected(self):
        with self.assertRaises(ValueError):
            make_fixture("unknown")
        with self.assertRaises(ValueError):
            representative_k_indices(129)


if __name__ == "__main__":
    unittest.main()
