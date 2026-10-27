#!/usr/bin/env python3
"""Recompute host telemetry from the fresh faithful-comparison raw reports.

Uses Python's standard library only. Samples exclude warmup and validation.
Nested host spans and GPU/NPU overlap are explicitly not additive device time.
Run from any directory; --root may name an extracted faithful_comparison tree.
"""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics


HERE = Path(__file__).resolve().parent


def stats(values):
    values = sorted(float(v) for v in values)
    if not values or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("host intervals must be nonempty, finite and nonnegative")

    def percentile(q):
        index = (len(values) - 1) * q
        lo, hi = math.floor(index), math.ceil(index)
        return values[lo] + (values[hi] - values[lo]) * (index - lo)

    return dict(count=len(values), median=statistics.median(values),
                p10=percentile(.1), p90=percentile(.9),
                mean=statistics.mean(values), minimum=values[0], maximum=values[-1])


def candidate_sample(sample):
    d = sample["diagnostics"]
    npu = d["npu"]
    stage, waits = npu["stages"], npu["dispatch_wait_us"]
    result = dict(wall_us=sample["wall_us"],
        input_gpu_to_host_us=d["input_gpu_to_host_us"],
        output_stage_and_boundary_wait_us=d["output_stage_and_boundary_wait_us"],
        npu_branch_host_wall_us=npu["branch_host_wall_us"],
        input_layout_us=stage["input_layout_us"],
        down_input_layout_us=stage["down_input_layout_us"],
        output_layout_us=stage["output_layout_us"])
    for name in ("swiglu", "down"):
        result[name + "_dispatch_wait_us"] = waits[name]
        result[name + "_with_host_io_us"] = stage[name + "_with_host_io_us"]
        # Compute each residual before summarizing; a difference of medians
        # would not preserve the same per-invocation interval relationship.
        result[name + "_host_io_outside_wait_us"] = stage[name + "_with_host_io_us"] - waits[name]
    return result


def summarize_samples(samples, extractor):
    rows = [extractor(s) for s in samples]
    if not rows:
        raise ValueError("missing samples")
    return {name: stats(row[name] for row in rows) for name in rows[0]}


def analyze(root):
    manifest_raw = (root / "comparison_manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    result = dict(schema_version=1, units="microseconds unless field explicitly says ratio",
        source_manifest_sha256=sha256(manifest_raw).hexdigest(),
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        scope="Only fresh faithful_comparison jobs; timed samples only, excluding warmup and validation invocations.",
        semantics={
            "wall_us": "Complete ready-GPU-input to synchronized-GPU-output FFN host latency.",
            "native_wrapper_overhead_us": "Per-sample outer wall_us minus binding_wall_us; includes Python/binding overhead and the binding's redundant readiness sync.",
            "native_diagnostic": "Separate synchronized stage run: gate_up includes both native futures plus GPU completion, followed by GPU pointwise and full GPU down. Not ordinary timing or isolated NPU cycles.",
            "npu_branch_host_wall_us": "Candidate host interval covering both launches, BO I/O and layouts. Excludes the preceding finite-input scan; outer wall includes that scan.",
            "dispatch_wait_us": "Host XRT launch plus blocking completion wait, including device work, transfers, stalls and runtime. Not device cycles.",
            "host_io_outside_wait_us": "Per-sample with_host_io_us minus its contained dispatch_wait_us: surrounding BO write/sync/read host work. Not measured DRAM bandwidth.",
            "output_stage_and_boundary_wait_us": "CPU copy to pinned staging, H2D, GPU output sum and any unfinished GPU suffix. Cannot identify transfer cost or GPU compute alone.",
            "nonadditivity": "NPU stages nest within branch_host_wall, while GPU work overlaps the NPU branch. Do not sum nested intervals or stage medians into device latency. Concurrent-minus-serial changes are descriptive, not causal attribution."},
        jobs=[], candidate_overlap_comparisons=[])
    for job in manifest["jobs"]:
        path = root / job["report_path"]
        raw = path.read_bytes()
        digest = sha256(raw).hexdigest()
        if digest != job["evidence"]["report_sha256"]:
            raise ValueError("raw report hash differs from manifest: " + job["report_path"])
        report = json.loads(raw)
        item = {key: job[key] for key in ("id", "variant", "mode", "block", "npu_channels", "report_path")}
        item.update(report_sha256=digest, status=report["status"],
                    numerical_passed=job["evidence"]["accuracy_passed"],
                    acceptance=job["evidence"]["accuracy_policy"], modes={})
        if job["variant"] == "native":
            for mode in ("baseline", "native"):
                samples = [s for s in report["samples"] if s["mode"] == mode]

                def extract(sample):
                    row = dict(wall_us=sample["wall_us"], binding_wall_us=sample["binding_wall_us"],
                        native_wrapper_overhead_us=sample["wall_us"] - sample["binding_wall_us"])
                    if job["mode"] == "diagnostic":
                        row.update({name + "_synchronized_host_us": value
                                    for name, value in sample["stages_host_us"].items()})
                    return row

                item["modes"][mode] = summarize_samples(samples, extract)
        else:
            if job["mode"] != "ordinary" or len(report["partitions"]) != 1:
                raise ValueError("unexpected candidate report geometry")
            samples = report["partitions"][0]["samples"]
            for mode in ("baseline", "serial", "concurrent"):
                selected = [s for s in samples if s["mode"] == mode]
                item["modes"][mode] = summarize_samples(selected,
                    (lambda s: {"wall_us": s["wall_us"]}) if mode == "baseline" else candidate_sample)
            # Match iterations/inputs; the two calls are separate observations
            # and may differ in order, interference, clocks and host scheduling.
            serial = {s["iteration"]: s for s in samples if s["mode"] == "serial"}
            pairs = []
            for concurrent in (s for s in samples if s["mode"] == "concurrent"):
                control = serial[concurrent["iteration"]]
                if concurrent["input_index"] != control["input_index"]:
                    raise ValueError("serial/concurrent paired inputs differ")
                c, s = candidate_sample(concurrent), candidate_sample(control)
                pairs.append({key + "_ratio": c[key] / s[key] for key in
                    ("wall_us", "npu_branch_host_wall_us", "swiglu_dispatch_wait_us", "down_dispatch_wait_us")})
            result["candidate_overlap_comparisons"].append(dict(job=job["id"],
                label="Concurrent/serial ratios paired by iteration; descriptive host intervals, not device slowdown attribution.",
                ratios={key: stats(row[key] for row in pairs) for key in pairs[0]}))
        result["jobs"].append(item)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=HERE / "results/faithful_comparison")
    parser.add_argument("--output", type=Path, default=HERE / "analysis.json")
    args = parser.parse_args()
    result = analyze(args.root)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    for job in result["jobs"]:
        print(job["id"], {mode: {key: round(value["median"], 3) for key, value in fields.items()}
                         for mode, fields in job["modes"].items()})


if __name__ == "__main__":
    main()
