"""Compare repeated and cyclic XRT contexts with initialized, fixed BOs.

This is an NPU dispatch diagnostic, not a complete FFN latency benchmark.
Run from the repository root with
``python -m experiments.ffn_partition.profile_contexts --help``.
No GPU is used. All input writes, host layout changes, and output readbacks
are outside the reported dispatch intervals. Timing differences can include
program/context state, caches, scheduling, clocks, and run-order effects;
they do not independently measure context-switch overhead.
"""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import traceback

import numpy as np

from .contract import (benchmark_stats, error_metrics, random_weights,
                       reference_full, validate_shape)
from .npu_backend import NPUBranch, build_artifacts
from prefill_reference import bf16_bits, bf16_from_bits


ROOT = Path(__file__).resolve().parents[2]
STAGES = ("gate", "up", "silu_mul", "down")


def _save(report, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    temporary.replace(output)


def _provenance():
    paths = [Path(__file__), Path(__file__).with_name("npu_backend.py"),
             Path(__file__).with_name("contract.py"),
             ROOT / "npu/ffn/xrt_runner.py", ROOT / "npu/ffn/reference.py",
             ROOT / "npu/ffn/prefill_reference.py"]
    return {
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).strip(),
        "platform": platform.platform(), "python": platform.python_version(),
        "numpy": np.__version__,
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                          for path in paths},
    }


def _counts(runners):
    return {name: {"input_write_counts": list(runner.input_write_counts),
                   "completed_dispatches": int(runner.completed_dispatches)}
            for name, runner in runners.items()}


def _verify_snapshots(runners, snapshots, initial_counts):
    checks = {}
    for name, runner in runners.items():
        actual, expected = runner.output_bits(), snapshots[name]
        compatible = actual.shape == expected.shape and actual.dtype == expected.dtype
        mismatches = int(np.count_nonzero(actual != expected)) if compatible else None
        writes_unchanged = list(runner.input_write_counts) == initial_counts[name]["input_write_counts"]
        checks[name] = {
            "passed": bool(compatible and mismatches == 0 and writes_unchanged),
            "comparison": "exact BF16 bits against initialization snapshot",
            "mismatched_elements": mismatches, "input_writes_unchanged": writes_unchanged,
            "output_sha256": sha256(actual.tobytes()).hexdigest(),
        }
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, default=512)
    parser.add_argument("--hidden", type=int, default=4096)
    parser.add_argument("--npu-channels", type=int, default=512)
    parser.add_argument("--npu-design", choices=("array8", "legacy"), default="array8")
    parser.add_argument("--columns", type=int, default=8)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--artifact-root", type=Path, default=Path("experiments/ffn_partition/artifacts"))
    parser.add_argument("--iron-python", default=os.environ.get("IRON_PYTHON"))
    parser.add_argument("--output", type=Path,
                        default=Path("experiments/ffn_partition/results/context_profile.json"))
    args = parser.parse_args()
    validate_shape(args.m, args.hidden, args.npu_channels, args.npu_channels)
    if not 1 <= args.iterations <= 1000 or not 0 <= args.warmup <= 100:
        parser.error("iterations must be 1..1000 and warmup 0..100 for this bounded diagnostic")
    report = {
        "schema_version": 1, "status": "preparing",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "config": {key: str(value) if isinstance(value, Path) else value
                   for key, value in vars(args).items()},
        "scope": "NPU dispatch/context diagnostic; no GPU or end-to-end FFN acceleration measurement",
        "timing_scope": "host kernel submission through completed XRT wait, with all BO inputs already initialized",
        "excluded_from_dispatch_intervals": ["compilation", "weight packing/upload", "input writes",
                                             "host layout conversions", "output readback", "CPU reference"],
        "mode_order": ["same_context_blocks", "cyclic_contexts"],
        "interpretation": (
            "Differences can include program/context state, cache behavior, scheduling, clocks and mode-order effects. "
            "These intervals do not isolate context-switch cost. Cyclic launches reuse frozen stage inputs; "
            "they are not an FFN dataflow execution or a complete inference timing."
        ),
        "validation_scope": "completion checked on every dispatch; exact output readback checked after each mode",
        "provenance": _provenance(), "checks": {}, "modes": {},
    }
    try:
        build_artifacts(args.m, args.hidden, args.npu_channels, args.artifact_root,
                        args.columns, args.iron_python, npu_design=args.npu_design)
        weights = random_weights(args.hidden, args.npu_channels, args.seed)
        x = np.random.default_rng(args.seed + 1).normal(
            size=(args.m, args.hidden)).astype(np.float32)
        x_bits = bf16_bits(x)
        branch = NPUBranch(weights.gate, weights.up, weights.down, args.m,
                           args.artifact_root, args.columns, npu_design=args.npu_design)
        report["npu_metadata"] = branch.metadata
        report["input_sha256"] = sha256(x_bits.tobytes()).hexdigest()
        # Initialize every stage's dynamic BOs once and validate the real,
        # complete NPU branch before taking frozen-output snapshots.
        output = branch.run(x_bits)
        expected = reference_full(bf16_from_bits(x_bits), weights)
        initial_check = error_metrics(bf16_from_bits(output), expected)
        report["checks"]["initial_full_ffn_reference"] = initial_check
        if not initial_check["passed"]:
            raise RuntimeError(f"initial full NPU FFN failed the fixed correctness thresholds: {initial_check}")
        runners = dict(zip(STAGES, (branch.gate, branch.up, branch.silu, branch.down)))
        snapshots = {name: runner.output_bits() for name, runner in runners.items()}
        initial_counts = _counts(runners)
        report["initial_counts"] = initial_counts
        report["snapshot_sha256"] = {name: sha256(value.tobytes()).hexdigest()
                                     for name, value in snapshots.items()}
        for name, runner in (("gate", branch.gate), ("up", branch.up), ("down", branch.down)):
            if runner.input_write_counts[1] != 1:
                raise RuntimeError(f"{name} fixed weight was not uploaded exactly once")
        _save(report, args.output)

        blocked = {"warmup_dispatch_us": {}, "dispatch_us": {}, "stats": {}}
        report["modes"]["same_context_blocks"] = blocked
        for name, runner in runners.items():
            print(f"Repeated same context: {name}", flush=True)
            blocked["warmup_dispatch_us"][name] = [runner.dispatch_wait() for _ in range(args.warmup)]
            samples = []
            blocked["dispatch_us"][name] = samples
            for _ in range(args.iterations):
                samples.append(float(runner.dispatch_wait()))
            blocked["stats"][name] = benchmark_stats(samples)
        blocked["checks"] = _verify_snapshots(runners, snapshots, initial_counts)
        blocked["counts_after"] = _counts(runners)
        if not all(check["passed"] for check in blocked["checks"].values()):
            raise RuntimeError("same-context mode changed an output snapshot or wrote an input BO")
        _save(report, args.output)

        cyclic = {"stage_order": list(STAGES), "warmup_rounds": [], "rounds": [], "stats": {}}
        report["modes"]["cyclic_contexts"] = cyclic
        print("Cyclic contexts: gate -> up -> silu_mul -> down", flush=True)
        for iteration in range(-args.warmup, args.iterations):
            before = time.perf_counter_ns()
            samples = {name: float(runner.dispatch_wait()) for name, runner in runners.items()}
            wall_us = (time.perf_counter_ns() - before) / 1000.0
            record = {"iteration": iteration, "dispatch_us": samples,
                      "dispatch_sum_us": sum(samples.values()), "host_cycle_wall_us": wall_us}
            cyclic["warmup_rounds" if iteration < 0 else "rounds"].append(record)
        cyclic["stats"] = {name: benchmark_stats([r["dispatch_us"][name] for r in cyclic["rounds"]])
                           for name in STAGES}
        cyclic["host_cycle_wall_stats"] = benchmark_stats([r["host_cycle_wall_us"] for r in cyclic["rounds"]])
        cyclic["checks"] = _verify_snapshots(runners, snapshots, initial_counts)
        cyclic["counts_after"] = _counts(runners)
        if not all(check["passed"] for check in cyclic["checks"].values()):
            raise RuntimeError("cyclic-context mode changed an output snapshot or wrote an input BO")
        report["cyclic_over_same_context_median_dispatch_ratio"] = {
            name: cyclic["stats"][name]["median_us"] / blocked["stats"][name]["median_us"]
            for name in STAGES
        }
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        _save(report, args.output)
        raise
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    _save(report, args.output)
    print(json.dumps({"status": report["status"], "output": str(args.output),
                      "cyclic_over_same_context_median_dispatch_ratio":
                      report["cyclic_over_same_context_median_dispatch_ratio"]}), flush=True)


if __name__ == "__main__":
    main()
