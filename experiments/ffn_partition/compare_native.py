"""Run fresh W4A16 native HeteroMosaic and channel-partition FFN comparisons.

Ordinary latency and synchronized native diagnostics run in separate processes.
No historical timings enter this comparison. NPU power is observed, not changed.
Use --plan-only to prepare commands without importing Torch or opening devices.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from .contract import benchmark_stats, validate_shape
from .sweep_partition import (COMPLETED_STATUSES, ROOT, candidate_accuracy, comma_ints,
                              completed_status, query_power, save_json, source_hashes,
                              utc_now, validate_report)


def build_jobs(args):
    jobs = []
    arithmetic, policy = candidate_accuracy(args)
    variants = [("native", None), *[("swiglu", p) for p in args.npu_channels]]
    schedules = [("ordinary", b, variants if b % 2 == 0 else variants[::-1])
                 for b in range(args.blocks)]
    schedules.append(("diagnostic", 0, variants))
    for mode, block, ordered in schedules:
        for variant, p in ordered:
            tag = f"b{block}_{variant}" + (f"_p{p}" if p else "") + f"_{mode}"
            if variant != "native" and arithmetic == "bfp16":
                tag += "_bfp16"
            iterations = args.iterations if mode == "ordinary" else args.diagnostic_iterations
            report_path = f"jobs/{tag}.json"
            common = ["--m", "512", "--hidden", "4096", "--intermediate", "14336",
                      "--seed", str(args.seed), "--warmup", str(args.warmup),
                      "--iterations", str(iterations), "--output", str(args.output_dir / report_path)]
            if variant == "native":
                command = [sys.executable, "-m", "experiments.ffn_partition.native_heteromosaic",
                           *common, "--npu-rows", "256", "--mode",
                           "latency" if mode == "ordinary" else "diagnostic",
                           "--native-root", str(args.native_root)]
                if args.native_library:
                    command += ["--native-library", str(args.native_library)]
                if args.driver_include:
                    command += ["--driver-include", str(args.driver_include)]
            else:
                module = "run" if mode == "ordinary" else "profile_timeline"
                command = [sys.executable, "-m", f"experiments.ffn_partition.{module}",
                           *common, "--npu-channels", str(p), "--npu-design", "array8",
                           "--columns", "8", "--fuse-swiglu", "--artifact-root", str(args.artifact_root),
                           "--npu-arithmetic", arithmetic, "--accuracy-policy", policy]
                if args.iron_python:
                    command += ["--iron-python", args.iron_python]
            jobs.append(dict(id=tag, variant=variant, mode=mode, block=block, m=512,
                             npu_channels=p, fuse_gate_up=True, fuse_swiglu=True,
                             npu_arithmetic=arithmetic if variant != "native" else "native_unmodified",
                             accuracy_policy=policy if variant != "native" else "strict",
                             iterations=iterations, command=command, report_path=report_path,
                             log_path=f"logs/{tag}.log", status="planned",
                             power_before=f"power/{tag}_before.json",
                             power_after=f"power/{tag}_after.json"))
    return jobs


def validate_native(report, job, args):
    if report.get("status") != "passed":
        raise ValueError("native report did not pass; no speedup claim is permitted")
    expected = dict(m=512, hidden=4096, intermediate=14336, npu_rows=256,
                    seed=args.seed, warmup=args.warmup, iterations=job["iterations"],
                    mode="latency" if job["mode"] == "ordinary" else "diagnostic")
    if any(report.get("config", {}).get(k) != v for k, v in expected.items()):
        raise ValueError("native configuration differs from the planned comparison")
    required_checks = set()
    for repetition, index in enumerate((0, 1, 2, 0)):
        prefix = f"run{repetition}_input{index}_"
        required_checks.update(prefix + f"{mode}_{stage}_{owner}"
                               for mode in ("baseline", "native") for stage in ("gate", "up", "output")
                               for owner in ("all", "gpu_rows", "npu_rows"))
        required_checks.update(prefix + f"native_vs_gpu_{stage}" for stage in ("gate", "up", "output"))
    checks = report.get("correctness", {})
    if not required_checks.issubset(checks) or not all(c.get("passed") is True for c in checks.values()):
        raise ValueError("missing or failed native numerical checks")
    if any(any(checks[name].get(key) != value for key, value in
               (("rtol", 0.03), ("atol", 0.05), ("l2_limit", 0.02), ("finite", True)))
           for name in required_checks):
        raise ValueError("native correctness thresholds differ from the fixed contract")
    samples = report.get("samples", [])
    if len(samples) != 2 * job["iterations"]:
        raise ValueError("native report must include its interleaved GPU control")
    for mode in ("baseline", "native"):
        selected = [s for s in samples if s.get("mode") == mode]
        if sorted(s.get("iteration", -1) for s in selected) != list(range(job["iterations"])):
            raise ValueError("missing or duplicate native iteration")
        benchmark_stats([s["wall_us"] for s in selected])
    if not all(s.get("correctness_passed") is True and
               s.get("input_index") == s["iteration"] % 2 for s in samples):
        raise ValueError("native timed samples lack alternating-input correctness")
    completed = report.get("completed_npu_dispatches", 0)
    expected_count = 2 * (4 + args.warmup + job["iterations"])
    if completed != expected_count or completed != report.get("expected_npu_dispatches"):
        raise ValueError("native successful NPU completion evidence is missing")
    if not all(s.get("completed_npu_dispatches") == (2 if s["mode"] == "native" else 0) for s in samples):
        raise ValueError("native sample did not complete exactly its two NPU calls")
    return dict(completed_npu_dispatches=completed, timed_invocations=len(samples),
                explicit_checks=len(checks), status="passed", accuracy_policy="strict",
                accuracy_passed=True, accuracy_accepted=True, accuracy_status="within_tolerance")


def validate_candidate(path, job, args):
    evidence = validate_report(path, job, args)
    report = json.loads(path.read_text())
    if job["mode"] == "ordinary":
        samples = report["partitions"][0]["samples"]
        groups = [[s for s in samples if s["mode"] == mode] for mode in ("baseline", "serial", "concurrent")]
    else:
        groups = [report["samples"]]
    for group in groups:
        if sorted(s.get("iteration", -1) for s in group) != list(range(job["iterations"])):
            raise ValueError("missing or duplicate candidate iteration")
        key = "wall_us" if job["mode"] == "ordinary" else "instrumented_wall_us"
        benchmark_stats([s[key] for s in group])
    return evidence


def summarize(manifest, output_dir):
    """Recompute ordinary medians from raw samples; never turn diagnostics into latency."""
    rows = []
    for job in manifest["jobs"]:
        if job["status"] not in COMPLETED_STATUSES or job["mode"] != "ordinary":
            continue
        path = output_dir / job["report_path"]
        if sha256(path.read_bytes()).hexdigest() != job["evidence"]["report_sha256"]:
            raise ValueError("measurement report changed after verification")
        report = json.loads(path.read_text())
        samples = report["samples"] if job["variant"] == "native" else report["partitions"][0]["samples"]
        candidate_mode = "native" if job["variant"] == "native" else "concurrent"
        stats = {mode: benchmark_stats([s["wall_us"] for s in samples if s["mode"] == mode])
                 for mode in ("baseline", candidate_mode)}
        accuracy_passed = job["status"] == "passed"
        ratio = stats["baseline"]["median_us"] / stats[candidate_mode]["median_us"]
        rows.append(dict(block=job["block"], variant=job["variant"], npu_channels=job["npu_channels"],
                         npu_arithmetic=job.get("npu_arithmetic", "native_unmodified" if job["variant"] == "native" else "bf16"),
                         accuracy_policy=job.get("accuracy_policy", "strict"), accuracy_passed=accuracy_passed,
                         accuracy_status="within_tolerance" if accuracy_passed else "reported_deviations",
                         baseline_us=stats["baseline"], candidate_us=stats[candidate_mode],
                         latency_ratio_vs_own_gpu=ratio,
                         speedup_vs_own_gpu=ratio if accuracy_passed else None,
                         report_path=job["report_path"]))
    comparisons = []
    # A common observed power mode is required even if each individual job passes.
    modes = {job.get("power_before_summary", {}).get("mode") for job in manifest["jobs"]
             if job["status"] in COMPLETED_STATUSES}
    same_power = len(modes) == 1 and None not in modes
    if same_power:
        for native in [r for r in rows if r["variant"] == "native"]:
            for candidate in [r for r in rows if r["variant"] == "swiglu" and r["block"] == native["block"]]:
                comparisons.append(dict(block=native["block"], npu_channels=candidate["npu_channels"],
                                        npu_arithmetic=candidate["npu_arithmetic"],
                                        accuracy_passed=candidate["accuracy_passed"],
                                        accuracy_status=candidate["accuracy_status"],
                                        comparison_kind=("validated_latency" if candidate["accuracy_passed"]
                                                         else "experimental_latency_with_numerical_deviations"),
                                        native_median_us=native["candidate_us"]["median_us"],
                                        candidate_median_us=candidate["candidate_us"]["median_us"],
                                        native_over_candidate=native["candidate_us"]["median_us"] /
                                        candidate["candidate_us"]["median_us"],
                                        gpu_control_ratio=native["baseline_us"]["median_us"] /
                                        candidate["baseline_us"]["median_us"]))
    return dict(status=manifest["status"], ordinary=rows, comparisons=comparisons,
                same_observed_power_mode=same_power, observed_power_modes=sorted(m for m in modes if m),
                limitations=["Synthetic isolated prefill FFN, not model prefill or TTFT.",
                             "BFP16 report-only candidates may exceed fixed numerical limits; their ratios are experimental latency comparisons, not accuracy-validated speedup.",
                             "Native HeteroMosaic and GPU controls always retain strict numerical acceptance.",
                             "Native and candidate run in separate processes; GPU controls reveal drift but do not correct it.",
                             "Native diagnostics synchronize stages; candidate HIP/host probes have different timing semantics.",
                             "NPU host waits include compute, transfers, stalls and runtime; no hardware bandwidth claim."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--native-root", type=Path, default=Path("/notebooks/HeteroMosaic-baseline"))
    parser.add_argument("--native-library", type=Path, default=os.environ.get("HETEROMOSAIC_NATIVE_LIBRARY"))
    parser.add_argument("--driver-include", type=Path)
    parser.add_argument("--artifact-root", type=Path, default=ROOT / "experiments/ffn_partition/artifacts")
    parser.add_argument("--iron-python", default=os.environ.get("IRON_PYTHON"))
    parser.add_argument("--npu-channels", type=comma_ints, default=[1024, 1152])
    parser.add_argument("--npu-arithmetic", choices=("bf16", "bfp16"), default="bf16")
    parser.add_argument("--accuracy-policy", choices=("strict", "report"),
                        help="candidate only: BF16 defaults strict, BFP16 defaults report; native baseline stays strict")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--diagnostic-iterations", type=int, default=10)
    parser.add_argument("--blocks", type=int, default=2)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--xrt-smi", default="/opt/xilinx/xrt/bin/xrt-smi")
    parser.add_argument("--power-device", default="0000:66:00.1")
    parser.add_argument("--required-power-mode", choices=("default", "performance", "balanced", "powersaver", "turbo"))
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--job-timeout", type=int, default=1800)
    args = parser.parse_args()
    try:
        args.npu_arithmetic, args.accuracy_policy = candidate_accuracy(args)
    except ValueError as error:
        parser.error(str(error))
    args.hidden, args.intermediate = 4096, 14336  # shared validators
    for p in args.npu_channels:
        validate_shape(512, 4096, 14336, p)
        if not 0 < p <= 8192:
            parser.error("SwiGLU comparison requires 0 < NPU channels <=8192")
    if not (1 <= args.blocks <= 8 and 1 <= args.iterations <= 1000 and
            1 <= args.diagnostic_iterations <= 1000 and 0 <= args.warmup <= 100 and args.job_timeout > 0):
        parser.error("invalid block, sample, warmup or timeout count")
    args.output_dir = args.output_dir.resolve()
    manifest_path = args.output_dir / "comparison_manifest.json"
    if manifest_path.exists():
        parser.error("use a fresh output directory to preserve earlier evidence")
    sources = source_hashes()
    for path in [Path(__file__), *Path(__file__).parent.glob("native_heteromosaic*")]:
        if path.is_file():
            sources[str(path.relative_to(ROOT))] = sha256(path.read_bytes()).hexdigest()
    manifest = dict(schema_version=1, status="planned", started_utc=utc_now(),
                    config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                    source_sha256=sources, jobs=build_jobs(args))
    save_json(manifest_path, manifest)
    if args.plan_only:
        print(json.dumps({"manifest": str(manifest_path), "planned_jobs": len(manifest["jobs"])}))
        return
    manifest["status"] = "running"
    for job in manifest["jobs"]:
        job["status"], job["started_utc"] = "running", utc_now()
        save_json(manifest_path, manifest)
        try:
            job["power_before_summary"] = query_power(args, job["power_before"])
            log = args.output_dir / job["log_path"]
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("w") as stream:
                result = subprocess.run(job["command"], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                        timeout=args.job_timeout, check=False)
            job["returncode"] = result.returncode
            if result.returncode:
                raise RuntimeError(f"measurement exited {result.returncode}; inspect {log}")
            path = args.output_dir / job["report_path"]
            evidence = (validate_native(json.loads(path.read_text()), job, args) if job["variant"] == "native"
                        else validate_candidate(path, job, args))
            evidence["report_sha256"] = sha256(path.read_bytes()).hexdigest()
            job["evidence"], job["status"] = evidence, evidence["status"]
        except Exception as error:
            job["status"], job["error"] = "failed", str(error)
        finally:
            if "power_before_summary" in job:
                try:
                    job["power_after_summary"] = query_power(args, job["power_after"])
                    if job["power_before_summary"]["mode"] != job["power_after_summary"]["mode"]:
                        raise RuntimeError("NPU power mode changed during the job")
                except Exception as error:
                    job["status"], job["power_error"] = "failed", str(error)
            job["finished_utc"] = utc_now()
            save_json(manifest_path, manifest)
        print(json.dumps({"job": job["id"], "status": job["status"], "error": job.get("error")}), flush=True)
        if job["status"] not in COMPLETED_STATUSES:
            break
    manifest["status"] = completed_status(manifest["jobs"])
    manifest["finished_utc"] = utc_now()
    save_json(manifest_path, manifest)
    save_json(args.output_dir / "comparison_summary.json", summarize(manifest, args.output_dir))
    if manifest["status"] not in COMPLETED_STATUSES:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
