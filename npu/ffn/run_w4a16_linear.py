"""Validate the small W4A16 decode core and its output/input-channel slices.

``--self-test`` checks payload packing and slice algebra without MLIR-AIE or
XRT. An NPU run requires artifacts compiled with the same K and N. Launch
times cover a standalone core; they are not FFN or model-inference latency.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from reference import W4A16, bf16, pack_int4


def pack_payload(weight):
    """Pack canonical W4A16 into the core's three-region uint8 BO payload."""
    if weight.group_size != 128:
        raise ValueError("the AIE core requires group_size=128")
    n, k = weight.shape
    if k % 128 or n % 64:
        raise ValueError("the AIE core requires K aligned to 128 and N aligned to 64")
    scale_bits = (bf16(weight.scales).view(np.uint32) >> 16).astype("<u2")
    return np.concatenate((weight.packed.reshape(-1), scale_bits.view(np.uint8).reshape(-1),
                           weight.zeros.astype(np.uint8).reshape(-1)))


def unpack_payload(payload, k, n):
    """Independent host decoder of the documented byte regions."""
    payload = np.asarray(payload)
    qbytes, groups = n * k // 2, n * (k // 128)
    if payload.dtype != np.uint8 or payload.shape != (qbytes + 3 * groups,):
        raise ValueError("payload has the wrong dtype or size")
    q = payload[:qbytes].reshape(n, k // 2)
    bits = payload[qbytes:qbytes + 2 * groups].copy().view("<u2").astype(np.uint32) << 16
    scales = bits.view(np.float32).reshape(n, k // 128)
    zeros = payload[qbytes + 2 * groups:].reshape(n, k // 128)
    return W4A16(q, scales, zeros, 128)


def random_weight(rng, n, k):
    q = rng.integers(0, 16, (n, k), dtype=np.uint8)
    scales = rng.uniform(0.005, 0.08, (n, k // 128)).astype(np.float32)
    zeros = rng.integers(0, 16, (n, k // 128), dtype=np.uint8)
    return W4A16(pack_int4(q), scales, zeros, 128)


def projection(x, weight):
    return bf16(bf16(x) @ weight.dequantize(bf16_io=True).T)


def self_test():
    rng = np.random.default_rng(813)
    cases = 0
    for k in (128, 256):
        full = random_weight(rng, 192, k)
        x = rng.normal(size=k).astype(np.float32)
        full_result = projection(x, full)
        for start in (0, 64, 128):
            part = full.output_slice(start, start + 64)
            decoded = unpack_payload(pack_payload(part), k, 64)
            np.testing.assert_array_equal(decoded.dequantize(True), part.dequantize(True))
            np.testing.assert_array_equal(projection(x, decoded), full_result[start:start + 64])
            cases += 1
    # Down projections split K on a quantization-group boundary. Compare the
    # sum before final output rounding, as cross-device reduction would do.
    full = random_weight(rng, 64, 256)
    x = bf16(rng.normal(size=256).astype(np.float32))
    shards = [unpack_payload(pack_payload(full.input_slice(start, start + 128)), 128, 64)
              for start in (0, 128)]
    partial_sum = sum(x[start:start + 128] @ shard.dequantize(True).T
                      for start, shard in zip((0, 128), shards))
    np.testing.assert_allclose(partial_sum, x @ full.dequantize(True).T, rtol=2e-5, atol=2e-5)
    return {"host_self_test": "passed", "output_slice_cases": cases,
            "input_slice_cases": 1, "hardware_test": False}


def emit_result(result, output_path):
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print(text, end="")


def check_result(actual, expected, opts):
    actual = np.asarray(actual).astype(np.float32).reshape(opts.N)
    finite = bool(np.all(np.isfinite(actual)))
    errors = np.abs(actual - expected)
    exact_zero = not np.any(expected)
    passed = finite and bool(np.allclose(actual, expected,
                                         rtol=0 if exact_zero else opts.rtol,
                                         atol=0 if exact_zero else opts.atol))
    return {"correctness": "passed" if passed else "failed",
            "finite": finite,
            "max_abs_error": float(np.max(errors)) if finite else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--xclbin")
    parser.add_argument("--insts")
    parser.add_argument("-K", type=int, default=128)
    parser.add_argument("-N", type=int, default=64)
    parser.add_argument("--iters", type=int, default=10)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--rtol", type=float, default=0.01)
    parser.add_argument("--atol", type=float, default=0.001)
    parser.add_argument("--json", type=Path, help="write validation and launch timing metrics to this JSON file")
    opts = parser.parse_args()
    if opts.self_test:
        emit_result(self_test(), opts.json)
        return
    if not opts.xclbin or not opts.insts:
        parser.error("--xclbin and --insts are required for an NPU run")
    if opts.K <= 0 or opts.K % 128 or opts.N <= 0 or opts.N % 64:
        parser.error("K must be positive/aligned to 128, N positive/aligned to 64")
    if opts.iters < 1 or opts.warmup < 0:
        parser.error("iters must be positive and warmup nonnegative")
    if not np.isfinite(opts.rtol) or not np.isfinite(opts.atol) or opts.rtol < 0 or opts.atol < 0:
        parser.error("tolerances must be finite and nonnegative")

    from ml_dtypes import bfloat16
    from xrt_runner import XrtRunner, load_manifest

    manifest = load_manifest(opts.xclbin, opts.insts, "w4a16_linear_bf16")
    if manifest.get("k") != opts.K or manifest.get("n") != opts.N or manifest.get("group_size") != 128:
        raise ValueError("requested K/N/group_size do not match the compiled artifact manifest")

    rng = np.random.default_rng(813)
    full = random_weight(rng, 2 * opts.N, opts.K)
    # Exercise a nonzero output-channel offset in the host slicing adapter.
    weight = full.output_slice(opts.N, 2 * opts.N)
    payload = pack_payload(weight)
    x = rng.normal(size=opts.K).astype(bfloat16)
    runner = XrtRunner(opts.xclbin, opts.insts,
                       [((opts.K,), bfloat16), (payload.shape, np.uint8), ((opts.N,), bfloat16)])

    # Each case uploads different data into the same BOs. Zero cases detect
    # stale output/accumulation and unsigned-int4/zero-point mistakes.
    zeros = rng.integers(0, 16, (opts.N, opts.K // 128), dtype=np.uint8)
    zero_weight = W4A16(pack_int4(np.repeat(zeros, 128, axis=1)),
                        weight.scales.copy(), zeros, 128)
    down_full = random_weight(rng, opts.N, 2 * opts.K)
    down_shard = down_full.input_slice(opts.K, 2 * opts.K)
    down_x_full = rng.normal(size=2 * opts.K).astype(bfloat16)
    cases = [
        ("random_output_slice", x, weight, {"output_slice": [opts.N, 2 * opts.N]}),
        ("zero_activations", np.zeros(opts.K, dtype=bfloat16), weight, {}),
        ("quantized_equals_zero_point", x, zero_weight, {}),
        ("nonzero_input_slice", down_x_full[opts.K:].copy(), down_shard,
         {"input_slice": [opts.K, 2 * opts.K]}),
    ]
    case_results = []
    for name, case_x, case_weight, metadata in cases:
        actual, elapsed_us = runner.run([case_x, pack_payload(case_weight)])
        expected = projection(case_x.astype(np.float32), case_weight)
        result = {"name": name, **metadata, **check_result(actual, expected, opts),
                  "launch_us": float(elapsed_us)}
        case_results.append(result)

    # Only the representative random shard is timed repeatedly. Input upload
    # and output download are outside XrtRunner's launch-to-completion timer.
    timings = []
    timing_passed = True
    expected = projection(x.astype(np.float32), weight)
    for i in range(opts.warmup + opts.iters):
        actual, elapsed_us = runner.run([x, payload])
        timing_passed &= check_result(actual, expected, opts)["correctness"] == "passed"
        if i >= opts.warmup:
            timings.append(elapsed_us)
    passed = timing_passed and all(case["correctness"] == "passed" for case in case_results)
    result = {"correctness": "passed" if passed else "failed", "M": 1, "K": opts.K, "N": opts.N,
              "artifact": {"xclbin": str(Path(opts.xclbin).resolve()),
                           "insts": str(Path(opts.insts).resolve()), **manifest},
              "rtol": opts.rtol, "atol": opts.atol, "cases": case_results,
              "timing_case": "random_output_slice", "timing_outputs_verified": timing_passed,
              "median_launch_us": float(np.median(timings)), "iterations": opts.iters,
              "warmup": opts.warmup,
              "timing_scope": "XRT launch to completion; excludes host input/output copies",
              "down_partial_rounding": "Core output is BF16. CPU slice algebra tests reduce FP32 partials; "
                                       "device-partial BF16 rounding and reduction need separate end-to-end validation.",
              "implementation": "scalar correctness-first, not optimized"}
    emit_result(result, opts.json)
    if not passed:
        raise AssertionError("one or more W4A16 NPU validation cases failed; see JSON metrics")


if __name__ == "__main__":
    main()
