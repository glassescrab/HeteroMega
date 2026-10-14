"""Check fused BF16 SiLU*up on NPU against exact and staged BF16 references."""

import argparse
import json
from pathlib import Path

import numpy as np
from ml_dtypes import bfloat16

from xrt_runner import XrtRunner, load_manifest


def exact_silu(x):
    x = np.asarray(x, dtype=np.float32)
    e = np.exp(-np.abs(x))
    return x * np.where(x >= 0, 1.0 / (1.0 + e), e / (1.0 + e))


def cases(length):
    rng = np.random.default_rng(2026)
    yield "normal", rng.normal(0, 2, length), rng.normal(0, 2, length)
    yield "wide", np.linspace(-16, 16, length), rng.uniform(-4, 4, length)
    yield "zeros", np.zeros(length), rng.normal(0, 2, length)
    special = np.array([-64, -16, -8, -4, -1, -0.01, 0, 0.01, 1, 4, 8, 16, 64])
    yield "tails", np.resize(special, length), np.resize([-2, -1, 0, 1, 2], length)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xclbin", default="build/final.xclbin")
    p.add_argument("--insts", default="build/insts.bin")
    p.add_argument("--length", type=int, help="optional check against compiled length")
    p.add_argument("--iterations", type=int, default=20)
    p.add_argument("--rtol", type=float, default=0.04)
    p.add_argument("--atol", type=float, default=0.02)
    p.add_argument("--json", type=Path)
    args = p.parse_args()
    if not np.isfinite([args.rtol, args.atol]).all() or min(args.rtol, args.atol) < 0:
        p.error("tolerances must be finite and nonnegative")
    manifest = load_manifest(args.xclbin, args.insts, "silu_mul_bf16")
    if args.length is not None and args.length != manifest["size"]:
        p.error("--length must match the compiled artifact; rebuild to change it")
    args.length = manifest["size"]
    if args.length <= 0 or args.iterations <= 0:
        p.error("length and iterations must be positive")
    runner = XrtRunner(args.xclbin, args.insts, [((args.length,), bfloat16)] * 3)
    results = []
    for name, gate, up in cases(args.length):
        gate, up = gate.astype(bfloat16), up.astype(bfloat16)
        g, u = gate.astype(np.float32), up.astype(np.float32)
        expected = (exact_silu(g) * u).astype(bfloat16).astype(np.float32)
        staged = (exact_silu(g).astype(bfloat16).astype(np.float32) * u).astype(bfloat16).astype(np.float32)
        actual, _ = runner.run([gate, up])
        actual = actual.astype(np.float32)
        error = np.abs(actual - staged)
        allowed = args.atol + args.rtol * np.abs(staged)
        ok = np.isfinite(actual).all() and np.all(error <= allowed)
        row = dict(case=name, passed=bool(ok), max_abs_error=float(error.max()),
                   rms_error=float(np.sqrt(np.mean(error * error))),
                   max_abs_vs_single_round_bf16=float(np.abs(actual - expected).max()),
                   failed_elements=int(np.count_nonzero(error > allowed)))
        results.append(row)
        print(json.dumps(row), flush=True)
        if not ok:
            worst = int(np.argmax(error / np.maximum(allowed, np.finfo(np.float32).tiny)))
            row["worst_violation"] = dict(gate=float(g[worst]), up=float(u[worst]),
                                           actual=float(actual[worst]), expected=float(staged[worst]))
    timings = []
    repeated_outputs_passed = True
    for _ in range(args.iterations):
        repeated, elapsed = runner.run([gate, up])
        repeated_outputs_passed &= bool(np.allclose(repeated.astype(np.float32), staged,
                                                     rtol=args.rtol, atol=args.atol))
        timings.append(elapsed)
    report = dict(kernel="silu_mul_bf16", length=args.length, dtype="bfloat16",
                  rtol=args.rtol, atol=args.atol, reference="BF16(SiLU_BF16(gate) * up)", cases=results, iterations=args.iterations,
                  launch_wait_us_median=float(np.median(timings)),
                  launch_wait_us_min=float(min(timings)),
                  timing_scope="XRT dispatch + NPU DMA/compute + wait; excludes BO input/output sync and setup",
                  artifact=manifest, end_to_end_llm_validated=False)
    report["repeated_outputs_passed"] = repeated_outputs_passed
    report["passed"] = all(row["passed"] for row in results) and repeated_outputs_passed
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise AssertionError("fused SiLU*up NPU checks failed; see JSON metrics")
    print("PASS: fused SiLU*up NPU checks")


if __name__ == "__main__":
    main()
