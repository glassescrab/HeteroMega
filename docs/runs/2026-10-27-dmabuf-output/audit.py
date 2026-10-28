#!/usr/bin/env python3
"""Audit the retained DMA-BUF P4352 comparison evidence."""
import argparse, hashlib, json, pathlib, sys

def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def power_mode(path):
    data = json.loads(pathlib.Path(path).read_text())
    return data["devices"][0]["platforms"][0]["status"]["power_mode"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence-dir", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent)
    ap.add_argument("--output", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent / "audit.json")
    args = ap.parse_args()
    root = args.evidence_dir
    manifest = json.loads((root / "comparison_manifest.json").read_text())
    summary = json.loads((root / "comparison_summary.json").read_text())
    sources = json.loads((root / "source_manifest.json").read_text())
    checks = []
    def ok(name):
        checks.append(name)

    repo = root.parents[2]
    for rel, expected in sources["files"].items():
        require(sha(repo / rel) == expected, f"source hash changed: {rel}")
    for rel, expected in sources["evidence"].items():
        require(sha(root / rel) == expected, f"evidence hash changed: {rel}")
    ok(f"{len(sources['files'])} source hashes and {len(sources['evidence'])} evidence hashes")

    require(manifest["status"] == "completed_with_accuracy_deviations", "manifest status changed")
    require(summary["status"] == "completed_with_accuracy_deviations", "summary status changed")
    config = manifest["config"]
    require(config["npu_channels"] == [4352] and config["iterations"] == 100 and
            config["warmup"] == 5 and config["dmabuf_gpu_output"] is True and
            config["dmabuf_gpu_input"] is False and config["shared_intermediate"] is True and
            config["bfp16_native_layout"] is True and config["split_m32_a"] is True and
            config["preconvert_b"] is True and config["gpu_variant"] == "teammate",
            "selected configuration changed")
    ok("selected configuration")

    reports = {}
    fixtures = set()
    for job in manifest["jobs"]:
        evidence = job.get("evidence", {})
        require(job["status"] == "completed_with_accuracy_deviations", f"{job['id']} not completed")
        path = root / job["report_path"]
        require(path.is_file(), f"missing report {job['report_path']}")
        digest = sha(path)
        require(digest == evidence.get("report_sha256") == job.get("saved_report_sha256"),
                f"{job['id']} report hash differs")
        require(power_mode(root / job["power_before"]) == "default" and
                power_mode(root / job["power_after"]) == "default", f"{job['id']} power mode changed")
        report = json.loads(path.read_text())
        reports[job["id"]] = report
        require(report["accuracy"]["accepted"] is True and
                report["accuracy"]["accuracy_status"] == "reported_deviations",
                f"{job['id']} numerical deviation policy changed")
        fixture = tuple(report.get("native_packed_weight_sha256", [])) if job["variant"] == "native" else (
            tuple(report["original_weight_buffers"][name]["sha256"] for name in ("gate", "up", "down")))
        inputs = tuple(report.get("input_sha256", []))
        require(len(fixture) == 3 and len(inputs) == 3, f"{job['id']} fixture missing")
        fixtures.add((fixture, inputs))
        if job["variant"] == "native":
            require(report["completed_npu_dispatches"] == report["expected_npu_dispatches"] ==
                    evidence.get("completed_npu_dispatches"), f"{job['id']} native completions differ")
            require(report["accuracy"]["outside_tolerance_count"] > 0, f"{job['id']} native errors missing")
        else:
            part = report["partitions"][0]
            calls = part["completed_candidate_calls"]
            require(calls == 218 and part["completed_npu_dispatches_by_stage"] == {"swiglu": 218, "down": 218},
                    f"{job['id']} candidate completions differ")
            require(part["input_write_counts_by_stage"] == {"swiglu": [218, 1, 1], "down": [0, 1]} and
                    part["fixed_weight_upload_counts"] == {"gate": 1, "up": 1, "down": 1},
                    f"{job['id']} upload counts differ")
            require(part["gpu_output_sync_count"] == calls and part["npu"].get("gpu_output_dmabuf") is True and
                    part["npu"]["gpu_output_dmabuf_contract"]["copy_fallback"] is False,
                    f"{job['id']} DMA-BUF output evidence differs")
            require(report["original_weight_buffers_unchanged"] is True,
                    f"{job['id']} original weights changed")
            require(part["accuracy"]["outside_tolerance_count"] > 0,
                    f"{job['id']} reported deviations missing")
    require(len(fixtures) == 1, "weight/input fixtures differ across jobs")
    ok("reports, power, fixtures, dispatches and uploads")

    rows = {row["job"]: row for row in summary["ordinary"]}
    comparisons = {c["block"]: c for c in summary["comparisons"]}
    require(set(comparisons) == {0, 1}, "missing comparison block")
    for block in (0, 1):
        comp = comparisons[block]
        native = rows[comp["native_job"]]["candidate_us"]["median_us"]
        candidate = rows[comp["candidate_job"]]["candidate_us"]["median_us"]
        ratio = native / candidate
        require(abs(ratio - comp["native_over_candidate_latency_ratio"]) < 1e-12,
                f"block {block} ratio differs")
        require(candidate < native and ratio > 1.0, f"block {block} candidate did not win")
        require(comp["gpu_control_native_over_candidate"] ==
                rows[comp["native_job"]]["baseline_us"]["median_us"] /
                rows[comp["candidate_job"]]["baseline_us"]["median_us"],
                f"block {block} control ratio differs")
    ok("both reversed blocks favor the candidate")

    result = dict(passed=True, checks=checks, config=config,
        medians={row["job"]: row["candidate_us"]["median_us"] for row in summary["ordinary"]},
        ratios={block: comparisons[block]["native_over_candidate_latency_ratio"] for block in (0, 1)},
        scope=summary["claim_scope"])
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
