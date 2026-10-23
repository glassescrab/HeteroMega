"""CPU checks protecting sweep comparability and evidence classification."""

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

from experiments.ffn_partition.contract import accuracy_metrics
from experiments.ffn_partition.sweep_partition import build_jobs, completed_status, power_modes, validate_report


HERE = Path(__file__).resolve().parent


class SweepTests(unittest.TestCase):
    def args(self):
        return SimpleNamespace(m=[512], hidden=4096, intermediate=14336,
                               npu_channels=[128, 512], variants="both", measurements="both",
                               iterations=50, diagnostic_iterations=30, seed=12832, warmup=3,
                               artifact_root=Path("/tmp/unused-artifacts"), iron_python="/iron/python",
                               output_dir=Path("/tmp/unused-sweep"))

    def test_matching_seeds_and_alternating_variant_order(self):
        jobs = build_jobs(self.args())
        self.assertEqual(len(jobs), 8)
        self.assertEqual([job["fuse_gate_up"] for job in jobs[:4]], [False, True, True, False])
        self.assertEqual([job["mode"] for job in jobs], ["ordinary"] * 4 + ["diagnostic"] * 4)
        for job in jobs:
            cmd = job["command"]
            self.assertEqual(cmd[cmd.index("--seed") + 1], "12832")
            self.assertEqual("--fuse-gate-up" in cmd, job["fuse_gate_up"])

    def test_power_mode_requires_matching_npu_device(self):
        payload = json.loads((HERE / "results/power/default_before.json").read_text())
        self.assertEqual(power_modes(payload, "0000:66:00.1"), ["default"])
        self.assertEqual(power_modes(payload, "0000:00:00.0"), [])
        self.assertEqual(power_modes({}, "0000:66:00.1"), [])

    def test_swiglu_comparison_has_distinct_tags_flags_and_alternating_order(self):
        args = self.args()
        args.variants = "fusion-levels"
        jobs = build_jobs(args)
        self.assertEqual(len(jobs), 8)
        self.assertEqual([job["fuse_swiglu"] for job in jobs[:4]], [False, True, True, False])
        self.assertEqual(len({job["id"] for job in jobs}), len(jobs))
        for job in jobs:
            self.assertTrue(job["fuse_gate_up"])
            self.assertEqual("--fuse-swiglu" in job["command"], job["fuse_swiglu"])
        args.variants = "swiglu"
        self.assertTrue(all(job["fuse_swiglu"] for job in build_jobs(args)))

    def report(self, mode):
        filename = ("array8_default_m512_p512_hx370.json" if mode == "ordinary"
                    else "timeline_m512_p512_array8.json")
        report = json.loads((HERE / "results" / filename).read_text())
        # Historical fixtures predate this explicit false default. The timing
        # data is unchanged; tests exercise classification only.
        report["config"]["fuse_gate_up"] = False
        return report

    def validate(self, report, mode, args=None):
        args = args or self.args()
        job = {"mode": mode, "m": 512, "npu_channels": 512, "fuse_gate_up": False,
               "iterations": 50 if mode == "ordinary" else 30}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report))
            return validate_report(path, job, args)

    def bfp_report(self, mode):
        """Synthetic schema fixture; these mutations are not new hardware evidence."""
        report = self.report(mode)
        report["config"].update(npu_arithmetic="bfp16", accuracy_policy="report")
        entry = report["partitions"][0] if mode == "ordinary" else report
        containers = ([report["correctness"], entry["correctness"]] if mode == "ordinary"
                      else [report["checks"]])
        for checks in containers:
            for name, metrics in checks.items():
                gpu = name.startswith("baseline_input_") or name.endswith("_gpu_partial")
                metrics.update(accepted=True, accuracy_policy="strict" if gpu else "report",
                               accuracy_status="within_tolerance", structural_failures=[])
        for sample in entry["samples"]:
            gpu = sample.get("mode") == "baseline"
            sample["accuracy"] = accuracy_metrics(np.ones(1), np.ones(1), "strict" if gpu else "report")
            sample.update(accuracy_accepted=True, accuracy_status="within_tolerance")
            if not gpu:
                sample["npu_accuracy"] = accuracy_metrics(np.ones(1), np.ones(1), "report")
        sample = next(s for s in entry["samples"] if s.get("mode") != "baseline")
        sample["accuracy"] = accuracy_metrics(np.array([1.2]), np.ones(1), "report")
        sample.update(correctness_passed=False, accuracy_status="reported_deviation")
        count = 114 if mode == "ordinary" else 37
        entry["completed_npu_dispatches_by_stage"] = {name: count for name in ("gate", "up", "silu_mul", "down")}
        report.update(status="completed_with_accuracy_deviations",
                      accuracy=dict(passed=False, accepted=True, accuracy_policy="report",
                                    accuracy_status="reported_deviations"))
        return report

    def test_bfp_jobs_carry_explicit_arithmetic_and_resolved_policy(self):
        args = self.args()
        args.npu_arithmetic = "bfp16"
        jobs = build_jobs(args)
        for job in jobs:
            self.assertEqual(job["npu_arithmetic"], "bfp16")
            self.assertEqual(job["accuracy_policy"], "report")
            self.assertEqual(job["command"][job["command"].index("--accuracy-policy") + 1], "report")
            self.assertIn("_bfp16", job["id"])
        args.accuracy_policy = "strict"
        self.assertTrue(all(j["accuracy_policy"] == "strict" for j in build_jobs(args)))

    def test_bfp_deviations_require_explicit_planned_policy_and_remain_deviations(self):
        args = self.args()
        args.npu_arithmetic, args.accuracy_policy = "bfp16", "report"
        for mode in ("ordinary", "diagnostic"):
            with self.subTest(mode=mode):
                report = self.bfp_report(mode)
                evidence = self.validate(report, mode, args)
                self.assertFalse(evidence["accuracy_passed"])
                self.assertTrue(evidence["accuracy_accepted"])
                self.assertEqual(evidence["status"], "completed_with_accuracy_deviations")
                with self.assertRaises(ValueError):
                    self.validate(report, mode)
                strict_args = copy.copy(args)
                strict_args.accuracy_policy = "strict"
                with self.assertRaises(ValueError):
                    self.validate(report, mode, strict_args)
        self.assertEqual(completed_status([{"status": "passed"}, evidence]),
                         "completed_with_accuracy_deviations")

    def test_bfp_report_rejects_missing_guards_nonfinite_relabeling_and_missing_stages(self):
        args = self.args()
        args.npu_arithmetic, args.accuracy_policy = "bfp16", "report"
        report = self.bfp_report("ordinary")
        mutations = [
            lambda r: r.update(status="passed"),
            lambda r: r["accuracy"].update(passed=True),
            lambda r: r["partitions"][0]["correctness"].pop("serial_run_3_input_0_npu_partial"),
            lambda r: r["partitions"][0]["samples"][0]["accuracy"].update(structural_failures=["repeated_input_changed_output"]),
            lambda r: r["partitions"][0]["samples"][0]["accuracy"].update(finite=False),
            lambda r: r["partitions"][0]["samples"][0]["accuracy"].update(relative_l2_error=None),
            lambda r: r["partitions"][0]["samples"][0].pop("npu_accuracy"),
            lambda r: r["partitions"][0]["samples"][0].update(correctness_passed=True),
            lambda r: r["correctness"]["baseline_input_0"].update(accuracy_policy="report"),
            lambda r: r["partitions"][0]["completed_npu_dispatches_by_stage"].update(down=0),
            lambda r: r["partitions"][0].pop("completed_npu_dispatches_by_stage"),
        ]
        for mutation in mutations:
            bad = copy.deepcopy(report)
            mutation(bad)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.validate(bad, "ordinary", args)

    def test_existing_hardware_reports_satisfy_expected_counters(self):
        ordinary = self.validate(self.report("ordinary"), "ordinary")
        diagnostic = self.validate(self.report("diagnostic"), "diagnostic")
        self.assertEqual(ordinary["completed_npu_dispatches"], 456)
        self.assertEqual(diagnostic["completed_npu_dispatches"], 148)

    def test_rejects_failed_missing_or_mismatched_samples(self):
        original = self.report("ordinary")
        mutations = [
            lambda r: r.update(status="failed"),
            lambda r: r["config"].update(seed=1),
            lambda r: r["partitions"][0]["samples"].pop(),
            lambda r: r["partitions"][0]["samples"][0].update(correctness_passed=False),
            lambda r: r["partitions"][0]["samples"][0].update(input_index=99),
        ]
        for mutation in mutations:
            report = copy.deepcopy(original)
            mutation(report)
            with self.assertRaises(ValueError):
                self.validate(report, "ordinary")

    def test_rejects_missing_npu_execution_and_repeated_weight_upload(self):
        report = self.report("diagnostic")
        report["completed_npu_dispatches"] = 0
        with self.assertRaisesRegex(ValueError, "completion count"):
            self.validate(report, "diagnostic")
        report = self.report("diagnostic")
        report["fixed_weight_upload_counts"]["gate"] = 2
        with self.assertRaisesRegex(ValueError, "exactly once"):
            self.validate(report, "diagnostic")


if __name__ == "__main__":
    unittest.main()
