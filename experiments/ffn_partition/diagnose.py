"""Diagnose complete-FFN correctness stage by stage; these are not timings.

Run with ``python -m experiments.ffn_partition.diagnose --help``. All metrics
retain the experiment's fixed tolerances. Raw arrays are saved for inspecting
packing, metadata, BO readback, approximation, and downstream error propagation.
"""

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import traceback

import numpy as np

from .contract import (bf16, error_metrics, packed_output_to_activation,
                       random_weights, reference_partitioned, split_weights,
                       validate_shape)
from .gpu_backend import GPUBranch
from .npu_backend import NPUBranch, build_artifacts
from prefill_reference import bf16_bits, bf16_from_bits, unpack_activations, unpack_output
from reference import silu_multiply


def stage_reference(x, weights):
    gate = bf16(x @ weights.gate.dequantize(True).T)
    up = bf16(x @ weights.up.dequantize(True).T)
    silu = silu_multiply(gate, up, bf16_io=True)
    down = bf16(silu @ weights.down.dequantize(True).T)
    return {"gate": gate, "up": up, "silu": silu, "down": down}


def raw_bo_snapshot(runner, label, arrays):
    """Capture the actual pyxrt array before any dtype conversion is applied."""
    runner.buffers[-1].sync(runner.xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_FROM_DEVICE)
    shape, dtype = runner.specs[-1]
    requested = int(np.prod(shape)) * dtype.itemsize
    raw = runner.buffers[-1].read(requested, 0)
    observed = np.asarray(raw)
    description = {
        "python_type": f"{type(raw).__module__}.{type(raw).__name__}",
        "shape": list(observed.shape), "dtype": str(observed.dtype),
        "strides": list(observed.strides), "itemsize": observed.itemsize,
        "nbytes": observed.nbytes, "size": observed.size,
        "requested_nbytes": requested, "c_contiguous": bool(observed.flags.c_contiguous),
        "first_values": observed.reshape(-1)[:16].tolist(),
    }
    arrays[f"{label}_raw_read_values"] = observed.copy()
    # Compare the current runtime's numerical uint8 cast with a byte-preserving
    # copy/view. Do not change runtime behavior here; preserve both as evidence.
    current = np.ascontiguousarray(observed, dtype=np.uint8)
    bytes_preserved = np.ascontiguousarray(observed).view(np.uint8).reshape(-1)
    arrays[f"{label}_runtime_cast_bytes"] = current
    arrays[f"{label}_preserved_bytes"] = bytes_preserved
    description["runtime_cast_nbytes"] = current.nbytes
    description["preserved_nbytes"] = bytes_preserved.nbytes
    description["cast_equals_preserved_bytes"] = bool(np.array_equal(current.reshape(-1), bytes_preserved))
    description["preserved_bytes_sha256"] = sha256(bytes_preserved.tobytes()).hexdigest()
    if bytes_preserved.size == requested:
        arrays[f"{label}_preserved_bf16_bits"] = bytes_preserved.view(dtype).reshape(shape).copy()
    return description


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, default=128)
    parser.add_argument("--hidden", type=int, default=256)
    parser.add_argument("--intermediate", type=int, default=512)
    parser.add_argument("--npu-channels", type=int, default=128)
    parser.add_argument("--columns", type=int, default=8)
    parser.add_argument("--npu-design", choices=("array8", "legacy"), default="array8")
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--input-seed", type=int, default=12833)
    parser.add_argument("--input-index", type=int, default=0, choices=(0, 1, 2))
    parser.add_argument("--iron-python", default=os.environ.get("IRON_PYTHON"))
    parser.add_argument("--artifact-root", type=Path, default=Path("experiments/ffn_partition/artifacts"))
    parser.add_argument("--output-prefix", type=Path, default=Path("experiments/ffn_partition/results/diagnostic"))
    parser.add_argument("--verbose-build", action="store_true")
    args = parser.parse_args()
    validate_shape(args.m, args.hidden, args.intermediate, args.npu_channels)
    if not 0 < args.npu_channels < args.intermediate:
        parser.error("diagnostics require both branches: 0 < npu-channels < intermediate")
    arrays, report = {}, {"status": "preparing", "scope": "synchronized correctness diagnostics, not performance",
                          "config": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                          "checks": {}, "raw_bo_reads": {}}
    prefix = args.output_prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)

    def save():
        np.savez_compressed(str(prefix) + ".npz", **arrays)
        Path(str(prefix) + ".json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    def compare(label, actual, expected):
        try:
            metrics = error_metrics(actual, expected)
        except ValueError as error:
            metrics = {"passed": False, "error": str(error)}
        report["checks"][label] = metrics
        print(json.dumps({"check": label, **metrics}, allow_nan=False), flush=True)

    try:
        weights = random_weights(args.hidden, args.intermediate, args.seed)
        branches = split_weights(weights, args.npu_channels)
        rng = np.random.default_rng(args.input_seed)
        inputs = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32)) for _ in range(2)]
        inputs.append(np.zeros_like(inputs[0]))
        x = inputs[args.input_index]
        arrays["input"] = x
        refs = {}
        for label, branch in branches.items():
            refs[label] = stage_reference(x, branch)
            for stage, values in refs[label].items():
                arrays[f"cpu_{label}_{stage}"] = values
            for projection in ("gate", "up", "down"):
                weight = getattr(branch, projection)
                for component in ("packed", "scales", "zeros"):
                    arrays[f"{label}_{projection}_weight_{component}"] = getattr(weight, component)
        partition_ref, _ = reference_partitioned(x, weights, args.npu_channels)
        arrays["cpu_partition_output"] = partition_ref
        save()

        build_artifacts(args.m, args.hidden, args.npu_channels, args.artifact_root,
                        args.columns, args.iron_python, npu_design=args.npu_design)
        import torch
        gw, nw = branches["gpu"], branches["npu"]
        gpu = GPUBranch(gw.gate, gw.up, gw.down, args.m, verbose_build=args.verbose_build)
        report["gpu_metadata"] = gpu.metadata
        x_gpu = torch.from_numpy(x).to(device=gpu.device, dtype=torch.bfloat16)
        torch.cuda.synchronize(gpu.device)
        gpu.enqueue(x_gpu)
        gpu.synchronize()

        def gpu_values(tensor):
            return tensor.detach().float().cpu().numpy().copy()

        gpu_stages = {"up": gpu_values(gpu.up_output), "silu": gpu_values(gpu.gate_output),
                      "down": gpu_values(gpu.output)}
        # enqueue's in-place activation replaces gate. Rerun only gate into a
        # separate diagnostic buffer to observe its raw projection output.
        gate_buffer = torch.empty_like(gpu.up_output)
        stream = torch.cuda.current_stream(gpu.device)
        gpu._module.gemm(gate_buffer, x_gpu, gpu.weights[0], gpu.hidden, gpu.channels, int(stream.cuda_stream))
        stream.synchronize()
        gpu_stages["gate"] = gpu_values(gate_buffer)
        for stage, value in gpu_stages.items():
            arrays[f"gpu_{stage}"] = value
            compare(f"gpu_{stage}_vs_canonical", value, refs["gpu"][stage])
        gpu_local_silu = silu_multiply(gpu_stages["gate"], gpu_stages["up"], bf16_io=True)
        gpu_local_down = bf16(gpu_stages["silu"] @ gw.down.dequantize(True).T)
        arrays["cpu_gpu_silu_from_hardware_inputs"] = gpu_local_silu
        arrays["cpu_gpu_down_from_hardware_input"] = gpu_local_down
        compare("gpu_silu_vs_local_hardware_inputs", gpu_stages["silu"], gpu_local_silu)
        compare("gpu_down_vs_local_hardware_input", gpu_stages["down"], gpu_local_down)
        save()

        npu = NPUBranch(nw.gate, nw.up, nw.down, args.m, args.artifact_root, args.columns,
                        npu_design=args.npu_design)
        report["npu_metadata"] = npu.metadata
        x_bits = bf16_bits(x)
        output_bits = npu.run(x_bits)
        report["npu_dispatch_diagnostics"] = npu.last_diagnostics
        arrays["npu_returned_output_bits"] = output_bits
        npu_stages, packed_stages = {}, {}
        for stage, runner in (("gate", npu.gate), ("up", npu.up), ("silu", npu.silu), ("down", npu.down)):
            report["raw_bo_reads"][stage] = raw_bo_snapshot(runner, f"npu_{stage}", arrays)
            print(json.dumps({"raw_bo_read": stage, **report["raw_bo_reads"][stage]}, allow_nan=False), flush=True)
            bits = runner.output_bits()
            packed_stages[stage] = bits
            arrays[f"npu_{stage}_packed_bits"] = bits
            n = args.hidden if stage == "down" else args.npu_channels
            npu_stages[stage] = unpack_output(bits, args.m, n)
            arrays[f"npu_{stage}"] = npu_stages[stage]
            compare(f"npu_{stage}_vs_canonical", npu_stages[stage], refs["npu"][stage])
            save()
        returned = bf16_from_bits(output_bits)
        compare("npu_returned_vs_native_down_output", returned, npu_stages["down"])
        npu_local_silu = silu_multiply(npu_stages["gate"], npu_stages["up"], bf16_io=True)
        npu_local_down = bf16(npu_stages["silu"] @ nw.down.dequantize(True).T)
        arrays["cpu_npu_silu_from_hardware_inputs"] = npu_local_silu
        arrays["cpu_npu_down_from_hardware_input"] = npu_local_down
        compare("npu_silu_vs_local_hardware_inputs", npu_stages["silu"], npu_local_silu)
        compare("npu_down_vs_local_hardware_input", npu_stages["down"], npu_local_down)
        down_input_bits = packed_output_to_activation(packed_stages["silu"], args.m, args.npu_channels)
        decoded_down_input = unpack_activations(down_input_bits, args.m, args.npu_channels)
        arrays["npu_down_input_packed_bits"] = down_input_bits
        arrays["npu_down_input_decoded"] = decoded_down_input
        compare("npu_down_layout_preserves_silu", decoded_down_input, npu_stages["silu"])
        combined = bf16(gpu_stages["down"] + returned)
        arrays["hardware_partition_output"] = combined
        compare("combined_vs_partition_reference", combined, partition_ref)
        report["status"] = "passed" if all(check.get("passed") for check in report["checks"].values()) else "mismatch"
    except Exception as error:
        report["status"] = "error"
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        save()
        raise
    save()
    print(f"Saved {prefix}.json and {prefix}.npz; status={report['status']}", flush=True)


if __name__ == "__main__":
    main()
