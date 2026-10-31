"""CPU checks for comparison validity; these do not execute accelerator kernels."""

import argparse
import copy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.ffn_partition.compare_native import build_jobs, summarize, validate_candidate, validate_native


def arguments(output_dir):
    return argparse.Namespace(output_dir=Path(output_dir), npu_channels=[1024, 1152],
                              blocks=2, iterations=2, diagnostic_iterations=1, seed=12832,
                              warmup=3, native_root=Path("/native"), native_library=Path("/native/model.so"),
                              driver_include=None, artifact_root=Path("/artifacts"), iron_python=None)


def native_report():
    checks = {}
    for repetition, index in enumerate((0, 1, 2, 0)):
        prefix = f"run{repetition}_input{index}_"
        names = [prefix + f"{mode}_{stage}_{owner}" for mode in ("baseline", "native")
                 for stage in ("gate", "up", "output") for owner in ("all", "gpu_rows", "npu_rows")]
        names += [prefix + f"native_vs_gpu_{stage}" for stage in ("gate", "up", "output")]
        checks.update({name: dict(passed=True, finite=True, rtol=0.03, atol=0.05, l2_limit=0.02) for name in names})
    return dict(status="passed", config=dict(m=512, hidden=4096, intermediate=14336,
                npu_rows=256, seed=12832, warmup=3, iterations=2, mode="latency"),
                correctness=checks, completed_npu_dispatches=18,
                expected_npu_dispatches=18,
                samples=[dict(mode=mode, iteration=i, input_index=i % 2, wall_us=us,
                              correctness_passed=True, completed_npu_dispatches=2 if mode == "native" else 0)
                         for i in range(2) for mode, us in (("baseline", 22_000), ("native", 20_000))])


class ComparisonTests(unittest.TestCase):
    def test_reverse_order_and_separate_diagnostics(self):
        jobs = build_jobs(arguments("/output"))
        self.assertEqual(len(jobs), 9)
        ordinary = [j for j in jobs if j["mode"] == "ordinary"]
        self.assertEqual([j["variant"] for j in ordinary],
                         ["native", "swiglu", "swiglu", "swiglu", "swiglu", "native"])
        self.assertEqual([j["npu_channels"] for j in ordinary], [None, 1024, 1152, 1152, 1024, None])
        self.assertIn("--fuse-swiglu", jobs[1]["command"])
        self.assertIn("diagnostic", jobs[6]["command"])
        self.assertIn("experiments.ffn_partition.profile_timeline", jobs[7]["command"])

    def test_bfp_candidate_policy_does_not_relax_native_baseline(self):
        args = arguments("/output")
        args.npu_arithmetic = "bfp16"
        jobs = build_jobs(args)
        for job in jobs:
            if job["variant"] == "native":
                self.assertEqual(job["accuracy_policy"], "strict")
                self.assertNotIn("--npu-arithmetic", job["command"])
                self.assertNotIn("--accuracy-policy", job["command"])
            else:
                self.assertEqual(job["npu_arithmetic"], "bfp16")
                self.assertEqual(job["accuracy_policy"], "report")
                self.assertEqual(job["command"][job["command"].index("--npu-arithmetic") + 1], "bfp16")
        report = native_report()
        report["status"] = "completed_with_accuracy_deviations"
        with self.assertRaisesRegex(ValueError, "native report did not pass"):
            validate_native(report, jobs[0], args)

    def test_summary_preserves_experimental_numerical_deviations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = arguments(root)
            args.npu_arithmetic = "bfp16"
            jobs = build_jobs(args)[:2]
            candidate = {"status": "completed_with_accuracy_deviations", "partitions": [
                {"samples": [dict(mode=mode, wall_us=us) for _ in range(2)
                             for mode, us in (("baseline", 22_500), ("concurrent", 15_000))]}]}
            for job, report in ((jobs[0], native_report()), (jobs[1], candidate)):
                path = root / job["report_path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(report))
                job.update(status=report["status"], evidence={"report_sha256": sha256(path.read_bytes()).hexdigest()},
                           power_before_summary={"mode": "default"})
            result = summarize({"status": "completed_with_accuracy_deviations", "jobs": jobs}, root)
            row = result["ordinary"][1]
            self.assertFalse(row["accuracy_passed"])
            self.assertEqual(row["accuracy_status"], "reported_deviations")
            self.assertEqual(row["npu_arithmetic"], "bfp16")
            self.assertIsNone(row["speedup_vs_own_gpu"])
            self.assertEqual(row["latency_ratio_vs_own_gpu"], 1.5)
            self.assertEqual(result["comparisons"][0]["comparison_kind"],
                             "experimental_latency_with_numerical_deviations")
            self.assertAlmostEqual(result["comparisons"][0]["native_over_candidate"], 20 / 15)

    def test_native_rejects_failed_or_incomplete_evidence(self):
        args = arguments("/output")
        job = build_jobs(args)[0]
        report = native_report()
        self.assertEqual(validate_native(report, job, args)["timed_invocations"], 4)
        mutations = [lambda r: r.update(status="failed"),
                     lambda r: r["config"].update(seed=9),
                     lambda r: r.update(correctness={}),
                     lambda r: next(iter(r["correctness"].values())).update(passed=False),
                     lambda r: next(iter(r["correctness"].values())).update(l2_limit=0.2),
                     lambda r: r["correctness"].pop(next(iter(r["correctness"]))),
                     lambda r: r["samples"].pop(),
                     lambda r: r["samples"][2].update(iteration=0),
                     lambda r: r["samples"][0].update(wall_us=-1),
                     lambda r: r["samples"][0].update(input_index=1),
                     lambda r: r["samples"][1].update(completed_npu_dispatches=0),
                     lambda r: r.update(completed_npu_dispatches=0),
                     lambda r: r.update(completed_npu_dispatches=1, expected_npu_dispatches=1),
                     lambda r: r.update(expected_npu_dispatches=20)]
        for mutation in mutations:
            bad = copy.deepcopy(report)
            mutation(bad)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_native(bad, job, args)

    def test_candidate_rejects_duplicate_iterations_even_when_legacy_validator_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            args = arguments(directory)
            job = build_jobs(args)[1]
            path = Path(directory) / "report.json"
            samples = [dict(mode=mode, iteration=i, input_index=i % 2, wall_us=1)
                       for i in range(2) for mode in ("baseline", "serial", "concurrent")]
            report = {"partitions": [{"samples": samples}]}
            path.write_text(json.dumps(report))
            with patch("experiments.ffn_partition.compare_native.validate_report", return_value={"passed": True}):
                validate_candidate(path, job, args)
                for sample in samples:
                    sample.update(iteration=0, input_index=0)
                path.write_text(json.dumps(report))
                with self.assertRaises(ValueError):
                    validate_candidate(path, job, args)

    def test_summary_uses_raw_ordinary_samples_not_diagnostics_or_cached_stats(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jobs = build_jobs(arguments(root))
            native = native_report()
            candidate = {"stats": {"concurrent": {"median_us": 1}}, "partitions": [
                {"samples": [dict(mode=mode, wall_us=us) for _ in range(2)
                             for mode, us in (("baseline", 22_500), ("concurrent", 19_000))]}]}
            for job, report in ((jobs[0], native), (jobs[1], candidate)):
                path = root / job["report_path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(report))
                job.update(status="passed", evidence={"report_sha256": sha256(path.read_bytes()).hexdigest()},
                           power_before_summary={"mode": "default"})
            jobs[6].update(status="passed", power_before_summary={"mode": "default"})
            manifest = {"status": "incomplete", "jobs": jobs}
            result = summarize(manifest, root)
            self.assertEqual(len(result["ordinary"]), 2)
            self.assertAlmostEqual(result["comparisons"][0]["native_over_candidate"], 20 / 19)
            jobs[1]["power_before_summary"]["mode"] = "performance"
            self.assertEqual(summarize(manifest, root)["comparisons"], [])
            (root / jobs[0]["report_path"]).write_text("{}")
            with self.assertRaises(ValueError):
                summarize(manifest, root)


if __name__ == "__main__":
    unittest.main()
