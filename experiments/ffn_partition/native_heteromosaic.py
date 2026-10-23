"""Isolated original HeteroMosaic W4A16 shared-buffer FFN, without model loading.

python -m experiments.ffn_partition.native_heteromosaic --help

Requires an existing ROCm build of the native model extension and its pinned
XDNA headers/artifacts. The new binding links that extension; it does not compile
or replace the native runtime/kernels. Run one instance per fresh process because
the native runtime owns process-global contexts and imported-pointer caches.
"""

import argparse
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

from .contract import benchmark_stats, bf16, error_metrics, random_weights, silu_multiply
from .gpu_backend import PACKED_LAYOUT, pack_heteromosaic_weights

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = Path(__file__).with_name("native_heteromosaic_bindings.cpp")
FW_DIR = "hw_bins/npu2/8192x4096x14336/bf16_int4AWQ_bf16_M"
ARTIFACT_STEM = "256x4096x14336_64x128x64_8c_bf16_int4AWQ_bf16"


def native_config(m=512, hidden=4096, intermediate=14336, npu_rows=256):
    """The recorded M512 FFN subset, with exact native chunk-id-zero keys."""
    if (m, hidden, intermediate, npu_rows) != (512, 4096, 14336, 256):
        raise ValueError("bounded native baseline supports M512/H4096/I14336/NPU-rows256 only")
    kernels = [dict(use=True, layer=layer, forM=m, forK=hidden, forN=intermediate,
                    npuM=npu_rows, npuK=hidden, npuN=intermediate, chunk_id=0,
                    config=-1, num_tiles=32, fw_path=FW_DIR + "/",
                    tile_size="64x128x64", col="8c", dtype="bf16_int4AWQ_bf16")
               for layer in ("gate", "up")]
    return dict(heterogeneity="hetero", warmup=False, dummy_weights=False,
                debug_verbosity=0, usePackedWeights=True, padPackedWeights=False,
                usePreSavedWeights=False, prompt_len=m, minimal_pdi=True,
                cpu_decode=False, gemv_driven_split_K=False, chunking=False,
                kernels_gemm=kernels, kernels_gemv=[])


def seeded_inputs(m, hidden, seed):
    """Exactly the input generator/order used by run.py, including zero probe."""
    rng = np.random.default_rng(seed + 1)
    values = [bf16(rng.normal(size=(m, hidden)).astype(np.float32)) for _ in range(2)]
    return values + [np.zeros_like(values[0])]


def array_hash(array):
    return sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def save(report, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def reference_stages(x, weights):
    """Independent FP32 products with the same BF16 storage boundaries."""
    if not np.any(x):
        return {"gate": np.zeros((x.shape[0], weights.intermediate), np.float32),
                "up": np.zeros((x.shape[0], weights.intermediate), np.float32),
                "output": np.zeros_like(x)}
    gate = bf16(x @ weights.gate.dequantize(True).T)
    up = bf16(x @ weights.up.dequantize(True).T)
    z = silu_multiply(gate, up, bf16_io=True)
    return {"gate": gate, "up": up, "output": bf16(z @ weights.down.dequantize(True).T)}


def checked_metrics(actual, expected):
    metrics = error_metrics(actual, expected)
    if metrics["finite"]:
        index = np.unravel_index(np.argmax(np.abs(actual.astype(np.float64) - expected)), expected.shape)
        metrics["max_error_index"] = [int(i) for i in index]
        metrics["actual_at_max_error"] = float(actual[index])
        metrics["expected_at_max_error"] = float(expected[index])
    metrics["actual_sha256"] = array_hash(actual)
    metrics["expected_sha256"] = array_hash(expected)
    return metrics


def find_driver_include(native_root, explicit=None):
    candidates = [Path(explicit)] if explicit else []
    if os.environ.get("DRIVER_PATH"):
        candidates.append(Path(os.environ["DRIVER_PATH"]) / "src/include/uapi/drm_local")
    cache = native_root / "build/CMakeCache.txt"
    if cache.exists():
        for line in cache.read_text().splitlines():
            if line.startswith("DRIVER_PATH:") and "=" in line:
                candidates.append(Path(line.split("=", 1)[1]) / "src/include/uapi/drm_local")
    for path in candidates:
        if (path / "amdxdna_accel.h").is_file():
            return path.resolve()
    raise RuntimeError("pinned native XDNA headers unavailable; pass --driver-include containing amdxdna_accel.h")


def load_native_extension(args):
    import torch
    if not torch.version.hip or not torch.cuda.is_available():
        raise RuntimeError("native HeteroMosaic requires ROCm Torch and AMD GPU/NPU hardware")
    if not Path("/dev/accel/accel0").exists():
        raise RuntimeError("native XDNA device /dev/accel/accel0 is unavailable")
    library = args.native_library.resolve()
    if not library.is_file():
        raise RuntimeError(f"existing native model extension not found: {library}")
    driver_include = find_driver_include(args.native_root, args.driver_include)
    rocm = Path(os.environ.get("HETEROMEGA_ROCM_PATH", os.environ.get("ROCM_PATH", "/opt/rocm"))).resolve()
    if not (rocm / "include/hip/hip_runtime.h").is_file():
        raise RuntimeError("set HETEROMEGA_ROCM_PATH to the native build's ROCm installation")
    os.environ["ROCM_HOME"] = str(rocm)
    from torch.utils.cpp_extension import load
    info = {"native_library": str(library), "native_library_sha256": file_hash(library),
            "native_source_root": str(args.native_root), "driver_include": str(driver_include),
            "driver_header_sha256": file_hash(driver_include / "amdxdna_accel.h"),
            "binding_sha256": file_hash(BINDINGS), "torch": str(torch.__version__),
            "hip": str(torch.version.hip), "rocm": str(rocm),
            "binary_source_match": "library hash recorded; source-to-binary provenance requires original build records"}
    fingerprint = sha256(json.dumps(info, sort_keys=True).encode()).hexdigest()
    build = Path(os.environ.get("HETEROMEGA_NATIVE_BUILD_ROOT", Path.home() / ".cache/heteromega/native_ffn")) / fingerprint[:20]
    build.mkdir(parents=True, exist_ok=True)
    module = load(name="heteromega_native_ffn_" + fingerprint[:16], sources=[str(BINDINGS)],
                  extra_include_paths=[str(args.native_root / "include"), str(driver_include), str(rocm / "include")],
                  extra_cflags=["-O3", "-std=c++17", "-D__HIP_PLATFORM_AMD__=1"],
                  extra_ldflags=[str(library), f"-Wl,-rpath,{library.parent}",
                                 f"-L{rocm / 'lib'}", f"-Wl,-rpath,{rocm / 'lib'}", "-lamdhip64"],
                  with_cuda=False, build_directory=str(build), verbose=args.verbose_build)
    info["binding_library_sha256"] = file_hash(module.__file__)
    return module, info


def source_provenance(native_root):
    relative = ["src/unified_llm_w4a16_hetero/hetero_compute.cpp",
                "src/unified_llm_w4a16_hetero/npuSetup.cpp",
                "src/unified_llm_w4a16_hetero/unified_llm_w4a16.cpp",
                "src/npu_matmul_func/npu_matmul_func.cpp", "src/hipkernels/w4a16_gemm_packed.cu",
                "include/unified_llm_w4a16_hetero/npuSetup.hpp",
                "include/unified_llm_w4a16_hetero/hetero_compute.hpp",
                "include/npu_matmul_func/npu_util.hpp", "include/npu_matmul_func/npu_matmul_func.hpp"]
    source = {str(native_root / path): file_hash(native_root / path) for path in relative if (native_root / path).exists()}
    for path in (Path(__file__), BINDINGS, Path(__file__).with_name("contract.py"),
                 Path(__file__).with_name("gpu_backend.py"), ROOT / "npu/ffn/reference.py"):
        source[str(path)] = file_hash(path)
    return {"started_at_utc": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__,
            "source_sha256": source,
            "native_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=native_root, text=True).strip(),
            "native_git_status": subprocess.check_output(["git", "status", "--short"], cwd=native_root, text=True).strip()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in (("m", 512), ("hidden", 4096), ("intermediate", 14336),
                          ("npu-rows", 256), ("seed", 12832), ("iterations", 30), ("warmup", 3)):
        parser.add_argument("--" + name, type=int, default=default)
    parser.add_argument("--mode", choices=("latency", "diagnostic"), default="latency")
    parser.add_argument("--native-root", type=Path, default=ROOT)
    parser.add_argument("--native-library", type=Path, default=os.environ.get("HETEROMOSAIC_NATIVE_LIBRARY"))
    parser.add_argument("--driver-include", type=Path)
    parser.add_argument("--output", type=Path, default=Path("experiments/ffn_partition/results/native_heteromosaic.json"))
    parser.add_argument("--prepare-only", action="store_true", help="write/validate bounded config without loading Torch or hardware")
    parser.add_argument("--verbose-build", action="store_true")
    args = parser.parse_args(argv)
    args.native_root = args.native_root.resolve()
    if args.native_library is None:
        args.native_library = args.native_root / "build/py/unified_llm_w4a16/unified_llm_w4a16_hetero_libtorch.so"
    if args.iterations < 1 or args.warmup < 0:
        parser.error("iterations must be positive and warmup nonnegative")
    config = native_config(args.m, args.hidden, args.intermediate, args.npu_rows)
    report = {"schema_version": 1, "status": "preparing",
              "config": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
              "scope": "isolated synthetic W4A16 prefill FFN; not complete model prefill/TTFT",
              "boundary": "ready GPU BF16 input to synchronized GPU BF16 output; excludes norm/residual",
              "timer": "Python perf_counter_ns around native binding invocation; includes dispatch/return and a conservative redundant in-binding readiness sync; binding_wall_us separately records its internal scope",
              "baseline": "same native shared library's original packed GPU gate/up/down and BF16 SiLU/multiply",
              "native": "original direct-XDNA M-split gate/up 256 GPU + 256 NPU rows; GPU pointwise and down",
              "timing_kind": "ordinary complete FFN latency" if args.mode == "latency" else "separate synchronized stage diagnostic",
              "stage_warning": "ordinary stage host spans are not GPU/NPU execution durations and are omitted; diagnostic stage barriers perturb overlap",
              "excluded": ["setup", "input preparation", "packing/upload/imports", "reference computation", "validation readback"],
              "samples": [], "warmup_samples": [], "correctness": {},
              "completed_npu_dispatches": 0, "expected_npu_dispatches": 0,
              "packed_layout": PACKED_LAYOUT, "native_config": config,
              "provenance": source_provenance(args.native_root)}
    module = None
    config_path = args.output.with_suffix(".native_config.json").resolve()
    save(config, config_path)
    report["native_config_path"] = str(config_path)
    report["native_config_sha256"] = file_hash(config_path)
    try:
        artifacts = [args.native_root / FW_DIR / f"final_{ARTIFACT_STEM}.pdi",
                     args.native_root / FW_DIR / f"insts_{ARTIFACT_STEM}.txt"]
        report["native_artifacts"] = [{"path": str(path), "exists": path.exists(),
                                      "sha256": file_hash(path) if path.exists() else None} for path in artifacts]
        if args.prepare_only:
            report["status"] = "prepared_not_executed"
            save(report, args.output)
            return report
        if any(not path.is_file() for path in artifacts):
            raise RuntimeError("required original native M256 gate/up PDI or instructions missing")
        os.environ["HETEROMOSAIC_ROOT"] = str(args.native_root)
        module, report["native_build"] = load_native_extension(args)
        import torch
        torch.cuda.set_device(0)
        report["provenance"].update(torch=str(torch.__version__), hip=str(torch.version.hip),
                                    gpu_name=torch.cuda.get_device_name(0))
        weights = random_weights(args.hidden, args.intermediate, args.seed)
        canonical = [weights.gate, weights.up, weights.down]
        report["canonical_weights"] = {name: {"packed_sha256": array_hash(weight.packed),
                                             "scales_sha256": array_hash(weight.scales), "zeros_sha256": array_hash(weight.zeros)}
                                       for name, weight in zip(("gate", "up", "down"), canonical)}
        packed = [pack_heteromosaic_weights(weight) for weight in canonical]
        report["native_packed_weight_sha256"] = [array_hash(value) for value in packed]
        gpu_weights = [torch.from_numpy(value).to("cuda") for value in packed]
        inputs = seeded_inputs(args.m, args.hidden, args.seed)
        report["input_sha256"] = [array_hash(value) for value in inputs]
        gpu_inputs = [torch.from_numpy(value).to(device="cuda", dtype=torch.bfloat16) for value in inputs]
        gate = torch.empty((args.m, args.intermediate), dtype=torch.bfloat16, device="cuda")
        up = torch.empty_like(gate)
        output = torch.empty((args.m, args.hidden), dtype=torch.bfloat16, device="cuda")
        torch.cuda.synchronize()
        report["selected_native_configs"] = module.initialize(str(config_path), args.npu_rows)
        # Keep all imported allocations alive until process exit; native caches
        # pointers globally and has no lifetime invalidation API.
        imported = gpu_inputs + gpu_weights[:2] + [gate, up]
        report["imported_handles"] = [int(module.import_tensor(value)) for value in imported]
        references = [reference_stages(value, weights) for value in inputs]
        save(report, args.output)

        def invoke(mode, index, diagnostic=False, capture=False):
            if mode == "native":
                report["expected_npu_dispatches"] += 2
            torch.cuda.synchronize()
            started = time.perf_counter_ns()
            result = module.run(gpu_inputs[index], gate, up, output, gpu_weights,
                                mode == "native", diagnostic, capture)
            elapsed_us = (time.perf_counter_ns() - started) / 1000
            result["binding_wall_us"] = result["wall_us"]
            result["wall_us"] = elapsed_us
            report["completed_npu_dispatches"] = int(module.completed_npu_dispatches())
            if result["completed_npu_dispatches"] != (2 if mode == "native" else 0):
                raise RuntimeError("native FFN completion count mismatch")
            if not diagnostic:
                result.pop("stages_host_us", None)
            return result

        # All validation outputs/readbacks are outside ordinary timing. Preserve
        # failing metrics for both row owners and the complete FFN before abort.
        for repetition, index in enumerate((0, 1, 2, 0)):
            values = {}
            for mode in ("baseline", "native"):
                result = invoke(mode, index, capture=True)
                values[mode] = {name: result[name].float().cpu().numpy() for name in ("gate", "up")}
                values[mode]["output"] = output.float().cpu().numpy()
                for stage in ("gate", "up", "output"):
                    actual, reference = values[mode][stage], references[index][stage]
                    for owner, rows in (("all", slice(None)), ("gpu_rows", slice(0, 256)), ("npu_rows", slice(256, None))):
                        label = f"run{repetition}_input{index}_{mode}_{stage}_{owner}"
                        report["correctness"][label] = checked_metrics(actual[rows], reference[rows])
            for stage in ("gate", "up", "output"):
                report["correctness"][f"run{repetition}_input{index}_native_vs_gpu_{stage}"] = checked_metrics(
                    values["native"][stage], values["baseline"][stage])
            save(report, args.output)
            if not all(item["passed"] for item in report["correctness"].values()):
                raise RuntimeError("native/GPU numerical validation failed; no performance claim is valid")

        order = random.Random(args.seed)
        modes = ["baseline", "native"]
        for iteration in range(-args.warmup, args.iterations):
            index = iteration % 2
            order.shuffle(modes)
            for mode in modes:
                result = invoke(mode, index, diagnostic=args.mode == "diagnostic")
                actual = output.float().cpu().numpy()
                metrics = checked_metrics(actual, references[index]["output"])
                sample = dict(result, mode=mode, iteration=iteration, input_index=index,
                              correctness_passed=bool(metrics["passed"]))
                report["samples" if iteration >= 0 else "warmup_samples"].append(sample)
                if not metrics["passed"]:
                    report["correctness"][f"timed_{iteration}_{mode}"] = metrics
                    raise RuntimeError(f"reused-buffer correctness failed: iteration={iteration} mode={mode}")
            save(report, args.output)
        report["stats"] = {mode: benchmark_stats([sample["wall_us"] for sample in report["samples"] if sample["mode"] == mode])
                           for mode in ("baseline", "native")}
        if args.mode == "diagnostic":
            report["stage_stats"] = {mode: {stage: benchmark_stats([sample["stages_host_us"][stage]
                                      for sample in report["samples"] if sample["mode"] == mode])
                                      for stage in ("gate_up", "silu_multiply", "down")}
                                     for mode in ("baseline", "native")}
        if report["completed_npu_dispatches"] != report["expected_npu_dispatches"]:
            raise RuntimeError("total NPU completion count mismatch")
        report["speedup_native_vs_gpu"] = report["stats"]["baseline"]["median_us"] / report["stats"]["native"]["median_us"]
        report["status"] = "passed"
    except Exception as error:
        if module is not None:
            report["completed_npu_dispatches"] = int(module.completed_npu_dispatches())
        report.update(status="failed", error=str(error), traceback=traceback.format_exc())
        save(report, args.output)
        raise
    save(report, args.output)
    print(json.dumps({"status": report["status"], "stats": report["stats"],
                      "completed_npu_dispatches": report["completed_npu_dispatches"]}), flush=True)
    return report


if __name__ == "__main__":
    main()
