"""HeteroMosaic FFN ratio probe (user request 2026-11-15): uniform gate/up/down npuM per chunk on the FFN-only 512-row tables.
  hm_ratio.py CFGDIR probe            write hp_<combo>.json (from hm_1024.json) for every probe combo
  hm_ratio.py CFGDIR pick PROBE_DIR   pick the combo with the lowest H1 median (summary.csv col 5, mean over processes),
                                      keep hm_<L>.json as hm_<L>.shipped.json, rewrite hm_1024/2048/4096 with that combo in every chunk

Regime-1 (1 in flight) probe, plan v4 section 2.1/10.2; never touches hm_<L>.json or hm_<L>.shipped.json:
  hm_ratio.py CFGDIR combos1          the 26 uniform combos (gate, up, down in {0,256,512}, not all zero)
  hm_ratio.py CFGDIR probe1 L         L=1024: write hp1_<combo>.json for all 26; L>1024: hp1_<combo>_<L>.json for the top 3 of hm_rank1.txt
  hm_ratio.py CFGDIR top1 [N]         top N combos of hm_rank1.txt (default 3)
  hm_ratio.py CFGDIR rank1 L DIR      rank the H1 screen of 1024 (DIR=.../hprobe1-1024) -> hm_rank1.txt
  hm_ratio.py CFGDIR pick1 L DIR...   winner over the H1 processes in DIRs -> hm1_<L>.json (HP1, from H1) and hm1o_<L>.json (HP0, from H0, ranked separately); ties within 0.5% go to fewer NPU operators
  hm_ratio.py CFGDIR hbprobe L        token-split candidates for HB: L=1024 writes hb_1024.json (g256u256d256, best token split of hprobe-1024); else hb_<c>_<L>.json
  hm_ratio.py CFGDIR hbpick L DIR     best H1 mean of DIR (hbcheck-<L>, inflight 2) -> hb_<L>.json
  hm_ratio.py CFGDIR same A.json B.json L   exit 0 if gate/up/down (chunk, npuM, use) of the prompt_len=L groups agree
Per-micro-batch placement search at 2 in flight (11-15 user; no operator split by tokens). Pattern = one letter per chunk:
  A = 512/512/0, B = 0/0/512, G = 0/0/0 (FFN on the GPU), N = 512/512/512 (FFN on the NPU). Configs pm_<pattern>_<L>.json.
  hm_ratio.py CFGDIR pmb_mid L        middle patterns (all A, all B, A/B alternating, N/G alternating), first = last = A -> pmb_mid_<L>.txt
  hm_ratio.py CFGDIR pmb_ends L [DIR] best middle of DIR (pmb1-<L>; none at 1024), then first x last in {A,B,G,N} -> pmb_ends_<L>.txt
  hm_ratio.py CFGDIR pmb_top L DIR... the 2 best patterns of the screens, uniform A excluded (it runs as H1) -> pmb_top_<L>.txt; also writes uniform B (0/0/512)
  hm_ratio.py CFGDIR pats L PAT...    write pm_<PAT>_<L>.json for the given patterns (-> pats_<L>.txt)
  hm_ratio.py CFGDIR pmb_win L DIR    pattern with the lowest median of H1.<pattern> process medians in DIR (apmbc-<L>) -> pmb_win_<L>.txt
Processes with a BAD_CONFIG file (rk_check.py gate) are left out of every ranking.
Combo "g256u256d0" = gate npuM 256, up 256, down 0 (= shipped at 1024). Same prebuilt binaries (npuM is a runtime M)."""
import glob, json, os, re, statistics, sys

COMBOS1 = [f"g{g}u{u}d{d}" for g in (0, 256, 512) for u in (0, 256, 512) for d in (0, 256, 512) if g or u or d]
HB_COMBOS = ["g256u256d0", "g256u256d256", "g256u256d512", "g512u512d256"]   # operator-splitting (npuM=256 somewhere) candidates for HB at 2 in flight
COMBOS = ["g256u256d0", "g512u512d0", "g256u256d256", "g256u256d512", "g512u512d256", "g0u0d512"]


def parse(combo):
    g, u, d = map(int, re.fullmatch(r"g(\d+)u(\d+)d(\d+)", combo).groups())
    return {"gate": g, "up": u, "down": d}


def apply(cfg, length, combo):
    m = parse(combo)
    n = 0
    for group in cfg["kernels_gemm_chunked"]:
        sched = group.get("hetero_chunk_size_schedule") or [group.get("hetero_chunk_size")]
        if group["prompt_len"] != length or set(sched) != {512}:
            continue
        for k in group["kernels"]:
            if k["layer"] in m:
                k["npuM"], k["use"] = m[k["layer"]], m[k["layer"]] > 0
                n += 1
    assert n > 0 and n % (3 * (length // 512)) == 0, (length, n)  # each 512-row table: one gate, up and down entry per chunk
    return cfg


def nops(combo):
    return sum(v > 0 for v in parse(combo).values())


def h1_means(L, dirs, role="H1"):
    """{tag: [process medians ms]} from <dir>/<role>.<tag>-<L>-s*/summary.csv."""
    res = {}
    for dr in dirs:
        for d in glob.glob(f"{dr}/{role}.*-{L}-s*"):
            if os.path.exists(f"{d}/BAD_CONFIG"):
                continue
            tag = re.search(rf"{role}\.(\w+)-{L}-s", d).group(1)
            try:
                row = open(f"{d}/summary.csv").read().strip().splitlines()[-1].split(",")
                res.setdefault(tag, []).append(float(row[4]))
            except (OSError, ValueError, IndexError):
                pass
    return res


def winner(res):
    order = sorted(res, key=lambda t: statistics.mean(res[t]))
    best = statistics.mean(res[order[0]])
    near = [t for t in order if statistics.mean(res[t]) <= best * 1.005]
    return min(near, key=lambda t: (nops(t) if re.fullmatch(r"g\d+u\d+d\d+", t) else 9, statistics.mean(res[t]))), order


def shipped_or_apply(cfgdir, L, combo):
    return apply(json.load(open(f"{cfgdir}/hm_{L}.shipped.json")), L, combo)


def entries(path, L):
    out = set()
    for g in json.load(open(path))["kernels_gemm_chunked"]:
        if g["prompt_len"] == L:
            out |= {(g.get("hetero_chunk_size") or 0, k["chunk_id"], k["layer"], k["npuM"], bool(k["use"])) for k in g["kernels"] if k["layer"] in ("gate", "up", "down")}
    return out


def top1(cfgdir, n=3):
    return [l.split(":")[0] for l in open(f"{cfgdir}/hm_rank1.txt").read().splitlines() if l.strip()][:n]


PLACE = {"A": "g512u512d0", "B": "g0u0d512", "G": "g0u0d0", "N": "g512u512d512", "Q": "g256u256d0"}   # Q: the author's 1-in-flight entry (1024)


def apply_chunks(cfg, length, pat):
    """Placement PLACE[pat[c]] for chunk c of the 512-row group of this length; every chunk must have gate, up and down entries."""
    assert len(pat) == length // 512, (length, pat)
    seen = set()
    for group in cfg["kernels_gemm_chunked"]:
        sched = group.get("hetero_chunk_size_schedule") or [group.get("hetero_chunk_size")]
        if group["prompt_len"] != length or set(sched) != {512}:
            continue
        for k in group["kernels"]:
            if k["layer"] in ("gate", "up", "down"):
                m = parse(PLACE[pat[k["chunk_id"]]])[k["layer"]]
                k["npuM"], k["use"] = m, m > 0
                seen.add((k["chunk_id"], k["layer"]))
    assert seen == {(c, l) for c in range(len(pat)) for l in ("gate", "up", "down")}, (length, pat, sorted(seen))
    return cfg


def write_pats(cfgdir, L, pats, name):
    for p in pats:
        json.dump(apply_chunks(json.load(open(f"{cfgdir}/hm_{L}.shipped.json")), L, p), open(f"{cfgdir}/pm_{p}_{L}.json", "w"), indent=1)
    open(f"{cfgdir}/{name}_{L}.txt", "w").write(" ".join(pats) + "\n")
    print(name, L, " ".join(pats))


def pmb_mid(n):
    mid = n - 2
    return {"AA": "A" * mid, "BB": "B" * mid, "AB": ("AB" * n)[:mid], "NG": ("NG" * n)[:mid]}


def main_v4(cfgdir, mode, a):
    if mode == "r1u":   # 11-15 user: HeteroMosaic at 1 in flight = the author's 1-in-flight entry 256/256/0 on every micro-batch, at any length
        L = int(a[0]); write_pats(cfgdir, L, ["Q" * (L // 512)], "r1u"); return
    if mode == "pats":
        write_pats(cfgdir, int(a[0]), a[1:], "pats"); return
    if mode == "pmb_win":
        L = int(a[0]); res = {t: v for t, v in h1_means(L, a[1:]).items() if len(t) == L // 512 and set(t) <= set(PLACE)}
        order = sorted(res, key=lambda t: statistics.median(res[t]))
        for t in order:
            print(f"{t}: process medians {', '.join(f'{x:.1f}' for x in res[t])} median {statistics.median(res[t]):.1f}")
        open(f"{cfgdir}/pmb_win_{L}.txt", "w").write(order[0] + "\n")
        print("pmb_win", L, order[0]); return
    if mode in ("pmb_mid", "pmb_ends", "pmb_top"):
        L = int(a[0]); n = L // 512
        if mode == "pmb_mid":
            write_pats(cfgdir, L, ["A" + m + "A" for m in pmb_mid(n).values()], "pmb_mid")
        elif mode == "pmb_ends":
            mid = ""
            if n > 2:
                res = {t: v for t, v in h1_means(L, a[1:]).items() if t in ["A" + m + "A" for m in pmb_mid(n).values()]}
                order = sorted(res, key=lambda t: statistics.mean(res[t]))
                for t in order:
                    print(f"middle {t}: H1 process medians {', '.join(f'{x:.1f}' for x in res[t])}")
                mid = order[0][1:-1]
                open(f"{cfgdir}/pmb_pick.txt", "a").write(f"{L} middle {order[0]}\n")
            write_pats(cfgdir, L, [f + mid + l for f in "ABGN" for l in "ABGN"], "pmb_ends")
        else:
            res = {t: v for t, v in h1_means(L, a[1:]).items() if len(t) == n and set(t) <= set(PLACE) and t != "A" * n}
            order = sorted(res, key=lambda t: statistics.mean(res[t]))
            for t in order:
                print(f"{t}: H1 screen process medians {', '.join(f'{x:.1f}' for x in res[t])}")
            open(f"{cfgdir}/pmb_top_{L}.txt", "w").write(" ".join(order[:2]) + "\n")
            open(f"{cfgdir}/pmb_pick.txt", "a").write(f"{L} top {' '.join(order[:2])}\n")
            print("pmb_top", L, " ".join(order[:2]))
            write_pats(cfgdir, L, ["B" * n], "pmb_rev")   # uniform 0/0/512, always in the confirmation stage
        return
    if mode == "combos1":
        print(" ".join(COMBOS1))
    elif mode == "top1":
        print(" ".join(top1(cfgdir, int(a[0]) if a else 3)))
    elif mode == "probe1":
        L = int(a[0])
        for c in (COMBOS1 if L == 1024 else top1(cfgdir)):
            json.dump(shipped_or_apply(cfgdir, L, c), open(f"{cfgdir}/hp1_{c}{'' if L == 1024 else f'_{L}'}.json", "w"), indent=1)
        print("probe1 written for", L)
    elif mode == "rank1":
        L, res = int(a[0]), h1_means(int(a[0]), a[1:])
        lines = [f"{t}: {statistics.mean(v):.1f} ms (H1 process medians {', '.join(f'{x:.1f}' for x in v)})" for t, v in sorted(res.items(), key=lambda x: statistics.mean(x[1]))]
        open(f"{cfgdir}/hm_rank1.txt", "w").write("\n".join(lines) + "\n")
        print("\n".join(lines))
    elif mode == "pick1":
        L = int(a[0])
        keep = set(top1(cfgdir))   # at 1024 the top 3 of the screen were re-run: only they compete (the screen is one process each)
        for role, out in (("H1", "hm1"), ("H0", "hm1o")):   # HP1 config from the H1 ranking, HP0 config from the H0 ranking (ranked separately)
            res = h1_means(L, a[1:], role)
            if L == 1024:
                res = {t: v for t, v in res.items() if t in keep}
            if not res:
                print(f"pick1: no {role} processes for {L}, {out}_{L}.json not written")
                continue
            best, order = winner(res)
            for t in order:
                print(f"{role} {t}: process medians {', '.join(f'{x:.1f}' for x in res[t])} mean {statistics.mean(res[t]):.1f}")
            cfg = json.load(open(f"{cfgdir}/hm_{L}.shipped.json")) if best == "shipped" else shipped_or_apply(cfgdir, L, best)
            json.dump(cfg, open(f"{cfgdir}/{out}_{L}.json", "w"), indent=1)
            open(f"{cfgdir}/hm1_pick.txt", "a").write(f"{L} {role} {best}\n")
            print("pick1", L, role, best, "->", f"{out}_{L}.json (hm_{L}.json and hm_{L}.shipped.json untouched)")
    elif mode == "hbprobe":
        L = int(a[0])
        if L == 1024:
            json.dump(shipped_or_apply(cfgdir, L, "g256u256d256"), open(f"{cfgdir}/hb_1024.json", "w"), indent=1)
        else:
            for c in HB_COMBOS:
                json.dump(shipped_or_apply(cfgdir, L, c), open(f"{cfgdir}/hb_{c}_{L}.json", "w"), indent=1)
        print("hbprobe written for", L)
    elif mode == "hbpick":
        L = int(a[0])
        res = h1_means(L, a[1:])
        best, order = winner(res)
        for t in order:
            print(f"{t}: H1 inflight-2 process medians {', '.join(f'{x:.1f}' for x in res[t])}")
        json.dump(shipped_or_apply(cfgdir, L, best), open(f"{cfgdir}/hb_{L}.json", "w"), indent=1)
        print("hbpick", L, best, "-> hb_%d.json" % L)
    elif mode == "same":
        sys.exit(0 if entries(a[0], int(a[2])) == entries(a[1], int(a[2])) else 1)
    else:
        raise SystemExit("unknown mode " + mode)


def main():
    cfgdir, mode = sys.argv[1:3]
    if mode in ("combos1", "top1", "probe1", "rank1", "pick1", "hbprobe", "hbpick", "same", "pmb_mid", "pmb_ends", "pmb_top", "r1u", "pats", "pmb_win"):
        return main_v4(cfgdir, mode, sys.argv[3:])
    if mode == "combos":
        print(" ".join(COMBOS))
        return
    if mode == "probe":
        for c in COMBOS:
            cfg = apply(json.load(open(f"{cfgdir}/hm_1024.json")), 1024, c)
            json.dump(cfg, open(f"{cfgdir}/hp_{c}.json", "w"), indent=1)
        print("written", " ".join(f"hp_{c}.json" for c in COMBOS))
        return
    probe = sys.argv[3]
    res = {}
    for d in glob.glob(f"{probe}/H1.*-1024-s*"):
        tag = re.search(r"H1\.(\w+)-1024", d).group(1)
        try:
            row = open(f"{d}/summary.csv").read().strip().splitlines()[-1].split(",")
            res.setdefault(tag, []).append(float(row[4]))
        except (OSError, ValueError, IndexError):
            pass
    for tag, v in sorted(res.items(), key=lambda x: statistics.mean(x[1])):
        print(f"{tag}: H1 median ms per process {', '.join(f'{x:.1f}' for x in v)}")
    best = min(res, key=lambda t: statistics.mean(res[t]))
    for L in (1024, 2048, 4096):
        p = f"{cfgdir}/hm_{L}.json"
        if not os.path.exists(f"{cfgdir}/hm_{L}.shipped.json"):
            os.rename(p, f"{cfgdir}/hm_{L}.shipped.json")
        json.dump(apply(json.load(open(f"{cfgdir}/hm_{L}.shipped.json")), L, best), open(p, "w"), indent=1)
    open(f"{cfgdir}/hm_ratio.txt", "w").write(best + "\n")
    print("best", best, "-> hm_1024/2048/4096.json (shipped ratios kept as hm_<L>.shipped.json)")


if __name__ == "__main__":
    main()
