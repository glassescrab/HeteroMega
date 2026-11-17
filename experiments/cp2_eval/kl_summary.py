#!/usr/bin/env python3
"""Median last-token (step-1) KL vs G0 per stem over the comparison-<seed>.json files of a quality dir, plus the selection / in-flight lines
of each stem's logs.   kl_summary.py QDIR [STEM ...]"""
import glob, json, re, statistics, sys
from pathlib import Path
q, want = Path(sys.argv[1]), sys.argv[2:]
kl = {}
for f in sorted(q.glob("comparison-*.json")):
    for r in json.loads(f.read_text()):
        kl.setdefault(r["run"], []).append((f.stem.split("-")[1], r.get("step1_kl_nats"), r["step1"]["argmax_equal"], r["greedy"]["agree"], r["greedy"]["total"]))
for run in (want or sorted(kl)):
    v = kl.get(run, [])
    ks = [x[1] for x in v if x[1] is not None]
    sel = sorted({m.group(0) for lg in glob.glob(f"{q}/seed*/{run}.log") for m in [re.search(r"chunk_size=\d+, chunk_schedule=\[[^]]*\], inflight=\d+, prompt_len=\d+", open(lg, errors="ignore").read())] if m})
    infl = sorted({m for lg in glob.glob(f"{q}/seed*/{run}.log") for m in re.findall(r"pipeline enabled with (\d+) inflight", open(lg, errors="ignore").read())})
    print(f"{run:24s} prompts={len(ks)} median_KL={statistics.median(ks) if ks else float('nan'):.3e} min={min(ks) if ks else 0:.2e} max={max(ks) if ks else 0:.2e} "
          f"argmax_equal={sum(x[2] for x in v)}/{len(v)} greedy_agree={[f'{x[3]}/{x[4]}' for x in sorted(v)]} selection={sel or '-'} inflight={infl or '-'}")

# Against both references, from the saved .npz logits (as kl_ref.py): GPU-only old kernels (gpu_original-L-r0) and GPU-only new kernels (G1-L-r0).
import numpy as np, os
def lsm(x): x = x.astype(np.float64); m = x.max(); return x - m - np.log(np.exp(x - m).sum())
seeds = sorted(q.glob("seed*"))
stems = sorted({f.stem for sd in seeds for f in sd.glob("*.npz")})
Ls = sorted({s.rsplit("-", 2)[-2] for s in stems if s.count("-") >= 2})
for L in Ls:
    for ref in (f"gpu_original-{L}-r0", f"G1-{L}-r0"):
        print(f"== {q.name} ref={ref} prompts={len(seeds)}")
        for c in [s for s in stems if s.endswith(f"-{L}-r0") or s.endswith(f"-{L}-r1")]:
            if c == ref or (want and c not in want and not c.startswith("gpu_original")): continue
            kl, top = [], []
            for sd in seeds:
                a, b = sd / f"{ref}.npz", sd / f"{c}.npz"
                if not (a.exists() and b.exists()): continue
                pa, pb = lsm(np.load(a)["logits"]), lsm(np.load(b)["logits"])
                kl.append(float((np.exp(pa) * (pa - pb)).sum())); top.append(int(pa.argmax() == pb.argmax()))
            if kl: print(f"  {c:24s} n={len(kl)} median KL={statistics.median(kl):.2e} top1={sum(top)}/{len(top)}")
