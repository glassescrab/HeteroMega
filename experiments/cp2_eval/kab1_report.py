#!/usr/bin/env python3
"""Kernel ablation at 1 micro-batch in flight (stage kab1-1024 / smoke kab1s-1024), user request 2026-11-15.
  kab1_report.py RES STAGE   -> effective config matrix (from case.txt, env.txt, info.txt, the config file), adjacent-rung diffs,
                                and for a timed stage the cells table and step ratios (all within STAGE)."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate import load, stats, ratio, verdict, table, f, role   # noqa: E402

LADDERS = [("GPU-only", ["G0", "GKM", "G1F", "G1"]),
           ("HeteroMosaic, author's 1024 entry", ["HK0", "HKM", "HK1", "HKU"]),
           ("ours, p = 5120 on every rung", ["O0p5120", "OKMp5120", "OK1p5120", "O1Fp5120", "O1p5120"])]
STEP = {"GKM": "+ new GEMM (incl. shared Q/K/V input)", "G1F": "+ new attention", "G1": "+ FFN fusion (gpu_ffn_all method, build-gpuffn)",
        "HKM": "+ new GEMM (incl. shared Q/K/V input)", "HK1": "+ new attention", "HKU": "+ UNCACHED",
        "OKMp5120": "+ new GEMM (+ RESIDUAL_NORM, which needs the new GEMM)", "OK1p5120": "+ new attention", "O1Fp5120": "+ UNCACHED",
        "O1p5120": "+ FFN fusion"}
FALLBACK = {"HKU": "HKUnU", "HKUp": "HKUnU", "O1Fp5120": "O1FnUp5120", "O1p5120": "O1nUp5120", "G1": "G1F"}


def kv(path):
    return dict(l.split("=", 1) for l in path.read_text().splitlines() if "=" in l) if path.exists() else {}


def split_of(cfgdir, name, L):
    """Per micro-batch gate/up/down NPU rows of every 512-row group of prompt_len L in the config file (distinct sets joined by ' | ')."""
    if not name:
        return ""
    cfg = json.loads((cfgdir / name).read_text())
    out = []
    for g in cfg["kernels_gemm_chunked"]:
        sched = g.get("hetero_chunk_size_schedule") or [g.get("hetero_chunk_size")]
        if g["prompt_len"] != L or set(sched) != {512}:
            continue
        per = {}
        for k in g["kernels"]:
            if k["layer"] in ("gate", "up", "down"):
                per.setdefault(k["chunk_id"], {})[k["layer"]] = k["npuM"] if k["use"] else 0
        s = ", ".join(f"{d.get('gate', 0)}/{d.get('up', 0)}/{d.get('down', 0)}" for _, d in sorted(per.items()))
        if s not in out:
            out.append(s)
    return " | ".join(out)


def matrix(res, stage):
    sd, rows, fp = Path(res) / stage, [], {}
    for D in sorted(sd.glob("*-s[0-9]*")):
        case, info = kv(D / "case.txt"), kv(D / "info.txt")
        env = " ".join(sorted(x.replace("HETEROMEGA_", "") for x in (D / "env.txt").read_text().split() if "FINITE_CHECK" not in x)) if (D / "env.txt").exists() else "?"
        method = case.get("method", "")
        part = (f"channel split, NPU channels [0,{case.get('p')})" if method == "merged_ffn" else
                "all on GPU" if method.startswith("gpu") else split_of(Path(res) / "configs", case.get("config", ""), int(case.get("L", 1024))))
        status = "DONE" if (D / "DONE").exists() else "FAILED(OOM)" if (D / "FAILED").exists() else "incomplete"
        cell = case.get("cell", D.name)
        key = (method, case.get("build"), part, env, info.get("inflight_seen"), case.get("config"))
        fp.setdefault(cell, set()).add(key)
        rows.append([cell, method, case.get("build"), case.get("config", "") or "-", part, env or "(none)", case.get("inflight"),
                     info.get("inflight_seen", "?"), info.get("uncached_fallback", "?"), info.get("selection", "")[:90] or "-", status])
    out = ["### Effective config matrix (" + stage + "; read from case.txt, env.txt, info.txt and the config file)\n" +
           table(["cell", "method", "build", "config", "gate/up/down per micro-batch (NPU rows)", "switches set", "in flight (case)",
                  "in flight (log)", "UNCACHED_FALLBACK", "selected group", "status"], rows)]
    bad = [c for c, s in fp.items() if len(s) > 1]
    out.append("Processes of one cell with differing effective configs: " + (", ".join(bad) if bad else "none") + "\n")
    diffs = []
    for name, cells in LADDERS:
        for a, b in zip(cells, cells[1:]):
            if a in fp and b in fp and len(fp[a]) == 1 and len(fp[b]) == 1:
                ka, kb = next(iter(fp[a])), next(iter(fp[b]))
                sa, sb = set(ka[3].split()), set(kb[3].split())
                other = [f"{n}: {x} -> {y}" for n, x, y in zip(["method", "build", "partition", "switches", "in flight", "config"], ka, kb)
                         if n != "switches" and x != y]
                diffs.append([name, f"{a} -> {b}", STEP.get(b, ""), " ".join(sorted(sb - sa)) or "-", " ".join(sorted(sa - sb)) or "-",
                              "; ".join(other) or "-"])
    out.append("### Adjacent-rung diff (only the named switch may change)\n" +
               table(["ladder", "step", "named step", "switches added", "switches removed", "other fields that differ"], diffs))
    return "\n".join(out)


def timed(res, stage):
    procs, _ = load(res)
    cells = {}
    for p in procs:
        if p["stage"] == stage and p["tag"] == "":
            cells.setdefault(p["cell"], []).append(p)
    rows, srows = [], []
    if "HKU" in cells and "HKUnU" in cells and any(p["fb"] for p in cells["HKU"]):   # rule: any UNCACHED_FALLBACK = does not fit -> the labelled no-UNCACHED cell is used
        cells["HKU (UNCACHED partial, %d fallback calls; not used)" % sum(p["fb"] for p in cells["HKU"])] = cells.pop("HKU")
    for name, ladder in LADDERS:
        for c in ladder:
            use = c if c in cells else FALLBACK.get(c) if FALLBACK.get(c) in cells else None
            if not use:
                if stage.startswith("kab1"):
                    rows.append([name, c, "missing", "", "", "", "", ""])
                continue
            s = stats([p["med"] for p in cells[use]])
            r0 = stats([p["rep0"] for p in cells[use]])
            rows.append([name, use + ("" if use == c else f" (labelled fallback for {c})"), f"{s['n']}x{cells[use][0]['n']}", f(s["med"]), f(s["std"]),
                         f"{f(s['ci'][0])}-{f(s['ci'][1])}" if s.get("ci") else "n/a", f"{f(s['lo'])}-{f(s['hi'])}", f(r0["med"])])
        prev = None
        for c in (ladder if stage.startswith("kab1") else []):   # step ratios only in the ablation stage
            use = c if c in cells else FALLBACK.get(c) if FALLBACK.get(c) in cells else None
            if use and prev:
                r, ci = ratio(stats([p["med"] for p in cells[use]]), stats([p["med"] for p in cells[prev]]))
                srows.append([name, f"{use} / {prev}", STEP.get(c, ""), f"{r:.4f}", "n/a" if ci is None else f"{ci[0]:.4f}-{ci[1]:.4f}", verdict(ci)])
            prev = use or prev
        first, last = ladder[0], ladder[-1]
        lu = last if last in cells else FALLBACK.get(last)
        if stage.startswith("kab1") and first in cells and lu in cells:
            r, ci = ratio(stats([p["med"] for p in cells[lu]]), stats([p["med"] for p in cells[first]]))
            srows.append([name, f"{lu} / {first}", "whole ladder (all on / all off)", f"{r:.4f}", "n/a" if ci is None else f"{ci[0]:.4f}-{ci[1]:.4f}", verdict(ci)])
    for title, pairs in (("regime 1, author's HeteroMosaic setting (ours at p*_on 5120 / p*_off 6144)", [("O1p5120", "HKU"), ("O1p5120", "G1"), ("O0p6144", "HK0"), ("O0p6144", "G0")]),
                         ("secondary, kernels off -> on (each method's full bundle)", [("HKU", "HK0"), ("G1", "G0"), ("O1p5120", "O0p6144")])):
        for a, b in pairs:
            ua = a if a in cells else FALLBACK.get(a) if FALLBACK.get(a) in cells else None
            ub = b if b in cells else FALLBACK.get(b) if FALLBACK.get(b) in cells else None
            if ua and ub:
                r, ci = ratio(stats([p["med"] for p in cells[ua]]), stats([p["med"] for p in cells[ub]]))
                srows.append([title, f"{ua} / {ub}", "", f"{r:.4f}", "n/a" if ci is None else f"{ci[0]:.4f}-{ci[1]:.4f}", verdict(ci)])
    extra = sorted(set(cells) - {c for _, l in LADDERS for c in l} - set(FALLBACK.values()))
    for c in extra:
        s = stats([p["med"] for p in cells[c]])
        rows.append(["(other cell)", c, f"{s['n']}x{cells[c][0]['n']}", f(s["med"]), f(s["std"]), f"{f(s['ci'][0])}-{f(s['ci'][1])}", f"{f(s['lo'])}-{f(s['hi'])}",
                     f(stats([p["rep0"] for p in cells[c]])["med"])])
    return ("### Cells (" + stage + ", one randomized stage, 1 micro-batch in flight; ms, process = median of reps 1-4)\n" +
            table(["ladder", "cell", "proc x reps", "median ms", "std", "95% t-CI (log)", "min-max of proc medians", "rep0 median"], rows) +
            "\n### Step ratios (this rung / previous rung; < 1 = the step speeds up; all within the stage)\n" +
            table(["ladder", "ratio", "step", "ratio of medians", "95% CI", "verdict"], srows))


if __name__ == "__main__":
    res, stage = sys.argv[1], sys.argv[2]
    print(matrix(res, stage))
    if not stage.startswith("kab1s"):
        print(timed(res, stage))
