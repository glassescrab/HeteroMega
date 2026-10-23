"""CPU checks for experimental BFP16 acceptance without hiding broken execution."""

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from experiments.ffn_partition.contract import (
    OutputIntegrity, accuracy_metrics, accuracy_summary, error_metrics,
    resolve_accuracy_policy,
)
from experiments.ffn_partition import profile_timeline, run


class BFPAccuracyTests(unittest.TestCase):
    def setUp(self):
        self.expected = np.array([[1.0, -2.0], [3.0, -4.0]], dtype=np.float32)

    def test_arithmetic_defaults_and_explicit_override(self):
        self.assertEqual(resolve_accuracy_policy(), "strict")
        self.assertEqual(resolve_accuracy_policy("bf16"), "strict")
        self.assertEqual(resolve_accuracy_policy("bfp16"), "report")
        self.assertEqual(resolve_accuracy_policy("bfp16", "strict"), "strict")
        for arithmetic, policy in (("fp32", None), ("bf16", "ignore")):
            with self.assertRaises(ValueError):
                resolve_accuracy_policy(arithmetic, policy)

    def test_report_keeps_failed_fixed_metrics_and_accepts_finite_deviation(self):
        actual = self.expected * 1.2
        original = error_metrics(actual, self.expected)
        report = accuracy_metrics(actual, self.expected, "report")
        self.assertFalse(report["passed"])
        self.assertEqual(report["correctness"], "failed")
        self.assertTrue(report["accepted"])
        self.assertEqual(report["accuracy_status"], "reported_deviation")
        for key, value in original.items():
            self.assertEqual(report[key], value)
        strict = accuracy_metrics(actual, self.expected, "strict")
        self.assertFalse(strict["accepted"])
        self.assertEqual(strict["accuracy_status"], "outside_tolerance")

    def test_report_rejects_nonfinite_and_zero_contract_failures(self):
        cases = [
            (np.full_like(self.expected, np.nan), self.expected, "nonfinite_output"),
            (np.full_like(self.expected, np.inf), self.expected, "nonfinite_output"),
            (np.full_like(self.expected, 1e-9), np.zeros_like(self.expected),
             "zero_reference_nonzero_output"),
            (np.zeros_like(self.expected), self.expected, "nonzero_reference_zero_output"),
        ]
        for actual, expected, reason in cases:
            with self.subTest(reason=reason):
                metrics = accuracy_metrics(actual, expected, "report")
                self.assertFalse(metrics["accepted"])
                self.assertIn(reason, metrics["structural_failures"])
                self.assertEqual(metrics["accuracy_status"], "structural_failure")
                # JSON output must remain valid even when actual contains NaNs.
                json.dumps(metrics, allow_nan=False)

    def test_report_rejects_stale_response_to_different_inputs(self):
        integrity = OutputIntegrity()
        actual = self.expected * 1.2
        first = accuracy_metrics(actual, self.expected, "report", integrity, 0)
        self.assertTrue(first["accepted"])
        stale = accuracy_metrics(actual, -self.expected, "report", integrity, 1)
        self.assertFalse(stale["accepted"])
        self.assertIn("distinct_inputs_identical_output", stale["structural_failures"])

    def test_repeated_inputs_are_exact_and_snapshots_survive_buffer_reuse(self):
        integrity = OutputIntegrity()
        output = self.expected * 1.2
        first = output.copy()
        self.assertTrue(accuracy_metrics(output, self.expected, "report", integrity, 0)["accepted"])
        output[:] = -first
        self.assertTrue(accuracy_metrics(output, -self.expected, "report", integrity, 1)["accepted"])
        output[:] = 0
        self.assertTrue(accuracy_metrics(output, output, "report", integrity, 2)["accepted"])
        output[:] = first
        self.assertTrue(accuracy_metrics(output, self.expected, "report", integrity, 0)["accepted"])
        output[0, 0] += np.float32(1e-6)
        changed = accuracy_metrics(output, self.expected, "report", integrity, 0)
        self.assertFalse(changed["accepted"])
        self.assertIn("repeated_input_changed_output", changed["structural_failures"])

    def test_gpu_check_remains_strict_and_records_failed_metrics(self):
        checks = {}
        with self.assertRaisesRegex(RuntimeError, "correctness failed"):
            run.check(self.expected * 1.2, self.expected, "gpu_baseline", checks)
        self.assertFalse(checks["gpu_baseline"]["accepted"])
        self.assertEqual(checks["gpu_baseline"]["accuracy_policy"], "strict")
        self.assertTrue(run.check(self.expected, self.expected, "good_gpu", checks)["accepted"])

    def test_summary_distinguishes_numerical_pass_from_accepted_experiment(self):
        checks = [accuracy_metrics(self.expected, self.expected),
                  accuracy_metrics(self.expected * 1.2, self.expected, "report")]
        summary = accuracy_summary(checks)
        self.assertFalse(summary["passed"])
        self.assertTrue(summary["accepted"])
        self.assertEqual(summary["outside_tolerance_count"], 1)
        self.assertEqual(summary["accuracy_status"], "reported_deviations")

    def test_latency_ratios_survive_deviations_without_validated_speedup(self):
        stats = {mode: {"median_us": value}
                 for mode, value in (("baseline", 22_000), ("serial", 30_000), ("concurrent", 20_000))}
        failed = run.comparison_metrics(stats, accuracy_passed=False)
        self.assertEqual(failed["latency_ratio_vs_gpu_baseline"], 1.1)
        self.assertEqual(failed["latency_ratio_vs_serial_partition"], 1.5)
        self.assertIsNone(failed["speedup_vs_gpu_baseline"])
        self.assertIsNone(failed["speedup_vs_serial_partition"])
        passed = run.comparison_metrics(stats, accuracy_passed=True)
        self.assertEqual(passed["speedup_vs_gpu_baseline"], 1.1)
        self.assertEqual(passed["speedup_vs_serial_partition"], 1.5)
        self.assertEqual(passed["latency_ratio_vs_gpu_baseline"], failed["latency_ratio_vs_gpu_baseline"])
        self.assertEqual(passed["latency_ratio_vs_serial_partition"], failed["latency_ratio_vs_serial_partition"])

    def test_failed_or_missing_stage_completions_are_fatal(self):
        npu = SimpleNamespace(fuse_swiglu=True, swiglu=SimpleNamespace(completed_dispatches=4),
                              down=SimpleNamespace(completed_dispatches=0))
        with self.assertRaisesRegex(RuntimeError, "completion counters"):
            profile_timeline.completion_counts(npu, 4)
        npu.down.completed_dispatches = 4
        self.assertEqual(profile_timeline.completion_counts(npu, 4), {"swiglu": 4, "down": 4})

    def test_ordinary_cli_plumbs_arithmetic_and_default_policy_into_artifact_build(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            argv = ["ffn", "--m", "128", "--hidden", "128", "--intermediate", "384",
                    "--npu-channels", "128", "--npu-arithmetic", "bfp16", "--build-only",
                    "--output", str(output)]
            with mock.patch("sys.argv", argv), mock.patch.object(run, "provenance", return_value={}), \
                    mock.patch.object(run, "build_artifacts") as build:
                run.main()
            self.assertEqual(build.call_args.kwargs["npu_arithmetic"], "bfp16")
            report = json.loads(output.read_text())
            self.assertEqual(report["config"]["accuracy_policy"], "report")
            self.assertEqual(report["status"], "build_complete")

    def test_diagnostic_cli_plumbs_arithmetic_and_strict_override(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            argv = ["profile", "--m", "128", "--hidden", "128", "--intermediate", "384",
                    "--npu-channels", "128", "--npu-arithmetic", "bfp16",
                    "--accuracy-policy", "strict", "--output", str(output)]
            with mock.patch("sys.argv", argv), mock.patch.object(profile_timeline, "provenance", return_value={}), \
                    mock.patch.object(profile_timeline, "build_artifacts", side_effect=RuntimeError("stop before hardware")) as build:
                with self.assertRaisesRegex(RuntimeError, "stop before hardware"):
                    profile_timeline.main()
            self.assertEqual(build.call_args.kwargs["npu_arithmetic"], "bfp16")
            report = json.loads(output.read_text())
            self.assertEqual(report["config"]["accuracy_policy"], "strict")
            self.assertEqual(report["status"], "failed")


if __name__ == "__main__":
    unittest.main()
