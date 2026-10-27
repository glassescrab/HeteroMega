"""Fresh original-HeteroMosaic versus direct-weight BFP16 prefill FFN runs.

Two reversed blocks retain each implementation's own interleaved GPU control.
Native diagnostics, when requested, are a separate process and never latency.
No numerical failure of the native baseline can authorize a speedup claim.
"""

import argparse
from functools import lru_cache
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from .compare_native import validate_native as _validate_native
from .contract import accuracy_summary, benchmark_stats
from .run_upstream_partition import selected_options
from .sweep_partition import (COMPLETED_STATUSES, ROOT, comma_ints, completed_status,
                              query_power, save_json, source_hashes, utc_now)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def valid_hash(value):
    require(isinstance(value, str) and len(value) == 64 and
            all(c in "0123456789abcdef" for c in value), "missing or malformed SHA256")
    return value


@lru_cache(maxsize=8)
def zero_hash(rows=512, columns=4096):
    return sha256(bytes(rows * columns * 4)).hexdigest()


def build_jobs(args):
    variants = [("native", None), *[("upstream", p) for p in args.npu_channels]]
    schedule = [("ordinary", block, variants if block == 0 else variants[::-1]) for block in range(2)]
    if args.native_diagnostic:
        schedule.append(("diagnostic", 0, [("native", None)]))
    jobs = []
    for mode, block, ordered in schedule:
        for variant, p in ordered:
            tag = f"b{block}_{variant}" + (f"_p{p}" if p else "") + f"_{mode}"
            report_path = f"jobs/{tag}.json"
            iterations = args.iterations if mode == "ordinary" else args.diagnostic_iterations
            common = ["--m", "512", "--hidden", "4096", "--intermediate", "14336", "--seed", "12832",
                      "--warmup", str(args.warmup), "--iterations", str(iterations),
                      "--output", str(args.output_dir / report_path)]
            if variant == "native":
                command = [sys.executable, "-m", "experiments.ffn_partition.native_heteromosaic", *common,
                           "--npu-rows", "256", "--mode", "latency" if mode == "ordinary" else "diagnostic",
                           "--native-root", str(args.native_root)]
                for name in ("native_library", "driver_include"):
                    if getattr(args, name):
                        command += ["--" + name.replace("_", "-"), str(getattr(args, name))]
            else:
                command = [sys.executable, "-m", "experiments.ffn_partition.run_upstream_partition", *common,
                           "--npu-channels", str(p), "--npu-arithmetic", "bfp16", "--accuracy-policy", "report",
                           "--artifact-root", str(args.artifact_root)]
                if args.iron_python:
                    command += ["--iron-python", args.iron_python]
                if args.no_build_candidate:
                    command += ["--no-build"]
            jobs.append(dict(id=tag, variant=variant, mode=mode, block=block, npu_channels=p,
                iterations=iterations, npu_arithmetic="bfp16" if p else "native_unmodified",
                accuracy_policy="report" if p else "strict", command=command, report_path=report_path,
                log_path=f"logs/{tag}.log", status="planned", power_before=f"power/{tag}_before.json",
                power_after=f"power/{tag}_after.json"))
    return jobs


def fixture_identity(report, variant):
    """Compare the full original packed buffers, not partition-specific buffers."""
    if variant == "native":
        weights = report.get("native_packed_weight_sha256", [])
        require(len(weights) == 3, "native full packed-weight hashes missing")
    else:
        originals = report.get("original_weight_buffers", {})
        require(set(originals) == {"gate", "up", "down"}, "candidate original weights missing")
        require(report.get("original_weight_buffers_unchanged") is True and
                report.get("original_weight_buffers_after") == originals, "original weights changed")
        for name, (k, n) in dict(gate=(4096, 14336), up=(4096, 14336), down=(14336, 4096)).items():
            item = originals[name]
            require(item.get("k") == k and item.get("n") == n and item.get("readonly") is True and
                    item.get("bytes") == (k // 128) * (n // 64) * 4352, "original weight shape/layout differs")
        weights = [originals[name]["sha256"] for name in ("gate", "up", "down")]
        require(report.get("gpu_baseline_packed_weight_sha256") ==
                dict(zip(("gate", "up", "down"), weights)), "GPU/NPU original packed weights differ")
    inputs = report.get("input_sha256", [])
    require(len(inputs) == 3 and inputs[2] == zero_hash() and len(set(inputs)) == 3,
            "missing changed/zero input fixture hashes")
    for value in weights + inputs:
        valid_hash(value)
    return dict(full_packed_weight_sha256=weights, input_sha256=inputs)


def validate_metric(value, policy=None):
    require(value.get("finite") is True and all(value.get(k) == v for k, v in
            (("rtol", .03), ("atol", .05), ("l2_limit", .02))), "nonfinite or changed error tolerances")
    for key in ("max_abs_error", "relative_l2_error", "normalized_max_error", "rms_error", "reference_max_abs", "max_error_limit"):
        x = value.get(key)
        require(isinstance(x, (int, float)) and math.isfinite(x) and x >= 0, "missing finite numerical metrics")
    maximum, reference = value["max_abs_error"], value["reference_max_abs"]
    limit = .05 + .03 * reference
    require(math.isclose(value["max_error_limit"], limit, rel_tol=1e-12), "changed max-error limit")
    passed = maximum == 0 if reference == 0 else maximum <= limit and value["relative_l2_error"] <= .02
    require(value.get("passed") is passed and value.get("correctness") == ("passed" if passed else "failed"),
            "numerical verdict disagrees with original tolerances")
    require(reference != 0 or maximum == 0, "nonzero output for zero reference")
    if policy is not None:
        require(value.get("accuracy_policy") == policy and value.get("accepted") is True and
                value.get("structural_failures") == [] and
                value.get("accuracy_status") == ("within_tolerance" if passed else "reported_deviation"),
                "invalid structural acceptance or accuracy policy")
    require(passed or policy == "report", "strict native/GPU numerical validation failed")
    return passed


def validate_native(report, job, args):
    evidence = _validate_native(report, job, args)
    for metric in report["correctness"].values():
        validate_metric(metric, "strict")
        require(metric.get("numerical_passed") is True and metric.get("structural_passed") is True,
                "native numerical/structural evidence missing")
    # The native runner stores output hashes for its initial stage controls.
    for mode in ("baseline", "native"):
        for stage in ("gate", "up", "output"):
            for owner in ("all", "gpu_rows", "npu_rows"):
                hashes = [valid_hash(report["correctness"][f"run{run}_input{idx}_{mode}_{stage}_{owner}"]["actual_sha256"])
                          for run, idx in enumerate((0, 1, 2, 0))]
                require(hashes[0] == hashes[3] and hashes[0] != hashes[1], "native changed/repeat-input check failed")
                require(hashes[2] == zero_hash(512 if owner == "all" else 256, 4096 if stage == "output" else 14336),
                        "native zero output hash failed")
    warmups = report.get("warmup_samples", [])
    require(len(warmups) == 2 * args.warmup, "native warmup samples missing")
    for mode in ("baseline", "native"):
        records = [s for s in warmups if s.get("mode") == mode]
        require(sorted(s.get("iteration") for s in records) == list(range(-args.warmup, 0)), "native warmup coverage failed")
        for s in records:
            benchmark_stats([s["wall_us"]])
            require(s.get("correctness_passed") is True and s.get("input_index") == s["iteration"] % 2 and
                    s.get("completed_npu_dispatches") == (2 if mode == "native" else 0), "native warmup validation failed")
    for s in warmups + report["samples"]:
        validate_metric(s.get("accuracy", {}), "strict")
        expected = report["correctness"][f"run{s['input_index']}_input{s['input_index']}_{s['mode']}_output_all"]["actual_sha256"]
        require(s.get("output_sha256") == s["accuracy"].get("actual_sha256") == expected,
                "native timed output hash differs from initial control")
    for phase in ("before", "after"):
        integrity = report.get("buffer_integrity_" + phase, {})
        require(integrity.get("passed") is True and integrity.get("checks") == dict(
            host_weights_match_initial=True, device_weights_match_initial=True,
            host_inputs_match_initial=True, device_inputs_match_initial=True), "native buffer integrity checks missing")
        require(integrity.get("host_packed_weight_sha256") == integrity.get("device_packed_weight_sha256") ==
                report.get("native_packed_weight_sha256") and integrity.get("host_input_sha256") ==
                integrity.get("device_input_sha256") == report.get("input_sha256"), "native host/device fixture bytes changed")
    evidence["fixture"] = fixture_identity(report, "native")
    return evidence


def validate_candidate(report, job, args):
    require(report.get("status") in COMPLETED_STATUSES, "candidate report did not complete")
    expected = dict(m=512, hidden=4096, intermediate=14336, seed=12832, npu_channels=str(job["npu_channels"]),
                    warmup=args.warmup, iterations=job["iterations"], npu_arithmetic="bfp16", accuracy_policy="report")
    require(all(report.get("config", {}).get(k) == v for k, v in expected.items()), "candidate configuration differs")
    require(report.get("npu_options") == selected_options("bfp16") and report.get("copy_output_bits") is False,
            "candidate does not use the selected direct-buffer options")
    fixture = fixture_identity(report, "upstream")
    parts = report.get("partitions", [])
    require(len(parts) == 1, "each candidate process must measure exactly one partition")
    part, p = parts[0], job["npu_channels"]
    require(part.get("npu_channels") == p and part.get("gpu_channels") == 14336 - p and
            part.get("npu_channel_start") == 0 and part.get("accuracy_policy") == "report", "candidate partition differs")
    require(part.get("original_weight_buffers_unchanged") is True and
            part.get("weight_buffers_after") == report["original_weight_buffers"], "partition changed original weights")
    npu = part.get("npu", {})
    require(all(npu.get(k) == v for k, v in dict(arithmetic="bfp16", npu_arithmetic="bfp16", compute_format="bfp16",
            weight_repacking=False, full_weight_buffers=True, full_intermediate=14336, channel_start=0, channels=p,
            columns_requested=8, worker_count=32, launches_per_run=2, host_output_readback="borrowed_until_consumed").items()),
            "candidate direct-buffer/eight-column arithmetic contract differs")
    require(report.get("gpu_baseline", {}).get("backend") == "heteromosaic_original_gpu_packed" and
            part.get("gpu", {}).get("backend") == "heteromosaic_original_gpu_packed" and
            part["gpu"].get("source_sha256") == report["gpu_baseline"].get("source_sha256"), "GPU control changed")
    initial = report.get("correctness", {})
    require(set(initial) == {f"baseline_run_{i}_input_{idx}" for i, idx in enumerate((0, 1, 2, 0))}, "initial GPU controls missing")
    for metric in initial.values():
        validate_metric(metric, "strict")
    validations, warmups, samples = (part.get(k, []) for k in ("validation_runs", "warmup_samples", "samples"))
    require([(s.get("run"), s.get("input_index"), s.get("mode")) for s in validations] ==
            [(i, idx, mode) for i, idx in enumerate((0, 1, 2, 0)) for mode in ("serial", "concurrent")], "candidate probes missing")
    require(len(warmups) == 3 * args.warmup and len(samples) == 3 * job["iterations"], "candidate samples missing")
    for records, indexes in ((warmups, range(-args.warmup, 0)), (samples, range(job["iterations"]))):
        for mode in ("baseline", "serial", "concurrent"):
            require(sorted(s.get("iteration") for s in records if s.get("mode") == mode) == list(indexes), "missing/duplicate iteration")
        for iteration in indexes:
            group = [s for s in records if s["iteration"] == iteration]
            require([s.get("order_index") for s in group] == [0, 1, 2] and
                    all(s.get("input_index") == iteration % 2 for s in group), "candidate input/order coverage differs")
    seen, named, calls = {}, {}, 0
    suffixes = dict(output="partition_reference", baseline="gpu_baseline", gpu="gpu_partial", npu="npu_partial")
    for sample in validations + warmups + samples:
        benchmark_stats([sample["wall_us"]])
        mode, idx = sample["mode"], sample["input_index"]
        key = ("baseline" if mode == "baseline" else "candidate", idx)
        digest = valid_hash(sample.get("output_sha256"))
        require(key not in seen or seen[key] == digest, "output changed on repeated input or serial/concurrent mode")
        seen[key] = digest
        require(idx != 2 or digest == zero_hash(), "candidate zero output hash failed")
        label = f"validation_{sample['run']}_{mode}" if "run" in sample else f"iteration_{sample['iteration']}_{mode}"
        metrics = sample.get("accuracy", {})
        require(set(metrics) == ({"output"} if mode == "baseline" else set(suffixes)), "sample numerical checks missing")
        for kind, metric in metrics.items():
            validate_metric(metric, "strict" if mode == "baseline" or kind == "gpu" else "report")
            named[label if mode == "baseline" else label + "_" + suffixes[kind]] = metric
        if mode != "baseline":
            calls += 1
            diag = sample.get("diagnostics", {}).get("npu", {})
            require(diag.get("completed_dispatches_total") == 2 * calls and
                    diag.get("weight_upload_counts") == dict(gate=1, up=1, down=1), "candidate per-call completion/upload mismatch")
    require(seen[("candidate", 0)] != seen[("candidate", 1)], "changed input produced stale candidate output")
    if ("baseline", 0) in seen and ("baseline", 1) in seen:
        require(seen[("baseline", 0)] != seen[("baseline", 1)], "changed input produced stale GPU output")
    require(named == part.get("correctness"), "sample/named correctness evidence differs")
    expected_calls = 8 + 2 * (args.warmup + job["iterations"])
    require(calls == expected_calls == part.get("completed_candidate_calls") == part.get("expected_npu_dispatches_per_stage") and
            part.get("completed_npu_dispatches_by_stage") == dict(swiglu=calls, down=calls) and
            part.get("input_write_counts_by_stage") == dict(swiglu=[calls, 1, 1], down=[calls, 1]) and
            part.get("fixed_weight_upload_counts") == dict(gate=1, up=1, down=1), "candidate total completion/upload mismatch")
    accuracy = accuracy_summary(list(named.values()))
    overall = accuracy_summary([*initial.values(), *named.values()])
    status = "passed" if overall["passed"] else "completed_with_accuracy_deviations"
    require(part.get("accuracy") == accuracy and report.get("accuracy") == overall and
            part.get("status") == status == report.get("status"), "candidate numerical summary was relabeled")
    return dict(status=status, accuracy_passed=overall["passed"], accuracy_accepted=True, accuracy_policy="report",
                completed_npu_dispatches=2 * calls, timed_invocations=len(samples), explicit_checks=len(initial) + len(named),
                accuracy_status=overall["accuracy_status"], fixture=fixture)


def summarize(manifest, output_dir):
    rows, modes, fixtures = [], set(), []
    native_failed = any(j["variant"] == "native" and j["status"] == "failed" for j in manifest["jobs"])
    for job in manifest["jobs"]:
        if job["status"] not in COMPLETED_STATUSES:
            continue
        evidence = job["evidence"]
        path = output_dir / job["report_path"]
        require(file_hash(path) == evidence["report_sha256"], "measurement report changed after validation")
        modes.update(job.get(f"power_{boundary}_summary", {}).get("mode") for boundary in ("before", "after"))
        fixtures.append(evidence["fixture"])
        if job["mode"] != "ordinary":
            continue
        report = json.loads(path.read_text())
        samples = report["samples"] if job["variant"] == "native" else report["partitions"][0]["samples"]
        measured = "native" if job["variant"] == "native" else "concurrent"
        stats = {mode: benchmark_stats([s["wall_us"] for s in samples if s["mode"] == mode]) for mode in ("baseline", measured)}
        ratio = stats["baseline"]["median_us"] / stats[measured]["median_us"]
        rows.append(dict(job=job["id"], block=job["block"], variant=job["variant"], npu_channels=job["npu_channels"],
            accuracy_passed=evidence["accuracy_passed"], accuracy_policy=evidence["accuracy_policy"],
            baseline_us=stats["baseline"], candidate_us=stats[measured], latency_ratio_vs_own_gpu=ratio,
            speedup_vs_own_gpu=ratio if evidence["accuracy_passed"] else None, report_path=job["report_path"]))
    same_fixtures = bool(fixtures) and all(f == fixtures[0] for f in fixtures)
    same_power = len(modes) == 1 and None not in modes
    comparisons = []
    if same_fixtures and same_power and not native_failed:
        for native in (r for r in rows if r["variant"] == "native"):
            for candidate in (r for r in rows if r["variant"] == "upstream" and r["block"] == native["block"]):
                ratio = native["candidate_us"]["median_us"] / candidate["candidate_us"]["median_us"]
                comparisons.append(dict(block=native["block"], npu_channels=candidate["npu_channels"],
                    native_job=native["job"], candidate_job=candidate["job"],
                    comparison_kind="within_original_tolerance" if candidate["accuracy_passed"] else "experimental_latency_with_numerical_deviations",
                    native_over_candidate_latency_ratio=ratio, speedup_vs_native=ratio if candidate["accuracy_passed"] else None,
                    gpu_control_native_over_candidate=native["baseline_us"]["median_us"] / candidate["baseline_us"]["median_us"]))
    return dict(status=manifest["status"], ordinary=rows, comparisons=comparisons,
        native_failed=native_failed, full_packed_weights_and_inputs_match=same_fixtures, common_power_mode=same_power,
        fixture=fixtures[0] if same_fixtures else None,
        claim_scope="synthetic complete prefill FFN only; not model prefill/TTFT or pretrained accuracy",
        notes=["Raw ordinary wall samples determine medians; native diagnostics are excluded.",
               "Native and candidate use different host wrappers, with their own fresh GPU controls.",
               "Native ordinary timing has a conservative redundant readiness sync inside its binding.",
               "Power snapshots are boundary observations, not continuous clock telemetry.",
               "No native comparison is admitted after a failed native job, mismatched fixtures, or mismatched power."])


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--native-library", type=Path)
    parser.add_argument("--driver-include", type=Path)
    parser.add_argument("--npu-channels", type=comma_ints, default=[2560, 2816])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--native-diagnostic", action="store_true")
    parser.add_argument("--diagnostic-iterations", type=int, default=10)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--iron-python", default=os.environ.get("IRON_PYTHON"))
    parser.add_argument("--no-build-candidate", "--no-build", action="store_true", help="validate candidate cache without compiling")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--xrt-smi", default="/opt/xilinx/xrt/bin/xrt-smi")
    parser.add_argument("--power-device", default="0000:66:00.1")
    parser.add_argument("--required-power-mode", choices=("default", "powersaver", "balanced", "performance", "turbo"))
    parser.add_argument("--job-timeout", type=int, default=7200)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--keep-going", action="store_true", help="preserve failed evidence and continue; final exit remains nonzero")
    args = parser.parse_args(argv)
    args.seed = 12832
    if (not 1 <= args.iterations <= 1000 or not 0 <= args.warmup <= 100 or
            not 1 <= args.diagnostic_iterations <= 1000 or args.job_timeout <= 0):
        parser.error("invalid iteration/warmup/timeout bounds")
    if not all(p in (2560, 2816) for p in args.npu_channels):
        parser.error("bounded comparison supports P2560 and P2816")
    if not args.no_build_candidate and not args.iron_python:
        parser.error("provide --iron-python (or IRON_PYTHON) or --no-build-candidate")
    for name in ("native_root", "native_library", "driver_include", "artifact_root", "output_dir"):
        if getattr(args, name):
            setattr(args, name, getattr(args, name).resolve())
    return args


def main(argv=None):
    args = parse_args(argv)
    require(not args.output_dir.exists() or not any(args.output_dir.iterdir()), "use a new empty output directory")
    sources = source_hashes()
    for name in ("compare_upstream_native.py", "compare_native.py", "native_heteromosaic.py", "native_heteromosaic_bindings.cpp",
                 "run_upstream_partition.py", "upstream_npu.py"):
        path = Path(__file__).with_name(name)
        sources[str(path.relative_to(ROOT))] = file_hash(path)
    manifest = dict(schema_version=1, status="planned", started_at_utc=utc_now(),
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        source_sha256=sources, jobs=build_jobs(args),
        scope="M512/H4096/I14336 seed12832 synthetic complete FFN; two reversed fresh-process blocks",
        acceptance="native and GPU strict; direct BFP16 candidate report policy with structural hard failures")
    manifest_path = args.output_dir / "comparison_manifest.json"
    save_json(manifest_path, manifest)
    if args.plan_only:
        print(json.dumps(dict(manifest=str(manifest_path), planned_jobs=len(manifest["jobs"]))))
        return manifest
    manifest["status"] = "running"
    for job in manifest["jobs"]:
        job.update(status="running", started_at_utc=utc_now())
        save_json(manifest_path, manifest)
        print(f"Starting {job['id']}", flush=True)
        report_path = args.output_dir / job["report_path"]
        try:
            job["power_before_summary"] = query_power(args, job["power_before"])
            log_path = args.output_dir / job["log_path"]
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("w") as log:
                result = subprocess.run(job["command"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                        timeout=args.job_timeout, check=False)
            job["returncode"] = result.returncode
            require(result.returncode == 0, f"measurement exited {result.returncode}; inspect {log_path}")
            report = json.loads(report_path.read_text())
            evidence = (validate_native(report, job, args) if job["variant"] == "native" else validate_candidate(report, job, args))
            evidence["report_sha256"] = file_hash(report_path)
            if "fixture" in manifest:
                require(evidence["fixture"] == manifest["fixture"], "full packed weights or inputs differ across fresh processes")
            else:
                manifest["fixture"] = evidence["fixture"]
            job.update(evidence=evidence, status=evidence["status"])
        except Exception as error:
            job.update(status="failed", error=str(error))
        finally:
            if report_path.exists():
                job["saved_report_sha256"] = file_hash(report_path)
            if "power_before_summary" in job:
                try:
                    job["power_after_summary"] = query_power(args, job["power_after"])
                    require(job["power_before_summary"]["mode"] == job["power_after_summary"]["mode"], "power mode changed during job")
                except Exception as error:
                    job.update(status="failed", power_error=str(error))
            job["finished_at_utc"] = utc_now()
            save_json(manifest_path, manifest)
        print(json.dumps(dict(job=job["id"], status=job["status"], error=job.get("error"))), flush=True)
        if job["status"] not in COMPLETED_STATUSES and not args.keep_going:
            break
    status = "failed" if any(job["status"] == "failed" for job in manifest["jobs"]) else completed_status(manifest["jobs"])
    manifest.update(status=status, finished_at_utc=utc_now())
    save_json(manifest_path, manifest)
    save_json(args.output_dir / "comparison_summary.json", summarize(manifest, args.output_dir))
    if manifest["status"] not in COMPLETED_STATUSES:
        raise SystemExit(1)
    return manifest


if __name__ == "__main__":
    main()
