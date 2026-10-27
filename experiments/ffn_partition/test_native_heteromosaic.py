"""CPU-only checks; these do not establish native compilation or execution."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from experiments.ffn_partition.contract import OutputIntegrity, bf16, random_weights, reference_full
from experiments.ffn_partition.native_heteromosaic import (array_hash, checked_metrics, main, native_config,
                                                         record_buffer_integrity, reference_stages,
                                                         seeded_inputs)


class FakeDeviceTensor:
    """Copies stand in for device buffers; this is not a hardware test."""
    def __init__(self, value):
        self.value = value.copy()

    def detach(self):
        return self

    def cpu(self):
        return self

    def float(self):
        return FakeDeviceTensor(self.value.astype(np.float32))

    def numpy(self):
        return self.value


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

    def test_exact_repeat_guard_rejects_within_tolerance_change(self):
        reference = np.ones((2, 2), np.float32)
        integrity = OutputIntegrity()
        self.assertTrue(checked_metrics(reference, reference, integrity, 0)["passed"])
        repeated = reference.copy()
        repeated[0, 0] += .001
        metrics = checked_metrics(repeated, reference, integrity, 0)
        self.assertTrue(metrics["numerical_passed"])
        self.assertFalse(metrics["passed"])
        self.assertFalse(metrics["accepted"])
        self.assertEqual(metrics["structural_failures"], ["repeated_input_changed_output"])
        self.assertEqual((metrics["rtol"], metrics["atol"], metrics["l2_limit"]), (.03, .05, .02))

    def test_changed_input_guard_rejects_stale_within_tolerance_output(self):
        original = np.ones((2, 2), np.float32)
        changed = original + .001
        integrity = OutputIntegrity()
        checked_metrics(original, original, integrity, 0)
        metrics = checked_metrics(original, changed, integrity, 1)
        self.assertTrue(metrics["numerical_passed"])
        self.assertFalse(metrics["passed"])
        self.assertEqual(metrics["structural_failures"], ["distinct_inputs_identical_output"])

    def test_nonfinite_and_zero_remain_fatal_and_json_serializable(self):
        for actual, expected, failure in (
                (np.array([np.nan], np.float32), np.ones(1, np.float32), "nonfinite_output"),
                (np.ones(1, np.float32), np.zeros(1, np.float32), "zero_reference_nonzero_output")):
            with self.subTest(failure=failure):
                metrics = checked_metrics(actual, expected)
                self.assertFalse(metrics["passed"])
                self.assertFalse(metrics["structural_passed"])
                self.assertIn(failure, metrics["structural_failures"])
                json.dumps(metrics, allow_nan=False)

    def test_final_buffer_checks_detect_device_weights_and_host_input_changes(self):
        packed = [np.array([1, 2, 3], np.uint8)]
        inputs = [np.array([[1, 2]], np.float32)]
        device_weights = [FakeDeviceTensor(value) for value in packed]
        device_inputs = [FakeDeviceTensor(value) for value in inputs]
        report = dict(native_packed_weight_sha256=[array_hash(value) for value in packed],
                      input_sha256=[array_hash(value) for value in inputs])
        self.assertTrue(record_buffer_integrity(report, packed, inputs, device_weights, device_inputs, "before"))
        device_weights[0].value[0] = 9
        inputs[0][0, 0] = 3
        self.assertFalse(record_buffer_integrity(report, packed, inputs, device_weights, device_inputs, "after"))
        checks = report["buffer_integrity_after"]["checks"]
        self.assertFalse(checks["device_weights_match_initial"])
        self.assertFalse(checks["host_inputs_match_initial"])
        self.assertTrue(checks["host_weights_match_initial"])
        self.assertTrue(checks["device_inputs_match_initial"])
        self.assertTrue(report["buffer_integrity_before"]["passed"])
        json.dumps(report, allow_nan=False)

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
