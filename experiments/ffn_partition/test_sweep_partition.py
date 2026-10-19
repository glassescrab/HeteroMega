"""CPU checks protecting sweep comparability and evidence classification."""

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from experiments.ffn_partition.sweep_partition import build_jobs, power_modes, validate_report


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

    def validate(self, report, mode):
        args = self.args()
        job = {"mode": mode, "m": 512, "npu_channels": 512, "fuse_gate_up": False,
               "iterations": 50 if mode == "ordinary" else 30}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            path.write_text(json.dumps(report))
            return validate_report(path, job, args)

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
