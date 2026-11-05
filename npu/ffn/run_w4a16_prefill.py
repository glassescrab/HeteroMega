"""Validate and time a compiled multi-token tiled W4A16 prefill projection.

Use --cases full on a small build to check changed activations, exact zeros,
zero quantized weights, and nonzero down-projection input slices. Use smoke
for a large model-shaped shard. Every timing iteration is also verified.
This measures standalone XRT launch latency, not FFN/model inference latency.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from prefill_reference import (LAYOUT_VERSION, TILE_K, TILE_M, TILE_N,
                               WEIGHT_TILE_BYTES, error_metrics, pack_activations,
                               pack_weights, projection_reference, unpack_output,
                               validate_shape)
from reference import W4A16, pack_int4
from xrt_runner import XrtRunner, load_manifest


def random_weight(rng, n, k):
    q = rng.integers(0, 16, (n, k), dtype=np.uint8)
    scales = rng.uniform(0.003, 0.04, (n, k // TILE_K)).astype(np.float32)
    zeros = rng.integers(0, 16, scales.shape, dtype=np.uint8)
    return W4A16(pack_int4(q), scales, zeros, TILE_K)


def onehot_lane_cases(m, k, n):
    """Exact deterministic probes for metadata broadcasts and int4 lane order."""
    validate_shape(m, k, n)
    x = np.zeros((m, k), np.float32)
    x[np.arange(m), np.arange(m) % k] = 1.0
    channels = np.arange(n)
    groups = k // TILE_K
    zeros = np.broadcast_to((channels % 16).astype(np.uint8)[:, None], (n, groups)).copy()
    scales = np.broadcast_to(np.exp2(-(channels % 4)).astype(np.float32)[:, None], (n, groups)).copy()
    metadata_weight = W4A16(pack_int4(np.full((n, k), 9, np.uint8)), scales, zeros, TILE_K)
    lane_q = ((np.arange(k)[None, :] + 3 * channels[:, None]) % 16).astype(np.uint8)
    lane_weight = W4A16(pack_int4(lane_q), np.ones((n, groups), np.float32),
                        np.zeros((n, groups), np.uint8), TILE_K)
    return [
        ("onehot_metadata_lanes", x, metadata_weight,
         {"comparison": "exact", "onehot_k": "row % K", "q": 9,
          "zero_pattern": "n % 16", "scale_pattern": "2**-(n % 4)"}),
        ("onehot_quantized_lanes", x, lane_weight,
         {"comparison": "exact", "onehot_k": "row % K", "q_pattern": "(k + 3*n) % 16",
          "zero": 0, "scale": 1}),
    ]


def validate_manifest(manifest, opts):
    expected = {"m": opts.M, "k": opts.K, "n": opts.N,
                "tile_m": TILE_M, "tile_k": TILE_K, "tile_n": TILE_N}
    for name, value in expected.items():
        if manifest.get(name) != value:
            raise ValueError(f"requested {name}={value} does not match compiled manifest {manifest.get(name)!r}")
    if opts.columns is not None and opts.columns != manifest.get("cols"):
        raise ValueError("requested column count does not match compiled manifest")


def emit_result(result, output_path):
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text)
    print(text, end="")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xclbin", required=True, type=Path)
    parser.add_argument("--insts", required=True, type=Path)
    parser.add_argument("-M", type=int, default=128)
    parser.add_argument("-K", type=int, default=4096)
    parser.add_argument("-N", type=int, default=2048)
    parser.add_argument("-co", "--columns", type=int)
    parser.add_argument("--cases", choices=("smoke", "basic", "full"), default="basic")
    parser.add_argument("--iters", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--rtol", type=float, default=0.03)
    parser.add_argument("--atol", type=float, default=0.05)
    parser.add_argument("--l2-limit", type=float, default=0.02)
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--json", type=Path)
    opts = parser.parse_args()
    try:
        mb, kb, nb = validate_shape(opts.M, opts.K, opts.N)
    except ValueError as exc:
        parser.error(str(exc))
    if opts.iters < 1 or opts.warmup < 0:
        parser.error("iters must be positive; warmup must be nonnegative")
    if any(not np.isfinite(t) or t < 0 for t in (opts.rtol, opts.atol, opts.l2_limit)):
        parser.error("tolerances must be finite and nonnegative")

    # Reject binary, instruction, and shape mismatches before XRT allocation.
    manifest = load_manifest(opts.xclbin, opts.insts, "w4a16_prefill_bf16")
    validate_manifest(manifest, opts)
    from ml_dtypes import bfloat16

    rng = np.random.default_rng(opts.seed)
    full = random_weight(rng, opts.N + TILE_N, opts.K)
    weight = full.output_slice(TILE_N, TILE_N + opts.N)
    x = rng.normal(0, 0.25, (opts.M, opts.K)).astype(np.float32)
    a_buffer = pack_activations(x).view(bfloat16)
    w_buffer = pack_weights(weight)
    runner = XrtRunner(opts.xclbin, opts.insts,
                       [((opts.M * opts.K,), bfloat16),
                        ((nb * kb * WEIGHT_TILE_BYTES,), np.uint8),
                        ((opts.M * opts.N,), bfloat16)])

    cases = [("random_nonzero_output_slice", x, weight,
              {"output_slice": [TILE_N, TILE_N + opts.N]})]
    if opts.cases in ("basic", "full"):
        changed = rng.normal(0, 0.25, x.shape).astype(np.float32)
        cases.extend([("changed_activations", changed, weight, {}),
                      ("zero_activations", np.zeros_like(x), weight, {})])
    if opts.cases == "full":
        zero_q = np.repeat(weight.zeros, TILE_K, axis=1).astype(np.uint8)
        zero_weight = W4A16(pack_int4(zero_q), weight.scales.copy(), weight.zeros.copy(), TILE_K)
        down_full = random_weight(rng, opts.N, opts.K + TILE_K)
        down = down_full.input_slice(TILE_K, opts.K + TILE_K)
        down_x = rng.normal(0, 0.25, (opts.M, opts.K + TILE_K)).astype(np.float32)
        cases.extend([("quantized_equals_zero_point", x, zero_weight, {}),
                      ("nonzero_down_input_slice", down_x[:, TILE_K:].copy(), down,
                       {"input_slice": [TILE_K, opts.K + TILE_K]})])
        cases.extend(onehot_lane_cases(opts.M, opts.K, opts.N))

    case_results = []
    for name, case_x, case_weight, metadata in cases:
        actual, elapsed_us = runner.run([pack_activations(case_x).view(bfloat16), pack_weights(case_weight)])
        actual = unpack_output(np.asarray(actual).view(np.uint16).reshape(-1), opts.M, opts.N)
        expected = projection_reference(case_x, case_weight)
        exact = metadata.get("comparison") == "exact"
        metrics = error_metrics(actual, expected,
                                0.0 if exact else opts.rtol,
                                0.0 if exact else opts.atol,
                                0.0 if exact else opts.l2_limit)
        case_results.append({"name": name, "comparison": "exact" if exact else "tolerance",
                             **metadata, **metrics, "launch_us": float(elapsed_us)})

    # Reuse the original random buffers after other cases to detect stale
    # weights/results. Host DMA staging/copies are outside the launch timer.
    expected = projection_reference(x, weight)
    timings, timing_metrics = [], []
    for iteration in range(opts.warmup + opts.iters):
        actual, elapsed_us = runner.run([a_buffer, w_buffer])
        actual = unpack_output(np.asarray(actual).view(np.uint16).reshape(-1), opts.M, opts.N)
        metrics = error_metrics(actual, expected, opts.rtol, opts.atol, opts.l2_limit)
        timing_metrics.append(metrics)
        if iteration >= opts.warmup:
            timings.append(float(elapsed_us))
    timing_passed = all(item["correctness"] == "passed" for item in timing_metrics)
    passed = timing_passed and all(item["correctness"] == "passed" for item in case_results)
    median_us = float(np.median(timings))
    result = {
        "correctness": "passed" if passed else "failed", "mode": "prefill", "M": opts.M, "K": opts.K, "N": opts.N,
        "seed": opts.seed, "cases_mode": opts.cases,
        "artifact": {"xclbin": str(opts.xclbin.resolve()), "insts": str(opts.insts.resolve()), **manifest},
        "layout": LAYOUT_VERSION, "group_size": TILE_K,
        "compact_host_bytes": {"activations": a_buffer.nbytes, "weights": w_buffer.nbytes,
                               "output": 2 * opts.M * opts.N},
        "host_weight_replication_across_m": False, "host_activation_replication_across_n": False,
        "tolerances": {"max_error_atol": opts.atol, "max_error_rtol": opts.rtol, "relative_l2_limit": opts.l2_limit},
        "cases": case_results, "timing_case": "random_nonzero_output_slice",
        "timing_outputs_verified": timing_passed,
        "timing_max_abs_error": max((item["max_abs_error"] for item in timing_metrics if item["finite"]), default=None),
        "launch_us": timings, "median_launch_us": median_us, "iterations": opts.iters, "warmup": opts.warmup,
        "effective_gops": (2.0 * opts.M * opts.K * opts.N / (median_us * 1000.0)) if median_us > 0 else None,
        "timing_scope": "XRT launch to completion; excludes host input/output copies and CPU reference",
        "numerical_reference": "BF16 activation/dequantized weight, FP32 full-K accumulation, BF16 output; not AIE2P BFP16 emulation",
        "down_partial_rounding": "Kernel output rounds each device partial to BF16; reduced FFN correctness requires a separate test.",
        "implementation": "tiled prefill W4A16 projection; standalone NPU microbenchmark, no FFN or model latency claim",
    }
    emit_result(result, opts.json)
    if not passed:
        raise AssertionError("one or more prefill validation cases failed; inspect JSON metrics")


if __name__ == "__main__":
    main()
