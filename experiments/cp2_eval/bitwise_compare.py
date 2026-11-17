"""compare.py logits DIR: torch.equal of step-1 logits, ref vs new. compare.py runs DIR: prefill/decode/token match per ref/new pair."""
import json, statistics, sys
from pathlib import Path
import numpy as np
import torch

mode, d = sys.argv[1], Path(sys.argv[2])
if mode == "logits":
    for ref in sorted(d.glob("*-ref.npz")):
        new = ref.with_name(ref.name.replace("-ref.npz", "-new.npz"))
        if not new.exists():
            print(ref.stem, "no new run"); continue
        a, b = np.load(ref), np.load(new)
        eq = lambda k: bool(torch.equal(torch.from_numpy(a[k]), torch.from_numpy(b[k])))
        sc = a["scored_logits"], b["scored_logits"]
        print(ref.stem[:-4], f"step1 logits equal={eq('logits')} repeat equal={eq('logits_repeat')} greedy64 equal={eq('tokens')}",
              f"first token diff at {next((i for i, (x, y) in enumerate(zip(a['tokens'], b['tokens'])) if x != y), None)};",
              f"scored decode rows: argmax agree {float(np.mean(sc[0].argmax(1) == sc[1].argmax(1))):.3f},",
              f"max abs {float(np.max(np.abs(sc[0][1:].astype(np.float64) - sc[1][1:]))):.4g}, scored row0 (prefill) equal={bool(np.array_equal(sc[0][0], sc[1][0]))}")
else:
    def load(label):
        files = list((d / label).glob("*.result.json"))
        return json.loads(files[0].read_text()) if files else None
    for refdir in sorted(p for p in d.iterdir() if p.is_dir() and p.name.endswith("-ref")):
        label = refdir.name[:-4]
        r, n = load(label + "-ref"), load(label + "-new")
        def desc(x, tag):
            if x is None: return f"{tag}: failed"
            pre = [rep["prefill_s"] * 1e3 for rep in x["reps"]]; dec = [rep["decode_tok_s"] for rep in x["reps"]]
            peak = max(int(v) for v in (d / f"{label}-{tag}.gtt").read_text().split())
            return f"{tag}: prefill ms {[round(v, 1) for v in pre]} median {statistics.median(pre):.1f}; decode tok/s median {statistics.median(dec):.2f}; peakGTT {peak} MB; warmup matches_ref={x.get('matches_reference')}"
        print(label, "|", desc(r, "ref"), "|", desc(n, "new"))
        if r and n:
            same = r["warmup_ids"] == n["warmup_ids"] and all(a["generated_ids"] == b["generated_ids"] for a, b in zip(r["reps"], n["reps"]))
            print("   greedy tokens identical ref vs new (warmup + every rep):", same)
