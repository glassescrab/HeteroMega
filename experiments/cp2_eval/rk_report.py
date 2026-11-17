#!/usr/bin/env python3
"""Config fingerprint per cell of an rk* / apmb* stage (from each process's fingerprint.txt, written by rk_check.py) and cell medians
(cellmed.py rule: process = median of reps 1-4, cell = median of processes; DONE processes only).   rk_report.py RES STAGE
A cell whose DONE processes have more than one fingerprint is flagged; BAD_CONFIG / FAILED / incomplete processes are listed."""
import json, statistics, sys
from pathlib import Path

KEYS = ("tree", "switches", "group", "inflight_seen", "split", "attn", "fw_dir", "pdi")


def kv(p):
    return dict(l.split("=", 1) for l in p.read_text().splitlines() if "=" in l) if p.exists() else {}


res, stage = Path(sys.argv[1]), sys.argv[2]
cells = {}
for D in sorted((res / stage).glob("*-s[0-9]*")):
    name = D.name.rsplit("-s", 1)[0]
    fp, st = kv(D / "fingerprint.txt"), "DONE" if (D / "DONE").exists() else "BAD_CONFIG" if (D / "BAD_CONFIG").exists() else \
        "FAILED(OOM)" if (D / "FAILED").exists() else "incomplete"
    med = None
    if st == "DONE":
        js = list(D.glob("*.result.json"))
        t = [1000 * x["prefill_s"] for x in sorted(json.loads(js[0].read_text())["reps"], key=lambda x: x["rep"])]
        med = statistics.median(t[1:]) if len(t) > 1 else t[0]   # 1-rep smoke: that rep
    c = cells.setdefault(name, {"fp": set(), "med": [], "st": [], "peak": []})
    c["st"].append(st)
    c["peak"].append(kv(D / "info.txt").get("peak_gtt_mib", "?"))
    if st == "DONE":
        c["fp"].add(tuple(fp.get(k, "-") for k in KEYS))
        c["med"].append(med)
print(f"### {stage}: config fingerprint and cell median per cell (ms; process = median of reps 1-4, a 1-rep smoke = that rep)")
print("| cell | DONE / procs | cell median | min-max | " + " | ".join(KEYS) + " | peak GTT MiB | other status |")
print("|---" * (len(KEYS) + 6) + "|")
for n, c in cells.items():
    fps = sorted(c["fp"]) or [("-",) * len(KEYS)]
    m = c["med"]
    flag = " (FINGERPRINT DIFFERS)" if len(fps) > 1 else ""
    stat = f"{statistics.median(m):.1f} | {min(m):.1f}-{max(m):.1f}" if m else "- | -"
    for f in fps:
        print(f"| {n}{flag} | {len(m)}/{len(c['st'])} | {stat} | " + " | ".join(f) + f" | {max(c['peak'], key=lambda x: int(x) if x.isdigit() else -1)} | "
              f"{', '.join(s for s in c['st'] if s != 'DONE') or '-'} |")
