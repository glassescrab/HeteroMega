"""CPU-only checks; these do not establish native compilation or execution."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from experiments.ffn_partition.contract import OutputIntegrity, bf16, random_weights, reference_full
from experiments.ffn_partition.native_heteromosaic import (accuracy_policy_for, array_hash, checked_metrics,
                                                         finish_accuracy_report, main, native_config,
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

    def test_report_accepts_native_numerical_failure_without_changing_verdict(self):
        expected = np.ones((2, 2), np.float32)
        actual = expected * 2
        for mode in ("native", "native_vs_gpu"):
            metrics = checked_metrics(actual, expected, policy=accuracy_policy_for(mode, "report"))
            self.assertFalse(metrics["passed"])
            self.assertFalse(metrics["numerical_passed"])
            self.assertTrue(metrics["accepted"])
            self.assertTrue(metrics["structural_passed"])
            self.assertEqual(metrics["accuracy_status"], "reported_deviation")
            self.assertEqual((metrics["rtol"], metrics["atol"], metrics["l2_limit"]), (.03, .05, .02))
        self.assertFalse(checked_metrics(actual, expected)["accepted"])

    def test_report_keeps_gpu_control_strict(self):
        expected = np.ones((2, 2), np.float32)
        metrics = checked_metrics(expected * 2, expected,
                                  policy=accuracy_policy_for("baseline", "report"))
        self.assertEqual(metrics["accuracy_policy"], "strict")
        self.assertFalse(metrics["accepted"])
        self.assertFalse(metrics["passed"])
        for mode, policy in (("unknown", "report"), ("native", "unknown")):
            with self.assertRaises(ValueError):
                accuracy_policy_for(mode, policy)

    def test_report_never_accepts_structural_failures(self):
        expected = np.ones((2, 2), np.float32)
        for actual, reference in ((np.full_like(expected, np.nan), expected),
                                  (np.zeros_like(expected), expected),
                                  (expected, np.zeros_like(expected))):
            metrics = checked_metrics(actual, reference, policy="report")
            self.assertFalse(metrics["accepted"])
            self.assertFalse(metrics["structural_passed"])
            self.assertFalse(metrics["passed"])
        for changed_id in (0, 1):
            integrity = OutputIntegrity()
            checked_metrics(expected, expected, integrity, 0, policy="report")
            actual = expected + .001 if changed_id == 0 else expected
            metrics = checked_metrics(actual, expected + .001, integrity, changed_id, policy="report")
            self.assertTrue(metrics["numerical_passed"])
            self.assertFalse(metrics["accepted"])
            self.assertFalse(metrics["structural_passed"])
            self.assertFalse(metrics["passed"])

    def test_report_finish_separates_latency_ratio_from_validated_speedup(self):
        expected = np.ones((2, 2), np.float32)
        baseline = checked_metrics(expected, expected)
        native = checked_metrics(expected * 2, expected, policy="report")
        report = dict(correctness={"baseline": baseline, "native": native},
                      warmup_samples=[dict(accuracy=native)], samples=[dict(accuracy=native)],
                      stats={"baseline": {"median_us": 30}, "native": {"median_us": 20}})
        finish_accuracy_report(report)
        self.assertEqual(report["status"], "completed_with_accuracy_deviations")
        self.assertTrue(report["accuracy"]["accepted"])
        self.assertFalse(report["accuracy"]["passed"])
        self.assertEqual(report["accuracy"]["check_count"], 4)
        self.assertEqual(report["accuracy"]["outside_tolerance_count"], 3)
        self.assertEqual(report["latency_ratio_native_vs_gpu"], 1.5)
        self.assertIsNone(report["speedup_native_vs_gpu"])
        report["correctness"]["baseline"] = checked_metrics(expected * 2, expected)
        with self.assertRaises(RuntimeError):
            finish_accuracy_report(report)

    def test_strict_finish_retains_validated_speedup(self):
        value = np.ones((2, 2), np.float32)
        report = dict(correctness={"baseline": checked_metrics(value, value)},
                      warmup_samples=[], samples=[],
                      stats={"baseline": {"median_us": 30}, "native": {"median_us": 20}})
        finish_accuracy_report(report)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["speedup_native_vs_gpu"], 1.5)
        self.assertEqual(report["latency_ratio_native_vs_gpu"], 1.5)

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
            self.assertEqual(report["config"]["accuracy_policy"], "strict")
            self.assertTrue(output.with_suffix(".native_config.json").exists())
            self.assertEqual(json.loads(output.read_text()), report)


if __name__ == "__main__":
    unittest.main()
