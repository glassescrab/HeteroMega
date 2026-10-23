"""Run matched fused/unfused FFN partition measurements with power evidence.

Each ordinary job retains its own interleaved GPU-only and serialized controls.
The separate diagnostic jobs add stage probes and must not supply the speedup
headline. Both programs reuse the same seeded weights, two alternating inputs,
zero/repeated-input checks and fixed correctness thresholds. This driver never
changes power mode. It queries it before and after every measurement process.

Run from the repository root. Start with ``--plan-only`` to inspect commands;
use a fresh output directory for each sweep (or ``--resume`` after interruption).
"""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from .contract import resolve_accuracy_policy, validate_shape


ROOT = Path(__file__).resolve().parents[2]
COMPLETED_STATUSES = ("passed", "completed_with_accuracy_deviations")


def candidate_accuracy(args):
    arithmetic = getattr(args, "npu_arithmetic", "bf16")
    policy = resolve_accuracy_policy(arithmetic, getattr(args, "accuracy_policy", None))
    if arithmetic != "bfp16" and policy == "report":
        raise ValueError("orchestrated report-only accuracy requires experimental BFP16")
    return arithmetic, policy


def completed_status(jobs):
    if not all(job["status"] in COMPLETED_STATUSES for job in jobs):
        return "incomplete"
    return ("completed_with_accuracy_deviations"
            if any(job["status"] == "completed_with_accuracy_deviations" for job in jobs) else "passed")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def comma_ints(value):
    try:
        result = list(dict.fromkeys(int(item) for item in value.split(",")))
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected comma-separated integers") from error
    if not result:
        raise argparse.ArgumentTypeError("at least one integer is required")
    return result


def source_hashes():
    # Include graph/kernel/host code that can change the measured execution.
    # Plotters and documentation do not affect resume eligibility.
    paths = [ROOT / "experiments/ffn_partition" / name for name in
             ("sweep_partition.py", "run.py", "profile_timeline.py", "contract.py",
              "gpu_backend.py", "gpu_bindings.cpp", "npu_backend.py")]
    paths += [path for pattern in ("*.py", "*.cc") for path in
              (ROOT / "npu/ffn").glob(pattern) if not path.name.startswith("test_")]
    paths += [ROOT / "src/hipkernels/w4a16_gemm_packed.cu",
              ROOT / "include/hipkernels/w4a16_gemm_packed.hpp"]
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def build_jobs(args):
    """Keep paired variants adjacent and alternate their order across points."""
    jobs = []
    arithmetic, policy = candidate_accuracy(args)
    variants = {"both": [(False, False), (True, False)],
                "unfused": [(False, False)], "fused": [(True, False)],
                "swiglu": [(True, True)],
                "fusion-levels": [(True, False), (True, True)]}[args.variants]
    modes = {"both": ["ordinary", "diagnostic"], "ordinary": ["ordinary"],
             "diagnostic": ["diagnostic"]}[args.measurements]
    for mode in modes:
        for m_index, m in enumerate(args.m):
            for p_index, p in enumerate(args.npu_channels):
                order = variants[::-1] if (m_index + p_index) % 2 else variants
                for fused, swiglu in order:
                    variant = "swiglu" if swiglu else "fused" if fused else "unfused"
                    tag = f"m{m}_p{p}_{variant}_{mode}" + ("_bfp16" if arithmetic == "bfp16" else "")
                    report_path = f"jobs/{tag}.json"
                    iterations = args.iterations if mode == "ordinary" else args.diagnostic_iterations
                    module = "run" if mode == "ordinary" else "profile_timeline"
                    command = [sys.executable, "-m", f"experiments.ffn_partition.{module}",
                               "--m", str(m), "--hidden", str(args.hidden),
                               "--intermediate", str(args.intermediate), "--npu-channels", str(p),
                               "--npu-design", "array8", "--columns", "8",
                               "--npu-arithmetic", arithmetic, "--accuracy-policy", policy,
                               "--seed", str(args.seed), "--warmup", str(args.warmup),
                               "--iterations", str(iterations), "--artifact-root", str(args.artifact_root),
                               "--output", str(args.output_dir / report_path)]
                    if args.iron_python:
                        command += ["--iron-python", args.iron_python]
                    if fused:
                        command += ["--fuse-gate-up"]
                    if swiglu:
                        command += ["--fuse-swiglu"]
                    jobs.append({"id": tag, "mode": mode, "m": m, "npu_channels": p,
                                 "npu_arithmetic": arithmetic, "accuracy_policy": policy,
                                 "fuse_gate_up": fused, "fuse_swiglu": swiglu, "iterations": iterations,
                                 "command": command, "report_path": report_path,
                                 "log_path": f"logs/{tag}.log", "status": "planned",
                                 "power_before": f"power/{tag}_before.json",
                                 "power_after": f"power/{tag}_after.json"})
    return jobs


def power_modes(payload, device):
    """Extract the actual NPU platform status, never a CPU governor setting."""
    return [platform["status"]["power_mode"]
            for entry in payload.get("devices", []) if entry.get("device_id") == device
            for platform in entry.get("platforms", [])
            if isinstance(platform.get("status", {}).get("power_mode"), str)]


def query_power(args, relative_path):
    path = args.output_dir / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    # A resumed failed job gets a fresh snapshot; old successful evidence is
    # protected by the manifest/report hash check before reaching this point.
    if path.exists():
        path.unlink()
    command = [args.xrt_smi, "examine", "-d", args.power_device, "-r", "platform",
               "-f", "JSON", "-o", str(path)]
    before = utc_now()
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=60, check=False)
    path.with_suffix(".log").write_text(result.stdout)
    if result.returncode != 0 or not path.is_file():
        raise RuntimeError(f"NPU power query failed; see {path.with_suffix('.log')}")
    modes = power_modes(json.loads(path.read_text()), args.power_device)
    if len(modes) != 1:
        raise RuntimeError("power query must identify exactly one NPU platform mode")
    if args.required_power_mode and modes[0] != args.required_power_mode:
        raise RuntimeError(f"NPU reports {modes[0]!r}, expected {args.required_power_mode!r}")
    return {"mode": modes[0], "queried_at_utc": before, "completed_at_utc": utc_now(),
            "command": command, "sha256": sha256(path.read_bytes()).hexdigest()}


def validate_report(path, job, args):
    report = json.loads(path.read_text())
    return {**validate_report_data(report, job, args),
            "report_sha256": sha256(path.read_bytes()).hexdigest()}


def validate_report_data(report, job, args):
    """Require strict evidence, or explicitly planned BFP16 report-only evidence.

    Report-only runs remain numerically failed where limits are exceeded. They
    must also carry the new finite/zero/repeatability guards, complete input
    sequences, strict GPU checks, and per-stage NPU completion evidence.
    """
    arithmetic, policy = candidate_accuracy(args)
    relaxed = arithmetic == "bfp16" and policy == "report"
    if (report.get("status") not in COMPLETED_STATUSES or
            (report.get("status") != "passed" and not relaxed)):
        raise ValueError("measurement report did not pass")
    if (job.get("npu_arithmetic", arithmetic) != arithmetic or
            job.get("accuracy_policy", policy) != policy):
        raise ValueError("planned arithmetic/accuracy policy differs from the requested comparison")
    config = report.get("config", {})
    if (config.get("npu_arithmetic", "bf16") != arithmetic or
            config.get("accuracy_policy", "strict") != policy):
        raise ValueError("measurement arithmetic/accuracy policy differs from the planned comparison")
    expected = {"m": job["m"], "hidden": args.hidden, "intermediate": args.intermediate,
                "seed": args.seed, "warmup": args.warmup, "iterations": job["iterations"],
                "fuse_gate_up": job["fuse_gate_up"], "columns": 8, "npu_design": "array8"}
    if any(report.get("config", {}).get(key) != value for key, value in expected.items()):
        raise ValueError("measurement configuration does not match the planned comparison")
    if report.get("config", {}).get("fuse_swiglu", False) != job.get("fuse_swiglu", False):
        raise ValueError("SwiGLU fusion configuration does not match the planned comparison")
    launches = 2 if job.get("fuse_swiglu", False) else 3 if job["fuse_gate_up"] else 4
    if job["mode"] == "ordinary":
        entries = report.get("partitions", [])
        if len(entries) != 1 or entries[0].get("npu_channels") != job["npu_channels"]:
            raise ValueError("ordinary report must contain exactly its planned partition")
        entry = entries[0]
        samples = entry.get("samples", [])
        if len(samples) != 3 * job["iterations"]:
            raise ValueError("ordinary report must have three timed modes per iteration")
        for mode in ("baseline", "serial", "concurrent"):
            mode_samples = [sample for sample in samples if sample.get("mode") == mode]
            if len(mode_samples) != job["iterations"]:
                raise ValueError(f"missing ordinary {mode} samples")
        named_checks = {**report.get("correctness", {}), **entry.get("correctness", {})}
        checks = list(named_checks.values())
        npu_samples = [sample["diagnostics"]["npu"] for sample in samples
                       if sample.get("mode") != "baseline"]
        count = max(sample["completed_dispatches_total"] for sample in npu_samples)
        expected_count = (8 + 2 * args.warmup + 2 * job["iterations"]) * launches
        uploads = npu_samples[-1]["weight_upload_counts"]
        stage_counts = entry.get("completed_npu_dispatches_by_stage", {})
        expected_calls = 8 + 2 * args.warmup + 2 * job["iterations"]
        required_checks = {f"baseline_input_{index}" for index in range(3)}
        required_checks.update(f"{mode}_run_{repetition}_input_{index}_{comparison}"
                              for repetition, index in enumerate((0, 1, 2, 0))
                              for mode in ("serial", "concurrent")
                              for comparison in ("partition_reference", "gpu_baseline", "gpu_partial", "npu_partial"))
    else:
        if report.get("config", {}).get("npu_channels") != job["npu_channels"]:
            raise ValueError("diagnostic partition does not match the planned comparison")
        samples = report.get("samples", [])
        if len(samples) != job["iterations"]:
            raise ValueError("missing diagnostic samples")
        named_checks = report.get("checks", {})
        checks = list(named_checks.values())
        count = report.get("completed_npu_dispatches")
        expected_count = (4 + args.warmup + job["iterations"]) * launches
        uploads = report.get("fixed_weight_upload_counts", {})
        stage_counts = report.get("completed_npu_dispatches_by_stage", {})
        expected_calls = 4 + args.warmup + job["iterations"]
        required_checks = {f"initial_{repetition}_input_{index}_{comparison}"
                           for repetition, index in enumerate((0, 1, 2, 0))
                           for comparison in ("partition_reference", "unpartitioned_reference", "gpu_partial", "npu_partial")}
    if not checks or not samples:
        raise ValueError("explicit or timed correctness checks are missing")
    if relaxed:
        if not required_checks.issubset(named_checks):
            raise ValueError("report-only accuracy requires complete zero/changed/repeated-input checks")

        def validate_check(check, gpu=False):
            passed = check.get("passed")
            expected_policy = "strict" if gpu else "report"
            expected_status = "within_tolerance" if passed is True else "reported_deviation"
            if (not isinstance(passed, bool) or check.get("finite") is not True or
                    check.get("accepted") is not True or check.get("structural_failures") != [] or
                    check.get("accuracy_policy") != expected_policy or
                    check.get("accuracy_status") != expected_status or
                    check.get("correctness") != ("passed" if passed else "failed") or
                    any(check.get(key) != value for key, value in
                        (("rtol", 0.03), ("atol", 0.05), ("l2_limit", 0.02))) or
                    (gpu and not passed)):
                raise ValueError("invalid report-only numerical/structural evidence or non-strict GPU control")
            for field in ("max_abs_error", "relative_l2_error", "normalized_max_error", "rms_error",
                          "reference_max_abs", "max_error_limit"):
                value = check.get(field)
                if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError("report-only numerical metrics must be finite and complete")
            if check["reference_max_abs"] == 0 and check["max_abs_error"] != 0:
                raise ValueError("report-only accuracy cannot accept nonzero output for a zero reference")
            limit = 0.05 + 0.03 * check["reference_max_abs"]
            numeric_pass = (check["max_abs_error"] == 0 if check["reference_max_abs"] == 0 else
                            check["relative_l2_error"] <= 0.02 and check["max_abs_error"] <= limit)
            if passed != numeric_pass or not math.isclose(check["max_error_limit"], limit, rel_tol=1e-12):
                raise ValueError("recorded pass/fail must agree with the unchanged numerical limits")
            return passed

        numerical_passes = [validate_check(check, name.startswith("baseline_input_") or name.endswith("_gpu_partial"))
                            for name, check in named_checks.items()]
        for sample in samples:
            is_baseline = sample.get("mode") == "baseline"
            metrics = sample.get("accuracy", {})
            numerical_passes.append(validate_check(metrics, is_baseline))
            if (sample.get("correctness_passed") is not metrics["passed"] or
                    sample.get("accuracy_accepted") is not True or
                    sample.get("accuracy_status") != metrics["accuracy_status"]):
                raise ValueError("timed numerical status is missing or was relabeled")
            if not is_baseline:
                numerical_passes.append(validate_check(sample.get("npu_accuracy", {})))
        expected_stages = ({"swiglu", "down"} if job.get("fuse_swiglu", False) else
                           {"gate_up", "silu_mul", "down"} if job["fuse_gate_up"] else
                           {"gate", "up", "silu_mul", "down"})
        if set(stage_counts) != expected_stages or any(value != expected_calls for value in stage_counts.values()):
            raise ValueError("report-only run requires successful completion of every NPU stage")
        accuracy_passed = all(numerical_passes)
        expected_status = "passed" if accuracy_passed else "completed_with_accuracy_deviations"
        summary = report.get("accuracy", {})
        if (report["status"] != expected_status or summary.get("passed") is not accuracy_passed or
                summary.get("accepted") is not True or summary.get("accuracy_policy") != policy or
                summary.get("accuracy_status") != ("within_tolerance" if accuracy_passed else "reported_deviations")):
            raise ValueError("report-only summary must preserve numerical deviation status")
    else:
        if not all(check.get("passed") is True for check in checks):
            raise ValueError("explicit correctness checks are missing or failed")
        if not all(sample.get("correctness_passed") is True for sample in samples):
            raise ValueError("timed correctness checks are missing or failed")
        accuracy_passed = True
    if any(sample.get("input_index") != sample.get("iteration", -1) % 2 for sample in samples):
        raise ValueError("timed samples did not use the expected alternating inputs")
    if count != expected_count:
        raise ValueError(f"NPU completion count {count} does not match {expected_count}")
    if len(uploads) != (2 if job["fuse_gate_up"] else 3) or any(value != 1 for value in uploads.values()):
        raise ValueError("fixed projection weights were not uploaded exactly once")
    return {"completed_npu_dispatches": count, "timed_invocations": len(samples),
            "explicit_checks": len(checks),
            "status": report["status"], "npu_arithmetic": arithmetic, "accuracy_policy": policy,
            "accuracy_passed": accuracy_passed, "accuracy_accepted": True,
            "accuracy_status": "within_tolerance" if accuracy_passed else "reported_deviations"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=comma_ints, default=[512])
    parser.add_argument("--hidden", type=int, default=4096)
    parser.add_argument("--intermediate", type=int, default=14336)
    parser.add_argument("--npu-channels", type=comma_ints, default=[128, 512, 1024, 2048, 4096, 7168])
    parser.add_argument("--variants", choices=("both", "unfused", "fused", "swiglu", "fusion-levels"), default="both",
                        help="fusion-levels compares combined gate/up against on-chip SwiGLU")
    parser.add_argument("--measurements", choices=("both", "ordinary", "diagnostic"), default="both")
    parser.add_argument("--npu-arithmetic", choices=("bf16", "bfp16"), default="bf16")
    parser.add_argument("--accuracy-policy", choices=("strict", "report"),
                        help="candidate default: BF16 strict, experimental BFP16 report; GPU controls stay strict")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--diagnostic-iterations", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--artifact-root", type=Path, default=ROOT / "experiments/ffn_partition/artifacts")
    parser.add_argument("--iron-python", default=os.environ.get("IRON_PYTHON"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--xrt-smi", default="/opt/xilinx/xrt/bin/xrt-smi")
    parser.add_argument("--power-device", default="0000:66:00.1")
    parser.add_argument("--required-power-mode", choices=("default", "powersaver", "balanced", "performance", "turbo"))
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--keep-going", action="store_true", help="record failed points and continue; exit remains nonzero")
    args = parser.parse_args()
    try:
        args.npu_arithmetic, args.accuracy_policy = candidate_accuracy(args)
    except ValueError as error:
        parser.error(str(error))
    args.output_dir = args.output_dir.resolve()
    args.artifact_root = args.artifact_root.resolve()
    if not 1 <= args.iterations <= 1000 or not 1 <= args.diagnostic_iterations <= 1000 or not 0 <= args.warmup <= 100:
        parser.error("iterations must be 1..1000 and warmup 0..100")
    for m in args.m:
        for p in args.npu_channels:
            validate_shape(m, args.hidden, args.intermediate, p)
            if not 0 < p < args.intermediate:
                parser.error("sweep requires both device branches; GPU-only is measured inside every ordinary job")
            if args.variants != "unfused" and p > 8192:
                parser.error("current fused gate/up graph supports P<=8192; endpoints are not measured")
    config = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()
              if key not in ("plan_only", "resume", "keep_going")}
    manifest_path = args.output_dir / "sweep_manifest.json"
    planned = build_jobs(args)
    sources = source_hashes()
    if manifest_path.exists():
        if not args.resume:
            parser.error("output already contains a sweep; use a new directory or --resume")
        manifest = json.loads(manifest_path.read_text())
        if manifest["config"] != config or manifest["source_sha256"] != sources:
            parser.error("resume requires identical configuration and measurement sources")
        if [job["command"] for job in manifest["jobs"]] != [job["command"] for job in planned]:
            parser.error("resume job commands differ from the existing manifest")
    else:
        manifest = {"schema_version": 1, "started_at_utc": utc_now(), "status": "planned",
                    "config": config, "source_sha256": sources, "jobs": planned,
                    "scope": "synthetic complete prefill FFN, not model prefill/TTFT; optimum only over tested points",
                    "measurement_notes": ["ordinary jobs retain interleaved GPU-only and serial controls",
                                          "fused/unfused job order alternates across partition points",
                                          "diagnostics are separate instrumented runs, not ordinary latency",
                                          "same seeded weights and alternating inputs for every variant",
                                          "power snapshots are boundaries, not continuous clock telemetry",
                                          "shared-host drift may remain; compare each point with its own baseline"]}
    save_json(manifest_path, manifest)
    if args.plan_only:
        print(json.dumps({"manifest": str(manifest_path), "planned_jobs": len(planned)}))
        return
    manifest["status"] = "running"
    for job in manifest["jobs"]:
        report_path = args.output_dir / job["report_path"]
        if job["status"] in COMPLETED_STATUSES:
            evidence = validate_report(report_path, job, args)
            if evidence["report_sha256"] != job["evidence"]["report_sha256"]:
                raise RuntimeError("saved measurement changed after verification")
            for boundary in ("before", "after"):
                path = args.output_dir / job[f"power_{boundary}"]
                if sha256(path.read_bytes()).hexdigest() != job[f"power_{boundary}_summary"]["sha256"]:
                    raise RuntimeError("saved power evidence changed after verification")
            continue
        job["status"], job["started_at_utc"] = "running", utc_now()
        save_json(manifest_path, manifest)
        print(f"Starting {job['id']}", flush=True)
        before = None
        try:
            before = query_power(args, job["power_before"])
            job["power_before_summary"] = before
            log_path = args.output_dir / job["log_path"]
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("w") as output:
                result = subprocess.run(job["command"], cwd=ROOT, stdout=output,
                                        stderr=subprocess.STDOUT, check=False)
            job["returncode"] = result.returncode
            if result.returncode != 0:
                raise RuntimeError(f"measurement exited {result.returncode}; see {log_path}")
            job["evidence"] = validate_report(report_path, job, args)
            job["status"] = job["evidence"]["status"]
        except Exception as error:
            job["status"], job["error"] = "failed", str(error)
        finally:
            if before is not None:
                try:
                    after = query_power(args, job["power_after"])
                    job["power_after_summary"] = after
                    if after["mode"] != before["mode"]:
                        raise RuntimeError("power mode changed across the measurement process")
                except Exception as error:
                    job["status"] = "failed"
                    job["power_error"] = str(error)
            job["finished_at_utc"] = utc_now()
            save_json(manifest_path, manifest)
        print(json.dumps({"id": job["id"], "status": job["status"], "error": job.get("error"),
                          "power_error": job.get("power_error")}), flush=True)
        if job["status"] not in COMPLETED_STATUSES and not args.keep_going:
            break
    manifest["status"] = completed_status(manifest["jobs"])
    manifest["finished_at_utc"] = utc_now()
    save_json(manifest_path, manifest)
    if manifest["status"] not in COMPLETED_STATUSES:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
