"""GPU + direct-weight NPU prefill FFN partition microbenchmark.

Run in the ROCm/PyXRT environment; provide the separate IRON Python explicitly
for builds. The boundary is ready GPU input through synchronized GPU output.
Canonical synthetic weights are packed once into the original full GPU ABI for
the NPU. Graph DMA selects its prefix; no compact NPU repacking occurs.
"""

import argparse
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import time
import traceback

import numpy as np

from .contract import (OutputIntegrity, accuracy_summary, benchmark_stats, bf16,
                       random_weights, reference_full, reference_partitioned,
                       resolve_accuracy_policy, split_weights, validate_shape)
from .gpu_backend import GPUBranch, pack_heteromosaic_weights
from .run import TimedFFN, check, comparison_metrics, cpu_values, provenance, save
from .upstream_npu import (UpstreamNpuFFN, UpstreamWeightBuffer, _ffn_specs,
                           _load_artifact, build_upstream_artifacts)


def selected_options(arithmetic="bfp16"):
    return dict(arithmetic=arithmetic, segment_pipeline_depth=2,
                swiglu_reuse=2, down_reuse=4,
                swiglu_activation_fifo_depth=2, down_activation_fifo_depth=1,
                vector_zero=True, mmul_m_reuse=1, output_layout="down_a",
                swiglu_input_layout="row_major")


def array_hash(value):
    return sha256(np.ascontiguousarray(value).view(np.uint8)).hexdigest()


def gpu_preflight():
    """Fail before graph compilation if ROCm/device access is unavailable."""
    import torch
    if torch.version.hip is None or not torch.cuda.is_available():
        raise RuntimeError("run in a ROCm Torch environment with an accessible AMD GPU")
    value = torch.ones(128, dtype=torch.bfloat16, device="cuda")
    result = value + value
    torch.cuda.synchronize()
    if not bool(torch.all(result == 2).item()):
        raise RuntimeError("GPU add/synchronize preflight failed")
    return dict(torch=str(torch.__version__), hip=str(torch.version.hip),
                gpu_name=torch.cuda.get_device_name(), gpu_preflight="add_and_sync_passed")


def prepare_original_weights(weights):
    """Pack each FULL original GPU buffer once, retaining its exact storage."""
    result = []
    for canonical in (weights.gate, weights.up, weights.down):
        packed = pack_heteromosaic_weights(canonical)
        packed.flags.writeable = False
        n, k = canonical.shape
        result.append(UpstreamWeightBuffer(packed, k, n))
    return tuple(result)


def weight_metadata(weights):
    return {name: dict(k=weight.k, n=weight.n, bytes=weight.nbytes,
                       sha256=array_hash(weight.data), readonly=not weight.data.flags.writeable)
            for name, weight in zip(("gate", "up", "down"), weights)}


def runtime_counts(npu):
    return {"completed_npu_dispatches_by_stage": {
                name: stage.completed_dispatches for name, stage in npu.runners.items()},
            "input_write_counts_by_stage": {
                name: list(stage.input_write_counts) for name, stage in npu.runners.items()},
            "fixed_weight_upload_counts": {
                "gate": npu.swiglu.input_write_counts[1],
                "up": npu.swiglu.input_write_counts[2],
                "down": npu.down.input_write_counts[1]}}


def assert_runtime_counts(npu, calls):
    counts = runtime_counts(npu)
    if counts["completed_npu_dispatches_by_stage"] != {"swiglu": calls, "down": calls}:
        raise RuntimeError(f"NPU completion count differs from {calls}: {counts}")
    if counts["input_write_counts_by_stage"] != {
            "swiglu": [calls, 1, 1], "down": [calls, 1]}:
        raise RuntimeError(f"activation/weight upload counts changed: {counts}")
    return counts


def _validate_candidate(actual, candidate, gpu, refs, partials, baseline_output,
                        policy, integrity, index, label, checks):
    """Validate outside timing; GPU controls always retain strict policy."""
    result = {"output": check(actual, refs, label + "_partition_reference", checks,
                              policy, integrity["output"], index),
              "baseline": check(actual, baseline_output, label + "_gpu_baseline", checks,
                                policy),
              "gpu": check(cpu_values(gpu.output), partials["gpu"], label + "_gpu_partial",
                           checks, "strict", integrity["gpu"], index),
              "npu": check(cpu_values(candidate.host_y), partials["npu"], label + "_npu_partial",
                           checks, policy, integrity["npu"], index)}
    return result


def run_partition(args, p, weights, original, baseline_gpu, baseline, inputs,
                  gpu_inputs, references, baseline_outputs, baseline_integrity, entry):
    """One live NPU pair at a time; retain counters even if validation fails."""
    gpu = npu = candidate = runner = output = None
    initial_weights = weight_metadata(original)
    integrity = {name: OutputIntegrity() for name in ("output", "gpu", "npu")}
    entry.update(status="preparing", accuracy_policy=args.accuracy_policy,
                 correctness={}, samples=[], warmup_samples=[], validation_runs=[])
    all_checks = entry["correctness"]
    npu_calls = 0
    try:
        before = time.perf_counter()
        suffix = split_weights(weights, p)["gpu"]
        gpu = GPUBranch(suffix.gate, suffix.up, suffix.down, args.m,
                        device=baseline_gpu.device, verbose_build=args.verbose_build)
        npu = UpstreamNpuFFN(args.m, args.hidden, p, *original, args.artifact_root,
                             channel_start=0, copy_output_bits=False,
                             **selected_options(args.npu_arithmetic))
        candidate = TimedFFN(gpu, npu, args.m, args.hidden, baseline_gpu.device)
        entry.update(setup_seconds=time.perf_counter() - before, gpu=gpu.metadata,
                     npu=npu.metadata)
        assert_runtime_counts(npu, 0)
        refs, partials = [], []
        for index, x in enumerate(inputs):
            if index == 2:
                ref, partial = np.zeros_like(x), {"gpu": np.zeros_like(x), "npu": np.zeros_like(x)}
            else:
                ref, partial = reference_partitioned(x, weights, p)
            refs.append(ref)
            partials.append(partial)

        # Each branch sees changed input, exact zero, and an earlier input again.
        for run_index, index in enumerate((0, 1, 2, 0)):
            for mode in ("serial", "concurrent"):
                output, elapsed, diagnostics = candidate.run(gpu_inputs[index], serial=mode == "serial")
                npu_calls += 1
                actual = cpu_values(output)
                record = dict(run=run_index, input_index=index, mode=mode, wall_us=elapsed,
                              output_sha256=array_hash(actual), diagnostics=diagnostics)
                entry["validation_runs"].append(record)
                assert_runtime_counts(npu, npu_calls)
                record["accuracy"] = _validate_candidate(actual, candidate, gpu,
                    refs[index], partials[index], baseline_outputs[index], args.accuracy_policy,
                    integrity, index, f"validation_{run_index}_{mode}", all_checks)

        modes = ["baseline", "serial", "concurrent"]
        rng = random.Random(args.seed + p)
        for iteration in range(-args.warmup, args.iterations):
            index = iteration % 2
            rng.shuffle(modes)
            for ordinal, mode in enumerate(modes):
                runner = baseline if mode == "baseline" else candidate
                output, elapsed, diagnostics = runner.run(gpu_inputs[index], serial=mode == "serial")
                actual = cpu_values(output)
                label = f"iteration_{iteration}_{mode}"
                record = dict(iteration=iteration, order_index=ordinal, input_index=index,
                              mode=mode, wall_us=elapsed, diagnostics=diagnostics,
                              output_sha256=array_hash(actual))
                entry["samples" if iteration >= 0 else "warmup_samples"].append(record)
                if mode == "baseline":
                    record["accuracy"] = {"output": check(actual, references[index], label,
                        all_checks, "strict", baseline_integrity, index)}
                else:
                    npu_calls += 1
                    assert_runtime_counts(npu, npu_calls)
                    record["accuracy"] = _validate_candidate(actual, candidate, gpu,
                        refs[index], partials[index], baseline_outputs[index], args.accuracy_policy,
                        integrity, index, label, all_checks)
            print(f"P={p}: completed round {iteration + 1}/{args.iterations}", flush=True)

        expected = 8 + 2 * (args.warmup + args.iterations)
        entry["expected_npu_dispatches_per_stage"] = expected
        assert_runtime_counts(npu, expected)
        entry["accuracy"] = accuracy_summary(list(all_checks.values()))
        entry["stats"] = {mode: benchmark_stats([r["wall_us"] for r in entry["samples"]
                                                if r["mode"] == mode]) for mode in modes}
        entry.update(comparison_metrics(entry["stats"], entry["accuracy"]["passed"]))
        entry["status"] = "passed" if entry["accuracy"]["passed"] else "completed_with_accuracy_deviations"
    except Exception as error:
        entry.update(status="failed", error=str(error))
        raise
    finally:
        if npu is not None:
            entry.update(runtime_counts(npu))
        entry["completed_candidate_calls"] = npu_calls
        entry["weight_buffers_after"] = weight_metadata(original)
        entry["original_weight_buffers_unchanged"] = entry["weight_buffers_after"] == initial_weights
        # Drop every owner before constructing the next partition's contexts.
        runner = output = candidate = gpu = npu = None
        gc.collect()
        if not entry["original_weight_buffers_unchanged"]:
            entry.update(status="failed", error="original packed weights changed")
            raise RuntimeError("original packed weights changed")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, default=512)
    parser.add_argument("--hidden", type=int, default=4096)
    parser.add_argument("--intermediate", type=int, default=14336)
    parser.add_argument("--npu-channels", default="1024,1792,2560,3072")
    parser.add_argument("--npu-arithmetic", choices=("bf16", "bfp16"), default="bfp16")
    parser.add_argument("--accuracy-policy", choices=("strict", "report"))
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--artifact-root", type=Path, default=Path("experiments/ffn_partition/artifacts"))
    parser.add_argument("--iron-python", default=os.environ.get("IRON_PYTHON"),
                        help="explicit configured IRON interpreter; required unless --no-build")
    parser.add_argument("--output", type=Path, default=Path("experiments/ffn_partition/results/upstream_partition.json"))
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--no-build", action="store_true", help="validate existing artifact contracts without invoking compiler")
    parser.add_argument("--verbose-build", action="store_true")
    args = parser.parse_args(argv)
    if not args.no_build and not args.iron_python:
        parser.error("provide --iron-python or IRON_PYTHON for the separate build environment")
    if args.iterations < 1 or args.warmup < 0:
        parser.error("iterations must be positive and warmup nonnegative")
    try:
        channels = list(dict.fromkeys(int(value) for value in args.npu_channels.split(",")))
        for p in channels:
            validate_shape(args.m, args.hidden, args.intermediate, p)
            if not 0 < p < args.intermediate:
                raise ValueError("each partition must leave positive GPU and NPU channel counts")
    except ValueError as error:
        parser.error(str(error))
    args.accuracy_policy = resolve_accuracy_policy(args.npu_arithmetic, args.accuracy_policy)
    return args, channels


def main(argv=None):
    args, channels = parse_args(argv)
    report = dict(schema_version=1, status="preparing", config={
        k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        scope="prefill FFN microbenchmark, not whole-model prefill/TTFT or attention interference",
        baseline="original HeteroMosaic packed GPU GEMMs; all FFN channels on GPU; BF16 SiLU and multiplication",
        boundary="ready GPU BF16 [M,H] input to synchronized GPU BF16 [M,H] output, including input/output host staging, NPU BO I/O/layouts, synchronization and partial-output reduction",
        excluded=["compilation", "weight preparation/upload", "setup allocations", "CPU references", "validation output readback"],
        diagnostic_semantics="host intervals; dispatch_wait is host launch-plus-wait, not device cycles; overlapping diagnostics are not additive",
        weights="fixed seeded unsigned W4A16 group128; NPU receives unchanged full original 4352-byte-tile GPU buffers; GPU complement is packed from the matching canonical suffix outside timing",
        npu_options=selected_options(args.npu_arithmetic), copy_output_bits=False,
        provenance=provenance(), correctness={}, partitions=[], artifacts={})
    original = None
    try:
        if not args.build_only:
            report["provenance"].update(gpu_preflight())
        weights = random_weights(args.hidden, args.intermediate, args.seed)
        original = prepare_original_weights(weights)
        report["original_weight_buffers"] = weight_metadata(original)
        for p in channels:
            print(f"Building/verifying direct-weight NPU artifacts: M={args.m} H={args.hidden} P={p}", flush=True)
            if args.no_build:
                specs = _ffn_specs(args.m, args.hidden, p, *original, args.artifact_root,
                                   channel_start=0, **selected_options(args.npu_arithmetic))
                artifacts = {name: _load_artifact(spec) for name, spec in specs.items()}
            else:
                artifacts = build_upstream_artifacts(args.m, args.hidden, p, *original,
                    args.artifact_root, channel_start=0, python_executable=args.iron_python,
                    **selected_options(args.npu_arithmetic))
            report["artifacts"][str(p)] = artifacts
            save(report, args.output)
        if args.build_only:
            report["status"] = "build_complete"
            return report

        import torch
        report["provenance"].update(torch=str(torch.__version__), hip=str(torch.version.hip))
        baseline_gpu = GPUBranch(weights.gate, weights.up, weights.down, args.m,
                                 verbose_build=args.verbose_build)
        device = baseline_gpu.device
        report["gpu_baseline"] = baseline_gpu.metadata
        report["provenance"]["gpu_name"] = torch.cuda.get_device_name(device)
        # Check the actual GPU-resident baseline buffers against the NPU source.
        gpu_hashes = {name: array_hash(value.detach().cpu().numpy())
                      for name, value in zip(("gate", "up", "down"), baseline_gpu.weights)}
        report["gpu_baseline_packed_weight_sha256"] = gpu_hashes
        if gpu_hashes != {name: item["sha256"] for name, item in report["original_weight_buffers"].items()}:
            raise RuntimeError("GPU baseline packed weight bytes differ from full NPU source buffers")
        baseline = TimedFFN(baseline_gpu, None, args.m, args.hidden, device)
        rng = np.random.default_rng(args.seed + 1)
        inputs = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32)) for _ in range(2)]
        inputs.append(np.zeros_like(inputs[0]))
        report["input_sha256"] = [array_hash(x) for x in inputs]
        gpu_inputs = [torch.from_numpy(x).to(device=device, dtype=torch.bfloat16) for x in inputs]
        torch.cuda.synchronize(device)
        references = [reference_full(x, weights) if index != 2 else np.zeros_like(x)
                      for index, x in enumerate(inputs)]
        baseline_outputs = [None] * len(inputs)
        baseline_integrity = OutputIntegrity()
        print("Validating full GPU baseline against independent CPU FFN", flush=True)
        for run_index, index in enumerate((0, 1, 2, 0)):
            output, _, _ = baseline.run(gpu_inputs[index])
            actual = cpu_values(output)
            check(actual, references[index], f"baseline_run_{run_index}_input_{index}",
                  report["correctness"], "strict", baseline_integrity, index)
            baseline_outputs[index] = actual.copy()
        save(report, args.output)
        for p in channels:
            print(f"Validating/timing direct-weight partition P={p}/{args.intermediate}", flush=True)
            entry = dict(npu_channels=p, gpu_channels=args.intermediate - p,
                         npu_fraction=p / args.intermediate, npu_channel_start=0)
            report["partitions"].append(entry)
            try:
                run_partition(args, p, weights, original, baseline_gpu, baseline, inputs,
                              gpu_inputs, references, baseline_outputs, baseline_integrity, entry)
            finally:
                save(report, args.output)
            print(json.dumps({key: entry[key] for key in ("npu_channels", "status", "stats",
                  "latency_ratio_vs_gpu_baseline", "speedup_vs_gpu_baseline")}), flush=True)
        report["accuracy"] = accuracy_summary([
            *report["correctness"].values(),
            *(metrics for entry in report["partitions"] for metrics in entry["correctness"].values())])
        report["status"] = "passed" if report["accuracy"]["passed"] else "completed_with_accuracy_deviations"
        return report
    except Exception as error:
        report.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        if original is not None:
            report["original_weight_buffers_after"] = weight_metadata(original)
            report["original_weight_buffers_unchanged"] = (
                report["original_weight_buffers_after"] == report["original_weight_buffers"])
            if not report["original_weight_buffers_unchanged"]:
                report.update(status="failed", error="original packed weights changed")
        save(report, args.output)


if __name__ == "__main__":
    main()
