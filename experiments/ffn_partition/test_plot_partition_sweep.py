"""CPU checks for evidence eligibility and timing interpretation, not rendering."""

import json
import copy
from pathlib import Path
import tempfile
import unittest

try:
    from .plot_partition_sweep import (_groups, _label, collect, extract_report,
                                      render, repeat_comparison, statistics, write_tables)
except ImportError:
    from plot_partition_sweep import (_groups, _label, collect, extract_report,
                                     render, repeat_comparison, statistics, write_tables)


RESULTS = Path(__file__).with_name("results")


def ordinary():
    return json.loads((RESULTS/"array8_default_m512_p512_hx370.json").read_text())


def bfp_fixture(mode="ordinary"):
    # Shared synthetic validation schema; no modified fixture is hardware data.
    from experiments.ffn_partition.test_sweep_partition import SweepTests
    return SweepTests().bfp_report(mode)


def swiglu_fixture():
    """Synthetic parser fixture only; never save or present as hardware data."""
    metadata = {"fuse_gate_up": True, "fuse_swiglu": True, "launches_per_run": 2,
                "fixed_weight_uploads": 2, "cpu_activation_fallback": False,
                "artifacts": {"swiglu": {}, "down": {}}}
    npu = {"dispatch_wait_us": {"swiglu": 1000, "down": 500},
           "weight_upload_counts": {"swiglu": 1, "down": 1},
           "completed_dispatches_total": 2, "branch_host_wall_us": 2000,
           "stages": {"swiglu_with_host_io_us": 1200, "down_with_host_io_us": 600,
                      "input_layout_us": 100, "down_input_layout_us": 20, "output_layout_us": 80}}
    sample = {"correctness_passed": True, "instrumented_wall_us": 2400,
              "gpu_event_intervals": {name: {"duration_us": 100}
                                      for name in ("gate", "up", "silu", "multiply", "down",
                                                   "input_d2h", "output_h2d", "reduction")},
              "gpu_stage_submit_host": {"gate": {"duration_us": 10}},
              "npu_submit_wait_host": {stage: {"submit_host_us": 10, "wait_host_us": duration - 10}
                                       for stage, duration in npu["dispatch_wait_us"].items()}, "npu": npu}
    return {"status": "passed", "config": {"m": 128, "hidden": 256, "intermediate": 512,
            "npu_channels": 128, "npu_design": "array8", "fuse_swiglu": True},
            "samples": [sample], "npu_metadata": metadata,
            "npu_stage_sequence": ["swiglu", "down"],
            "completed_npu_dispatches": 2, "expected_npu_dispatches": 2}


class PlotEvidenceTests(unittest.TestCase):
    def test_bfp_deviations_require_opt_in_and_keep_latency_ratios_separate(self):
        for mode in ("ordinary", "diagnostic"):
            fixture = bfp_fixture(mode)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                extract_report(fixture, "CPU_ONLY_BFP_FIXTURE.json")
            ordinary_rows, diagnostic_rows = extract_report(
                fixture, "CPU_ONLY_BFP_FIXTURE.json", allow_accuracy_deviations=True)
            row = (ordinary_rows or diagnostic_rows)[0]
            self.assertEqual(row["npu_arithmetic"], "bfp16")
            self.assertFalse(row["accuracy_passed"])
            self.assertEqual(row["accuracy_status"], "reported_deviations")
            self.assertIn("BFP16", _label(_groups([row])[0][0]))
            self.assertIn("numerical deviations", _label(_groups([row])[0][0]))
            if mode == "ordinary":
                self.assertIsNone(row["speedup"])
                self.assertIsNone(row["paired_speedup"])
                self.assertGreater(row["latency_ratio"], 1)

    def test_bfp_opt_in_cannot_bypass_execution_or_strict_gpu_guards(self):
        for mutate in (
            lambda r: r["partitions"][0]["completed_npu_dispatches_by_stage"].update(down=0),
            lambda r: r["partitions"][0]["samples"][0]["accuracy"].update(structural_failures=["distinct_inputs_identical_output"]),
            lambda r: r["correctness"]["baseline_input_0"].update(accuracy_policy="report"),
        ):
            fixture = bfp_fixture()
            mutate(fixture)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                extract_report(fixture, "CPU_ONLY_BFP_FIXTURE.json", allow_accuracy_deviations=True)

    def test_arithmetic_and_accuracy_status_are_distinct_plot_series(self):
        bf16 = extract_report(ordinary(), "observed.json", "same_run")[0][0]
        bfp = extract_report(bfp_fixture(), "CPU_ONLY_BFP_FIXTURE.json", "same_run",
                             allow_accuracy_deviations=True)[0][0]
        within = dict(bfp, accuracy_passed=True, accuracy_status="within_tolerance")
        groups = _groups([bf16, bfp, within])
        self.assertEqual(len(groups), 3)
        self.assertTrue(all(len(rows) == 1 for _, rows in groups))

    def test_bfp_manifest_collection_and_export_do_not_relabel_deviations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "report.json").write_text(json.dumps(bfp_fixture()))
            manifest = {"jobs": [{"report_path": "report.json", "status": "completed_with_accuracy_deviations",
                                  "npu_arithmetic": "bfp16", "accuracy_policy": "report"}]}
            (root / "sweep_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "no eligible"):
                collect([root])
            summary = collect([root], allow_accuracy_deviations=True)
            self.assertEqual(len(summary["ordinary"]), 1)
            write_tables(summary, root / "tables")
            exported = json.loads((root / "tables/summary.json").read_text())["ordinary"][0]
            self.assertIsNone(exported["speedup"])
            self.assertEqual(exported["accuracy_status"], "reported_deviations")
            csv_text = (root / "tables/ordinary.csv").read_text()
            self.assertIn("latency_ratio", csv_text)
            self.assertIn("reported_deviations", csv_text)

    def test_bfp_svg_labels_experimental_latency_and_preserves_null_speedup(self):
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            self.skipTest("matplotlib unavailable")
        rows, stages = extract_report(bfp_fixture(), "CPU_ONLY_BFP_FIXTURE.json",
                                      allow_accuracy_deviations=True)
        summary = {"ordinary": rows, "diagnostic": stages}
        with tempfile.TemporaryDirectory() as directory:
            paths = render(summary, directory, formats=("svg",))
            svg = Path(paths[0]).read_text()
            self.assertIn("BFP16", svg)
            self.assertIn("numerical deviations", svg)
            self.assertIn("Matched GPU-only / candidate latency", svg)
            self.assertIsNone(summary["sampled_best"][0]["speedup"])

    def test_raw_sample_statistics_and_matched_pairing(self):
        report = ordinary()
        # Cached summaries must not override actual samples.
        report["partitions"][0]["stats"]["baseline"]["median_us"] = 1
        rows, diagnostics = extract_report(report, "observed.json")
        self.assertFalse(diagnostics)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["timing_ms"]["baseline"]["median"], 22.208414)
        self.assertEqual(rows[0]["paired_wins"], 50)
        self.assertAlmostEqual(rows[0]["speedup"], 1.087333856704182)

    def test_reject_failed_or_unpaired_samples(self):
        report = ordinary()
        report["partitions"][0]["samples"][0]["correctness_passed"] = False
        with self.assertRaises(ValueError):
            extract_report(report, "failed.json")
        report = ordinary()
        report["partitions"][0]["samples"].pop(0)
        with self.assertRaises(ValueError):
            extract_report(report, "unpaired.json")

    def test_diagnostic_preserves_clock_and_nested_interval_categories(self):
        report = json.loads((RESULTS/"timeline_m512_p512_array8.json").read_text())
        rows, diagnostics = extract_report(report, "timeline.json")
        self.assertFalse(rows)
        metrics = diagnostics[0]["metrics_ms"]
        self.assertAlmostEqual(metrics["gpu_event"]["reduction"]["median"], .13291800022125244)
        self.assertAlmostEqual(metrics["npu_wait"]["gate"]["median"], 4.3587465)
        self.assertGreater(metrics["npu_stage_host_io"]["gate"]["median"],
                           metrics["npu_wait"]["gate"]["median"])
        report["config"]["fuse_gate_up"] = True  # labels cannot relabel a four-launch measurement
        with self.assertRaises(ValueError):
            extract_report(report, "mislabeled_fused.json")

    def test_manifest_failure_and_hash_tampering_exclude_raw_passed_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = ordinary()
            for name in ("good", "failed_power", "tampered"):
                (root/(name+".json")).write_text(json.dumps(report))
            power = {"devices": [{"platforms": [{"status": {"power_mode": "default"}}]}]}
            for when in ("before", "after"):
                (root/(when+".json")).write_text(json.dumps(power))
            base = dict(power_before="before.json", power_after="after.json", status="passed")
            jobs = [dict(base, report_path="good.json"),
                    dict(base, report_path="failed_power.json", status="failed"),
                    dict(base, report_path="tampered.json", evidence={"report_sha256": "bad"})]
            (root/"sweep_manifest.json").write_text(json.dumps({"jobs": jobs}))
            summary = collect([root])
            self.assertEqual(len(summary["ordinary"]), 1)
            self.assertEqual(summary["ordinary"][0]["power"]["mode"], "default")
            self.assertEqual(len(summary["ignored_inputs"]), 2)

    def test_repeated_reports_are_not_pooled(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("first", "repeat"):
                (root/(name+".json")).write_text(json.dumps(ordinary()))
            summary = collect([root])
            self.assertEqual(len(summary["ordinary"]), 2)
            self.assertEqual(len({row["series"] for row in summary["ordinary"]}), 2)
            self.assertTrue(all(row["paired_count"] == 50 for row in summary["ordinary"]))

    def test_quantiles_and_nonfinite_values(self):
        values = statistics([1, 2, 3, 4])
        self.assertEqual(values["median"], 2.5)
        self.assertAlmostEqual(values["p10"], 1.3)
        self.assertAlmostEqual(values["p90"], 3.7)
        for bad in ([], [-1], [float("inf")], [float("nan")]):
            with self.assertRaises(ValueError):
                statistics(bad)

    def test_repeat_runs_keep_samples_independent_and_sort_by_start(self):
        # Reuse observed durations with synthetic labels/timestamps solely as
        # a grouping fixture; no new hardware measurement is asserted/saved.
        report = json.loads((RESULTS/"array8_m512_h4096_i14336_hx370.json").read_text())
        rows, _ = extract_report(report, "observed.json", "first")
        rows = [r for r in rows if r["npu_channels"] in (128, 512)]
        for i, row in enumerate(rows):
            row["fused"] = True
            row["started_utc"] = f"2026-10-18T10:0{i}:00+00:00"
        later = copy.deepcopy(rows)
        for i, row in enumerate(later):
            row["series"] = "second"
            row["started_utc"] = f"2026-10-18T11:0{1-i}:00+00:00"
        comparison = repeat_comparison({"ordinary": later+rows}, [128, 512])
        self.assertEqual([r["series"] for r in comparison["runs"]], ["first", "second"])
        self.assertEqual([r["candidate_order"] for r in comparison["runs"]], [[128, 512], [512, 128]])
        self.assertTrue(all(row["timing_ms"]["concurrent"]["count"] == 20
                            for run in comparison["runs"] for row in run["candidates"]))
        self.assertEqual(len(comparison["runs"]), 2)

    def test_repeat_comparison_excludes_missing_candidate_or_timestamp(self):
        report = json.loads((RESULTS/"array8_m512_h4096_i14336_hx370.json").read_text())
        rows, _ = extract_report(report, "observed.json", "fixture")
        for row in rows:
            row["fused"] = True
        incomplete = repeat_comparison({"ordinary": rows[:1]}, [128, 512])
        self.assertFalse(incomplete["runs"])
        rows[0]["started_utc"] = None
        missing_time = repeat_comparison({"ordinary": rows}, [128, 512])
        self.assertFalse(missing_time["runs"])
        with self.assertRaises(ValueError):
            repeat_comparison({"ordinary": rows}, [512, 512])

    def test_swiglu_is_distinct_and_has_comparable_complete_frontend(self):
        fixture = swiglu_fixture()
        _, rows = extract_report(fixture, "CPU_ONLY_FIXTURE.json", "fixture")
        row = rows[0]
        self.assertTrue(row["fuse_swiglu"])
        self.assertTrue(row["fused"])  # SwiGLU implies gate/up fusion.
        key, _ = _groups(rows)[0]
        self.assertEqual(key[2], "swiglu")
        self.assertIn("On-chip NPU SwiGLU", _label(key))
        self.assertEqual(set(row["metrics_ms"]["npu_stage_host_io"]), {"swiglu", "down"})
        self.assertAlmostEqual(row["metrics_ms"]["npu_frontend_stage_host_io"]["swiglu"]["median"], 1.2)
        self.assertAlmostEqual(row["metrics_ms"]["npu_frontend_wait"]["swiglu"]["median"], .99)
        self.assertNotIn("gate_up", row["metrics_ms"]["npu_stage_host_io"])
        # Earlier paths need gate+up+pointwise, summed per invocation before
        # aggregation, to compare the same work with the single fused launch.
        old = json.loads((RESULTS/"timeline_m512_p512_array8.json").read_text())
        _, old_rows = extract_report(old, "observed.json")
        expected = statistics([sum(s["npu"]["stages"][key+"_with_host_io_us"]
                                    for key in ("gate", "up", "silu_mul"))/1000
                               for s in old["samples"]])
        self.assertEqual(old_rows[0]["metrics_ms"]["npu_frontend_stage_host_io"]["swiglu"], expected)

    def test_swiglu_rejects_mislabeled_runners_and_incomplete_counters(self):
        for fault in ("three_launches", "missing_stage", "extra_submit", "reupload", "count", "metadata_flag"):
            fixture = swiglu_fixture()
            if fault == "three_launches":
                fixture["npu_metadata"]["launches_per_run"] = 3
            elif fault == "missing_stage":
                del fixture["samples"][0]["npu"]["dispatch_wait_us"]["swiglu"]
            elif fault == "extra_submit":
                fixture["samples"][0]["npu_submit_wait_host"]["silu_mul"] = {"submit_host_us": 1, "wait_host_us": 1}
            elif fault == "reupload":
                fixture["samples"][0]["npu"]["weight_upload_counts"]["swiglu"] = 2
            elif fault == "count":
                fixture["completed_npu_dispatches"] = 4
            else:
                fixture["npu_metadata"]["fuse_swiglu"] = False
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                extract_report(fixture, "CPU_ONLY_FIXTURE.json")
        fixture = swiglu_fixture()
        fixture["samples"].append(copy.deepcopy(fixture["samples"][0]))
        with self.assertRaisesRegex(ValueError, "advance by two"):
            extract_report(fixture, "CPU_ONLY_FIXTURE.json")

    def test_ordinary_swiglu_requires_actual_two_stage_evidence(self):
        fixture = swiglu_fixture()
        npu = fixture["samples"][0]["npu"]
        report = {"status": "passed", "config": fixture["config"],
                  "partitions": [{"npu_channels": 128, "npu": fixture["npu_metadata"],
                    "samples": [{"iteration": 0, "mode": "baseline", "wall_us": 3000,
                                 "correctness_passed": True},
                                {"iteration": 0, "mode": "concurrent", "wall_us": 2400,
                                 "correctness_passed": True, "diagnostics": {"npu": npu}}]}]}
        rows, _ = extract_report(report, "CPU_ONLY_FIXTURE.json")
        self.assertEqual(_groups(rows)[0][0][2], "swiglu")
        self.assertFalse(repeat_comparison({"ordinary": rows}, [128, 256])["runs"])
        del report["partitions"][0]["samples"][1]["diagnostics"]
        with self.assertRaises(ValueError):
            extract_report(report, "CPU_ONLY_FIXTURE.json")

    def test_fusion_variants_do_not_merge_within_one_series(self):
        row = extract_report(ordinary(), "observed.json", "same_run")[0][0]
        fused = dict(row, fused=True)
        swiglu = dict(row, fused=True, fuse_swiglu=True)
        groups = _groups([row, swiglu, fused])
        self.assertEqual([key[2] for key, _ in groups], ["unfused", "fused", "swiglu"])
        self.assertTrue(all(len(rows) == 1 for _, rows in groups))


if __name__ == "__main__":
    unittest.main()
