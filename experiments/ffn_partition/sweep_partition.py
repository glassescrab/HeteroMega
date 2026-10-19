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
import os
from pathlib import Path
import subprocess
import sys

from .contract import validate_shape


ROOT = Path(__file__).resolve().parents[2]


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
                    tag = f"m{m}_p{p}_{variant}_{mode}"
                    report_path = f"jobs/{tag}.json"
                    iterations = args.iterations if mode == "ordinary" else args.diagnostic_iterations
                    module = "run" if mode == "ordinary" else "profile_timeline"
                    command = [sys.executable, "-m", f"experiments.ffn_partition.{module}",
                               "--m", str(m), "--hidden", str(args.hidden),
                               "--intermediate", str(args.intermediate), "--npu-channels", str(p),
                               "--npu-design", "array8", "--columns", "8",
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
    """Fail closed on incomplete/correctness-failed or mismatched evidence."""
    report = json.loads(path.read_text())
    if report.get("status") != "passed":
        raise ValueError(f"measurement report did not pass: {path}")
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
        checks = [*report.get("correctness", {}).values(), *entry.get("correctness", {}).values()]
        npu_samples = [sample["diagnostics"]["npu"] for sample in samples
                       if sample.get("mode") != "baseline"]
        count = max(sample["completed_dispatches_total"] for sample in npu_samples)
        expected_count = (8 + 2 * args.warmup + 2 * job["iterations"]) * launches
        uploads = npu_samples[-1]["weight_upload_counts"]
    else:
        if report.get("config", {}).get("npu_channels") != job["npu_channels"]:
            raise ValueError("diagnostic partition does not match the planned comparison")
        samples = report.get("samples", [])
        if len(samples) != job["iterations"]:
            raise ValueError("missing diagnostic samples")
        checks = list(report.get("checks", {}).values())
        count = report.get("completed_npu_dispatches")
        expected_count = (4 + args.warmup + job["iterations"]) * launches
        uploads = report.get("fixed_weight_upload_counts", {})
    if not checks or not all(check.get("passed") is True for check in checks):
        raise ValueError("explicit correctness checks are missing or failed")
    if not samples or not all(sample.get("correctness_passed") is True for sample in samples):
        raise ValueError("timed correctness checks are missing or failed")
    if any(sample.get("input_index") != sample.get("iteration", -1) % 2 for sample in samples):
        raise ValueError("timed samples did not use the expected alternating inputs")
    if count != expected_count:
        raise ValueError(f"NPU completion count {count} does not match {expected_count}")
    if len(uploads) != (2 if job["fuse_gate_up"] else 3) or any(value != 1 for value in uploads.values()):
        raise ValueError("fixed projection weights were not uploaded exactly once")
    return {"completed_npu_dispatches": count, "timed_invocations": len(samples),
            "explicit_checks": len(checks), "report_sha256": sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=comma_ints, default=[512])
    parser.add_argument("--hidden", type=int, default=4096)
    parser.add_argument("--intermediate", type=int, default=14336)
    parser.add_argument("--npu-channels", type=comma_ints, default=[128, 512, 1024, 2048, 4096, 7168])
    parser.add_argument("--variants", choices=("both", "unfused", "fused", "swiglu", "fusion-levels"), default="both",
                        help="fusion-levels compares combined gate/up against on-chip SwiGLU")
    parser.add_argument("--measurements", choices=("both", "ordinary", "diagnostic"), default="both")
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
        if job["status"] == "passed":
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
            job["status"] = "passed"
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
        if job["status"] != "passed" and not args.keep_going:
            break
    manifest["status"] = "passed" if all(job["status"] == "passed" for job in manifest["jobs"]) else "incomplete"
    manifest["finished_at_utc"] = utc_now()
    save_json(manifest_path, manifest)
    if manifest["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
