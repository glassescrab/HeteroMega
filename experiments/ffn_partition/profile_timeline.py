"""Instrument the concurrent FFN without adding GPU stage synchronization.

This is a diagnostic, not an ordinary-latency or speedup benchmark. HIP events
measure the five GPU operations, whole GPU branch, transfers and reduction.
Host timestamps measure submission calls and the existing XRT waits. The
mandatory GPU-to-host input wait and final reduction wait are preserved; no
per-operation GPU waits are added. Event/probe overhead can change scheduling.

Run from the repo root with
``python -m experiments.ffn_partition.profile_timeline --help``.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import traceback

import numpy as np

from .contract import (OutputIntegrity, accuracy_metrics, accuracy_summary, bf16,
                       random_weights, reference_full, reference_partitioned,
                       resolve_accuracy_policy, split_weights, validate_shape)
from .gpu_backend import GPUBranch
from .npu_backend import NPUBranch, build_artifacts
from .run import TimedFFN, cpu_values, provenance, save


GPU_STAGES = ("gate", "up", "silu", "multiply", "down")


def npu_runners(npu):
    """One entry per actual launch; composite graphs get one host probe."""
    if getattr(npu, "fuse_swiglu", False):
        return {"swiglu": npu.swiglu, "down": npu.down}
    if npu.fuse_gate_up:
        return {"gate_up": npu.gate_up, "silu_mul": npu.silu, "down": npu.down}
    return {"gate": npu.gate, "up": npu.up, "silu_mul": npu.silu, "down": npu.down}


def fixed_weight_upload_counts(npu):
    # Both fusion variants use one concatenated gate/up weight BO. A swiglu
    # runner returns only Z; a gate_up runner returns two projection outputs.
    return {name: runner.input_write_counts[1]
            for name, runner in npu_runners(npu).items() if name != "silu_mul"}


def completion_counts(npu, expected_calls):
    """Check every graph, so a repeated launch cannot hide a skipped graph."""
    counts = {name: runner.completed_dispatches
              for name, runner in npu_runners(npu).items()}
    if any(count != expected_calls for count in counts.values()):
        raise RuntimeError(
            f"NPU per-stage completion counters differ from {expected_calls} calls: {counts}")
    return counts


def diagnostic_stats(samples):
    """Event durations can be zero at the timer's resolution."""
    values = np.asarray(samples, dtype=np.float64)
    if values.ndim != 1 or not values.size or not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("diagnostic durations must be finite and nonnegative")
    return {"count": int(values.size), "median_us": float(np.median(values)),
            "p10_us": float(np.percentile(values, 10)),
            "p90_us": float(np.percentile(values, 90)),
            "min_us": float(values.min()), "max_us": float(values.max())}


class _RunProbe:
    """Forward the real wait result, including error states, unchanged."""

    def __init__(self, handle, sample):
        self.handle, self.sample = handle, sample

    def wait(self, *args, **kwargs):
        before = time.perf_counter_ns()
        try:
            return self.handle.wait(*args, **kwargs)
        finally:
            self.sample["wait_start_ns"] = before
            self.sample["wait_end_ns"] = time.perf_counter_ns()


class KernelSubmissionProbe:
    """Wrap only an initialized runner's callable; BO setup is unaffected."""

    def __init__(self, kernel):
        self.kernel, self.last = kernel, None

    def __call__(self, *args, **kwargs):
        before = time.perf_counter_ns()
        handle = self.kernel(*args, **kwargs)
        after = time.perf_counter_ns()
        self.last = {"submit_start_ns": before, "submit_end_ns": after}
        return _RunProbe(handle, self.last)

    def snapshot(self, origin_ns):
        if self.last is None or "wait_end_ns" not in self.last:
            raise RuntimeError("NPU timing probe has no completed wait")
        value = self.last
        return {
            "submit_host_us": (value["submit_end_ns"] - value["submit_start_ns"]) / 1000,
            "wait_host_us": (value["wait_end_ns"] - value["wait_start_ns"]) / 1000,
            "submit_start_offset_us": (value["submit_start_ns"] - origin_ns) / 1000,
            "submit_end_offset_us": (value["submit_end_ns"] - origin_ns) / 1000,
            "wait_start_offset_us": (value["wait_start_ns"] - origin_ns) / 1000,
            "wait_end_offset_us": (value["wait_end_ns"] - origin_ns) / 1000,
        }


class ProfiledGPUBranch(GPUBranch):
    """Same operation order and buffers as GPUBranch, with event brackets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with self._torch.cuda.device(self.device):
            self.events = {name: (self._torch.cuda.Event(enable_timing=True),
                                  self._torch.cuda.Event(enable_timing=True))
                           for name in (*GPU_STAGES, "branch")}
        self.last_submit = {}

    def enqueue(self, x_gpu, stream=None):
        torch = self._torch
        if (x_gpu.device != self.device or x_gpu.dtype != torch.bfloat16
                or tuple(x_gpu.shape) != (self.m, self.hidden) or not x_gpu.is_contiguous()):
            raise ValueError("profile input must be a compact BF16 [M,H] tensor on the branch GPU")
        self.last_submit = {}
        with torch.cuda.device(self.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self.device)
            if selected.device != self.device:
                raise ValueError("stream belongs to a different GPU")
            with torch.cuda.stream(selected):
                if self._has_run and selected != self._last_stream:
                    selected.wait_event(self._done)
                handle = int(selected.cuda_stream)
                self.events["branch"][0].record(selected)

                def operation(name, call):
                    self.events[name][0].record(selected)
                    before = time.perf_counter_ns()
                    call()
                    after = time.perf_counter_ns()
                    self.events[name][1].record(selected)
                    self.last_submit[name] = (before, after)

                operation("gate", lambda: self._module.gemm(
                    self.gate_output, x_gpu, self.weights[0], self.hidden, self.channels, handle))
                operation("up", lambda: self._module.gemm(
                    self.up_output, x_gpu, self.weights[1], self.hidden, self.channels, handle))
                operation("silu", lambda: torch.nn.functional.silu(self.gate_output, inplace=True))
                operation("multiply", lambda: self.gate_output.mul_(self.up_output))
                operation("down", lambda: self._module.gemm(
                    self.output, self.gate_output, self.weights[2], self.channels, self.hidden, handle))
                self.events["branch"][1].record(selected)
                self._done.record(selected)
            self._last_stream, self._has_run = selected, True
        return self.output


class ProfiledFFN(TimedFFN):
    """Concurrent schedule copied from TimedFFN.run; normal runner unchanged."""

    def __init__(self, gpu, npu, m, hidden, device):
        if gpu is None or npu is None:
            raise ValueError("timeline diagnostic requires both GPU and NPU branches")
        super().__init__(gpu, npu, m, hidden, device)
        with self.torch.cuda.device(device):
            self.events = {name: (self.torch.cuda.Event(enable_timing=True),
                                  self.torch.cuda.Event(enable_timing=True))
                           for name in ("input_d2h", "output_h2d", "reduction")}
        self.probes = {}
        for name, runner in npu_runners(npu).items():
            probe = KernelSubmissionProbe(runner.kernel)
            self.probes[name] = probe
            runner.kernel = probe

    def run(self, x):
        self.torch.cuda.synchronize(x.device)  # outside the timing boundary
        host_intervals, host_submit = {}, {}
        start = time.perf_counter_ns()
        before = time.perf_counter_ns()
        y_gpu = self.gpu.enqueue(x, self.compute)
        self.gpu_done.record(self.compute)
        host_intervals["gpu_enqueue_including_event_records"] = (before, time.perf_counter_ns())

        before = time.perf_counter_ns()
        with self.torch.cuda.stream(self.transfer):
            self.events["input_d2h"][0].record(self.transfer)
            submitted = time.perf_counter_ns()
            self.host_x.copy_(x, non_blocking=True)
            host_submit["input_d2h"] = (submitted, time.perf_counter_ns())
            self.events["input_d2h"][1].record(self.transfer)
        # Existing, required dependency: NPU/CPU must see the copied input.
        self.transfer.synchronize()
        host_intervals["input_d2h_and_wait"] = (before, time.perf_counter_ns())

        before = time.perf_counter_ns()
        y_npu = self.npu.run(self.host_x_bits)
        host_intervals["npu_branch_call"] = (before, time.perf_counter_ns())

        before = time.perf_counter_ns()
        copied = time.perf_counter_ns()
        np.copyto(self.host_y_bits, y_npu)
        host_intervals["output_host_copy"] = (copied, time.perf_counter_ns())
        with self.torch.cuda.stream(self.transfer):
            self.events["output_h2d"][0].record(self.transfer)
            submitted = time.perf_counter_ns()
            self.npu_gpu_output.copy_(self.host_y, non_blocking=True)
            host_submit["output_h2d"] = (submitted, time.perf_counter_ns())
            self.events["output_h2d"][1].record(self.transfer)
            self.copy_done.record(self.transfer)
        with self.torch.cuda.stream(self.reduce):
            self.reduce.wait_event(self.copy_done)
            self.reduce.wait_event(self.gpu_done)
            # Start AFTER dependencies so this span excludes waiting on them.
            self.events["reduction"][0].record(self.reduce)
            submitted = time.perf_counter_ns()
            self.torch.add(y_gpu, self.npu_gpu_output, out=self.output)
            host_submit["reduction"] = (submitted, time.perf_counter_ns())
            self.events["reduction"][1].record(self.reduce)
        self.reduce.synchronize()
        end = time.perf_counter_ns()
        host_intervals["output_stage_and_boundary_wait"] = (before, end)

        # All event queries and report construction happen after the boundary.
        events = {**self.gpu.events, **self.events}
        origin = self.gpu.events["branch"][0]
        gpu_intervals = {
            name: {"start_offset_us": float(origin.elapsed_time(pair[0]) * 1000),
                   "end_offset_us": float(origin.elapsed_time(pair[1]) * 1000),
                   "duration_us": float(pair[0].elapsed_time(pair[1]) * 1000)}
            for name, pair in events.items()
        }

        def host_span(pair):
            return {"start_offset_us": (pair[0] - start) / 1000,
                    "end_offset_us": (pair[1] - start) / 1000,
                    "duration_us": (pair[1] - pair[0]) / 1000}

        return self.output, {
            "instrumented_wall_us": (end - start) / 1000,
            "gpu_event_intervals": gpu_intervals,
            "host_intervals": {name: host_span(pair) for name, pair in host_intervals.items()},
            "gpu_stage_submit_host": {name: host_span(pair) for name, pair in self.gpu.last_submit.items()},
            "transfer_reduction_submit_host": {name: host_span(pair) for name, pair in host_submit.items()},
            "npu_submit_wait_host": {name: probe.snapshot(start) for name, probe in self.probes.items()},
            "npu": self.npu.last_diagnostics,
        }


def summarize(samples):
    if not samples:
        raise ValueError("at least one diagnostic sample is required")
    stages = tuple(samples[0]["npu_submit_wait_host"])
    if stages not in (("gate", "up", "silu_mul", "down"),
                      ("gate_up", "silu_mul", "down"), ("swiglu", "down")):
        raise ValueError(f"unrecognized NPU stage sequence: {stages}")
    if any(tuple(sample["npu_submit_wait_host"]) != stages for sample in samples):
        raise ValueError("a diagnostic cannot mix NPU stage sequences")
    return {
        "instrumented_wall": diagnostic_stats([s["instrumented_wall_us"] for s in samples]),
        "gpu_event_us": {name: diagnostic_stats([s["gpu_event_intervals"][name]["duration_us"] for s in samples])
                         for name in (*GPU_STAGES, "branch", "input_d2h", "output_h2d", "reduction")},
        "host_interval_us": {name: diagnostic_stats([s["host_intervals"][name]["duration_us"] for s in samples])
                             for name in samples[0]["host_intervals"]},
        "gpu_stage_submit_host_us": {name: diagnostic_stats([s["gpu_stage_submit_host"][name]["duration_us"] for s in samples])
                                     for name in GPU_STAGES},
        "transfer_reduction_submit_host_us": {
            name: diagnostic_stats([s["transfer_reduction_submit_host"][name]["duration_us"] for s in samples])
            for name in ("input_d2h", "output_h2d", "reduction")},
        "npu_submit_host_us": {name: diagnostic_stats([s["npu_submit_wait_host"][name]["submit_host_us"] for s in samples])
                               for name in stages},
        "npu_wait_host_us": {name: diagnostic_stats([s["npu_submit_wait_host"][name]["wait_host_us"] for s in samples])
                             for name in stages},
        "npu_dispatch_wait_host_us": {name: diagnostic_stats([s["npu"]["dispatch_wait_us"][name] for s in samples])
                                      for name in stages},
        "npu_stage_host_us": {name: diagnostic_stats([s["npu"]["stages"][name] for s in samples])
                              for name in samples[0]["npu"]["stages"]},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, default=512)
    parser.add_argument("--hidden", type=int, default=4096)
    parser.add_argument("--intermediate", type=int, default=14336)
    parser.add_argument("--npu-channels", type=int, default=512)
    parser.add_argument("--npu-design", choices=("array8", "legacy"), default="array8")
    parser.add_argument("--npu-arithmetic", choices=("bf16", "bfp16"), default="bf16",
                        help="projection arithmetic; BFP16 is experimental and may have larger numerical error")
    parser.add_argument("--accuracy-policy", choices=("strict", "report"),
                        help="default: strict for BF16, report deviations for BFP16; GPU partial remains strict")
    parser.add_argument("--owned-npu-readback", action="store_true",
                        help="retain the previous extra BO readback copy for controlled comparison")
    parser.add_argument("--fuse-gate-up", action="store_true",
                        help="profile one two-output gate/up NPU launch; GPU path is unchanged")
    parser.add_argument("--fuse-swiglu", action="store_true",
                        help="profile on-chip gate/up + SiLU/multiply in one NPU launch; implies --fuse-gate-up")
    parser.add_argument("--columns", type=int, default=8)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--artifact-root", type=Path, default=Path("experiments/ffn_partition/artifacts"))
    parser.add_argument("--iron-python", default=os.environ.get("IRON_PYTHON"))
    parser.add_argument("--verbose-build", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("experiments/ffn_partition/results/timeline_profile.json"))
    args = parser.parse_args()
    args.accuracy_policy = resolve_accuracy_policy(args.npu_arithmetic, args.accuracy_policy)
    if args.fuse_swiglu:
        args.fuse_gate_up = True
    validate_shape(args.m, args.hidden, args.intermediate, args.npu_channels)
    if not 0 < args.npu_channels < args.intermediate:
        parser.error("both GPU and NPU branches are required")
    if not 1 <= args.iterations <= 1000 or not 0 <= args.warmup <= 100:
        parser.error("iterations must be 1..1000 and warmup 0..100")
    if args.fuse_gate_up and args.npu_design != "array8":
        parser.error("gate/up fusion requires the array8 design")
    report = {
        "schema_version": 1, "status": "preparing",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "config": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        "scope": "instrumented concurrent prefill FFN diagnostic; not ordinary latency or a speedup comparison",
        "weights": "seeded synthetic unsigned W4A16, group 128; same generator/seed as ordinary benchmark",
        "boundary": "ready GPU BF16 [M,H] input to synchronized GPU BF16 [M,H] output",
        "interpretation": {
            "gpu_events": "HIP event spans include device scheduling, event overhead and possible submission gaps; not pure arithmetic cycles",
            "gpu_clock_origin": "branch-start HIP event; GPU intervals share one device clock, including cross-stream transfers/reduction",
            "host_clock_origin": "perf_counter_ns at instrumented FFN boundary; not synchronized to the GPU event clock",
            "cross_device_alignment": "Do not overlay CPU/NPU-host offsets and GPU-event offsets as an exact physical timeline",
            "npu": "submit_host_us measures the Python/XRT kernel call; wait_host_us measures wait(10000), not NPU-only execution",
            "composite_npu_stage": "swiglu is one gate/up + SiLU/multiply graph; its host probe does not separate the internal operations",
            "cpu_submit": "Python/C++ API call intervals; may include runtime work, not driver-only launch overhead",
            "synchronization": "preserves required D2H input wait and final reduction wait; no extra stage waits",
            "reduction": "GPU event start follows both dependency waits; reduction span excludes those waits",
            "aggregation": "individual medians are not additive and cannot reconstruct one invocation",
            "power_mode": "not inferred; record independent xrt-smi evidence before and after this diagnostic",
        },
        "excluded": ["compilation", "weight packing/upload", "setup", "CPU references", "validation output readback", "event result extraction"],
        "provenance": provenance(), "checks": {}, "warmup_samples": [], "samples": [],
    }

    def check(actual, expected, label, policy=None, integrity=None, input_id=None):
        metrics = accuracy_metrics(actual, expected, policy or args.accuracy_policy, integrity, input_id)
        report["checks"][label] = metrics
        if not metrics["accepted"]:
            raise RuntimeError(f"accuracy or output integrity failed: {label}: {metrics}")
        return metrics

    try:
        build_artifacts(args.m, args.hidden, args.npu_channels, args.artifact_root,
                        args.columns, args.iron_python, npu_design=args.npu_design,
                        fuse_gate_up=args.fuse_gate_up, fuse_swiglu=args.fuse_swiglu,
                        npu_arithmetic=args.npu_arithmetic)
        import torch
        weights = random_weights(args.hidden, args.intermediate, args.seed)
        branches = split_weights(weights, args.npu_channels)
        g, n = branches["gpu"], branches["npu"]
        gpu = ProfiledGPUBranch(g.gate, g.up, g.down, args.m, verbose_build=args.verbose_build)
        npu = NPUBranch(n.gate, n.up, n.down, args.m, args.artifact_root, args.columns,
                        npu_design=args.npu_design, fuse_gate_up=args.fuse_gate_up,
                        fuse_swiglu=args.fuse_swiglu, npu_arithmetic=args.npu_arithmetic,
                        copy_output_bits=args.owned_npu_readback)
        runner = ProfiledFFN(gpu, npu, args.m, args.hidden, gpu.device)
        report["gpu_metadata"], report["npu_metadata"] = gpu.metadata, npu.metadata
        report["provenance"].update(torch=str(torch.__version__), hip=str(torch.version.hip),
                                     gpu_name=torch.cuda.get_device_name(gpu.device))
        rng = np.random.default_rng(args.seed + 1)
        inputs = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32)) for _ in range(2)]
        inputs.append(np.zeros_like(inputs[0]))
        gpu_inputs = [torch.from_numpy(x).to(device=gpu.device, dtype=torch.bfloat16) for x in inputs]
        torch.cuda.synchronize(gpu.device)
        refs, partials, full_refs = [], [], []
        print("Preparing independent CPU references", flush=True)
        for index, x in enumerate(inputs):
            if index == 2:
                ref, partial = np.zeros_like(x), {"gpu": np.zeros_like(x), "npu": np.zeros_like(x)}
                full = ref
            else:
                ref, partial = reference_partitioned(x, weights, args.npu_channels)
                full = reference_full(x, weights)
            refs.append(ref)
            partials.append(partial)
            full_refs.append(full)
        integrity = {name: OutputIntegrity() for name in ("output", "gpu", "npu")}
        # Changed input, zero, then reused input catches stale outputs/BOs,
        # including when BFP16 numerical differences are only reported.
        for iteration, index in enumerate((0, 1, 2, 0)):
            output, _ = runner.run(gpu_inputs[index])
            actual = cpu_values(output)
            label = f"initial_{iteration}_input_{index}"
            check(actual, refs[index], label + "_partition_reference",
                  integrity=integrity["output"], input_id=index)
            check(actual, full_refs[index], label + "_unpartitioned_reference")
            check(cpu_values(gpu.output), partials[index]["gpu"], label + "_gpu_partial",
                  policy="strict", integrity=integrity["gpu"], input_id=index)
            check(cpu_values(runner.npu_gpu_output), partials[index]["npu"], label + "_npu_partial",
                  integrity=integrity["npu"], input_id=index)
        save(report, args.output)
        print(f"Profiling {args.warmup} warmup + {args.iterations} concurrent invocations", flush=True)
        for iteration in range(-args.warmup, args.iterations):
            index = iteration % 2
            output, sample = runner.run(gpu_inputs[index])
            metrics = check(cpu_values(output), refs[index], f"iteration_{iteration}_input_{index}",
                            integrity=integrity["output"], input_id=index)
            # runner.run has already closed its instrumented time boundary.
            # GPU arithmetic stays strict even in BFP16 report-only runs.
            gpu_metrics = check(cpu_values(gpu.output), partials[index]["gpu"],
                                f"iteration_{iteration}_input_{index}_gpu_partial",
                                policy="strict", integrity=integrity["gpu"], input_id=index)
            npu_metrics = check(cpu_values(runner.host_y), partials[index]["npu"],
                                f"iteration_{iteration}_input_{index}_npu",
                                integrity=integrity["npu"], input_id=index)
            sample.update(iteration=iteration, input_index=index, correctness_passed=metrics["passed"],
                          accuracy_accepted=metrics["accepted"], accuracy_status=metrics["accuracy_status"],
                          accuracy=metrics, gpu_accuracy=gpu_metrics, npu_accuracy=npu_metrics)
            report["warmup_samples" if iteration < 0 else "samples"].append(sample)
        report["stats"] = summarize(report["samples"])
        report["npu_stage_sequence"] = list(npu_runners(npu))
        expected_calls = 4 + args.warmup + args.iterations
        report["completed_npu_dispatches_by_stage"] = completion_counts(npu, expected_calls)
        report["expected_npu_dispatches_per_stage"] = expected_calls
        report["completed_npu_dispatches"] = sum(report["completed_npu_dispatches_by_stage"].values())
        expected_dispatches = expected_calls * len(npu_runners(npu))
        report["expected_npu_dispatches"] = expected_dispatches
        if report["completed_npu_dispatches"] != expected_dispatches:
            raise RuntimeError("NPU completion counter does not match the executed diagnostic calls")
        report["fixed_weight_upload_counts"] = fixed_weight_upload_counts(npu)
        if any(count != 1 for count in report["fixed_weight_upload_counts"].values()):
            raise RuntimeError("fixed projection weights were not uploaded exactly once")
        report["accuracy"] = accuracy_summary(report["checks"].values())
        report["accuracy"]["accuracy_policy"] = args.accuracy_policy
        report["status"] = ("passed" if report["accuracy"]["passed"]
                            else "completed_with_accuracy_deviations")
    except Exception as error:
        report["status"], report["error"] = "failed", str(error)
        report["traceback"] = traceback.format_exc()
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        save(report, args.output)
        raise
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save(report, args.output)
    print(json.dumps({"status": report["status"], "output": str(args.output),
                      "gpu_event_us": report["stats"]["gpu_event_us"],
                      "instrumented_wall": report["stats"]["instrumented_wall"]}), flush=True)


if __name__ == "__main__":
    main()
