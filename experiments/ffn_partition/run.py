"""Measure a complete prefill FFN with GPU-resident input and output.

Run as ``python -m experiments.ffn_partition.run --help`` from the repo root.
The CPU reference and all compilation/weight preparation are outside timing.
"""

import argparse
import gc
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import time
import traceback

import numpy as np

from .contract import (OutputIntegrity, accuracy_metrics, accuracy_summary,
                       benchmark_stats, bf16, random_weights, reference_full,
                       reference_partitioned, resolve_accuracy_policy, split_weights,
                       validate_shape)
from .gpu_backend import GPUBranch
from .npu_backend import NPUBranch, build_artifacts


ROOT = Path(__file__).resolve().parents[2]


def cpu_values(tensor):
    return tensor.detach().float().cpu().numpy()


class TimedFFN:
    """Explicit streams prevent accidental serialization on the default stream.

    GPU work is submitted before the CPU enters blocking XRT waits, so GPU and
    NPU can execute simultaneously without relying on Python thread scheduling.
    This is a host-staged prototype, not a shared-BO zero-copy implementation.
    """

    def __init__(self, gpu, npu, m, hidden, device):
        import torch
        self.torch, self.gpu, self.npu = torch, gpu, npu
        self.compute = torch.cuda.Stream(device=device)
        self.transfer = torch.cuda.Stream(device=device)
        self.reduce = torch.cuda.Stream(device=device)
        self.gpu_done, self.copy_done = torch.cuda.Event(), torch.cuda.Event()
        self.output = torch.empty((m, hidden), device=device, dtype=torch.bfloat16)
        if npu is not None:
            self.host_x = torch.empty((m, hidden), dtype=torch.bfloat16, pin_memory=True)
            self.host_y = torch.empty_like(self.host_x, pin_memory=True)
            self.host_x_bits = self.host_x.view(torch.uint16).numpy()
            self.host_y_bits = self.host_y.view(torch.uint16).numpy()
            self.npu_gpu_output = torch.empty_like(self.output)
        torch.cuda.synchronize(device)

    def run(self, x, serial=False):
        # Inputs are ready before the boundary. The previous iteration's
        # validation also completes outside this region.
        self.torch.cuda.synchronize(x.device)
        diagnostics = {}
        start = time.perf_counter_ns()
        if self.gpu is not None:
            y_gpu = self.gpu.enqueue(x, self.compute)
            self.gpu_done.record(self.compute)
            if serial or self.npu is None:
                self.compute.synchronize()
        if self.npu is not None:
            before = time.perf_counter_ns()
            with self.torch.cuda.stream(self.transfer):
                self.host_x.copy_(x, non_blocking=True)
            self.transfer.synchronize()
            diagnostics["input_gpu_to_host_us"] = (time.perf_counter_ns() - before) / 1000
            y_npu = self.npu.run(self.host_x_bits)
            before = time.perf_counter_ns()
            np.copyto(self.host_y_bits, y_npu)
            with self.torch.cuda.stream(self.transfer):
                self.npu_gpu_output.copy_(self.host_y, non_blocking=True)
                self.copy_done.record(self.transfer)
            with self.torch.cuda.stream(self.reduce):
                self.reduce.wait_event(self.copy_done)
                if self.gpu is not None:
                    self.reduce.wait_event(self.gpu_done)
                    self.torch.add(y_gpu, self.npu_gpu_output, out=self.output)
                else:
                    self.output.copy_(self.npu_gpu_output)
            self.reduce.synchronize()
            diagnostics["output_stage_and_boundary_wait_us"] = (time.perf_counter_ns() - before) / 1000
            result = self.output
        else:
            result = y_gpu
        elapsed_us = (time.perf_counter_ns() - start) / 1000
        # Report extraction is outside timing. Each stage field is a host
        # interval; overlapping fields must not be summed into device latency.
        if self.npu is not None:
            diagnostics["npu"] = self.npu.last_diagnostics
        return result, elapsed_us, diagnostics


def provenance():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    paths = [*Path(__file__).parent.glob("*.py"), Path(__file__).with_name("gpu_bindings.cpp"),
             ROOT / "src/hipkernels/w4a16_gemm_packed.cu"]
    cpu_info = Path("/proc/cpuinfo")
    cpu_model = next((line.split(":", 1)[1].strip() for line in cpu_info.read_text().splitlines()
                      if line.startswith("model name")), platform.processor()) if cpu_info.exists() else platform.processor()
    return {"started_at_utc": datetime.now(timezone.utc).isoformat(),
            "git_head": git("rev-parse", "HEAD"), "git_branch": git("branch", "--show-current"),
            "git_status": git("status", "--short"),
            "source_sha256": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in paths},
            "platform": platform.platform(), "python": platform.python_version(),
            "numpy": np.__version__, "cpu_model": cpu_model,
            "environment": {name: os.environ.get(name) for name in
                            ("HETEROMEGA_ROCM_PATH", "ROCM_PATH", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "HSA_OVERRIDE_GFX_VERSION")}}


def check(actual, expected, label, checks, policy="strict", integrity=None, input_id=None):
    metrics = accuracy_metrics(actual, expected, policy, integrity, input_id)
    checks[label] = metrics
    if not metrics["accepted"]:
        raise RuntimeError(f"correctness failed: {label}: {metrics}")
    return metrics


def save(report, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    temporary.replace(output)


def comparison_metrics(stats, accuracy_passed):
    """Retain measured latency ratios without claiming accurate speedup after deviations."""
    gpu_ratio = stats["baseline"]["median_us"] / stats["concurrent"]["median_us"]
    serial_ratio = stats["serial"]["median_us"] / stats["concurrent"]["median_us"]
    return {"latency_ratio_vs_gpu_baseline": gpu_ratio,
            "latency_ratio_vs_serial_partition": serial_ratio,
            "speedup_vs_gpu_baseline": gpu_ratio if accuracy_passed else None,
            "speedup_vs_serial_partition": serial_ratio if accuracy_passed else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, default=128)
    parser.add_argument("--hidden", type=int, default=4096)
    parser.add_argument("--intermediate", type=int, default=14336)
    parser.add_argument("--npu-channels", default="128,512,2048")
    parser.add_argument("--columns", type=int, default=8)
    parser.add_argument("--npu-design", choices=("array8", "legacy"), default="array8",
                        help="array8 uses all 8 columns/32 workers; legacy preserves the measured old graph")
    parser.add_argument("--npu-arithmetic", choices=("bf16", "bfp16"), default="bf16",
                        help="projection arithmetic; BFP16 is experimental and may have larger numerical error")
    parser.add_argument("--accuracy-policy", choices=("strict", "report"),
                        help="default: strict for BF16, report deviations for BFP16; GPU controls remain strict")
    parser.add_argument("--owned-npu-readback", action="store_true",
                        help="retain the previous extra BO readback copy for controlled comparison")
    parser.add_argument("--fuse-gate-up", action="store_true",
                        help="array8 gate/up in one wider projection with two compact output BOs")
    parser.add_argument("--fuse-swiglu", action="store_true",
                        help="array8 gate/up plus on-chip SiLU/multiply in one launch; implies --fuse-gate-up")
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--artifact-root", type=Path, default=Path("experiments/ffn_partition/artifacts"))
    parser.add_argument("--iron-python", default=os.environ.get("IRON_PYTHON"))
    parser.add_argument("--output", type=Path, default=Path("experiments/ffn_partition/results/ffn.json"))
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--verbose-build", action="store_true")
    args = parser.parse_args()
    args.accuracy_policy = resolve_accuracy_policy(args.npu_arithmetic, args.accuracy_policy)
    args.fuse_gate_up = args.fuse_gate_up or args.fuse_swiglu
    channels = list(dict.fromkeys(int(value) for value in args.npu_channels.split(",")))
    for p in channels:
        validate_shape(args.m, args.hidden, args.intermediate, p)
    if args.iterations < 1 or args.warmup < 0:
        parser.error("iterations must be positive and warmup nonnegative")
    report = {"schema_version": 1, "status": "preparing", "config": vars(args).copy(),
              "scope": "prefill FFN microbenchmark, not whole-model prefill/TTFT",
              "weights": "seeded synthetic unsigned W4A16, group 128; same canonical weights for all modes",
              "baseline": "original HeteroMosaic packed GPU GEMMs, BF16 SiLU then multiply, all FFN channels on GPU",
              "boundary": "ready GPU BF16 [M,H] input to synchronized GPU BF16 [M,H] output, including all host staging/layout/copies/reduction; no normalization or residual",
              "excluded": ["compilation", "weight packing/upload", "one-time setup allocations", "reference computation", "validation output readback"],
              "provenance": provenance(), "partitions": [], "correctness": {}}
    report["config"] = {k: str(v) if isinstance(v, Path) else v for k, v in report["config"].items()}
    try:
        for p in channels:
            if p:
                print(f"Building/verifying NPU artifacts: M={args.m} H={args.hidden} P={p}", flush=True)
                build_artifacts(args.m, args.hidden, p, args.artifact_root, args.columns,
                                args.iron_python, npu_design=args.npu_design, fuse_gate_up=args.fuse_gate_up,
                                fuse_swiglu=args.fuse_swiglu, npu_arithmetic=args.npu_arithmetic)
        if args.build_only:
            report["status"] = "build_complete"
            save(report, args.output)
            return
        import torch
        report["provenance"].update(torch=str(torch.__version__), hip=str(torch.version.hip))
        weights = random_weights(args.hidden, args.intermediate, args.seed)
        baseline_gpu = GPUBranch(weights.gate, weights.up, weights.down, args.m,
                                 verbose_build=args.verbose_build)
        device = baseline_gpu.device
        report["gpu_baseline"] = baseline_gpu.metadata
        report["provenance"]["gpu_name"] = torch.cuda.get_device_name(device)
        baseline = TimedFFN(baseline_gpu, None, args.m, args.hidden, device)
        rng = np.random.default_rng(args.seed + 1)
        inputs = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32)) for _ in range(2)]
        inputs.append(np.zeros_like(inputs[0]))
        gpu_inputs = [torch.from_numpy(x).to(device=device, dtype=torch.bfloat16) for x in inputs]
        torch.cuda.synchronize(device)
        references, baseline_outputs = [], []
        baseline_integrity = OutputIntegrity()
        print("Validating original GPU FFN against independent CPU reference", flush=True)
        for index, x in enumerate(inputs):
            ref = np.zeros_like(x) if index == 2 else reference_full(x, weights)
            references.append(ref)
            output, _, _ = baseline.run(gpu_inputs[index])
            actual = cpu_values(output)
            check(actual, ref, f"baseline_input_{index}", report["correctness"],
                  integrity=baseline_integrity, input_id=index)
            baseline_outputs.append(actual)
        save(report, args.output)
        for p in channels:
            print(f"Validating partition P={p}/{args.intermediate}", flush=True)
            entry = {"npu_channels": p, "gpu_channels": args.intermediate - p,
                     "npu_fraction": p / args.intermediate, "correctness": {}, "samples": []}
            report["partitions"].append(entry)
            branches = split_weights(weights, p)
            before = time.perf_counter()
            g, n = branches["gpu"], branches["npu"]
            gpu = GPUBranch(g.gate, g.up, g.down, args.m) if g is not None else None
            npu = NPUBranch(n.gate, n.up, n.down, args.m, args.artifact_root, args.columns,
                            npu_design=args.npu_design, fuse_gate_up=args.fuse_gate_up,
                            fuse_swiglu=args.fuse_swiglu,
                            npu_arithmetic=args.npu_arithmetic,
                            copy_output_bits=args.owned_npu_readback) if n is not None else None
            candidate = TimedFFN(gpu, npu, args.m, args.hidden, device)
            policy = args.accuracy_policy if npu is not None else "strict"
            entry["accuracy_policy"] = policy
            integrity = {name: OutputIntegrity() for name in ("output", "gpu", "npu")}
            timed_checks = []
            entry["setup_seconds"] = time.perf_counter() - before
            entry["gpu"] = gpu.metadata if gpu is not None else None
            entry["npu"] = npu.metadata if npu is not None else None
            partition_refs, partial_refs = [], []
            for index, x in enumerate(inputs):
                if index == 2:
                    ref, partial = np.zeros_like(x), {"gpu": np.zeros_like(x), "npu": np.zeros_like(x)}
                else:
                    ref, partial = reference_partitioned(x, weights, p)
                partition_refs.append(ref)
                partial_refs.append(partial)
            # Changed input followed by zero and repeated input catches stale
            # BOs, overwritten weights, missing waits and graph finite-loop reuse.
            for run_index, index in enumerate((0, 1, 2, 0)):
                for mode in ("serial", "concurrent"):
                    output, _, diagnostics = candidate.run(gpu_inputs[index], serial=(mode == "serial"))
                    label = f"{mode}_run_{run_index}_input_{index}"
                    actual = cpu_values(output)
                    check(actual, partition_refs[index], label + "_partition_reference", entry["correctness"],
                          policy, integrity["output"], index)
                    check(actual, baseline_outputs[index], label + "_gpu_baseline", entry["correctness"], policy)
                    if gpu is not None:
                        check(cpu_values(gpu.output), partial_refs[index]["gpu"], label + "_gpu_partial", entry["correctness"],
                              integrity=integrity["gpu"], input_id=index)
                    if npu is not None:
                        check(cpu_values(candidate.npu_gpu_output), partial_refs[index]["npu"], label + "_npu_partial", entry["correctness"],
                              policy, integrity["npu"], index)
            initial_checks = list(entry["correctness"].values())
            modes = ["baseline", "serial", "concurrent"]
            order = random.Random(args.seed + p)
            for iteration in range(-args.warmup, args.iterations):
                index = iteration % 2
                order.shuffle(modes)
                for mode in modes:
                    runner = baseline if mode == "baseline" else candidate
                    output, elapsed, diagnostics = runner.run(gpu_inputs[index], serial=(mode == "serial"))
                    expected = references[index] if mode == "baseline" else partition_refs[index]
                    metrics = accuracy_metrics(cpu_values(output), expected,
                        "strict" if mode == "baseline" else policy,
                        baseline_integrity if mode == "baseline" else integrity["output"], index)
                    timed_checks.append(metrics)
                    if not metrics["accepted"]:
                        entry["correctness"][f"timed_{iteration}_{mode}"] = metrics
                        raise RuntimeError(f"changed/reused-buffer correctness failed during iteration {iteration}, {mode}")
                    gpu_metrics = None
                    if gpu is not None and mode != "baseline":
                        # Completed GPU partial readback and validation stay
                        # outside the measured ready-input/output boundary.
                        gpu_metrics = accuracy_metrics(cpu_values(gpu.output), partial_refs[index]["gpu"],
                                                       "strict", integrity["gpu"], index)
                        timed_checks.append(gpu_metrics)
                        if not gpu_metrics["accepted"]:
                            entry["correctness"][f"timed_{iteration}_{mode}_gpu_partial"] = gpu_metrics
                            raise RuntimeError(f"GPU partial correctness failed during iteration {iteration}, {mode}")
                    npu_metrics = None
                    if npu is not None and mode != "baseline":
                        # Host output already exists after the completed call;
                        # validate it outside timing without another GPU copy.
                        npu_metrics = accuracy_metrics(cpu_values(candidate.host_y), partial_refs[index]["npu"],
                                                       policy, integrity["npu"], index)
                        timed_checks.append(npu_metrics)
                        if not npu_metrics["accepted"]:
                            entry["correctness"][f"timed_{iteration}_{mode}_npu"] = npu_metrics
                            raise RuntimeError(f"NPU output integrity failed during iteration {iteration}, {mode}")
                    if iteration >= 0:
                        entry["samples"].append({"iteration": iteration, "input_index": index, "mode": mode,
                                                 "wall_us": elapsed, "correctness_passed": metrics["passed"],
                                                 "accuracy_accepted": metrics["accepted"],
                                                 "accuracy_status": metrics["accuracy_status"],
                                                 "accuracy": metrics, "gpu_accuracy": gpu_metrics,
                                                 "npu_accuracy": npu_metrics,
                                                 "diagnostics": diagnostics})
                    elif not metrics["passed"] or (npu_metrics is not None and not npu_metrics["passed"]):
                        entry["correctness"][f"warmup_{iteration}_{mode}"] = metrics
                        if npu_metrics is not None:
                            entry["correctness"][f"warmup_{iteration}_{mode}_npu"] = npu_metrics
            if npu is not None:
                expected_calls = 8 + 2 * (args.warmup + args.iterations)
                counts = {name: stage.completed_dispatches for name, stage in npu.runners.items()}
                entry["completed_npu_dispatches_by_stage"] = counts
                entry["expected_npu_dispatches_per_stage"] = expected_calls
                if not counts or any(count != expected_calls for count in counts.values()):
                    raise RuntimeError(f"NPU completion counters differ from {expected_calls} calls: {counts}")
            entry["accuracy"] = accuracy_summary([*initial_checks, *timed_checks])
            entry["stats"] = {mode: benchmark_stats([s["wall_us"] for s in entry["samples"] if s["mode"] == mode]) for mode in modes}
            entry.update(comparison_metrics(entry["stats"], entry["accuracy"]["passed"]))
            entry["status"] = ("passed" if entry["accuracy"]["passed"]
                               else "completed_with_accuracy_deviations")
            print(json.dumps({"P": p, "status": entry["status"], "accuracy": entry["accuracy"],
                              "stats": entry["stats"],
                              "latency_ratio_vs_gpu_baseline": entry["latency_ratio_vs_gpu_baseline"],
                              "latency_ratio_vs_serial_partition": entry["latency_ratio_vs_serial_partition"],
                              "speedup_vs_gpu_baseline": entry["speedup_vs_gpu_baseline"]}), flush=True)
            save(report, args.output)
            del runner, output, candidate, gpu, npu
            gc.collect()
        report["accuracy"] = {
            "accuracy_policy": args.accuracy_policy,
            "accepted": all(entry["accuracy"]["accepted"] for entry in report["partitions"]),
            "passed": all(entry["accuracy"]["passed"] for entry in report["partitions"]),
        }
        report["accuracy"]["accuracy_status"] = ("within_tolerance" if report["accuracy"]["passed"]
                                                   else "reported_deviations")
        report["status"] = ("passed" if report["accuracy"]["passed"]
                            else "completed_with_accuracy_deviations")
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        save(report, args.output)
        raise
    save(report, args.output)
    print(f"Saved {args.output}", flush=True)


if __name__ == "__main__":
    main()
