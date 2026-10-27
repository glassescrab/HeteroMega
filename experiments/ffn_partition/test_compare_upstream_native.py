"""CPU-only checks of the fresh native/direct-buffer comparison evidence gate."""

import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from experiments.ffn_partition import compare_upstream_native as driver
from experiments.ffn_partition.contract import accuracy_metrics, accuracy_summary


def arguments(directory):
    return driver.parse_args(["--native-root", "/native", "--artifact-root", "/artifacts",
        "--no-build-candidate", "--output-dir", str(directory), "--warmup", "1", "--iterations", "2"])


def metric(policy="strict", zero=False):
    x = np.zeros(2, np.float32) if zero else np.ones(2, np.float32)
    return accuracy_metrics(x, x, policy)


def fixtures():
    return dict(full_packed_weight_sha256=[c * 64 for c in "abc"],
                input_sha256=[c * 64 for c in "de"] + [driver.zero_hash()])


def native_report(args, job):
    fixture = fixtures()
    report = dict(status="passed", config=dict(m=512, hidden=4096, intermediate=14336, npu_rows=256,
        seed=12832, warmup=args.warmup, iterations=job["iterations"],
        mode="latency" if job["mode"] == "ordinary" else "diagnostic", accuracy_policy=args.native_accuracy_policy),
        correctness={}, samples=[], warmup_samples=[], native_packed_weight_sha256=fixture["full_packed_weight_sha256"],
        input_sha256=fixture["input_sha256"], completed_npu_dispatches=2 * (4 + args.warmup + job["iterations"]),
        expected_npu_dispatches=2 * (4 + args.warmup + job["iterations"]))
    for run, idx in enumerate((0, 1, 2, 0)):
        for mode in ("baseline", "native"):
            for stage in ("gate", "up", "output"):
                for owner in ("all", "gpu_rows", "npu_rows"):
                    value = metric("strict" if mode == "baseline" else args.native_accuracy_policy, zero=idx == 2)
                    value.update(numerical_passed=True, structural_passed=True, actual_sha256=(
                        driver.zero_hash(512 if owner == "all" else 256, 4096 if stage == "output" else 14336)
                        if idx == 2 else "12"[idx] * 64))
                    report["correctness"][f"run{run}_input{idx}_{mode}_{stage}_{owner}"] = value
        for stage in ("gate", "up", "output"):
            report["correctness"][f"run{run}_input{idx}_native_vs_gpu_{stage}"] = dict(
                metric(args.native_accuracy_policy, zero=idx == 2), numerical_passed=True, structural_passed=True)
    for iteration in range(-args.warmup, job["iterations"]):
        for mode in ("baseline", "native"):
            value = dict(metric("strict" if mode == "baseline" else args.native_accuracy_policy), actual_sha256="12"[iteration % 2] * 64,
                         numerical_passed=True, structural_passed=True)
            sample = dict(mode=mode, iteration=iteration, input_index=iteration % 2,
                wall_us=22000 if mode == "baseline" else 20000, correctness_passed=True,
                completed_npu_dispatches=2 if mode == "native" else 0, accuracy=value,
                output_sha256=value["actual_sha256"], accepted=True)
            report["samples" if iteration >= 0 else "warmup_samples"].append(sample)
    integrity = dict(host_packed_weight_sha256=fixture["full_packed_weight_sha256"],
        device_packed_weight_sha256=fixture["full_packed_weight_sha256"], host_input_sha256=fixture["input_sha256"],
        device_input_sha256=fixture["input_sha256"], passed=True,
        checks=dict(host_weights_match_initial=True, device_weights_match_initial=True,
                    host_inputs_match_initial=True, device_inputs_match_initial=True))
    report.update(buffer_integrity_before=copy.deepcopy(integrity), buffer_integrity_after=copy.deepcopy(integrity))
    refresh_native_accuracy(report)
    return report


def refresh_native_accuracy(report):
    report["accuracy"] = accuracy_summary([*report["correctness"].values(),
        *[s["accuracy"] for s in report["warmup_samples"] + report["samples"]]])
    report["status"] = "passed" if report["accuracy"]["passed"] else "completed_with_accuracy_deviations"


def native_deviation(report):
    value = report["correctness"]["run0_input0_native_gate_npu_rows"]
    value.update(accuracy_metrics(np.full(2, 2, np.float32), np.ones(2, np.float32), "report"), numerical_passed=False)
    refresh_native_accuracy(report)


def candidate_report(args, job):
    p = job["npu_channels"]
    fixture = fixtures()
    originals = {name: dict(k=k, n=n, bytes=k // 128 * (n // 64) * 4352, readonly=True, sha256=digest)
                 for name, k, n, digest in zip(("gate", "up", "down"), (4096, 4096, 14336),
                    (14336, 14336, 4096), fixture["full_packed_weight_sha256"])}
    report = dict(status="passed", config=dict(m=512, hidden=4096, intermediate=14336, seed=12832,
        npu_channels=str(p), warmup=args.warmup, iterations=job["iterations"], npu_arithmetic="bfp16", accuracy_policy="report"),
        npu_options=driver.selected_options("bfp16"), copy_output_bits=False, original_weight_buffers=originals,
        original_weight_buffers_after=copy.deepcopy(originals), original_weight_buffers_unchanged=True,
        input_sha256=fixture["input_sha256"], gpu_baseline_packed_weight_sha256={k: v["sha256"] for k, v in originals.items()},
        gpu_baseline=dict(backend="heteromosaic_original_gpu_packed", source_sha256={"gpu": "f" * 64}),
        correctness={f"baseline_run_{run}_input_{idx}": metric(zero=idx == 2) for run, idx in enumerate((0, 1, 2, 0))})
    part = dict(status="passed", npu_channels=p, gpu_channels=14336 - p, npu_channel_start=0, accuracy_policy="report",
        original_weight_buffers_unchanged=True, weight_buffers_after=copy.deepcopy(originals),
        gpu=copy.deepcopy(report["gpu_baseline"]), npu=dict(arithmetic="bfp16", npu_arithmetic="bfp16", compute_format="bfp16",
            weight_repacking=False, full_weight_buffers=True, full_intermediate=14336, channel_start=0, channels=p,
            columns_requested=8, worker_count=32, launches_per_run=2, host_output_readback="borrowed_until_consumed"),
        validation_runs=[], samples=[], warmup_samples=[], correctness={})
    calls = 0

    def record(mode, idx, label, **identifiers):
        nonlocal calls
        metrics = {"output": metric("strict", zero=idx == 2)} if mode == "baseline" else {
            kind: metric("strict" if kind == "gpu" else "report", zero=idx == 2) for kind in ("output", "baseline", "gpu", "npu")}
        suffixes = dict(output="partition_reference", baseline="gpu_baseline", gpu="gpu_partial", npu="npu_partial")
        for kind, value in metrics.items():
            part["correctness"][label if mode == "baseline" else label + "_" + suffixes[kind]] = value
        diagnostics = {}
        if mode != "baseline":
            calls += 1
            diagnostics = dict(npu=dict(completed_dispatches_total=2 * calls, weight_upload_counts=dict(gate=1, up=1, down=1)))
        return dict(mode=mode, input_index=idx, wall_us=22500 if mode == "baseline" else 18000,
            output_sha256=driver.zero_hash() if idx == 2 else ("34" if mode == "baseline" else "56")[idx] * 64,
            accuracy=metrics, diagnostics=diagnostics, **identifiers)

    for run, idx in enumerate((0, 1, 2, 0)):
        for mode in ("serial", "concurrent"):
            part["validation_runs"].append(record(mode, idx, f"validation_{run}_{mode}", run=run))
    for iteration in range(-args.warmup, job["iterations"]):
        for order, mode in enumerate(("baseline", "serial", "concurrent")):
            part["samples" if iteration >= 0 else "warmup_samples"].append(record(
                mode, iteration % 2, f"iteration_{iteration}_{mode}", iteration=iteration, order_index=order))
    part.update(completed_candidate_calls=calls, expected_npu_dispatches_per_stage=calls,
        completed_npu_dispatches_by_stage=dict(swiglu=calls, down=calls),
        input_write_counts_by_stage=dict(swiglu=[calls, 1, 1], down=[calls, 1]), fixed_weight_upload_counts=dict(gate=1, up=1, down=1))
    report["partitions"] = [part]
    refresh_accuracy(report)
    return report


def refresh_accuracy(report):
    part = report["partitions"][0]
    part["accuracy"] = accuracy_summary(list(part["correctness"].values()))
    report["accuracy"] = accuracy_summary([*report["correctness"].values(), *part["correctness"].values()])
    report["status"] = part["status"] = "passed" if report["accuracy"]["passed"] else "completed_with_accuracy_deviations"


class UpstreamNativeComparisonTests(unittest.TestCase):
    def test_plan_is_two_reversed_fresh_blocks_with_native_only_diagnostic(self):
        args = arguments("/output")
        args.native_diagnostic = True
        args.iron_python = "/iron/python"
        jobs = driver.build_jobs(args)
        self.assertEqual([(j["variant"], j["npu_channels"]) for j in jobs],
            [("native", None), ("upstream", 2560), ("upstream", 2816),
             ("upstream", 2816), ("upstream", 2560), ("native", None), ("native", None)])
        self.assertEqual([j["mode"] for j in jobs], ["ordinary"] * 6 + ["diagnostic"])
        for job in jobs:
            if job["variant"] == "upstream":
                self.assertIn("experiments.ffn_partition.run_upstream_partition", job["command"])
                self.assertIn("--no-build", job["command"])
                self.assertIn("/iron/python", job["command"])
                self.assertEqual(job["accuracy_policy"], "report")
            else:
                self.assertEqual(job["command"][job["command"].index("--accuracy-policy") + 1], "strict")
                self.assertEqual(job["accuracy_policy"], "strict")

    def test_native_report_policy_forwards_and_preserves_numeric_failure(self):
        args = arguments("/output")
        args.native_accuracy_policy = "report"
        job = driver.build_jobs(args)[0]
        self.assertEqual(job["command"][job["command"].index("--accuracy-policy") + 1], "report")
        report = native_report(args, job)
        native_deviation(report)
        result = driver.validate_native(report, job, args)
        self.assertFalse(result["accuracy_passed"])
        self.assertTrue(result["accuracy_accepted"])
        self.assertEqual(result["status"], "completed_with_accuracy_deviations")
        mutations = [lambda r: r["correctness"]["run0_input0_native_gate_npu_rows"].update(structural_failures=["stale"]),
            lambda r: r["correctness"]["run0_input0_baseline_gate_npu_rows"].update(accuracy_policy="report"),
            lambda r: r["correctness"]["run0_input0_baseline_gate_npu_rows"].update(
                accuracy_metrics(np.full(2, 2, np.float32), np.ones(2, np.float32), "strict"), numerical_passed=False),
            lambda r: r["samples"][1].update(output_sha256="0" * 64),
            lambda r: r["samples"][1].update(accepted=False),
            lambda r: r["samples"][1]["accuracy"].update(structural_passed=False),
            lambda r: r["buffer_integrity_after"]["device_packed_weight_sha256"].__setitem__(0, "0" * 64),
            lambda r: r.update(completed_npu_dispatches=0), lambda r: r.update(status="passed")]
        for mutation in mutations:
            bad = copy.deepcopy(report)
            mutation(bad)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                driver.validate_native(bad, job, args)
        strict = arguments("/output")
        with self.assertRaises(ValueError):
            driver.validate_native(report, driver.build_jobs(strict)[0], strict)

    def test_native_report_summary_labels_latency_without_validated_speedup(self):
        with tempfile.TemporaryDirectory() as directory:
            args = arguments(directory)
            args.native_accuracy_policy = "report"
            jobs = driver.build_jobs(args)[:2]
            for job in jobs:
                report = native_report(args, job) if job["variant"] == "native" else candidate_report(args, job)
                if job["variant"] == "native":
                    native_deviation(report)
                evidence = driver.validate_native(report, job, args) if job["variant"] == "native" else driver.validate_candidate(report, job, args)
                path = args.output_dir / job["report_path"]
                driver.save_json(path, report)
                evidence["report_sha256"] = driver.file_hash(path)
                job.update(evidence=evidence, status=report["status"], power_before_summary={"mode": "default"}, power_after_summary={"mode": "default"})
            summary = driver.summarize(dict(status="completed_with_accuracy_deviations", jobs=jobs), args.output_dir)
            self.assertFalse(summary["native_failed"])
            comparison = summary["comparisons"][0]
            self.assertEqual(comparison["comparison_kind"], "experimental_latency_with_numerical_deviations")
            self.assertFalse(comparison["native_accuracy_passed"])
            self.assertTrue(comparison["candidate_accuracy_passed"])
            self.assertIsNone(comparison["speedup_vs_native"])
            self.assertAlmostEqual(comparison["native_over_candidate_latency_ratio"], 20 / 18)
            self.assertIsNone(summary["ordinary"][0]["speedup_vs_own_gpu"])

    def test_native_requires_strict_numerics_and_actual_device_fixture_integrity(self):
        args = arguments("/output")
        job = driver.build_jobs(args)[0]
        report = native_report(args, job)
        self.assertEqual(driver.validate_native(report, job, args)["completed_npu_dispatches"], 14)
        mutations = [lambda r: r.update(status="failed"),
            lambda r: r["correctness"]["run0_input0_native_output_all"].update(structural_failures=["stale"]),
            lambda r: r["buffer_integrity_after"]["device_packed_weight_sha256"].__setitem__(0, "0" * 64),
            lambda r: r["warmup_samples"].pop(), lambda r: r["samples"][0].update(output_sha256="0" * 64),
            lambda r: r["samples"][0]["accuracy"].update(accuracy_policy="report")]
        for mutation in mutations:
            bad = copy.deepcopy(report)
            mutation(bad)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                driver.validate_native(bad, job, args)

    def test_candidate_requires_all_controls_completions_and_unchanged_buffers(self):
        args = arguments("/output")
        job = driver.build_jobs(args)[1]
        report = candidate_report(args, job)
        self.assertEqual(driver.validate_candidate(report, job, args)["fixture"], fixtures())
        mutations = [lambda r: r["config"].update(seed=0), lambda r: r.update(copy_output_bits=True),
            lambda r: r["gpu_baseline_packed_weight_sha256"].update(gate="0" * 64),
            lambda r: r["partitions"][0]["npu"].update(weight_repacking=True),
            lambda r: r["partitions"][0]["samples"][0].update(iteration=1),
            lambda r: r["partitions"][0]["validation_runs"][4].update(output_sha256="0" * 64),
            lambda r: r["partitions"][0]["samples"][2].update(output_sha256="0" * 64),
            lambda r: r["partitions"][0]["completed_npu_dispatches_by_stage"].update(down=0),
            lambda r: r["partitions"][0]["input_write_counts_by_stage"].update(down=[14, 2]),
            lambda r: r["partitions"][0]["validation_runs"][0]["accuracy"]["gpu"].update(accuracy_policy="report")]
        for mutation in mutations:
            bad = copy.deepcopy(report)
            mutation(bad)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                driver.validate_candidate(bad, job, args)

    def test_bfp_numeric_deviation_preserved_but_structural_failure_rejected(self):
        args = arguments("/output")
        job = driver.build_jobs(args)[1]
        report = candidate_report(args, job)
        value = report["partitions"][0]["validation_runs"][0]["accuracy"]["npu"]
        value.update(accuracy_metrics(np.full(2, 2, np.float32), np.ones(2, np.float32), "report"))
        refresh_accuracy(report)
        result = driver.validate_candidate(report, job, args)
        self.assertFalse(result["accuracy_passed"])
        self.assertEqual(result["status"], "completed_with_accuracy_deviations")
        value.update(structural_failures=["repeated_input_changed_output"])
        with self.assertRaises(ValueError):
            driver.validate_candidate(report, job, args)

    def test_summary_uses_raw_samples_and_blocks_failed_native_or_fixture_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            args = arguments(directory)
            jobs = driver.build_jobs(args)
            for job in jobs:
                report = native_report(args, job) if job["variant"] == "native" else candidate_report(args, job)
                evidence = driver.validate_native(report, job, args) if job["variant"] == "native" else driver.validate_candidate(report, job, args)
                report["stats"] = {"native": {"median_us": 1}}
                path = args.output_dir / job["report_path"]
                driver.save_json(path, report)
                evidence["report_sha256"] = driver.file_hash(path)
                job.update(evidence=evidence, status="passed", power_before_summary={"mode": "default"}, power_after_summary={"mode": "default"})
            manifest = dict(status="passed", jobs=jobs)
            summary = driver.summarize(manifest, args.output_dir)
            self.assertEqual(len(summary["comparisons"]), 4)
            self.assertAlmostEqual(summary["comparisons"][0]["speedup_vs_native"], 20 / 18)
            jobs[-1]["status"] = "failed"
            self.assertEqual(driver.summarize(manifest, args.output_dir)["comparisons"], [])
            jobs[-1]["status"] = "passed"
            jobs[1]["evidence"]["fixture"] = dict(fixtures(), input_sha256=["a" * 64] * 3)
            self.assertEqual(driver.summarize(manifest, args.output_dir)["comparisons"], [])
            jobs[1]["evidence"]["fixture"] = fixtures()
            jobs[0]["power_after_summary"]["mode"] = "performance"
            self.assertEqual(driver.summarize(manifest, args.output_dir)["comparisons"], [])
            (args.output_dir / jobs[0]["report_path"]).write_text("{}")
            with self.assertRaises(ValueError):
                driver.summarize(manifest, args.output_dir)

    def test_plan_only_never_opens_devices_or_starts_subprocesses(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver, "query_power") as power, patch.object(driver.subprocess, "run") as run:
            result = driver.main(["--native-root", "/native", "--artifact-root", "/artifacts", "--no-build-candidate",
                                  "--output-dir", directory, "--plan-only"])
            self.assertEqual(len(result["jobs"]), 6)
            power.assert_not_called()
            run.assert_not_called()

    def test_failed_native_retains_raw_report_hash_and_forbids_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            def failed(command, **kwargs):
                path = Path(command[command.index("--output") + 1])
                driver.save_json(path, dict(status="failed", error="strict native numerical failure", completed_npu_dispatches=2))
                return SimpleNamespace(returncode=1)
            with patch.object(driver, "query_power", return_value={"mode": "default"}), patch.object(driver.subprocess, "run", side_effect=failed):
                with self.assertRaises(SystemExit) as result:
                    driver.main(["--native-root", "/native", "--artifact-root", "/artifacts", "--no-build-candidate", "--output-dir", directory])
                self.assertEqual(result.exception.code, 1)
            manifest = json.loads((Path(directory) / "comparison_manifest.json").read_text())
            summary = json.loads((Path(directory) / "comparison_summary.json").read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["jobs"][0]["saved_report_sha256"], driver.file_hash(Path(directory) / manifest["jobs"][0]["report_path"]))
            self.assertTrue(summary["native_failed"])
            self.assertEqual(summary["comparisons"], [])


if __name__ == "__main__":
    unittest.main()
