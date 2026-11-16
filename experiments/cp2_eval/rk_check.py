#!/usr/bin/env python3
"""Cell gate of the config-ranking check stages (rk*, apmb*; any process with a src= tree).
  rk_check.py D                 process dir: writes D/fingerprint.txt; exit 1 with the reasons if anything differs from the intent
  rk_check.py dry CFG SRC L [WANT]  the effective config a heteromosaic process would load from CFG on tree SRC (no run)
Checks: a prefill median in summary.csv; the backend .so and every NPU file the log loaded lie under the cell's tree (a wrong
HETEROMOSAIC_ROOT would load hw_bins_ours from another tree or fall back to the GPU); in flight seen = intended; no 'Failed to create'
or 'Reached maximum' line. heteromosaic: the selection line = the group the C++ rule picks from the config the process ran
(result.config.json, after --inflight); the GEMMs loaded (Loading Instructions, in order) = that group's NPU entries; PDI contexts
loaded = the count under the tree's PDI cache key (old: npuK/tile/col/dtype; new: also npuM x npuN), at most MAX_NPU_HW_CTX = 6; all
files under <tree>/<bins>/ (bins: want file, else hw_bins_ours for *.ours.json configs); with want=: group, schedule, in flight,
gate/up/down and q/k/v/o NPU rows per micro-batch as the want file says. Token agreement is not checked."""
import glob, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_hm_configs import schedule_of, select   # noqa: E402
from make_rk_configs import ATT, FFN, rows   # noqa: E402

MAX_HW_CTX = 6


def kv(p):
    return dict(l.split("=", 1) for l in Path(p).read_text().splitlines() if "=" in l) if Path(p).exists() else {}


def new_key(src):
    return 'tile_size + "@" + std::to_string(npuM)' in Path(src, "src/unified_llm_w4a16_hetero/npuSetup.cpp").read_text()


def loaded(cfg, L):
    """(group index, group, NPU entries the loader keeps in order) for prompt length L, as load_npu_kernels."""
    gi, g = select(cfg, L)
    sch = schedule_of(g)
    mf = -1 if len(sch) > 1 else sch[0]
    ents = [k for k in g["kernels"] if k.get("use", True) and k["npuM"] > 0 and not (mf > 0 and k["forM"] != mf)]
    return gi, g, ents


def pdis(ents, newkey):
    return len({(k["npuK"], k["tile_size"] + (f"@{k['npuM']}x{k['npuN']}" if newkey else ""), k["col"], k["dtype"]) for k in ents})


def summary(cfg, L, src, newkey=None):
    gi, g, ents = loaded(cfg, L)
    return {"group": gi, "schedule": schedule_of(g), "inflight": g.get("hetero_inflight"), "gate/up/down": rows(g, FFN),
            "q/k/v/o": rows(g, ATT), "pdi": pdis(ents, new_key(src) if newkey is None else newkey),
            "bins": sorted({k["fw_path"].split("/")[0] for k in ents})}


def compare_want(eff, want, bad):
    for f in ("group", "schedule", "inflight", "gate/up/down", "q/k/v/o"):
        if eff[f] != want[f]:
            bad.append(f"{f}: config {eff[f]} != want {want[f]}")
    if eff["bins"] and eff["bins"] != [want["bins"]]:
        bad.append(f"bins: config {eff['bins']} != want {want['bins']}")


def check(D):
    D = Path(D)
    case, bad = kv(D / "case.txt"), []
    src, L, method = case["src"], int(case["L"]), case["method"]
    logs = "".join(Path(f).read_text(errors="ignore") for f in sorted(glob.glob(f"{D}/*.log")))
    try:
        ttft = float((D / "summary.csv").read_text().strip().splitlines()[-1].split(",")[4])
    except (OSError, ValueError, IndexError):
        ttft = None
        bad.append("no prefill median in summary.csv")
    res = [json.loads(Path(f).read_text()) for f in glob.glob(f"{D}/*.result.json")]
    be = res[0].get("backend", "") if res else ""
    if not be.startswith(f"{src}/{case['build']}/"):
        bad.append(f"backend {be or '?'} not under {src}/{case['build']}")
    for pat in ("Failed to create", "Reached maximum"):
        if pat in logs:
            bad.append(f"log has '{pat}'")
    seen = sorted({int(x) for x in re.findall(r"pipeline enabled with (\d+) inflight", logs)} | ({1} if "serial chunk execution" in logs else set()))
    want = json.loads((Path(case["cfgdir"]) / case["want"]).read_text()) if case.get("want") else None
    infl = int(case["inflight"]) if case.get("inflight") else want["inflight"] if want else None
    if infl is not None and seen != [infl]:
        bad.append(f"in flight seen {seen} != {infl}")
    fp = {"tree": src, "method": method, "switches": " ".join(sorted(x.replace("HETEROMEGA_", "") for x in (D / "env.txt").read_text().split()
                                                                     if "FINITE_CHECK" not in x)) or "(none)", "inflight_seen": seen, "prefill_ms": ttft}
    if method == "heteromosaic":
        cfg = json.loads(Path(glob.glob(f"{D}/*.result.config.json")[0]).read_text())
        nk = new_key(src)
        eff = summary(cfg, L, src, nk)
        gi, g, ents = loaded(cfg, L)
        sel = re.search(r"Using grouped kernels_gemm_chunked \(chunk_size=(\d+), chunk_schedule=\[([^]]*)\], inflight=(\d+), prompt_len=(\d+)", logs)
        sch = eff["schedule"]
        if not sel or [int(sel[1]), [int(x) for x in sel[2].split(",") if x.strip()], int(sel[3]), int(sel[4])] != [sch[0], sch, eff["inflight"], L]:
            bad.append(f"selection line {sel[0] if sel else 'missing'} != group #{gi} {sch} inflight {eff['inflight']}")
        got = [tuple(map(int, m)) for m in re.findall(r"Loading Instructions: \S*/insts_(\d+)x(\d+)x(\d+)_", logs)]
        exp = [(k["npuM"], k["npuK"], k["npuN"]) for k in ents]
        if got != exp:
            bad.append(f"GEMMs loaded {got} != group entries {exp}")
        files = re.findall(r"Loading (?:PDI|Instructions|GEMV PDI|GEMV Inst): (\S+)", logs)
        bins = want["bins"] if want else "hw_bins_ours" if case.get("config", "").endswith(".ours.json") else "hw_bins"
        off = [f for f in files if not f.startswith(f"{src}/{bins}/")]
        if off:
            bad.append(f"{len(off)} of {len(files)} NPU files not under {src}/{bins}/: {off[0]}")
        npdi, ngemv = len(re.findall(r"Loading PDI: ", logs)), len(re.findall(r"Loading GEMV PDI: ", logs))
        if npdi != eff["pdi"] or npdi + ngemv > MAX_HW_CTX:
            bad.append(f"PDI contexts loaded {npdi} (+{ngemv} GEMV) != expected {eff['pdi']} under the {'new' if nk else 'old'} key, or > {MAX_HW_CTX}")
        if want:
            compare_want(eff, want, bad)
        fp.update(key="new" if nk else "old", group=f"#{gi} {sch} inflight {eff['inflight']}", split=", ".join(eff["gate/up/down"]),
                  attn=", ".join(eff["q/k/v/o"]), fw_dir=sorted({f.rsplit("/", 3)[0] for f in files}), pdi=npdi, gemv_pdi=ngemv)
    (D / "fingerprint.txt").write_text("".join(f"{k}={v}\n" for k, v in fp.items()))
    print("\n".join(bad) if bad else "ok")
    return not bad


def dry(cfg, src, L, want=None):
    eff, bad = summary(json.loads(Path(cfg).read_text()), int(L), src), []
    if want:
        compare_want(eff, json.loads(Path(want).read_text()), bad)
    print(f"group #{eff['group']} {eff['schedule']} inflight(config) {eff['inflight']} | gate/up/down {', '.join(eff['gate/up/down'])} | "
          f"q/k/v/o {', '.join(eff['q/k/v/o'])} | bins {','.join(eff['bins']) or '-'} | PDIs {eff['pdi']} ({'new' if new_key(src) else 'old'} key)"
          + ("" if not bad else " | MISMATCH " + "; ".join(bad)))
    return not bad


if __name__ == "__main__":
    if sys.argv[1] == "dry":
        sys.exit(0 if dry(*sys.argv[2:]) else 1)
    sys.exit(0 if check(sys.argv[1]) else 1)
