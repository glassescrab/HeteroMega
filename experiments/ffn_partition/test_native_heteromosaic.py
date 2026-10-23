"""CPU-only checks; these do not establish native compilation or execution."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from experiments.ffn_partition.contract import bf16, random_weights, reference_full
from experiments.ffn_partition.native_heteromosaic import (checked_metrics, main, native_config,
                                                         reference_stages, seeded_inputs)


class NativeContractTest(unittest.TestCase):
    def test_exact_m_split_config(self):
        config = native_config()
        self.assertEqual(config["heterogeneity"], "hetero")
        self.assertEqual([kernel["layer"] for kernel in config["kernels_gemm"]], ["gate", "up"])
        for kernel in config["kernels_gemm"]:
            self.assertEqual([kernel[k] for k in ("forM", "forK", "forN", "npuM", "npuK", "npuN", "chunk_id")],
                             [512, 4096, 14336, 256, 4096, 14336, 0])
        self.assertFalse(config["padPackedWeights"])
        self.assertFalse(config["chunking"])

    def test_reject_unsupported_shape(self):
        for args in ((256, 4096, 14336, 256), (512, 4096, 14336, 128), (512, 4096, 8192, 256)):
            with self.assertRaises(ValueError):
                native_config(*args)

    def test_input_sequence_matches_common_contract(self):
        actual = seeded_inputs(128, 128, 12832)
        rng = np.random.default_rng(12833)
        for index in range(2):
            np.testing.assert_array_equal(actual[index], bf16(rng.normal(size=(128, 128)).astype(np.float32)))
        np.testing.assert_array_equal(actual[2], 0)
        self.assertFalse(np.array_equal(actual[0], actual[1]))

    def test_projection_reference_matches_complete_reference(self):
        weights = random_weights(128, 128, 91)
        for x in seeded_inputs(128, 128, 92):
            ref = reference_stages(x, weights)
            np.testing.assert_array_equal(ref["output"], reference_full(x, weights))
            self.assertEqual(ref["gate"].shape, (128, 128))

    def test_failed_metrics_preserve_location_and_limits(self):
        expected = np.zeros((3, 2), np.float32)
        actual = expected.copy()
        actual[2, 1] = 1.0
        metrics = checked_metrics(actual, expected)
        self.assertFalse(metrics["passed"])
        self.assertEqual(metrics["max_error_index"], [2, 1])
        self.assertEqual(metrics["rtol"], .03)
        self.assertEqual(metrics["atol"], .05)
        self.assertEqual(metrics["l2_limit"], .02)
        json.dumps(metrics, allow_nan=False)

    def test_prepare_never_claims_hardware_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            report = main(["--prepare-only", "--output", str(output)])
            self.assertEqual(report["status"], "prepared_not_executed")
            self.assertEqual(report["completed_npu_dispatches"], 0)
            self.assertEqual(report["expected_npu_dispatches"], 0)
            self.assertEqual(report["samples"], [])
            self.assertTrue(output.with_suffix(".native_config.json").exists())
            self.assertEqual(json.loads(output.read_text()), report)


if __name__ == "__main__":
    unittest.main()
