#!/usr/bin/env python3
"""Configs of the config-ranking check (11-16 user, settings S1-S4 = the reported rows). Only gate/up/down of the setting's group change.
    make_rk_configs.py CFGDIR HM_BINS_PY [abln]   (abln: only the abl1n/kab1n files, see ABLN)
  rk<S>_<cand>_b.json  BEFORE: the author's full entry (hr.json = configs_strixP_llama3_8b.json5 as shipped; attention on the NPU as
                       shipped), gemv_driven_split_K false, chunking_scheduled as the reported cell
  rk<S>_<cand>_a.json  AFTER: the reported cell's FFN-only config with the candidate split, fw_path -> hw_bins_ours (hm_bins.py config)
  rk<S>_<cand>_m.json  the same before conversion (original binaries); MIDDLE / KEYONLY run the reported cell's config file itself
  <name>.want.json     what the cell intends (group, schedule, in flight, gate/up/down and q/k/v/o NPU rows per micro-batch, binary
                       dir), from the candidate table and the author's group in hr.json, not from the written config; rk_check.py
                       compares it with the config a process ran and with its log. rk<S>_auth_m.want.json serves MIDDLE and KEYONLY."""
import copy, json, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_hm_configs import schedule_of, select   # noqa: E402

FFN, ATT = ("gate", "up", "down"), ("q", "k", "v", "o")
# S: (L, author group index, chunking_scheduled, in flight the reported cell ran, reported config, candidates: name -> (gate, up, down) per micro-batch)
SETTINGS = {
    1: (1024, 0, False, 1, "hm_1024.shipped.json",
        {"auth": None, "g512u0d0": [(512, 0, 0)] * 2, "g256u0d0": [(256, 0, 0)] * 2, "g0u0d256": [(0, 0, 256)] * 2}),
    2: (2048, 2, True, 4, "hm_2048.shipped.json",
        {"auth": None, "g512u512d0": [(512, 512, 0)] * 4, "AAAB": [(512, 512, 0)] * 3 + [(0, 0, 512)], "g256u256d256": [(256, 256, 256)] * 4}),
    3: (2048, 3, False, 2, "hs.json",
        {"auth": None, "g1024u1024d0": [(1024, 1024, 0)] * 2, "g1024u512d0": [(1024, 512, 0)] * 2, "g1024u1024d256": [(1024, 1024, 256)] * 2}),
    4: (4096, 4, False, 2, "hs.json",
        {"auth": None, "g2048u2048d0": [(2048, 2048, 0)] * 2, "g1536u1536d0_g1792u1280d0": [(1536, 1536, 0), (1792, 1280, 0)],
         "g2048u2048d512": [(2048, 2048, 512)] * 2}),
}
BUILT = {"gate": {256, 512, 1024, 1280, 1536, 1792, 2048}, "up": {256, 512, 1024, 1280, 1536, 1792, 2048}, "down": {256, 512, 1536}}  # hw_bins_ours


def rows(group, layers):
    per = {}
    for k in group["kernels"]:
        if k["layer"] in layers:
            per.setdefault(k["chunk_id"], {})[k["layer"]] = k["npuM"] if k["use"] else 0
    return ["/".join(str(per[c].get(l, 0)) for l in layers) for c in sorted(per)]


def set_split(cfg, gi, split):
    seen = set()
    for k in cfg["kernels_gemm_chunked"][gi]["kernels"]:
        if k["layer"] in FFN:
            m = split[k["chunk_id"]][FFN.index(k["layer"])]
            k["npuM"], k["use"] = m, m > 0
            seen.add((k["chunk_id"], k["layer"]))
    assert seen == {(c, l) for c in range(len(split)) for l in FFN}, sorted(seen)


def main():
    d, hm_bins = Path(sys.argv[1]), sys.argv[2]
    hr = json.loads((d / "hr.json").read_text())
    for s, (L, gi, sched, infl, reported, cands) in SETTINGS.items():
        ag = hr["kernels_gemm_chunked"][gi]
        assert ag["prompt_len"] == L, (s, ag["prompt_len"])
        base_a = json.loads((d / reported).read_text())
        base_b = copy.deepcopy(hr)
        base_b.update(gemv_driven_split_K=False, chunking_scheduled=sched)
        for c, split in cands.items():
            ffn = rows(ag, FFN) if split is None else ["/".join(map(str, x)) for x in split]
            for x in ffn:
                for l, m in zip(FFN, map(int, x.split("/"))):
                    assert m == 0 or m in BUILT[l], (s, c, l, m)   # AFTER needs our binary of that M
            for env, base in (("b", base_b), ("m", base_a)):
                cfg = copy.deepcopy(base)
                if split is not None:
                    set_split(cfg, gi, split)
                assert select(cfg, L)[0] == gi, (s, c, env, select(cfg, L)[0])   # the runtime picks the intended group
                (d / f"rk{s}_{c}_{env}.json").write_text(json.dumps(cfg, indent=1))
            subprocess.run([sys.executable, hm_bins, "config", str(d / f"rk{s}_{c}_m.json"), str(d / f"rk{s}_{c}_a.json")], check=True,
                           stdout=subprocess.DEVNULL)
            off = ["0/0/0/0"] * len(ffn)
            for env, att, bins in (("b", rows(ag, ATT), "hw_bins"), ("a", off, "hw_bins_ours"), ("m", off, "hw_bins")):
                want = {"setting": f"S{s}", "prompt_len": L, "group": gi, "schedule": schedule_of(ag), "inflight": infl,
                        "gate/up/down": ffn, "q/k/v/o": att, "bins": bins}
                (d / f"rk{s}_{c}_{env}.want.json").write_text(json.dumps(want) + "\n")
            print(f"S{s} {c:26s} group #{gi} schedule={schedule_of(ag)} in flight {infl}: gate/up/down {', '.join(ffn)}; "
                  f"BEFORE q/k/v/o {', '.join(rows(ag, ATT))}")

# 11-17 abl1n-1024 / kab1n-1024: the abl1-1024 / kab1-1024 HeteroMosaic configs unchanged but fw_path -> hw_bins_ours (<name>.ours.json),
# want abln_<name>_i<k>.want.json per in-flight count k (intent: the author's 1024 group, split below, attention on the GPU, our binaries)
ABLN = {"hm_1024.shipped": ([(256, 256, 0)] * 2, (1,)), "hm_1024": ([(512, 512, 0)] * 2, (1, 2)), "hp_g0u0d512": ([(0, 0, 512)] * 2, (1, 2))}


def abln(d, hm_bins):
    ag = json.loads((d / "hr.json").read_text())["kernels_gemm_chunked"][0]
    for name, (split, infls) in ABLN.items():
        subprocess.run([sys.executable, hm_bins, "config", str(d / f"{name}.json"), str(d / f"{name}.ours.json")], check=True, stdout=subprocess.DEVNULL)
        ffn = ["/".join(map(str, x)) for x in split]
        for i in infls:
            want = {"setting": f"abln_{name}", "prompt_len": 1024, "group": 0, "schedule": schedule_of(ag), "inflight": i,
                    "gate/up/down": ffn, "q/k/v/o": ["0/0/0/0"] * len(ffn), "bins": "hw_bins_ours"}
            (d / f"abln_{name}_i{i}.want.json").write_text(json.dumps(want) + "\n")
            print(f"abln_{name}_i{i}: {name}.ours.json", json.dumps(want))


if __name__ == "__main__":
    abln(Path(sys.argv[1]), sys.argv[2]) if sys.argv[3:] == ["abln"] else main()
