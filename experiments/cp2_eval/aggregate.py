#!/usr/bin/env python3
"""Aggregate the CP2 evaluation: aggregate.py RES [--write-best-p]   (RES = /notebooks/hm-results/cp2, or any dir of stage dirs)
Unit = process: median of reps 1-4 (reps 1.. for shorter runs), rep 0 kept apart. Per cell: median, std, t-interval on log times,
min-max of the process medians. Ratios (num/den of cell medians, <1 = numerator faster) with a Welch t-interval on log times;
"CI contains 1" = no difference claimed. Group P = channel-partition design, group K = generic kernels. Measured and derived are
separate sections. Writes RES/aggregate/report.md and per_process.csv; --write-best-p only (re)writes RES/best_p.txt from the sweeps.
Plan v4: stages are split by regime (1 = one chunk in flight, 2 = two or more) from their names; ratios only within one stage; a process whose log
shows another in-flight count than its case.txt is BAD_INFLIGHT and dropped; v3 (2-in-flight) stages only appear in an appendix.
  --write-best-p [--inflight 1]  writes best_p.txt (v3) or best_p1.txt (1-in-flight sweeps);  --out DIR  writes the report elsewhere (default RES/aggregate)
Dirs without case.txt (the 2026-11-14 jobs/eval.sh layout) are read too; their cells are named by LEGACY."""
import csv, glob, json, math, os, re, statistics as st, sys
from pathlib import Path

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 15: 2.131, 20: 2.086, 30: 2.042}
LEGACY = {"A_gpu_512x2": "G0", "Anew_gpu_512x2": "G1", "A_gpu_shipped": "GS", "Anew_gpu_shipped": "GS1", "B_heteromosaic": "HR",
          "C_p8192_old": "O0p8192", "Cnew_p8192_all": "O1p8192"}
FALLBACK = {"O1": "O1nU", "H1": "H1nU", "HP1": "HP1nU", "G1": "G1F", "O1F": "O1FnU"}
P_RATIOS = [("O1", "H1"), ("O1", "G1"), ("O0", "H0"), ("O0", "G0"), ("O1F", "O1")]   # O1F/O1 = A2, fusion off / on
K_RATIOS = [("G1", "G0"), ("H1", "H0"), ("O1", "O0")]
LADDERS = {"GPU-only": ["G0", "GA1", "G1F", "G1"], "HeteroMosaic": ["H0", "HA1", "H1"], "ours": ["O0", "OA1", "OA2", "O1F", "O1"]}
LOO = {"H1": ["HLs", "HLg"], "O1": ["OLs", "OLg", "O1nU"]}
SWEEP_MIN = {"on": 6, "off": 3}


def tq(df):
    df = max(1, int(df))
    return T975[max(k for k in T975 if k <= df)] if df < 30 else 2.0


def kv(path):
    out = {}
    if os.path.exists(path):
        for line in open(path):
            if "=" in line:
                a, b = line.rstrip("\n").split("=", 1)
                out[a] = b
    return out


def parse_ioctl(text):
    best = None
    for m in re.finditer(r"IOCTL_COUNTS ctx_ok=(\d+) exec_ok=(\d+) exec_fail=(\d+)", text):
        v = tuple(int(x) for x in m.groups())
        if best is None or v[1] >= best[1]:
            best = v
    return best


def load(res):
    procs, failed = [], []
    for stage_dir in sorted(p for p in Path(res).iterdir() if p.is_dir() and p.name != "aggregate"):
        for D in sorted(stage_dir.iterdir()):
            if not D.is_dir():
                continue
            case, info = kv(D / "case.txt"), kv(D / "info.txt")
            results = sorted(D.glob("*.result.json"))
            legacy = not case
            if (D / "FAILED").exists() or (case and not (D / "DONE").exists()):
                failed.append(dict(stage=stage_dir.name, label=D.name, oom=(D / "FAILED").exists(), peak=info.get("peak_gtt_mib", ""),
                                   error=(D / "error.txt").read_text().strip().replace("\n", " | ")[:160] if (D / "error.txt").exists() else ""))
                continue
            if not results or (case and not (D / "DONE").exists()):
                continue
            r = json.loads(results[0].read_text())
            reps = r.get("reps") or []
            if not reps:
                continue
            times = [x["prefill_s"] * 1000 for x in reps]
            label = re.sub(r"-\d+-r?[0-9a-z]+$", "", D.name)
            cell = case.get("cell") or LEGACY.get(label, label)
            tag = case.get("tag", "")
            if "." in cell:   # H1.<combo>: tag carries the suffix, the cell stays the role
                cell, _, suffix = cell.partition(".")
                tag = tag or suffix
            logs = "".join(f.read_text(errors="ignore") for f in list(D.glob("*.log")) + ([Path(str(D) + ".log")] if legacy and Path(str(D) + ".log").exists() else []))
            gtt = D / "gtt.txt" if (D / "gtt.txt").exists() else Path(str(D) + ".gtt")
            peak = max([int(x) for x in gtt.read_text().split()] or [0]) if gtt.exists() else None
            use = times[1:5]
            infl, seen, reg = case.get("inflight", ""), inflight_seen(D), regime_of(stage_dir.name)
            sig = reps[min(1, len(reps) - 1)]
            procs.append(dict(stage=stage_dir.name, dir=D, label=D.name, cell=cell, tag=tag, L=int(r["prompt_tokens"]), n=len(times),
                              group=case.get("group", "?"), p=int(m.group(1)) if (m := re.search(r"p(\d+)$", cell)) else None,
                              med=st.median(use) if use else float("nan"), rep0=times[0], gen=sig["generated_ids"], first=sig["prefill_ids"][:1],
                              ioctl=parse_ioctl(info.get("ioctl", "") or logs), peak=int(info["peak_gtt_mib"]) if info.get("peak_gtt_mib", "").isdigit() else peak,
                              fb=int(info["uncached_fallback"]) if "uncached_fallback" in info else logs.count("UNCACHED_FALLBACK"),
                              verdict=info.get("merged_ffn_verdict", ""), badsel=(D / "BAD_SELECTION").exists(), infl=infl, seen=seen, regime=reg,
                              badinfl=bool(reg and infl and seen != infl) or (D / "BAD_INFLIGHT").exists(),
                              gemm=info.get("hetero_gpu_gemm", ""), temp=info.get("temp_sclk_before", "")[:60],
                              klass="hprobe" if stage_dir.name.startswith("hprobe") else "sweep" if stage_dir.name.startswith("sweep") else "gate" if stage_dir.name == "gates" else
                              "repl" if stage_dir.name.startswith("repl") else "main"))
    return procs, failed


def role(cell):
    m = re.match(r"^(O[A-Za-z0-9]*)p(\d+)$", cell)
    return (m.group(1), int(m.group(2))) if m else (cell, None)


def stats(meds):
    meds = [m for m in meds if m == m]
    n = len(meds)
    d = dict(n=n, med=st.median(meds) if n else float("nan"), lo=min(meds) if n else float("nan"), hi=max(meds) if n else float("nan"))
    d["std"] = st.stdev(meds) if n > 1 else float("nan")
    logs = [math.log(m) for m in meds]
    d["lmean"], d["lvar"] = (st.mean(logs), st.variance(logs)) if n > 1 else (st.mean(logs) if n else float("nan"), float("nan"))
    if n > 1:
        h = tq(n - 1) * math.sqrt(d["lvar"] / n)
        d["ci"] = (math.exp(d["lmean"] - h), math.exp(d["lmean"] + h))
    else:
        d["ci"] = (float("nan"), float("nan"))
    return d


def ratio(a, b):
    if a["n"] < 2 or b["n"] < 2:
        return a["med"] / b["med"], None
    va, vb = a["lvar"] / a["n"], b["lvar"] / b["n"]
    se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / ((va ** 2 / (a["n"] - 1) if va else 0) + (vb ** 2 / (b["n"] - 1) if vb else 0) or 1e-12)
    d = a["lmean"] - b["lmean"]
    return a["med"] / b["med"], (math.exp(d - tq(df) * se), math.exp(d + tq(df) * se))


def f(x, nd=1):
    return "n/a" if x is None or x != x else f"{x:.{nd}f}"


def table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]) + "\n"


R1_STAGE = re.compile(r"^(hprobe1b?|sweep1(lo)?|main1|mech1|kcmp|repl1|uprobe1|gate4|kab1s?|main1as?|mech1a)(-|$)")
R2_STAGE = re.compile(r"^(main2(i4)?|ref2|repl2|ev2|hbcheck)(-|$)")
OK1_NOTE = "OK1 = ours with its internal fixes (RESIDUAL_NORM, SLOT_BO), no UNCACHED, no fusion; ladder OK1 -> O1F (+UNCACHED) -> O1 (+FFN_FUSE = A2)."


def regime_of(stage):
    return 1 if R1_STAGE.match(stage) else 2 if R2_STAGE.match(stage) else 0


def inflight_seen(D):
    """Effective in-flight count(s) of a process from its result log: 'pipeline enabled with N' lines, 'serial chunk execution' = 1."""
    text = "".join(f.read_text(errors="ignore") for f in Path(D).glob("*.result.log"))
    seen = set(re.findall(r"pipeline enabled with (\d+) inflight", text))
    if "serial chunk execution" in text:
        seen.add("1")
    return ",".join(sorted(seen))


def lratio(terms):
    """Product of medians^sign with a Welch-Satterthwaite t-interval on the log scale; terms = [(+1|-1, stats)]."""
    if any(s["n"] < 2 for _, s in terms):
        return math.prod(s["med"] ** sg for sg, s in terms), None
    v = [s["lvar"] / s["n"] for _, s in terms]
    se = math.sqrt(sum(v))
    df = sum(v) ** 2 / (sum(x ** 2 / (s["n"] - 1) for x, (_, s) in zip(v, terms)) or 1e-12)
    d = sum(sg * s["lmean"] for sg, s in terms)
    return math.prod(s["med"] ** sg for sg, s in terms), (math.exp(d - tq(df) * se), math.exp(d + tq(df) * se))


def verdict(ci):
    return "n/a (n<2)" if ci is None else "Favours" if ci[1] < 1 else "Against" if ci[0] > 1 else "Tie"


class V4Mixin:
    """eval_plan_v4 tables: regime 1 (1 in flight), regime 2 (>= 2), pre-registered verdicts (plan 6, 11), probes, mechanisms, quality."""

    def setup_v4(self):
        self.v4 = [p for p in self.all if p["regime"]]
        self.v4ok = [p for p in self.v4 if not p["badinfl"]]
        self.sc = {}   # (stage, L) -> {cell: procs}, untagged cells with >= 2 processes, BAD_INFLIGHT excluded
        for p in self.v4ok:
            if p["tag"] == "" and p["n"] >= 2 and p["klass"] in ("main", "repl"):
                self.sc.setdefault((p["stage"], p["L"]), {}).setdefault(p["cell"], []).append(p)
        self.R = {}   # (stage, L, num, den) -> (ratio, ci)

    def getc(self, stage, L, name):
        cs = self.sc.get((stage, L), {})
        found = []   # the cell itself and its labelled OOM fallback; the one with more processes is used, ties go to the cell itself
        for variant in (name, FALLBACK.get(name)):
            c = [(k, v) for k, v in cs.items() if role(k)[0] == variant]
            if c:
                k, v = max(c, key=lambda kv_: len(kv_[1]))
                found.append((len(v), variant == name, v, k + ("" if variant == name else f" (fallback for {name})")))
        if not found:
            return None
        _, _, v, k = max(found, key=lambda f: (f[0], f[1]))
        return v, k

    def ref_for(self, L):
        for st_ in (f"main1-{L}", f"kcmp-{L}"):
            c = self.getc(st_, L, "G0")
            if c:
                return c[0][0]["first"], c[0][0]["gen"]
        return None

    def agree2(self, procs, L):
        ref = self.ref_for(L)
        if not ref:
            return "n/a"
        first, gen = ref
        pre = [next((i for i, (a, b) in enumerate(zip(p["gen"], gen)) if a != b), min(len(p["gen"]), len(gen))) for p in procs]
        return f"first={'all' if all(p['first'] == first for p in procs) else 'DIFF'} prefix>={min(pre)}/{len(gen)}"

    def cells_table(self, stage, L):
        rows = []
        for cell, v in sorted(self.sc.get((stage, L), {}).items()):
            s = stats([p["med"] for p in v])
            r0 = [p["rep0"] for p in v]
            r_, p_ = role(cell)
            note = ""
            if r_ == "O0" and p_ == 6144:
                note = "p at the sweep range edge (6144)"
            if p_ == 13312:
                note = "p at the bound (13312)"
            rows.append([cell, f"{s['n']}x{v[0]['n']}", f(s["med"]), f(s["std"]), f"{f(s['ci'][0])}-{f(s['ci'][1])}", f"{f(s['lo'])}-{f(s['hi'])}",
                         f"{f(st.median(r0))} [{f(min(r0))}-{f(max(r0))}]", self.agree2(v, L), max([p["peak"] or 0 for p in v]),
                         sum(p["fb"] for p in v), ",".join(sorted({p["verdict"] for p in v if p["verdict"]})), note])
        return table(["cell", "proc x reps", "median ms", "std", "95% t-CI (log)", "min-max of proc medians", "rep0 median [range]", "tokens vs G0",
                      "peak GTT MiB", "UNCACHED_FALLBACK", "merged verdict", "note"], rows) if rows else ""

    def rtable(self, stage, L, pairs, label):
        rows = []
        for num, den in pairs:
            a, b = self.getc(stage, L, num), self.getc(stage, L, den)
            if a and b:
                r, ci = ratio(stats([p["med"] for p in a[0]]), stats([p["med"] for p in b[0]]))
                self.R[(stage, L, num, den)] = (r, ci)
                rows.append([label, f"{num}/{den}", L, f"{a[1]} / {b[1]}", f"{r:.4f}", "n/a" if ci is None else f"{ci[0]:.4f}-{ci[1]:.4f}", verdict(ci),
                             f"{len(a[0])}/{len(b[0])}"])
        return rows

    HEAD = ["set", "ratio (num/den, <1 = numerator faster)", "L", "cells", "ratio of medians", "95% CI", "verdict", "n proc"]

    def regime1(self):
        out = ["## Regime 1: one chunk in flight (stage main1-L; ratios only within one stage)\n" + OK1_NOTE + "\n"]
        for L in (1024, 2048, 4096):
            st_ = f"main1-{L}"
            if (st_, L) not in self.sc:
                continue
            out.append(f"### L={L}: cells ({st_})\n" + self.cells_table(st_, L))
            a2 = st_ if self.getc(st_, L, "O1F") else f"mech1-{L}"
            rows = (self.rtable(st_, L, [("O1", "HP1"), ("O1", "G1")], "headline") +
                    self.rtable(st_, L, [("O0", "HP0"), ("O0", "G0"), ("OK1", "HP1"), ("OK1", "G1F")], "robustness (off kernels; same generic kernels)") +
                    self.rtable(a2, L, [("O1", "O1F")], f"A2 fusion ({a2})") + self.rtable(st_, L, [("O1F", "OK1")], "ladder step +UNCACHED") +
                    self.rtable(st_, L, [("G1F", "G0"), ("HP1", "HP0"), ("OK1", "O0")], "secondary, comparable bundle (GEMM+SDPA) off->on") +
                    self.rtable(st_, L, [("G1", "G0"), ("O1", "O0")], "secondary, method's full on bundle (labelled)"))
            out.append(f"### L={L}: ratios\n" + table(self.HEAD, rows))
        return "\n".join(out)

    def regime2(self):
        out = ["## Regime 2: two or more chunks in flight, ours absent (stage main2-L)\nH = g512u512d0 (a point of HeteroMosaic's own config space), HT = shipped token split, "
               "HB = best token split of the grid (combo below; whole-operator combos such as g0u0d512 are not token splits).\n"]
        for L in (1024, 2048, 4096):
            st_ = f"main2-{L}"
            if (st_, L) not in self.sc:
                continue
            out.append(f"### L={L}: cells ({st_}); {self.hb_label(L)}\n" + self.cells_table(st_, L))
            rows = (self.rtable(st_, L, [("H1", "HT1")], "headline (shipped split)") + self.rtable(st_, L, [("H0", "HT0")], "robustness (off kernels)") +
                    self.rtable(st_, L, [("H1", "HB1"), ("H0", "HB0")], "vs the tuned token split") +
                    self.rtable(st_, L, [("H1", "H0"), ("HT1", "HT0"), ("HB1", "HB0")], "secondary: kernels off->on (identical bundle)"))
            out.append(f"### L={L}: ratios\n" + table(self.HEAD, rows))
            out.append(self.cross_stage(L))
        for L in (2048,):
            st_ = f"main2i4-{L}"
            if (st_, L) in self.sc:
                out.append(f"### L={L}: reference pair at 4 in flight ({st_})\n" + self.cells_table(st_, L) + table(
                    self.HEAD, self.rtable(st_, L, [("H1", "HT1"), ("H0", "HT0")], "reference (4 in flight)")))
        rows = [[st_[1], c, st_[0]] + [f(stats([p["med"] for p in v])["med"]), f"{len(v)}x{v[0]['n']}"] for st_, cs in self.sc.items() if st_[0].startswith("ref2")
                for c, v in cs.items()]
        if rows:
            out.append("### Reference rows (HS: shipped chunking and in-flight; never in a ratio)\n" + table(["L", "cell", "stage", "median ms", "proc x reps"], rows))
        return "\n".join(out)

    def cross_stage(self, L):
        """1-in-flight screening numbers (hprobe1-L, H1/H0 process medians) next to the regime-2 cells of the same configs; cross-stage, never a ratio."""
        rows = []
        for cfg, tag, c in (("g512u512d0", "g512u512d0", "H"), ("shipped token split", "g256u256d0" if L == 1024 else "shipped", "HT")):
            for k in ("1", "0"):
                pr = [p for p in self.v4ok if p["klass"] == "hprobe" and p["L"] == L and p["tag"] == tag and role(p["cell"])[0] == f"H{k}"]
                r2 = self.getc(f"main2-{L}", L, f"{c}{k}")
                if pr and r2:
                    t1, t2 = st.mean(p["med"] for p in pr), st.median(p["med"] for p in r2[0])
                    rows.append([cfg, f"{c}{k}", f"{f(t1)} ({len(pr)} proc, 1 in flight, hprobe1)", f"{f(t2)} ({len(r2[0])} proc, 2 in flight, main2)", f"{t1 / t2:.3f}"])
        return (f"### L={L}: cross-stage / screening, not a ratio: 1-in-flight probe numbers next to the regime-2 cells of the same configs\n"
                + table(["config", "cell", "1 in flight (probe)", "2 in flight (main2)", "quotient, indicative only"], rows)) if rows else ""

    def hb_label(self, L):
        f_ = self.res / f"hbcheck-{L}" / "hbpick.txt"
        if L == 1024:
            return "HB = g256u256d256 (hprobe-1024 winner among token splits)"
        if f_.exists():
            m = re.findall(r"hbpick \d+ (\S+)", f_.read_text())
            if m:
                return f"HB = {m[-1]} (hbcheck-{L})"
        return "HB = ? (hbcheck not run)"

    def replication(self):
        out = ["## Replication (second independent stage) and cross-job rows (not used in ratios)\n"]
        rows = []
        for stage, pairs in (("repl1-1024", [("O1", "HP1"), ("O1", "G1")]), ("repl2-1024", [("H1", "HT1")])):
            rows += self.rtable(stage, 1024, pairs, stage)
        if rows:
            out.append(table(self.HEAD, rows))
        rows = []
        for cell, st_ in (("G0", "main1-1024"), ("G1", "main1-1024"), ("H0", "main2-1024"), ("H1", "main2-1024")):
            v3, v4 = self.cells.get((cell, 1024, "main")), self.getc(st_, 1024, cell)
            if v3 and v4:
                a, b = st.median([p["med"] for p in v3]), st.median([p["med"] for p in v4[0]])
                rows.append([cell, f"v3 main-1024 (hm-cp2, {len(v3)} proc)", f(a), f"{st_} (hm-cp2b)", f(b), f"{b / a - 1:+.1%}"])
        if rows:
            out.append("v3 vs v4 same-setting cells (checkout differs; shown for drift only):\n" + table(["cell", "v3", "median ms", "v4", "median ms", "diff"], rows))
        return "\n".join(out) + "\n"

    def verdicts(self):
        out = ["## Pre-registered verdicts (plan 6 and 11): Favours = ratio CI below 1, Tie = CI contains 1, Against = CI above 1\n"]
        Ls = (1024, 2048, 4096)

        def get(stage_fmt, L, num, den):
            return self.R.get((stage_fmt.format(L), L, num, den))
        for title, fam, num, den in (("Regime 1: O1 vs HP1", "main1-{}", "O1", "HP1"), ("Regime 1: O1 vs G1", "main1-{}", "O1", "G1"),
                                     ("Regime 2: H1 vs HT1", "main2-{}", "H1", "HT1")):
            vs = {L: verdict(get(fam, L, num, den)[1]) for L in Ls if get(fam, L, num, den)}
            if not vs:
                continue
            lines = [f"- L={L}: {v} (ratio {get(fam, L, num, den)[0]:.4f})" for L, v in vs.items()]
            same = len(set(vs.values())) == 1
            out.append(f"**{title}**\n" + "\n".join(lines) + f"\n- headline sentence: {'allowed, ' + next(iter(vs.values())) + ' at ' + ', '.join(map(str, vs)) if same else 'NOT allowed, per-length sentences only'}"
                       + ("; lengths not yet measured: " + ", ".join(str(L) for L in Ls if L not in vs) if len(vs) < 3 else "") + "\n")
        for L in Ls:   # ours vs both baselines
            a, b = self.R.get((f"main1-{L}", L, "O1", "HP1")), self.R.get((f"main1-{L}", L, "O1", "G1"))
            if a and b and verdict(a[1]) != verdict(b[1]):
                out.append(f"- L={L}: O1 vs HP1 is {verdict(a[1])} but O1 vs G1 is {verdict(b[1])}: the sentence names which baseline.")
            for on, off in ((("O1", "HP1"), ("O0", "HP0")), (("O1", "G1"), ("O0", "G0"))):
                x, y = self.R.get((f"main1-{L}", L) + on), self.R.get((f"main1-{L}", L) + off)
                if x and y and verdict(x[1]) != verdict(y[1]):
                    out.append(f"- L={L}: kernels-off {off[0]}/{off[1]} is {verdict(y[1])} while {on[0]}/{on[1]} is {verdict(x[1])}: the sentence says so.")
            for st_, num, den in ((f"main1-{L}", "OK1", "HP1"), (f"main1-{L}", "OK1", "G1F")):
                x = self.R.get((st_, L, num, den))
                if x:
                    out.append(f"- L={L}: same-generic-kernel row {num}/{den}: {verdict(x[1])} (ratio {x[0]:.4f}, CI {'n/a' if x[1] is None else '%.4f-%.4f' % x[1]})")
        out.append("\n**Regime 2, two levels** (plan 11.3)")
        for L in Ls:
            h, b = self.R.get((f"main2-{L}", L, "H1", "HT1")), self.R.get((f"main2-{L}", L, "H1", "HB1"))
            if not h:
                continue
            vh, vb = verdict(h[1]), verdict(b[1]) if b else "n/a (no HB cell)"
            if vh == "Favours" and vb == "Favours":
                s = "general sentence allowed: token split inside an operator is not the best under pipelining (H1 beats HT1 and HB1)"
            elif vh == "Favours":
                s = f"H1 beats the shipped split only; against the tuned split ({self.hb_label(L)}): {vb}"
            else:
                s = f"H1 vs the shipped split is {vh}: no regime-2 sentence"
            out.append(f"- L={L}: H1 vs HT1 {vh}; H1 vs HB1 {vb} -> {s}")
        out.append("\n**Mechanism falsifiers** (plan 2.4)")
        for L in Ls:
            a2 = self.R.get((f"main1-{L}", L, "O1", "O1F")) or self.R.get((f"mech1-{L}", L, "O1", "O1F"))
            if a2:
                out.append(f"- L={L} A2: O1/O1F {a2[0]:.4f}, CI {'n/a' if a2[1] is None else '%.4f-%.4f' % a2[1]} -> " + (
                    "FALSIFIED (CI contains 1 or above 1: no latency effect)" if a2[1] is not None and a2[1][1] >= 1 else "holds" if a2[1] else "n/a"))
        ev = self.ev_map()
        for L in Ls:
            ok, hp = ev.get((L, "OK1")), ev.get((L, "HP1"))
            if ok and hp:
                a, b = st.median(ok["ffn_m"]), st.median(hp["ffn_m"])
                da = st.median(ok["attn_m"]) - st.median(hp["attn_m"])
                out.append(f"- L={L} A1 (ev1, OK1 vs HP1, FFN matched boundary ms): {a:.2f} vs {b:.2f} -> " + ("FALSIFIED (not below HP1)" if a >= b else "holds")
                           + ("; attention differs by more than the FFN gap: gap not FFN-driven" if abs(da) > abs(a - b) else ""))
        c = self.count_map()
        for L in Ls:
            if (L, "O1") in c and (L, "HP1") in c:
                out.append(f"- L={L} A1 submissions per prefill: O1 {c[(L, 'O1')]} vs HP1 {c[(L, 'HP1')]}" + (" -> equal: 'one dispatch' dropped" if c[(L, 'O1')] == c[(L, 'HP1')] else ""))
        return "\n".join(out) + "\n"

    def ev_map(self):
        out = {}
        for p in self.v4ok:
            if p["tag"] == "ev1":
                r = stage_sums(p["dir"] / "ev", p["L"], p["n"])
                if r and r["use"]["ffn"]:
                    out[(p["L"], role(p["cell"])[0])] = r["use"]
        return out

    def count_map(self):
        out = {}
        for p in self.v4ok:
            if p["tag"] in ("c1", "c2") and p["ioctl"]:
                out.setdefault((p["L"], role(p["cell"])[0]), {})[p["tag"]] = p["ioctl"][1]
        return {k: (v["c2"] - v["c1"]) / 2 for k, v in out.items() if len(v) == 2}

    def smoke_table(self):
        rows = [[p["stage"], p["label"], p["infl"], p["seen"], p["peak"], p["fb"], p["verdict"], "BAD_SELECTION" if p["badsel"] else "ok", "BAD_INFLIGHT" if p["badinfl"] else "ok"]
                for p in self.v4 if p["stage"] in ("gate4", "uprobe1")]
        return ("### Pre-launch smokes (gate4) and UNCACHED probe (uprobe1)\n" + table(["stage", "process", "case in-flight", "log in-flight", "peak GTT MiB", "UNCACHED_FALLBACK",
                "merged verdict", "selection", "inflight"], rows)) if rows else ""

    def probes_v4(self):
        out = []
        for L in (1024, 2048, 4096):
            pr = [p for p in self.v4ok if p["klass"] == "hprobe" and p["L"] == L]
            if pr:
                out.append(self.hprobe_table(pr, f"Regime 1 HeteroMosaic probe, {L}, 1 in flight (process medians of reps 1-4, ms; screening grade)"))
            pr = [p for p in self.v4ok if p["stage"] == f"hbcheck-{L}" and p["med"] == p["med"]]
            if pr:
                out.append(self.hprobe_table(pr, f"HB candidates (token splits) at {L}, 2 in flight"))
        sw = self.sweep([p for p in self.v4ok if p["klass"] == "sweep" and p["infl"] == "1"])
        if sw:
            out.append(self.sweep_report(sw, "Regime 1 sweep T(p), 1 in flight: 1 process x 3 reps, screening grade; best p goes to best_p1.txt"))
        return "\n".join(x for x in out if x)

    def derived_v4(self):
        out = ["## Derived (computed from configs and counters; no timing)\n"]
        try:
            from make_hm_configs import ffn_share, select
        except Exception as e:  # noqa: BLE001
            return "\n".join(out) + f"(make_hm_configs not importable: {e})\n"
        rows = []
        for L in (1024, 2048, 4096):
            for name in (f"hm1_{L}", f"hm1o_{L}", f"hm_{L}", f"hm_{L}.shipped", f"hb_{L}"):
                path = self.res / "configs" / f"{name}.json"
                if not path.exists():
                    continue
                g = select(json.load(open(path)), L)[1]
                chunks = len({k["chunk_id"] for k in g["kernels"]})
                on = {(k["chunk_id"], k["layer"]) for k in g["kernels"] if k["use"] and k["npuM"] > 0}
                joins = sum(any((c, l) in on for l in ("gate", "up")) + ((c, "down") in on) for c in range(chunks))
                rows.append([name, L, f"{ffn_share(g):.4f}", 32 * len(on), f"{joins / chunks:.2f}"])
            p = self.best1.get((L, "on"))
            if p:
                rows.append([f"ours p*_on={p}", L, f"{p / 14336:.4f}", 32 * L // 512, "1"])
        out.append("[D] FFN NPU share of FLOPs, NPU submissions per prefill (entries with use and npuM>0, x32 layers; ours: one per layer-chunk), GPU-NPU joins per layer-chunk "
                   "(HeteroMosaic: one after gate/up if either has NPU rows, one after down; ours: one).\n"
                   + table(["config", "L", "FFN NPU share of FLOPs", "NPU submissions per prefill", "joins per layer-chunk"], rows))
        return "\n".join(out)

    def quality_v4(self):
        out = ["### Q1 correctness (v4): last-token logits vs G0 (KL in nats; a correctness gate, not an advantage)\n"]
        for d in sorted(self.res.glob("quality-v4*")):
            per = {}
            for fjs in d.glob("comparison-*.json"):
                for r in json.loads(fjs.read_text()):
                    if r["run"].startswith("gpu_original") and not r["run"].endswith("-r1"):
                        continue
                    name = "G0ctl" if r["run"].startswith("gpu_original") else r["run"].rsplit("-", 2)[0]
                    per.setdefault(name, []).append((r["step1_kl_nats"], r["step1"]["argmax_equal"], r["step1"]["top5_overlap"]))
            if not per:
                continue
            out.append(f"{d.name}:\n" + table(["path", "prompts", "median KL", "max KL", "top-1 matches", "mean top-5"], [
                [n, len(v), f"{st.median(x[0] for x in v):.3e}", f"{max(x[0] for x in v):.3e}", f"{sum(x[1] for x in v)}/{len(v)}", f"{st.mean(x[2] for x in v):.2f}"]
                for n, v in sorted(per.items())]))
            for ref in ("HT1", "HP1", "HT0", "HP0"):
                if ref not in per:
                    continue
                for n in sorted(per):
                    if n == ref or n.startswith("G0") or (ref.endswith("1") != (n.endswith("1") or "O1p" in n)):
                        continue
                    ok = st.median(x[0] for x in per[n]) <= st.median(x[0] for x in per[ref]) and sum(x[1] for x in per[n]) >= sum(x[1] for x in per[ref])
                    out.append(f"- {n} vs {ref} (yardstick: {'shipped HeteroMosaic path, regime 2' if ref.startswith('HT') else 'HeteroMosaic best 1-in-flight path, regime 1'}): "
                               f"median KL {st.median(x[0] for x in per[n]):.3e} vs {st.median(x[0] for x in per[ref]):.3e}, top-1 {sum(x[1] for x in per[n])} vs {sum(x[1] for x in per[ref])} -> "
                               + ("pass" if ok else "does not pass (the sentence carries its KL)"))
        return "\n".join(out) + "\n"

    def report_v4(self):
        out = ["# CP2 v4 evaluation report (regime 1 = one chunk in flight, regime 2 = two or more; measured first, derived last)\n"]
        out.append(f"{len(self.v4)} v4 processes ({len(self.v4) - len(self.v4ok)} excluded as BAD_INFLIGHT). Times are prefill ms; process = median of reps 1-4. "
                   "Earlier 2-in-flight results are in the v3 appendix only.\n")
        bad = [p for p in self.v4 if p["badinfl"]]
        if bad:
            out.append("## BAD_INFLIGHT (log in-flight differs from case.txt; excluded)\n" + "\n".join(f"- {p['stage']}/{p['label']}: case {p['infl']}, log '{p['seen']}'" for p in bad) + "\n")
        bs = [p for p in self.v4 if p["badsel"]]
        if bs:
            out.append("## BAD_SELECTION (HeteroMosaic config did not pick the intended 512-row group)\n" + "\n".join(f"- {p['stage']}/{p['label']}" for p in bs) + "\n")
        fl = [x for x in self.failed if regime_of(x["stage"])]
        if fl:
            out.append("## Failed / incomplete v4 processes\n" + table(["stage", "process", "OOM-recorded", "peak GTT MiB", "error"], [[x["stage"], x["label"], x["oom"], x["peak"], x["error"]] for x in fl]))
        body = [self.regime1(), self.regime2(), self.replication()]   # fill self.R before the verdicts are written
        out += [self.verdicts()] + body + [self.smoke_table(), self.probes_v4(),
                "### Mechanisms (diagnostic processes, never latencies)\n" + self.diagnostics(self.v4ok, legacy=False), self.quality_v4(), self.derived_v4()]
        return "\n".join(x for x in out if x)


class Agg(V4Mixin):
    def __init__(self, res):
        self.res = Path(res)
        self.all, self.failed = load(res)
        self.procs = [p for p in self.all if p["regime"] == 0]   # v3 processes: the appendix tables and best_p.txt
        self.setup_v4()
        self.cells = {}
        for p in self.procs:
            if p["tag"] == "" and "." not in p["cell"] and p["klass"] in ("main", "repl") and p["n"] >= 2:
                self.cells.setdefault((p["cell"], p["L"], p["klass"]), []).append(p)
        self.best = self.read_best()
        self.best1 = self.read_best("best_p1.txt")
        self.ref = {}
        for L in {k[1] for k in self.cells}:
            g0 = [p for k, v in self.cells.items() if k[0] == "G0" and k[1] == L for p in v]
            if g0:
                self.ref[L] = (g0[0]["first"], g0[0]["gen"])

    def read_best(self, name="best_p.txt"):
        out, f_ = {}, self.res / name
        if f_.exists():
            for line in f_.read_text().split("\n"):
                if line.strip():
                    L, s, p = line.split()
                    out[(int(L), s)] = int(p)
        return out

    def pick(self, name, L, klass="main"):
        """The cell of this role at L (a fallback variant only if the primary has no data): (cell key, procs, label) or None."""
        for variant in (name, FALLBACK.get(name)):
            c = [(k, v) for k, v in self.cells.items() if k[1] == L and k[2] == klass and role(k[0])[0] == variant]
            if c:
                want = self.best.get((L, "off" if variant == "O0" else "on"))
                c.sort(key=lambda kv_: (role(kv_[0][0])[1] == want, len(kv_[1])), reverse=True)
                k, v = c[0]
                return k, v, k[0] + ("" if variant == name else " (fallback for %s)" % name)
        return None

    def agree(self, procs, L):
        if L not in self.ref:
            return "n/a"
        first, gen = self.ref[L]
        pre = []
        for p in procs:
            n = 0
            for a, b in zip(p["gen"], gen):
                if a != b:
                    break
                n += 1
            pre.append(n)
        return f"first={'all' if all(p['first'] == first for p in procs) else 'DIFF'} prefix>={min(pre)}/{len(gen)}"

    # -- sweeps -------------------------------------------------------------------------------------------------------------
    def sweep(self, procs=None):
        """(L, state) -> (variant, {p: median ms}) from the sweep stages; the variant with most points wins."""
        pts = {}
        for p in (self.procs if procs is None else procs):
            if p["klass"] == "sweep" and p["tag"] == "" and p["med"] == p["med"] and p["p"]:
                r = role(p["cell"])[0]
                state = "off" if r == "O0" else "on"
                pts.setdefault((p["L"], state, r), {}).setdefault(p["p"], []).append(p["med"])
        out = {}
        for (L, state, r), d in pts.items():
            cur = out.get((L, state))
            if cur is None or len(d) > len(cur[1]) or (len(d) == len(cur[1]) and r in ("O0", "O1")):
                out[(L, state)] = (r, {k: st.median(v) for k, v in d.items()})
        return out

    def write_best(self, inflight=None):
        new = dict(self.best1 if inflight == 1 else self.best)
        procs = [p for p in self.v4ok if p["klass"] == "sweep" and p["infl"] == "1"] if inflight == 1 else None
        for (L, state), (r, d) in self.sweep(procs).items():
            if len(d) >= SWEEP_MIN[state]:
                new[(L, state)] = min(d, key=lambda k: (d[k], k))
        (self.res / ("best_p1.txt" if inflight == 1 else "best_p.txt")).write_text("".join(f"{L} {s} {p}\n" for (L, s), p in sorted(new.items())))
        return new

    # -- report -------------------------------------------------------------------------------------------------------------
    def report(self):
        return self.report_v4() + "\n\n# Appendix: v3 results (2 in flight for H*/O*; replication only, not used in any v4 table)\n\n" + self.report_v3()

    def report_v3(self):
        out = ["# CP2 evaluation report, v3 (measured first, derived/estimated last)\n"]
        out.append(f"{len(self.procs)} finished processes, {len(self.failed)} failed or incomplete. Times are prefill ms; process median of reps 1-4.\n")
        if self.failed:
            out.append("## Failed / incomplete processes\n" + table(["stage", "process", "OOM-recorded", "peak GTT MiB", "error"],
                       [[x["stage"], x["label"], x["oom"], x["peak"], x["error"]] for x in self.failed]))
        bad = [p for p in self.procs if p["badsel"]]
        if bad:
            out.append("## BAD_SELECTION (HeteroMosaic config did not pick the intended 512-row group; excluded from nothing automatically)\n"
                       + "\n".join(f"- {p['stage']}/{p['label']}" for p in bad) + "\n")
        out.append("## Measured\n### Cells (Group P and K share the main cells)\n")
        rows = []
        for (cell, L, klass), v in sorted(self.cells.items(), key=lambda kv_: (kv_[0][1], kv_[0][2], kv_[0][0])):
            s = stats([p["med"] for p in v])
            r0 = [p["rep0"] for p in v]
            rows.append([self.group_of(cell), cell + ("" if klass == "main" else f" [{klass}]"), L, f"{s['n']}x{v[0]['n']}", f(s["med"]), f(s["std"]),
                         f"{f(s['ci'][0])}-{f(s['ci'][1])}", f"{f(s['lo'])}-{f(s['hi'])}", f"{f(st.median(r0))} [{f(min(r0))}-{f(max(r0))}]",
                         self.agree(v, L), max([p["peak"] or 0 for p in v]), sum(p["fb"] for p in v), ",".join(sorted({p["verdict"] for p in v if p["verdict"]}))])
        out.append(table(["group", "cell", "L", "proc x reps", "median ms", "std", "95% t-CI (log)", "min-max of proc medians", "rep0 median [range]",
                          "tokens vs G0", "peak GTT MiB", "UNCACHED_FALLBACK", "merged verdict"], rows))
        for title, pairs, grp in (("Table P1: Group P ratios, end-to-end prefill (num/den; <1 = numerator faster)", P_RATIOS, "P"),
                                  ("Table K1: Group K ratios, generic kernels off -> on", K_RATIOS, "K")):
            rows = []
            for L in sorted({k[1] for k in self.cells}):
                for num, den in pairs:
                    a, b = self.pick(num, L), self.pick(den, L)
                    if a and b:
                        r, ci = ratio(stats([p["med"] for p in a[1]]), stats([p["med"] for p in b[1]]))
                        rows.append([grp, f"{num}/{den}", L, f"{a[2]} / {b[2]}", f"{r:.4f}", "n/a" if ci is None else f"{ci[0]:.4f}-{ci[1]:.4f}",
                                     "n/a" if ci is None else ("CI contains 1: no difference" if ci[0] <= 1 <= ci[1] else "excludes 1"),
                                     f"{len(a[1])}/{len(b[1])}", self.agree(a[1], L) + " ; " + self.agree(b[1], L)])
            out.append(f"### {title}\n" + table(["group", "ratio", "L", "cells", "ratio of medians", "95% CI", "verdict", "n proc", "tokens vs G0 (num ; den)"], rows))
        rows = []
        for L in sorted({k[1] for k in self.cells}):
            for name in ("GS", "HS", "HR"):
                a = self.pick(name, L)
                if a:
                    s = stats([p["med"] for p in a[1]])
                    rows.append(["P (reference)", name, L, f"{s['n']}", f(s["med"]), f"{f(s['ci'][0])}-{f(s['ci'][1])}", self.agree(a[1], L)])
        if rows:
            out.append("### Reference rows (not in any comparison)\n" + table(["group", "cell", "L", "n proc", "median ms", "95% t-CI", "tokens vs G0"], rows))
        rows = []
        for L in sorted({k[1] for k in self.cells}):
            for name, rungs in LADDERS.items():
                prev = None
                for r_ in rungs:
                    a = self.pick(r_, L)
                    if a:
                        m = stats([p["med"] for p in a[1]])
                        rows.append(["K", name, L, a[2], f(m["med"]), f"{m['n']}", "" if prev is None else f"{m['med'] / prev:.4f}"])
                        prev = m["med"]
            for base, loos in LOO.items():
                b = self.pick(base, L)
                for c_ in loos:
                    a = self.pick(c_, L)
                    if a and b and L == 1024:
                        r, ci = ratio(stats([p["med"] for p in a[1]]), stats([p["med"] for p in b[1]]))
                        rows.append(["K", f"leave-one-out from {base}", L, a[2], f(stats([p["med"] for p in a[1]])["med"]), f"{len(a[1])}", f"{r:.4f} vs {base}"])
        if rows:
            out.append("### Table K2: ablation ladder (step ratio = this rung / previous rung)\n" + table(["group", "ladder", "L", "cell", "median ms", "n proc", "step ratio"], rows))
        out.append(self.diagnostics(self.procs))
        out.append(self.sweep_report())
        out.append(self.gate_report())
        out.append(self.quality_report())
        out.append(self.derived())
        return "\n".join(out)

    @staticmethod
    def group_of(cell):
        r = role(cell)[0]
        if r in ("GA1", "G1F", "HA1", "HA2", "OA1", "OA2", "HLs", "HLg", "H1nU", "OLs", "OLg", "O1nU"):
            return "K"
        return "P (reference)" if r in ("HR", "GS", "HS") else "P" if r == "O1F" else "P,K"

    def diagnostics(self, procs, legacy=True):
        d = [p for p in procs if p["tag"]]
        out = ["### Table P2: mechanisms (diagnostic processes, never used for latency; Group P)\n"]
        rows = []
        for L in sorted({p["L"] for p in d}):
            for c in sorted({role(p["cell"])[0] for p in d if p["L"] == L}):
                one = [p for p in d if p["L"] == L and role(p["cell"])[0] == c and p["tag"] == "c1" and p["ioctl"]]
                two = [p for p in d if p["L"] == L and role(p["cell"])[0] == c and p["tag"] == "c2" and p["ioctl"]]
                if one and two:
                    rows.append(["P", f"A1 NPU submissions, {c}", L, one[0]["ioctl"][1], two[0]["ioctl"][1], (two[0]["ioctl"][1] - one[0]["ioctl"][1]) / 2,
                                 f"ctx_ok={two[0]['ioctl'][0]} exec_fail={two[0]['ioctl'][2]}"])
        if rows:
            out.append("A1 count pairs: `--new-tokens 1`, reps 1 vs 2; the difference covers 2 prefills (each rep = generate(1) twice), so /2.\n"
                       + table(["group", "item", "L", "exec_ok reps=1", "exec_ok reps=2", "NPU submissions per prefill", "notes"], rows))
        rows = []
        for p in d:
            if p["tag"] in ("ev1", "ev2"):
                for k, v in stage_transitions(p["dir"] / "ev").items():
                    rows.append(["P", f"{role(p['cell'])[0]} inflight-1 stage events", p["L"], k, f"{v[0]:.3f}", f"{v[1]:.1%}", v[2]])
        if rows:
            out.append("Per-chunk stage latency from STAGE_EVENTS at inflight 1 (mean ms per occurrence over all passes of the process; not idle time):\n"
                       + table(["group", "case", "L", "transition", "mean ms", "share of sum", "occurrences"], rows))
        out.append(self.ffn_stage_table(d))
        if legacy:
            out.append(self.hprobe_table())
        rows = []
        for p in d:
            if p["tag"] in ("tm", "tms", "tmF"):
                for k, v in phase_means(p["dir"] / "tm").items():
                    rows.append(["P", p["tag"], p["L"], k, f"{v:.3f}"])
        if rows:
            out.append("FFN phase timers of O1 (`tm`) and with the GPU branch serialized (`tms`), mean ms per FFN call (timers add waits):\n"
                       + table(["group", "case", "L", "column", "mean ms"], rows))
        return "\n".join(out) + "\n"

    def ffn_stage_table(self, d):
        rows = []
        for p in sorted((p for p in d if p["tag"] in ("ev1", "ev2")), key=lambda p: (p["L"], p["cell"])):
            r = stage_sums(p["dir"] / "ev", p["L"], p["n"])
            if r is None:
                continue
            m = lambda k: f(st.median(r["use"][k]), 2) if r["use"][k] else "n/a"
            rows.append(["P", role(p["cell"])[0], p["L"], r["note"] or f"{len(r['use']['ffn'])} passes", m("attn"), m("attn_m"), m("ffn"), m("ffn_m"),
                         f(st.median(r["rep0"]["ffn"]), 2) if r["rep0"]["ffn"] else "n/a"])
        return ("### FFN stage time (diagnostic, inflight 1; ms per prefill, summed over layers and chunks; reps >= 1, median over passes)\n"
                "FFN = ready->end. Matched boundary: FFN + next layer's start->norm (ours' RESIDUAL_NORM runs the next residual+norm inside ready->end), "
                "attention = start->ready, matched = minus start->norm. The last layer has no next layer. Timers add waits: never a latency.\n"
                + table(["group", "cell", "L", "passes", "attention start->ready", "attention matched", "FFN ready->end", "FFN matched boundary",
                         "FFN ready->end, rep 0"], rows))

    def hprobe_table(self, procs=None, title="HeteroMosaic ratio probe, 1024 (process medians of reps 1-4 and their mean, ms; screening grade)"):
        by = {}
        for p in (self.procs if procs is None else procs):
            if p["klass"] == "hprobe" and p["med"] == p["med"]:
                by.setdefault((p["tag"], role(p["cell"])[0]), []).append(p["med"])
        if not by:
            return ""
        mean = {k: st.mean(v) for k, v in by.items()}
        best = {r: min((k for k in mean if k[1] == r), key=lambda k: mean[k], default=None) for r in ("H1", "H0")}
        rows = []
        for combo in sorted({k[0] for k in by}):
            row = ["P", combo]
            for r in ("H1", "H0"):
                v = by.get((combo, r))
                row += [", ".join(f(x) for x in v) if v else "n/a", (f(mean[(combo, r)]) + (" BEST" if best[r] == (combo, r) else "")) if v else "n/a"]
            rows.append(row)
        return (f"### {title}\n"
                + table(["group", "combo", "H1 process medians", "H1 mean", "H0 process medians", "H0 mean"], rows))

    def sweep_report(self, sw=None, title="Sweep T(p): 1 process x 3 reps, screening grade (median of reps 1-2); best p goes to best_p.txt"):
        rows, sw = [], (self.sweep() if sw is None else sw)
        for (L, state), (r, d) in sorted(sw.items()):
            best = min(d, key=lambda k: (d[k], k))
            for p_ in sorted(d):
                rows.append(["P", L, f"kernels {state} ({r})", p_, f(d[p_]), "<- best" if p_ == best else ""])
        return f"### {title}\n" + table(["group", "L", "state", "p", "ms", ""], rows)

    def gate_report(self):
        rows = []
        for p in sorted((p for p in self.procs if p["klass"] == "gate" and p["tag"] == ""), key=lambda p: (p["L"], p["cell"])):
            ref = {"O1p8192": 1004.2, "HR": 1325.2}.get(p["cell"]) if p["L"] == 1024 else None
            rows.append(["P", p["cell"], p["L"], p["n"], f(p["med"]), f(p["rep0"]), "" if ref is None else f"{p['med'] / ref - 1:+.1%} vs {ref} (11-14)",
                         p["peak"], p["fb"], p["verdict"], "BAD" if p["badsel"] else "ok", p["gemm"]])
        return "### Gates (1 process; 5 reps at 1024 = repro check, 1 rep at 4096 = memory probe)\n" + table(
            ["group", "cell", "L", "reps", "median ms (reps 1-4)", "rep0 ms", "vs 11-14", "peak GTT MiB", "UNCACHED_FALLBACK", "merged verdict", "selection", "HETERO_GPU_GEMM"], rows)

    def quality_report(self):
        out = ["### Q1 correctness: last-token logits vs G0 (KL in nats; shown as a check, not an advantage; Group P)\n"]
        for d in sorted(x for x in self.res.glob("quality*") if not x.name.startswith("quality-v4")):
            rows, per = [], {}
            for fjs in sorted(d.glob("comparison-*.json"), key=lambda x: int(re.findall(r"\d+", x.name)[0])):
                seed = re.findall(r"\d+", fjs.name)[0]
                for r in json.loads(fjs.read_text()):
                    name = r["run"].rsplit("-", 2)[0] + ("ctl" if r["run"].endswith("-r1") else "")
                    if r["run"].startswith("gpu_original") and not r["run"].endswith("-r1"):
                        continue
                    name = {"gpu_originalctl": "G0ctl"}.get(name, name)
                    per.setdefault(name, []).append((r["step1_kl_nats"], r["step1"]["argmax_equal"], r["step1"]["top5_overlap"]))
                    rows.append(["P", seed, name, f"{r['step1_kl_nats']:.3e}", r["step1"]["argmax_equal"], r["step1"]["top5_overlap"]])
            if not rows:
                continue
            out.append(f"{d.name}:\n" + table(["group", "prompt seed", "path", "KL", "top-1 equal", "top-5 overlap /5"], rows))
            summ = [["P", n, len(v), f"{st.median(x[0] for x in v):.3e}", f"{max(x[0] for x in v):.3e}", f"{sum(x[1] for x in v)}/{len(v)}", f"{st.mean(x[2] for x in v):.2f}"]
                    for n, v in sorted(per.items())]
            out.append(table(["group", "path", "prompts", "median KL", "max KL", "top-1 matches", "mean top-5"], summ))
            for o, h in (("O0", "H0"), ("O1", "H1")):
                if o in per and h in per:
                    out.append(f"- {o} vs {h}: median KL {st.median(x[0] for x in per[o]):.3e} vs {st.median(x[0] for x in per[h]):.3e}; top-1 {sum(x[1] for x in per[o])} vs {sum(x[1] for x in per[h])} -> "
                               + ("pass" if st.median(x[0] for x in per[o]) <= st.median(x[0] for x in per[h]) and sum(x[1] for x in per[o]) >= sum(x[1] for x in per[h]) else "does not pass"))
        return "\n".join(out) + "\n"

    def derived(self):
        out = ["## Derived / estimated (computed from configs and counters, no timing)\n"]
        try:
            from make_hm_configs import ffn_share, select
        except Exception as e:  # noqa: BLE001
            return "\n".join(out) + f"(make_hm_configs not importable: {e})\n"
        rows = []
        for L in (1024, 2048, 4096):
            cfg_path = self.res / "configs" / f"hm_{L}.json"
            if cfg_path.exists():
                g = select(json.load(open(cfg_path)), L)[1]
                n = sum(1 for k in g["kernels"] if k["layer"] in ("gate", "up", "down") and k["use"] and k["npuM"] > 0)
                chunks = len({k["chunk_id"] for k in g["kernels"]})
                on = {(k["chunk_id"], k["layer"]) for k in g["kernels"] if k["use"] and k["npuM"] > 0}
                # the host waits once after gate+up (unified_llm_w4a16.cpp ~2873-2878) and once after down (~2886-2888)
                joins = sum(any((c, l) in on for l in ("gate", "up")) + ((c, "down") in on) for c in range(chunks))
                rows.append(["P", f"HeteroMosaic hm_{L}", L, f"{ffn_share(g):.4f}", n * 32, f"{joins / chunks:.2f}"])
            rows.append(["P", f"ours p*={self.best.get((L, 'on'), '?')}", L, f"{self.best[(L, 'on')] / 14336:.4f}" if (L, "on") in self.best else "?", 32 * L // 512, "1"])
        out.append("[D] FFN NPU share of FLOPs, NPU submissions per prefill (table entries with use and npuM>0, x32 layers; ours: one per layer-chunk), "
                   "GPU-NPU joins per layer-chunk in the FFN (HeteroMosaic: one after gate/up if either has NPU rows, one after down if it has; ours: one).\n"
                   + table(["group", "config", "L", "FFN NPU share of FLOPs", "NPU submissions per prefill", "joins per layer-chunk"], rows))
        out.append("No estimated ([E]) value is produced by this script.\n")
        return "\n".join(out)


def stage_transitions(d):
    """Mean ms per stage transition in stages_<pid>.csv (chunk,slot,layer,stage,ms): one object = one chunk pass, split when the layer restarts."""
    acc = {}
    for fcsv in glob.glob(str(d / "stages_*.csv")):
        prev = None
        for line in open(fcsv):
            c = line.strip().split(",")
            if len(c) != 5:
                continue
            key, layer, stage, ms = (c[0], c[1]), int(c[2]), c[3], float(c[4])
            if prev and prev[0] == key and layer >= prev[1]:
                acc.setdefault(f"{prev[2]}->{stage}", []).append(ms - prev[3])
            prev = (key, layer, stage, ms)
    tot = sum(st.mean(v) for v in acc.values()) or 1
    return {k: (st.mean(v), st.mean(v) / tot, len(v)) for k, v in sorted(acc.items())}


def stage_sums(d, L, reps):
    """ev1 CSV (chunk,slot,layer,stage,ms) -> per-prefill sums. One object per chunk pass (split on chunk/slot change or layer restart);
    passes = warmup, then 2 per rep (generate(1), generate(n)), each L//512 objects. Rep 0 = passes 1-2, reps >= 1 = passes 3+."""
    objs = []
    for fcsv in glob.glob(str(d / "stages_*.csv")):
        prev = None
        for line in open(fcsv):
            c = line.strip().split(",")
            if len(c) != 5:
                continue
            key, layer = (c[0], c[1]), int(c[2])
            if prev is None or prev[0] != key or layer < prev[1]:
                objs.append({})
            objs[-1].setdefault(layer, {})[c[3]] = float(c[4])
            prev = (key, layer)
    k = L // 512
    if not objs or len(objs) != k * (1 + 2 * reps):
        return dict(use=dict(attn=[], attn_m=[], ffn=[], ffn_m=[]), rep0=dict(ffn=[]), note=f"irregular: {len(objs)} objects, expected {k * (1 + 2 * reps)}") if objs else None
    passes = []
    for i in range(0, len(objs), k):
        tot = dict(attn=0.0, attn_m=0.0, ffn=0.0, ffn_m=0.0)
        for o in objs[i:i + k]:
            for l, m in o.items():
                if "start" in m and "ready" in m and "end" in m:
                    sn = (o[l + 1]["norm"] - o[l + 1]["start"]) if l + 1 in o and "norm" in o[l + 1] and "start" in o[l + 1] else 0.0
                    own = (m["norm"] - m["start"]) if "norm" in m else 0.0
                    tot["attn"] += m["ready"] - m["start"]; tot["attn_m"] += m["ready"] - m["start"] - own
                    tot["ffn"] += m["end"] - m["ready"]; tot["ffn_m"] += m["end"] - m["ready"] + sn
        passes.append(tot)
    cols = ("attn", "attn_m", "ffn", "ffn_m")
    return dict(use={c: [p[c] for p in passes[3:]] for c in cols}, rep0=dict(ffn=[p["ffn"] for p in passes[1:3]]), note="")


def phase_means(d):
    out = {}
    for fcsv in glob.glob(str(d / "merged_ffn_phases_*.csv")):
        rows = list(csv.DictReader(open(fcsv)))
        for col in rows[0] if rows else []:
            if col.endswith("_ns") or col == "since_prev_end_ns":
                out[col] = st.mean(float(r[col]) for r in rows) / 1e6
    return out


def per_process_csv(a, outdir=None):
    out = Path(outdir) if outdir else a.res / "aggregate"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "per_process.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stage", "process", "group", "cell", "tag", "L", "p", "reps", "median_ms_reps1-4", "rep0_ms", "peak_gtt_mib", "ctx_ok", "exec_ok",
                    "uncached_fallback", "merged_verdict", "bad_selection", "regime", "inflight_case", "inflight_log", "bad_inflight", "temp_sclk_before"])
        for p in a.all:
            w.writerow([p["stage"], p["label"], p["group"], p["cell"], p["tag"], p["L"], p["p"], p["n"], f(p["med"], 3), f(p["rep0"], 3), p["peak"],
                        p["ioctl"][0] if p["ioctl"] else "", p["ioctl"][1] if p["ioctl"] else "", p["fb"], p["verdict"], p["badsel"], p["regime"], p["infl"], p["seen"], p["badinfl"], p["temp"]])
    return out


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    res = sys.argv[1]
    a = Agg(res)
    if "--write-best-p" in sys.argv:
        print("best_p:", a.write_best(int(sys.argv[sys.argv.index("--inflight") + 1]) if "--inflight" in sys.argv else None))
        return
    text = a.report()
    out = per_process_csv(a, sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None)
    (out / "report.md").write_text(text)
    print(text)
    print(f"written {out / 'report.md'} and per_process.csv")


if __name__ == "__main__":
    main()
