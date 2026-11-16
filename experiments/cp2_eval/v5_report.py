#!/usr/bin/env python3
"""v5 stages: per process the effective config (method, switches, selected group, per-chunk gate/up/down of that group, in flight from the log,
UNCACHED fallback, peak GTT, status).   v5_report.py RES STAGE"""
import json, re, sys
from pathlib import Path
res, stage = Path(sys.argv[1]), sys.argv[2]
kv = lambda p: dict(l.split("=", 1) for l in p.read_text().splitlines() if "=" in l) if p.exists() else {}
def group(cfg, sel):
    m = re.search(r"chunk_size=(\d+), chunk_schedule=\[([^]]*)\], inflight=(\d+), prompt_len=(\d+)", sel or "")
    if not m: return "no selection line", ""
    cs, sch, L = int(m[1]), [int(x) for x in m[2].split(",") if x.strip()], int(m[4])
    gs = [g for g in cfg["kernels_gemm_chunked"] if g["prompt_len"] == L]
    hit = [g for g in gs if g.get("hetero_chunk_size_schedule") == sch] or \
          [g for g in gs if "hetero_chunk_size_schedule" not in g and g.get("hetero_chunk_size") == cs]
    if len(hit) != 1: return f"{len(hit)} matching groups", ""
    g = hit[0]; per = {}
    for k in g["kernels"]:
        if k["layer"] in ("gate", "up", "down"): per.setdefault(k["chunk_id"], {})[k["layer"]] = k["npuM"] if k["use"] else 0
    name = f"schedule {g['hetero_chunk_size_schedule']}" if "hetero_chunk_size_schedule" in g else f"fixed chunk {g['hetero_chunk_size']}"
    return f"{name}, entry inflight {g.get('hetero_inflight')}", ", ".join(f"{d.get('gate',0)}/{d.get('up',0)}/{d.get('down',0)}" for _, d in sorted(per.items()))
print(f"### {stage}: effective config per process\n| process | method | switches | config | selected group (runtime line) | entry | gate/up/down per chunk | in flight (log) | fb | peak GTT MiB | status |\n|---|---|---|---|---|---|---|---|---|---|---|")
for D in sorted((res / stage).glob("*-s[0-9]*")):
    case, info = kv(D / "case.txt"), kv(D / "info.txt")
    sel = info.get("selection", "")
    if case.get("method", "").startswith("gpu"): ent, split = "-", "all on GPU"
    elif case.get("method") == "merged_ffn": ent, split = "-", f"channel split, NPU channels [0,{case.get('p')})"
    else: ent, split = group(json.loads((res / "configs" / case["config"]).read_text()), sel)
    st = "DONE" if (D / "DONE").exists() else "FAILED(OOM)" if (D / "FAILED").exists() else "incomplete"
    st += "".join(" " + b for b in ("BAD_INFLIGHT", "BAD_SELECTION") if (D / b).exists())
    print(f"| {D.name} | {case.get('method')} | {case.get('switches','').replace('HETEROMEGA_','').strip() or '(none)'} | {case.get('config') or '-'} | "
          f"{re.sub(r'^Using grouped kernels_gemm_chunked ', '', sel) or '-'} | {ent} | {split} | {info.get('inflight_seen','?')} | {info.get('uncached_fallback','?')} | {info.get('peak_gtt_mib','?')} | {st} |")
