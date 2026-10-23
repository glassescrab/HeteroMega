#!/usr/bin/env python3
"""Batch run_model_ffn.py without changing its synchronized generate(1) timer."""
import argparse
import csv
import json
import os
from pathlib import Path
import shlex
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
METHODS = {"gpu_original": ("gpu", "0"), "gpu_ffn_all": ("gpu", "1"), "heteromosaic": ("hetero", "0")}


def cases(args):
    for length in args.prompt_tokens:
        for round_id in range(args.rounds):
            order = args.methods if round_id % 2 == 0 else list(reversed(args.methods))
            for method in order:
                backend, ffn = METHODS[method]
                out = args.out / f"{method}-{length}-r{round_id}.result.json"
                cmd = [sys.executable, "-u", str(Path(__file__).with_name("run_model_ffn.py")),
                       "--ref", str(args.ref), "--out", str(out), "--build", args.build,
                       "--config", args.config, "--heterogeneity", backend, "--prompt-tokens", str(length),
                       "--reps", str(args.reps), "--new-tokens", str(args.new_tokens)]
                cmd += ["--dummy"] if args.dummy else ["--model", args.model or "MODEL_DIR"]
                env = dict(os.environ, HETEROMEGA_GPU_FFN=ffn)
                # PR #1's partial-channel mode omits the NPU output; these cases need the complete FFN.
                env.pop("HETEROMEGA_GPU_FFN_SPLIT", None)
                yield method, length, round_id, cmd, env, out


def signatures(runs):
    return {(tuple(r["warmup_ids"]), tuple(p["prefill_ids"]), tuple(p["generated_ids"]))
            for r in runs for p in r["reps"]}


def summarize(directory):
    groups = {}
    for path in sorted(directory.glob("*.result.json")):
        r = json.loads(path.read_text())
        groups.setdefault((r["method"], r["prompt_tokens"]), []).append(r)
    rows = []
    for (method, length), runs in sorted(groups.items()):
        times = [p["prefill_s"] * 1000 for r in runs for p in r["reps"]]
        baseline = groups.get(("gpu_original", length), [])
        same = len(signatures(runs) | signatures(baseline)) == 1 if baseline else None
        active = all(r["gpu_ffn_active"] for r in runs) if method == "gpu_ffn_all" else None
        refs = [r["matches_reference"] for r in runs if r["matches_reference"] is not None]
        reference_match = all(refs) if refs else None
        speedup = ""
        if baseline and same and active is not False and reference_match is not False:
            speedup = statistics.median(p["prefill_s"] * 1000 for r in baseline for p in r["reps"]) / statistics.median(times)
        rows.append(dict(method=method, prompt_tokens=length, dummy=any(r.get("dummy", False) for r in runs), samples=len(times),
                         prefill_median_ms=statistics.median(times), prefill_min_ms=min(times), prefill_max_ms=max(times),
                         speedup_vs_gpu=speedup, tokens_match_gpu=same, matches_reference=reference_match,
                         gpu_ffn_active=active, npu_execution="unverified" if method == "heteromosaic" else "not_requested"))
    if rows:
        with (directory / "summary.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model")
    p.add_argument("--dummy", action="store_true")
    p.add_argument("--ref", type=Path, default=ROOT / "docs/runs/2026-10-12-aup/gpu-model-result.json")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--build", default="build-model")
    p.add_argument("--config", default="py/unified_llm_w4a16/configs/configs_strixP_llama3_8b.json5")
    p.add_argument("--methods", nargs="+", choices=METHODS, default=["gpu_original", "gpu_ffn_all"])
    p.add_argument("--prompt-tokens", nargs="+", type=int, default=[1024])
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--reps", type=int, default=5)
    p.add_argument("--new-tokens", type=int, default=64)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--summarize", action="store_true")
    args = p.parse_args()
    args.out, args.ref = args.out.resolve(), args.ref.resolve()
    if args.summarize:
        print(json.dumps(summarize(args.out), indent=2))
        return
    available = len(json.loads(args.ref.read_text())["input_ids"][0])
    if any(n < 1 or n > available for n in args.prompt_tokens):
        p.error(f"reference has {available} tokens; provide a longer --ref for longer prompts")
    if min(args.rounds, args.reps, args.new_tokens) < 1:
        p.error("rounds, reps and new-tokens must be positive")
    if not args.model and not args.dummy and not args.dry_run:
        p.error("--model is required without --dummy")
    for method, length, round_id, cmd, env, out in cases(args):
        print(f"{method} length={length} round={round_id}: {shlex.join(cmd)}", flush=True)
        if args.dry_run:
            continue
        args.out.mkdir(parents=True, exist_ok=True)
        log = out.with_suffix(".log")
        with log.open("w") as f:
            subprocess.run(cmd, env=env, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, check=True)
        record = json.loads(out.read_text())
        record.update(method=method, round=round_id,
                      gpu_ffn_active="HeteroMega GPU FFN: 32 layers, 14336 prefill" in log.read_text())
        out.write_text(json.dumps(record, indent=2))
    if not args.dry_run:
        print(json.dumps(summarize(args.out), indent=2))


if __name__ == "__main__":
    main()
