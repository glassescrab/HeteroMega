#!/usr/bin/env python3
"""Analyze direct-buffer GPU/NPU FFN reports without pooling separate runs.

Requires NumPy and, unless --summary-only, Matplotlib. From any directory:
    python analyze.py --results-dir results --output-dir .

Only timed ``samples`` contribute latency/stage statistics. Warmups and
validation still contribute to the recorded correctness and completion checks.
The script never executes kernels, changes tolerances, or estimates device time.
"""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import textwrap

import numpy as np


MODES = ("baseline", "serial", "concurrent")
SUCCESS = ("passed", "completed_with_accuracy_deviations")
DIAGNOSTICS = {
    "gpu_to_host": ("input_gpu_to_host_us",),
    "final_boundary_wait": ("output_stage_and_boundary_wait_us",),
    "npu_branch": ("npu", "branch_host_wall_us"),
    "swiglu_host_io": ("npu", "stages", "swiglu_with_host_io_us"),
    "down_host_io": ("npu", "stages", "down_with_host_io_us"),
    "input_layout": ("npu", "stages", "input_layout_us"),
    "down_input_layout": ("npu", "stages", "down_input_layout_us"),
    "output_layout": ("npu", "stages", "output_layout_us"),
    "swiglu_dispatch_wait": ("npu", "dispatch_wait_us", "swiglu"),
    "down_dispatch_wait": ("npu", "dispatch_wait_us", "down"),
}
ERROR_METRICS = ("relative_l2_error", "max_abs_error", "normalized_max_error",
                 "rms_error")
CAVEATS = [
    "Complete isolated prefill FFN: ready GPU input through synchronized GPU output; not whole-model prefill, TTFT, or attention interference.",
    "Each report and each partition uses its own freshly interleaved GPU baseline. Separate runs are never pooled.",
    "Only timed samples enter latency/diagnostic statistics; p10-p90 describes observed samples, not a confidence interval.",
    "Ratios are ratios of medians, baseline/concurrent or serial/concurrent; greater than one means lower concurrent latency.",
    "Diagnostic intervals are host measurements and overlap. They are not additive and do not identify device cycles or stall percentages.",
    "Original tolerance verdicts and structural acceptance remain separate. Numerical error summaries include validation, warmup, and timed checks.",
]


def stats(values, *, allow_zero=False):
    values = np.asarray(values, dtype=np.float64)
    if (values.ndim != 1 or not len(values) or not np.all(np.isfinite(values))
            or np.any(values < 0 if allow_zero else values <= 0)):
        raise ValueError("expected nonempty finite timing samples with valid sign")
    return dict(count=len(values), median_us=float(np.median(values)),
                p10_us=float(np.percentile(values, 10)),
                p90_us=float(np.percentile(values, 90)),
                min_us=float(np.min(values)), max_us=float(np.max(values)))


def error_group(checks):
    """Retain worst magnitudes and the exact source check for each metric."""
    result = dict(check_count=len(checks),
                  original_tolerance_passed=(all(x.get("passed") is True for x in checks.values()) if checks else None),
                  accepted=(all(x.get("accepted") is True for x in checks.values()) if checks else None),
                  outside_tolerance_count=sum(x.get("passed") is not True for x in checks.values()),
                  structural_failures={label: item["structural_failures"]
                      for label, item in checks.items() if item.get("structural_failures")},
                  worst={})
    for metric in ERROR_METRICS:
        observed = [(float(item[metric]), label) for label, item in checks.items()
                    if item.get(metric) is not None]
        if observed:
            value, label = max(observed)
            result["worst"][metric] = dict(value=value, check=label)
    # Keep the original fixed tolerances, including exact-zero reference cases.
    result["tolerance_settings"] = [dict(zip(("rtol", "atol", "l2_limit"), values))
        for values in sorted({tuple(item.get(k) for k in ("rtol", "atol", "l2_limit"))
                              for item in checks.values()}, key=repr)]
    return result


def categorize_checks(checks):
    groups = {name: {} for name in ("total_vs_partition_cpu", "total_vs_gpu_baseline",
                                    "npu_partial_vs_cpu", "gpu_partial_vs_cpu",
                                    "strict_gpu_baseline_vs_cpu", "unclassified")}
    suffixes = (("_partition_reference", "total_vs_partition_cpu"),
                ("_gpu_baseline", "total_vs_gpu_baseline"),
                ("_npu_partial", "npu_partial_vs_cpu"),
                ("_gpu_partial", "gpu_partial_vs_cpu"),
                ("_baseline", "strict_gpu_baseline_vs_cpu"))
    for label, item in checks.items():
        category = next((name for suffix, name in suffixes if label.endswith(suffix)),
                        "strict_gpu_baseline_vs_cpu" if "baseline_run_" in label else "unclassified")
        groups[category][label] = item
    return {name: error_group(items) for name, items in groups.items() if items}


def nested_value(item, path):
    for key in path:
        if not isinstance(item, dict) or key not in item:
            return None
        item = item[key]
    return item


def analyze_partition(entry, config):
    samples = entry.get("samples", [])
    warnings = []
    timings = {}
    for mode in MODES:
        values = [sample["wall_us"] for sample in samples if sample["mode"] == mode]
        if values:
            timings[mode] = stats(values)
            stored = entry.get("stats", {}).get(mode)
            if stored is not None and any(not np.isclose(stored[key], value, rtol=1e-12, atol=1e-9)
                                          for key, value in timings[mode].items()):
                raise ValueError(f"P={entry['npu_channels']} {mode}: stored statistics differ from raw samples")
    complete = entry.get("status") in SUCCESS and all(mode in timings for mode in MODES)
    expected_samples = config.get("iterations")
    if complete and any(item["count"] != expected_samples for item in timings.values()):
        raise ValueError(f"P={entry['npu_channels']}: sample count differs from configured iterations")

    # Diagnostic totals and nested stages overlap; retain them as parallel rows.
    diagnostics = {}
    for name, path in DIAGNOSTICS.items():
        row = {}
        for mode in ("serial", "concurrent"):
            mode_samples = [sample for sample in samples if sample["mode"] == mode]
            values = [nested_value(sample.get("diagnostics", {}), path) for sample in mode_samples]
            present = [value for value in values if value is not None]
            if present:
                row[mode] = stats(present, allow_zero=True)
                if len(present) != len(values):
                    warnings.append(f"{name}/{mode}: only {len(present)} of {len(values)} diagnostics present")
        if "serial" in row and "concurrent" in row:
            serial, concurrent = row["serial"]["median_us"], row["concurrent"]["median_us"]
            row["concurrent_minus_serial_median_us"] = concurrent - serial
            row["concurrent_over_serial_median"] = concurrent / serial if serial else None
        if row:
            diagnostics[name] = row

    completions = entry.get("completed_npu_dispatches_by_stage", {})
    expected_dispatches = 8 + 2 * (config.get("warmup", 0) + config.get("iterations", 0))
    counts_match = completions == dict(swiglu=expected_dispatches, down=expected_dispatches)
    if complete and not counts_match:
        raise ValueError(f"P={entry['npu_channels']}: completed NPU dispatch counts differ from configured work")
    checks = entry.get("correctness", {})
    all_errors = error_group(checks)
    if complete and (not checks or not all_errors["accepted"]):
        raise ValueError(f"P={entry['npu_channels']}: successful report contains missing/rejected checks")
    if complete and entry.get("status") == "passed" and not all_errors["original_tolerance_passed"]:
        raise ValueError(f"P={entry['npu_channels']}: passed status contradicts original tolerance checks")
    if complete and (entry.get("original_weight_buffers_unchanged") is not True
            or entry.get("fixed_weight_upload_counts") != dict(gate=1, up=1, down=1)):
        raise ValueError(f"P={entry['npu_channels']}: successful report lacks unchanged, once-uploaded weights")
    result = dict(npu_channels=entry["npu_channels"], gpu_channels=entry.get("gpu_channels"),
                  npu_fraction=entry.get("npu_fraction"), status=entry.get("status"),
                  complete=complete, timings=timings, diagnostics=diagnostics,
                  accuracy=all_errors, accuracy_by_comparison=categorize_checks(checks),
                  completed_npu_dispatches_by_stage=completions,
                  completed_npu_dispatches=sum(completions.values()),
                  expected_npu_dispatches_per_stage=expected_dispatches,
                  completion_count_matches_expected=counts_match,
                  fixed_weight_upload_counts=entry.get("fixed_weight_upload_counts"),
                  original_weight_buffers_unchanged=entry.get("original_weight_buffers_unchanged"),
                  warnings=warnings)
    if entry.get("error"):
        result["error"] = entry["error"]
    if complete:
        baseline = timings["baseline"]["median_us"]
        serial = timings["serial"]["median_us"]
        concurrent = timings["concurrent"]["median_us"]
        result["ratios"] = dict(baseline_over_concurrent=baseline / concurrent,
            serial_over_concurrent=serial / concurrent,
            concurrent_latency_reduction_percent=100 * (1 - concurrent / baseline),
            original_tolerance_passed=all_errors["original_tolerance_passed"],
            speedup_if_original_tolerance_passed=(baseline / concurrent
                if all_errors["original_tolerance_passed"] else None))
    return result


def analyze_report(path):
    raw = path.read_bytes()
    report = json.loads(raw)
    if report.get("schema_version") != 1 or "partitions" not in report:
        raise ValueError(f"{path}: not a current direct-partition report")
    config = report["config"]
    partitions = [analyze_partition(entry, config) for entry in report["partitions"]]
    checks = dict(report.get("correctness", {}))
    for entry in report["partitions"]:
        checks.update({f"P{entry['npu_channels']}/{label}": item
                       for label, item in entry.get("correctness", {}).items()})
    complete = [entry for entry in partitions if entry["complete"]]
    if report.get("status") in SUCCESS and (not partitions or len(complete) != len(partitions)
            or report.get("original_weight_buffers_unchanged") is not True):
        raise ValueError(f"{path}: successful report has incomplete partitions or changed weights")
    result = dict(source_file=path.name, source_sha256=sha256(raw).hexdigest(),
                  status=report.get("status"), config=config, scope=report.get("scope"),
                  boundary=report.get("boundary"), baseline=report.get("baseline"),
                  started_at_utc=report.get("provenance", {}).get("started_at_utc"),
                  accuracy=error_group(checks), accuracy_by_comparison=categorize_checks(checks),
                  original_weight_buffers_unchanged=report.get("original_weight_buffers_unchanged"),
                  completed_npu_dispatches=sum(entry["completed_npu_dispatches"] for entry in partitions),
                  partitions=partitions)
    if complete:
        fastest = min(complete, key=lambda entry: entry["timings"]["concurrent"]["median_us"])
        result["lowest_concurrent_median_partition"] = fastest["npu_channels"]
    if report.get("error"):
        result["error"] = report["error"]
    return result


def make_plot(reports, output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    reports = [report for report in reports if report["status"] in SUCCESS
               and any(entry["complete"] for entry in report["partitions"])]
    if not reports:
        return []
    colors = dict(baseline="#66727E", serial="#9661AA", concurrent="#087F8C")
    names = dict(baseline="Fresh all-GPU FFN baseline", serial="GPU + NPU, serial",
                 concurrent="GPU + NPU, concurrent")
    markers = dict(baseline="s", serial="^", concurrent="o")
    columns = min(2, len(reports))
    rows = math.ceil(len(reports) / columns)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42})
    fig, axes = plt.subplots(rows, columns, figsize=(7.4 * columns, 4.8 * rows + 1.1), squeeze=False)
    for axis, report in zip(axes.flat, reports):
        entries = sorted((entry for entry in report["partitions"] if entry["complete"]),
                         key=lambda entry: entry["npu_channels"])
        xs = np.arange(len(entries), dtype=float)
        for offset, mode in zip((-0.08, 0, 0.08), MODES):
            values = [entry["timings"][mode] for entry in entries]
            median = np.array([item["median_us"] for item in values]) / 1000
            low = np.array([item["p10_us"] for item in values]) / 1000
            high = np.array([item["p90_us"] for item in values]) / 1000
            axis.errorbar(xs + offset, median, yerr=[median - low, high - median],
                          color=colors[mode], marker=markers[mode], linewidth=1.6,
                          markersize=5.5, capsize=3, label=names[mode])
        for x, entry in zip(xs, entries):
            ratio = entry["ratios"]["baseline_over_concurrent"]
            deviation = not entry["accuracy"]["original_tolerance_passed"]
            axis.annotate(f"{ratio:.3f}×" + (" †" if deviation else ""),
                (x + 0.08, entry["timings"]["concurrent"]["p10_us"] / 1000),
                xytext=(0, -18), textcoords="offset points", ha="center",
                color="#A33A2B" if deviation else colors["concurrent"], fontsize=9)
        config = report["config"]
        title = report["source_file"].removesuffix(".json").replace("_", " ")
        axis.set_title(f"{title}\nM={config.get('m')}, H={config.get('hidden')}, I={config.get('intermediate')} · "
                       f"{config.get('iterations')} samples/mode/partition · {config.get('npu_arithmetic', '?').upper()}",
                       loc="left", fontsize=11, pad=12)
        axis.set_xticks(xs, [str(entry["npu_channels"]) for entry in entries])
        axis.set_xlabel("NPU intermediate channels P (GPU owns remaining channels)", labelpad=8)
        axis.set_ylabel("Complete FFN latency (ms)")
        axis.set_ylim(bottom=0)
        axis.set_xlim(-0.45, len(entries) - 0.55)
        axis.grid(axis="y", color="#D9DFE5", linewidth=0.6)
        axis.set_axisbelow(True)
    for axis in list(axes.flat)[len(reports):]:
        axis.set_visible(False)
    fig.suptitle("Direct-buffer GPU + NPU prefill FFN partition", fontsize=17, y=0.985)
    handles = [Line2D([], [], color=colors[mode], marker=markers[mode], label=names[mode]) for mode in MODES]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.95), ncol=3, frameon=False)
    footer = ("Dots: median; bars: p10–p90. × labels: fresh GPU median / concurrent median. "
              "Each panel is a separate run; samples are never pooled. Timing includes host staging, "
              "BO I/O, waits and partial-output reduction. Isolated FFN only; no whole-model/TTFT claim. "
              "† Original tolerance deviation.")
    fig.text(0.5, 0.017, textwrap.fill(footer, width=100 if columns == 1 else 190),
             ha="center", va="bottom", fontsize=8.5, color="#444C55")
    fig.tight_layout(rect=(0.01, 0.13 if columns == 1 else 0.075, 0.99, 0.91))
    paths = []
    for suffix in ("png", "pdf"):
        path = output_dir / f"latency_comparison.{suffix}"
        fig.savefig(path, dpi=180, facecolor="white", metadata={"Creator": "HeteroMega analyze.py"})
        paths.append(path.name)
    plt.close(fig)
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path(__file__).parent / "results")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent)
    parser.add_argument("--pattern", default="*.json", help="filename glob within results-dir")
    parser.add_argument("--plot-m", type=int, help="plot only this prefill M; retain all reports in summary")
    parser.add_argument("--summary-only", action="store_true", help="omit Matplotlib figures")
    args = parser.parse_args(argv)
    paths = sorted(args.results_dir.glob(args.pattern))
    if not paths:
        parser.error(f"no reports matching {args.pattern!r} in {args.results_dir}")
    reports, ignored = [], []
    for path in paths:
        candidate = json.loads(path.read_bytes())
        if not isinstance(candidate, dict) or "partitions" not in candidate:
            ignored.append(dict(source_file=path.name, source_sha256=sha256(path.read_bytes()).hexdigest(),
                                reason="not a partition benchmark report"))
            continue
        reports.append(analyze_report(path))
    if not reports:
        parser.error("no partition benchmark reports found among matching JSON files")
    # Preserve chronological reports when available, independent of file naming.
    reports.sort(key=lambda report: (report.get("started_at_utc") or "", report["source_file"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plotted_reports = [report for report in reports
                       if args.plot_m is None or report["config"].get("m") == args.plot_m]
    figures = [] if args.summary_only else make_plot(plotted_reports, args.output_dir)
    summary = dict(schema_version=1, analysis_source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                   numpy_version=np.__version__, caveats=CAVEATS, reports=reports, figures=figures,
                   plot_m_filter=args.plot_m, ignored_nonbenchmark_files=ignored,
                   completed_npu_dispatches_across_reports=sum(report["completed_npu_dispatches"] for report in reports))
    output = args.output_dir / "summary.json"
    output.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {output}; {len(reports)} separate reports; "
          f"{summary['completed_npu_dispatches_across_reports']} recorded NPU completions")
    return summary


if __name__ == "__main__":
    main()
