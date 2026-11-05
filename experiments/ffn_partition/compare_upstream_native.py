"""Fresh original-HeteroMosaic versus direct-weight BFP16 prefill FFN runs.

Two reversed blocks retain each implementation's own interleaved GPU control.
Native diagnostics, when requested, are a separate process and never latency.
Native accuracy defaults to strict; explicit report mode retains numerical
failures while admitting faithful implementation latency with structural checks.
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

from .contract import accuracy_summary, benchmark_stats
from .run_upstream_partition import selected_options, kernel_options
from types import SimpleNamespace
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


def candidate_options(args):
    return kernel_options(SimpleNamespace(npu_arithmetic="bfp16",
        down_output_layout=getattr(args, "down_output_layout", "compact"),
        swiglu_reuse=getattr(args, "swiglu_reuse", 2),
        bfp16_native_layout=getattr(args, "bfp16_native_layout", False),
        split_m32_a=getattr(args, "split_m32_a", False),
        preconvert_b=getattr(args, "preconvert_b", False),
        preconvert_a=getattr(args, "preconvert_a", False)))


def validate_optimized_artifacts(report, part, args, p):
    """Cross-check requested options against the artifacts actually loaded.

    Older archived default reports predate these fields. New opt-in runs must
    retain complete manifest/build-contract evidence for both NPU launches.
    """
    options = candidate_options(args)
    native8 = getattr(args, "bfp16_native_layout", False)
    split_a = getattr(args, "split_m32_a", False)
    preconvert_b = getattr(args, "preconvert_b", False)
    preconvert_a = getattr(args, "preconvert_a", False)
    npu = part["npu"]
    accumulator = "bf16" if native8 else "float32"
    require(npu.get("bfp16_native_layout", False) is native8 and
            npu.get("accumulator_format", "float32") == accumulator and
            npu.get("split_m32_a", False) is split_a and
            npu.get("preconvert_b", False) is preconvert_b and
            npu.get("preconvert_a", False) is preconvert_a,
            "candidate execution arithmetic/layout differs from requested options")
    optimized = (native8 or getattr(args, "shared_intermediate", False) or
        getattr(args, "dmabuf_gpu_output", False) or
        getattr(args, "dmabuf_gpu_input", False) or
        getattr(args, "mapped_npu_output", False) or getattr(args, "swiglu_reuse", 2) != 2 or
        getattr(args, "down_output_layout", "compact") != "compact" or
        getattr(args, "gpu_variant", "original") != "original")
    if not optimized:
        return
    require(npu.get("segment_pipeline_depth") == options["segment_pipeline_depth"],
            "candidate execution pipeline differs")
    kernel = npu.get("kernel_options", {})
    expected_kernel = dict(options, bfp16_native_layout=native8,
        down_output_layout=options.get("down_output_layout", "compact"),
        swiglu_output_fifo_depth=options.get("swiglu_output_fifo_depth", 2),
        down_output_fifo_depth=options.get("down_output_fifo_depth", 2))
    expected_kernel.pop("segment_pipeline_depth")
    # Archived ordinary/native8 runs predate the optional split-A field.
    if split_a or "split_m32_a" in kernel:
        expected_kernel["split_m32_a"] = split_a
    if preconvert_b or "preconvert_b" in kernel:
        expected_kernel["preconvert_b"] = preconvert_b
    if preconvert_a or "preconvert_a" in kernel:
        expected_kernel["preconvert_a"] = preconvert_a
    require(all(kernel.get(key) == value for key, value in expected_kernel.items()),
            "candidate execution kernel options differ")
    artifacts = npu.get("artifacts", {})
    require(set(artifacts) == {"swiglu", "down"} and
            report.get("artifacts", {}).get(str(p)) == artifacts,
            "candidate built/loaded artifact evidence differs")
    common = dict(kind="w4a16_upstream_bfp16", arithmetic="bfp16", compute_format="bfp16",
        m=512, cols=8, compute_rows=4, worker_count=32, worker_stack_size=4096,
        weight_tile_bytes=4352, segment_pipeline_depth=2, vector_zero=True, mmul_m_reuse=1,
        bfp16_native_layout=native8, accumulator_format=accumulator, k_start=0, n_start=0)
    dependencies = None
    for stage, geometry in (("swiglu", dict(mode="swiglu", k=4096, n=p,
            weight_k=4096, weight_n=14336, input_layout="row_major", output_layout="down_a")),
            ("down", dict(mode="projection", k=p, n=4096, weight_k=14336, weight_n=4096,
             input_layout="compact", output_layout=options.get("down_output_layout", "compact")))):
        expected = dict(common, **geometry, m_reuse=options[stage + "_reuse"],
            activation_fifo_depth=options[stage + "_activation_fifo_depth"],
            output_fifo_depth=options.get(stage + "_output_fifo_depth", 2))
        artifact = artifacts[stage]
        manifest, contract = artifact.get("manifest", {}), artifact.get("build_contract", {})
        if split_a or "split_m32_a" in manifest or "activation_m_reuse" in manifest:
            expected.update(split_m32_a=split_a,
                            activation_m_reuse=2 if split_a else options[stage + "_reuse"])
        if preconvert_b or "preconvert_b" in manifest:
            expected["preconvert_b"] = preconvert_b
        if preconvert_a or "preconvert_a" in manifest:
            expected["preconvert_a"] = preconvert_a
        require(all(manifest.get(key) == value for key, value in expected.items()),
                f"candidate {stage} manifest options differ")
        recorded = contract.get("expected_manifest", {})
        require(all(recorded.get(key) == value for key, value in expected.items()) and
                all(manifest.get(key) == value for key, value in recorded.items()),
                f"candidate {stage} build contract differs from manifest")
        closure = manifest.get("dependency_sha256", {})
        require(isinstance(closure, dict) and {"w4a16_upstream.py", "w4a16_prefill_upstream.cc",
            "upstream_schedule.py", "upstream_output.py", "upstream_weights.py"}.issubset(closure),
            f"candidate {stage} source closure missing")
        for digest in closure.values():
            valid_hash(digest)
        require(contract.get("source_sha256") == closure and
                manifest.get("source_sha256") == closure["w4a16_prefill_upstream.cc"] and
                manifest.get("graph_sha256") == closure["w4a16_upstream.py"],
                f"candidate {stage} source identity differs")
        require(dependencies is None or dependencies == closure,
                "candidate stages were built from different source closures")
        dependencies = closure
        for name in ("xclbin_sha256", "insts_sha256"):
            valid_hash(manifest.get(name))


def validate_teammate_gpu(part, report, p):
    gpu = part.get("gpu", {})
    require(all(gpu.get(key) == value for key, value in dict(
        backend="teammate_three_kernel_gpu_ffn", m=512, hidden=4096,
        channels=14336-p, source_intermediate=14336, source_channel_begin=p,
        source_channel_end=14336, kernels_per_prefill=3, gemm_autotune=0).items()),
        "teammate GPU suffix metadata differs")
    require(gpu.get("source_packed_sha256") == report.get("gpu_baseline_packed_weight_sha256"),
            "teammate GPU suffix did not use the fixed full packed buffers")
    closure = gpu.get("source_sha256", {})
    required = {"experiments/ffn_partition/teammate_gpu_bindings.cpp",
        "experiments/ffn_partition/teammate_gpu.py", "kernels/gpu/src/gpu_ffn.cpp",
        "kernels/gpu/src/pack_w4a16.cpp", "kernels/gpu/src/silu_mul.cu",
        "src/hipkernels/w4a16_gemm_packed.cu"}
    require(isinstance(closure, dict) and required.issubset(closure), "teammate GPU source closure missing")
    for digest in closure.values():
        valid_hash(digest)
    for key, digest in report["gpu_baseline"].get("source_sha256", {}).items():
        if key in closure:
            require(closure[key] == digest, "teammate/common GPU source differs from baseline")
    prepared = gpu.get("prepared_packed_sha256", {})
    require(set(prepared) == {"gate_up", "down"}, "teammate prepared buffer hashes missing")
    for digest in (*prepared.values(), gpu.get("build_fingerprint"), gpu.get("binary_sha256")):
        valid_hash(digest)


def validate_dmabuf_output(report, part, args):
    enabled = getattr(args, "dmabuf_gpu_output", False)
    npu, runtime = part["npu"], part.get("runtime", {})
    require(report.get("config", {}).get("dmabuf_gpu_output", False) is enabled and
            npu.get("gpu_output_dmabuf", False) is enabled and
            runtime.get("gpu_output_dmabuf", False) is enabled,
            "DMA-BUF output selection/runtime differs")
    if not enabled:
        return
    contract = npu.get("gpu_output_dmabuf_contract", {})
    require(runtime.get("output") == contract and contract.get("shape") == [512, 4096] and
            contract.get("dtype") == "BF16" and contract.get("python_buffer_type") == "pyxrt.bo" and
            contract.get("output_argument") == 5 and contract.get("copy_fallback") is False and
            contract.get("fd_closed_after_import") is True,
            "DMA-BUF output binding/extent/ownership contract differs")
    allocation, imported, registry = (contract.get(key, {}) for key in ("allocation", "imported_bo", "registry"))
    offset = allocation.get("export_offset")
    require(type(offset) is int and offset >= 0 and offset % 4096 == 0,
            "DMA-BUF output export offset is not page aligned")
    require(offset == 0 or contract.get("sub_buffer_used") is True,
            "nonzero DMA-BUF output offset requires explicit sub-buffer evidence")
    if ("backing_nbytes" in allocation or any(key in contract for key in
            ("import_extent_policy", "imported_backing_bo", "sub_buffer_used", "sub_buffer_offset"))):
        require(contract.get("import_extent_policy") in (
                    "zero_offset_logical_subbuffer", "page_offset_logical_subbuffer", "whole_backing"),
                "unknown DMA-BUF logical/backing allocation policy")
        parent = contract.get("imported_backing_bo", {})
        backing = allocation.get("backing_nbytes")
        sub = contract.get("sub_buffer_used")
        require(type(backing) is int and backing >= 512 * 4096 * 2 and backing % 4096 == 0 and
                parent.get("nbytes") == backing and contract.get("sub_buffer_offset") == offset and
                sub is (backing != 512 * 4096 * 2 or offset != 0) and
                parent.get("group_id") == imported.get("group_id") and
                parent.get("bank_id") == imported.get("bank_id") and
                parent.get("flags") == imported.get("flags") and
                (parent.get("address") + offset == imported.get("address") if sub else
                 parent.get("address") == imported.get("address")),
                "DMA-BUF logical output is not a bounded view of its backing allocation")
    require(allocation.get("nbytes") == 512 * 4096 * 2 == imported.get("nbytes") and
            isinstance(offset, int) and offset >= 0 and
            allocation.get("export_fd_closed") is True and
            allocation.get("allocation") == "hipMalloc standalone allocation" and
            allocation.get("export") == "hsa_amd_portable_export_dmabuf" and
            imported.get("bank_id") == contract.get("kernel_bank_id") == (contract.get("kernel_group_id", -1) & 0xffff) and
            imported.get("flags_name") in ("normal", "host_only") and
            isinstance(imported.get("flags"), int), "DMA-BUF allocation/import metadata differs")
    for pointer in (allocation.get("gpu_pointer"), imported.get("address")):
        require(isinstance(pointer, int) and pointer > 0 and pointer % 4096 == 0,
                "DMA-BUF allocation/import address is not page aligned")
    require(registry.get("registered_types_shared") is True and registry.get("glibcxx_cxx11_abi") == 1 and
            registry.get("pybind_internals_id") ==
            f"__pybind11_internals_v5_gcc_libstdcpp_cxxabi{registry.get('gxx_abi_version')}__",
            "DMA-BUF bridge pyxrt registry/ABI differs")
    build = contract.get("build", {})
    require(set(build) == {"xrt_bridge", "hip_allocation"}, "DMA-BUF extension build evidence missing")
    for label, source in (("xrt_bridge", "xrt_dmabuf_bindings.cpp"),
                          ("hip_allocation", "hip_dmabuf_bindings.cpp")):
        info = build[label]
        closure = info.get("source_sha256", {})
        require({"experiments/ffn_partition/dmabuf_output.py", "experiments/ffn_partition/" + source}.issubset(closure),
                "DMA-BUF extension source closure missing")
        for path, digest in closure.items():
            valid_hash(digest)
            if path in report.get("provenance", {}).get("source_sha256", {}):
                require(report["provenance"]["source_sha256"][path] == digest,
                        "DMA-BUF extension/runtime source identity differs")
        valid_hash(info.get("build_fingerprint"))
        valid_hash(info.get("binding_library_sha256"))
    bridge = build["xrt_bridge"]
    require(bridge.get("registry") == registry and bridge.get("expected_pybind_internals_id") == registry["pybind_internals_id"],
            "DMA-BUF bridge build/loaded registry differs")
    for field in ("pyxrt_sha256", "xrt_library_sha256"):
        valid_hash(bridge.get(field))
    for field in ("xrt_header_sha256", "pybind_header_sha256"):
        require(bool(bridge.get(field)), "DMA-BUF dependency headers missing")
        for digest in bridge[field].values():
            valid_hash(digest)
    require(len(build["hip_allocation"].get("runtime_dependency_sha256", {})) == 4,
            "DMA-BUF HIP/HSA headers and runtime library identities missing")
    for digest in build["hip_allocation"]["runtime_dependency_sha256"].values():
        valid_hash(digest)


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
                           "--native-root", str(args.native_root), "--accuracy-policy", args.native_accuracy_policy]
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
                for flag in ("shared_intermediate", "mapped_npu_output", "bfp16_native_layout", "split_m32_a", "preconvert_b", "preconvert_a", "dmabuf_gpu_output", "dmabuf_gpu_input"):
                    if getattr(args, flag, False):
                        command += ["--" + flag.replace("_", "-")]
                for name, default in (("down_output_layout", "compact"), ("swiglu_reuse", 2), ("gpu_variant", "original")):
                    value = getattr(args, name, default)
                    if value != default:
                        command += ["--" + name.replace("_", "-"), str(value)]
            jobs.append(dict(id=tag, variant=variant, mode=mode, block=block, npu_channels=p,
                iterations=iterations, npu_arithmetic="bfp16" if p else "native_unmodified",
                accuracy_policy="report" if p else args.native_accuracy_policy, command=command, report_path=report_path,
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
    policy = getattr(args, "native_accuracy_policy", "strict")
    require(policy in ("strict", "report") and job.get("accuracy_policy", "strict") == policy,
            "native accuracy policy differs from planned comparison")
    require(report.get("status") in COMPLETED_STATUSES and
            (policy == "report" or report["status"] == "passed"), "native report did not complete under requested policy")
    expected = dict(m=512, hidden=4096, intermediate=14336, npu_rows=256,
                    seed=args.seed, warmup=args.warmup, iterations=job["iterations"],
                    mode="latency" if job["mode"] == "ordinary" else "diagnostic")
    config = report.get("config", {})
    require(all(config.get(k) == v for k, v in expected.items()) and
            config.get("accuracy_policy", "strict") == policy, "native configuration differs")
    required = {f"run{run}_input{idx}_{mode}_{stage}_{owner}" for run, idx in enumerate((0, 1, 2, 0))
                for mode in ("baseline", "native") for stage in ("gate", "up", "output")
                for owner in ("all", "gpu_rows", "npu_rows")}
    required.update(f"run{run}_input{idx}_native_vs_gpu_{stage}" for run, idx in enumerate((0, 1, 2, 0))
                    for stage in ("gate", "up", "output"))
    checks = report.get("correctness", {})
    require(required.issubset(checks), "native initial numerical checks missing")
    for name, metric in checks.items():
        passed = validate_metric(metric, "strict" if "_baseline_" in name or name.endswith("_baseline") else policy)
        require(metric.get("numerical_passed") is passed and metric.get("structural_passed") is True,
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
    samples = report.get("samples", [])
    require(len(warmups) == 2 * args.warmup and len(samples) == 2 * job["iterations"], "native samples missing")
    for group, indexes in ((warmups, range(-args.warmup, 0)), (samples, range(job["iterations"]))):
        for mode in ("baseline", "native"):
            require(sorted(s.get("iteration") for s in group if s.get("mode") == mode) == list(indexes),
                    "native missing or duplicate iteration")
    for s in warmups + samples:
        benchmark_stats([s["wall_us"]])
        passed = validate_metric(s.get("accuracy", {}), "strict" if s["mode"] == "baseline" else policy)
        require(s.get("correctness_passed") is passed and s["accuracy"].get("numerical_passed") is passed and
                s["accuracy"].get("structural_passed") is True and s.get("accepted", True) is True and
                s.get("input_index") == s["iteration"] % 2 and
                s.get("completed_npu_dispatches") == (2 if s["mode"] == "native" else 0), "native timed validation failed")
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
    completed = 2 * (4 + args.warmup + job["iterations"])
    require(report.get("completed_npu_dispatches") == report.get("expected_npu_dispatches") == completed,
            "native total completion count mismatch")
    accuracy = accuracy_summary([*checks.values(), *[s["accuracy"] for s in warmups + samples]])
    status = "passed" if accuracy["passed"] else "completed_with_accuracy_deviations"
    require(report["status"] == status, "native numerical status was relabeled")
    if policy == "report" or "accuracy" in report:
        require(report.get("accuracy") == accuracy, "native numerical summary differs")
    return dict(completed_npu_dispatches=completed, timed_invocations=len(samples), explicit_checks=len(checks),
                status=status, accuracy_policy=policy, accuracy_passed=accuracy["passed"], accuracy_accepted=True,
                accuracy_status=accuracy["accuracy_status"], fixture=fixture_identity(report, "native"))



def validate_dmabuf_input(report, part, args):
    """Require explicit GPU-owned input evidence when DMA-BUF input is requested."""
    enabled = getattr(args, "dmabuf_gpu_input", False)
    if not enabled:
        return
    npu, runtime = part.get("npu", {}), part.get("runtime", {})
    require(report.get("config", {}).get("dmabuf_gpu_input", False) is True and
            npu.get("gpu_input_dmabuf", False) is True and
            runtime.get("gpu_input_dmabuf", False) is True,
            "DMA-BUF GPU input was not executed on every evidence layer")
    require(report.get("config", {}).get("dmabuf_gpu_output", False) is True,
            "DMA-BUF GPU input requires the DMA-BUF output path")
    contract = npu.get("gpu_input_dmabuf_contract", {})
    require(contract.get("direction") == "gpu_write_to_npu_read" and
            contract.get("host_input_staging") == "none" and
            contract.get("copy_fallback") is False and
            contract.get("fd_closed_after_import") is True and
            contract.get("input_argument") == 3,
            "DMA-BUF GPU input contract differs")
    allocation, imported = contract.get("allocation", {}), contract.get("imported_bo", {})
    offset = allocation.get("export_offset")
    require(type(offset) is int and offset >= 0 and offset % 4096 == 0 and
            isinstance(allocation.get("nbytes"), int) and allocation["nbytes"] > 0 and
            allocation["nbytes"] % 4096 == 0 and
            allocation.get("export_fd_closed") is True,
            "DMA-BUF GPU input allocation evidence differs")
    require(offset == 0 or contract.get("sub_buffer_used") is True,
            "nonzero DMA-BUF GPU input offset requires explicit sub-buffer evidence")
    if contract.get("sub_buffer_used"):
        parent = contract.get("imported_backing_bo", {})
        require(parent.get("address", -1) + offset == imported.get("address") and
                contract.get("sub_buffer_offset") == offset,
                "DMA-BUF GPU input sub-buffer offset/address evidence differs")
    require(imported.get("bank_id") == contract.get("kernel_bank_id") and
            imported.get("nbytes") == allocation.get("nbytes"),
            "DMA-BUF GPU input import evidence differs")
    registry = contract.get("registry", {})
    require(registry.get("registered_types_shared") is True and
            registry.get("glibcxx_cxx11_abi") == 1,
            "DMA-BUF GPU input pybind registry differs")
    build = contract.get("build", {})
    for label, source in (("xrt_bridge", "xrt_dmabuf_bindings.cpp"),
                          ("hip_allocation", "hip_dmabuf_bindings.cpp")):
        item = build.get(label, {})
        require(isinstance(item.get("build_fingerprint"), str) and
                len(item.get("build_fingerprint", "")) == 64 and
                isinstance(item.get("binding_library_sha256"), str) and
                len(item.get("binding_library_sha256", "")) == 64,
                f"DMA-BUF GPU input {label} build evidence differs")
        closure = item.get("source_sha256", {})
        require({"experiments/ffn_partition/dmabuf_output.py",
                 "experiments/ffn_partition/" + source}.issubset(closure),
                f"DMA-BUF GPU input {label} source closure differs")
    adapter_sources = contract.get("source_sha256", {})
    require(isinstance(adapter_sources.get("experiments/ffn_partition/dmabuf_input.py"), str) and
            isinstance(adapter_sources.get("experiments/ffn_partition/dmabuf_output.py"), str),
            "DMA-BUF GPU input adapter source hashes missing")
    require(part.get("gpu_input_sync_count") == part.get("completed_candidate_calls"),
            "DMA-BUF GPU input total synchronization count differs")



def validate_candidate(report, job, args):
    require(report.get("status") in COMPLETED_STATUSES, "candidate report did not complete")
    require(report.get("config", {}).get("gpu_device_diagnostics", False) is False and
            report.get("measurement_mode", "ordinary_latency") != "gpu_device_diagnostic" and
            report.get("ordinary_headline_eligible", True) is True,
            "GPU diagnostic timing cannot enter ordinary native comparison")
    expected = dict(m=512, hidden=4096, intermediate=14336, seed=12832, npu_channels=str(job["npu_channels"]),
                    warmup=args.warmup, iterations=job["iterations"], npu_arithmetic="bfp16", accuracy_policy="report")
    require(all(report.get("config", {}).get(k) == v for k, v in expected.items()), "candidate configuration differs")
    require(report.get("npu_options") == candidate_options(args) and report.get("copy_output_bits") is False,
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
    dmabuf = getattr(args, "dmabuf_gpu_output", False)
    require(all(npu.get(k) == v for k, v in dict(arithmetic="bfp16", npu_arithmetic="bfp16", compute_format="bfp16",
            weight_repacking=False, full_weight_buffers=True, full_intermediate=14336, channel_start=0, channels=p,
            columns_requested=8, worker_count=32, launches_per_run=2,
            host_output_readback="gpu_owned_dmabuf" if dmabuf else "borrowed_until_consumed").items()),
            "candidate direct-buffer/eight-column arithmetic contract differs")
    require(report.get("gpu_baseline", {}).get("backend") == "heteromosaic_original_gpu_packed", "GPU control changed")
    if getattr(args, "gpu_variant", "original") == "original":
        require(part.get("gpu", {}).get("backend") == "heteromosaic_original_gpu_packed" and
                part["gpu"].get("source_sha256") == report["gpu_baseline"].get("source_sha256"), "GPU suffix changed")
    else:
        validate_teammate_gpu(part, report, p)
    shared = getattr(args, "shared_intermediate", False)
    dmabuf = getattr(args, "dmabuf_gpu_output", False)
    dmabuf_input = getattr(args, "dmabuf_gpu_input", False)
    require(bool(npu.get("shared_intermediate", False)) == shared and
            bool(npu.get("mapped_output", False)) == getattr(args, "mapped_npu_output", False),
            "candidate runtime options differ")
    validate_optimized_artifacts(report, part, args, p)
    validate_dmabuf_output(report, part, args)
    validate_dmabuf_input(report, part, args)
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
            if shared:
                require(diag.get("shared_input_completed_consumptions") == calls and
                        diag.get("down_input_host_write_count") == 0, "shared intermediate consumption mismatch")
            if dmabuf:
                require(diag.get("gpu_output_dmabuf") is True and diag.get("gpu_output_sync_count") == calls and
                        diag.get("final_output_bo_reads") == 0 and diag.get("final_output_h2d_copies") == 0 and
                        sample.get("diagnostics", {}).get("gpu_output_dmabuf") is True and
                        sample["diagnostics"].get("final_output_h2d_copies") == 0,
                        "DMA-BUF per-call output synchronization/copy evidence differs")
            if dmabuf_input:
                require(diag.get("gpu_input_dmabuf") is True and
                        diag.get("gpu_input_sync_count") == calls and
                        diag.get("host_input_write_count") == 0 and
                        sample.get("diagnostics", {}).get("gpu_input_dmabuf") is True and
                        sample["diagnostics"].get("input_gpu_to_gpu_copies") == 1 and
                        sample["diagnostics"].get("host_input_copies") == 0,
                        "DMA-BUF per-call input synchronization/copy evidence differs")
    require(seen[("candidate", 0)] != seen[("candidate", 1)], "changed input produced stale candidate output")
    if ("baseline", 0) in seen and ("baseline", 1) in seen:
        require(seen[("baseline", 0)] != seen[("baseline", 1)], "changed input produced stale GPU output")
    require(named == part.get("correctness"), "sample/named correctness evidence differs")
    expected_calls = 8 + 2 * (args.warmup + job["iterations"])
    require(calls == expected_calls == part.get("completed_candidate_calls") == part.get("expected_npu_dispatches_per_stage") and
            part.get("completed_npu_dispatches_by_stage") == dict(swiglu=calls, down=calls) and
            part.get("input_write_counts_by_stage") == dict(
                swiglu=[0 if dmabuf_input else calls, 1, 1], down=[0 if shared else calls, 1]) and
            part.get("fixed_weight_upload_counts") == dict(gate=1, up=1, down=1), "candidate total completion/upload mismatch")
    accuracy = accuracy_summary(list(named.values()))
    if dmabuf:
        require(part.get("gpu_output_sync_count") == calls, "DMA-BUF total output synchronization count differs")
    if dmabuf_input:
        require(part.get("gpu_input_sync_count") == calls, "DMA-BUF total input synchronization count differs")
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
                numerical_pass = native["accuracy_passed"] and candidate["accuracy_passed"]
                comparisons.append(dict(block=native["block"], npu_channels=candidate["npu_channels"],
                    native_job=native["job"], candidate_job=candidate["job"],
                    native_accuracy_passed=native["accuracy_passed"], candidate_accuracy_passed=candidate["accuracy_passed"],
                    native_accuracy_policy=native["accuracy_policy"], candidate_accuracy_policy=candidate["accuracy_policy"],
                    comparison_kind="within_original_tolerance" if numerical_pass else "experimental_latency_with_numerical_deviations",
                    native_over_candidate_latency_ratio=ratio, speedup_vs_native=ratio if numerical_pass else None,
                    gpu_control_native_over_candidate=native["baseline_us"]["median_us"] / candidate["baseline_us"]["median_us"]))
    return dict(status=manifest["status"], ordinary=rows, comparisons=comparisons,
        native_failed=native_failed, full_packed_weights_and_inputs_match=same_fixtures, common_power_mode=same_power,
        fixture=fixtures[0] if same_fixtures else None,
        claim_scope="synthetic complete prefill FFN only; not model prefill/TTFT or pretrained accuracy",
        notes=["Raw ordinary wall samples determine medians; native diagnostics are excluded.",
               "Native and candidate use different host wrappers, with their own fresh GPU controls.",
               "Native ordinary timing has a conservative redundant readiness sync inside its binding.",
               "Power snapshots are boundary observations, not continuous clock telemetry.",
               "Report-mode native numerical deviations retain an experimental latency ratio, not a tolerance-validated speedup.",
               "No native comparison is admitted after a failed native job, mismatched fixtures, or mismatched power."])


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--native-library", type=Path)
    parser.add_argument("--driver-include", type=Path)
    parser.add_argument("--native-accuracy-policy", choices=("strict", "report"), default="strict",
                        help="report permits native numerical deviations; GPU controls and structural checks remain strict")
    parser.add_argument("--npu-channels", type=comma_ints, default=[2560, 2816])
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--native-diagnostic", action="store_true")
    parser.add_argument("--shared-intermediate", action="store_true")
    parser.add_argument("--mapped-npu-output", action="store_true")
    parser.add_argument("--dmabuf-gpu-output", action="store_true")
    parser.add_argument("--dmabuf-gpu-input", action="store_true",
                        help="use a GPU-owned DMA-BUF SwiGLU input; requires --dmabuf-gpu-output")
    parser.add_argument("--down-output-layout", choices=("compact", "row_major"), default="compact")
    parser.add_argument("--swiglu-reuse", type=int, choices=(2, 4), default=2)
    parser.add_argument("--bfp16-native-layout", action="store_true")
    parser.add_argument("--split-m32-a", action="store_true")
    parser.add_argument("--preconvert-b", action="store_true")
    parser.add_argument("--preconvert-a", action="store_true")
    parser.add_argument("--gpu-variant", choices=("original", "teammate"), default="original")
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
    if args.split_m32_a and (not args.bfp16_native_layout or args.swiglu_reuse != 4):
        parser.error("--split-m32-a requires --bfp16-native-layout and --swiglu-reuse 4")
    if args.preconvert_b and not args.bfp16_native_layout:
        parser.error("--preconvert-b requires --bfp16-native-layout")
    if args.preconvert_a and (not args.split_m32_a or not args.preconvert_b):
        parser.error("--preconvert-a requires --split-m32-a and --preconvert-b")
    if args.dmabuf_gpu_output:
        if args.mapped_npu_output:
            parser.error("--dmabuf-gpu-output is incompatible with --mapped-npu-output")
        args.down_output_layout = "row_major"
    if args.dmabuf_gpu_input and not args.dmabuf_gpu_output:
        parser.error("--dmabuf-gpu-input requires --dmabuf-gpu-output")
    if (not 1 <= args.iterations <= 1000 or not 0 <= args.warmup <= 100 or
            not 1 <= args.diagnostic_iterations <= 1000 or args.job_timeout <= 0):
        parser.error("invalid iteration/warmup/timeout bounds")
    if not all(256 <= p <= 8192 and p % 256 == 0 for p in args.npu_channels):
        parser.error("comparison supports aligned P256..8192 in steps of 256")
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
        acceptance=f"native {args.native_accuracy_policy}; GPU strict; direct BFP16 candidate report; structural hard failures")
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
