"""HeteroMosaic configs for the CP2 evaluation, from the shipped configs_strixP_llama3_8b.json5. Usage: make_hm_configs.py SHIPPED OUTDIR
All FFN-only (q/k/v/o use=false, gate/up/down as shipped, gemv_driven_split_K=false: jobs/make_ffn_configs.py variant B):
  hm_1024  shipped fixed 512 group; hm_2048  chunking_scheduled, shipped [512]x4 group;
  hm_4096  chunking_scheduled, new [512]x8 group (chunks 4-7 = chunks 0-3) inserted before the shipped [2048,2048] group;
  hs       shipped chunking and tables (used at its shipped inflight); hr = shipped as is (attention split with the NPU).
Prints, per config and length, the group the C++ selection picks (npuSetup.cpp select_chunked_kernel_group, desired chunk -1)
and the NPU share of FFN FLOPs; exits non-zero if an hm_* config does not select a 512-row table."""
import copy, json, sys

SCHEDULE_KEYS = ("hetero_chunk_size_schedule", "hetero_chunk_schedule", "gpu_chunk_size_schedule", "gpu_chunk_schedule",
                 "gpu_chunk_shedule", "chunk_schedule")


def ffn_only(cfg):
    cfg = copy.deepcopy(cfg)
    cfg["gemv_driven_split_K"] = False
    for group in cfg["kernels_gemm_chunked"]:
        for k in group["kernels"]:
            if k["layer"] in ("q", "k", "v", "o"):
                k["use"] = False
    return cfg


def schedule_of(group):
    for key in SCHEDULE_KEYS:
        if key in group:
            return list(group[key])
    return [group["hetero_chunk_size"]]


def select(cfg, length):
    """First group of this prompt_len whose mode (has schedule key) matches chunking_scheduled, else first of the other mode."""
    scheduled = cfg.get("chunking_scheduled", True)
    same = [(i, g) for i, g in enumerate(cfg["kernels_gemm_chunked"]) if g["prompt_len"] == length]
    match = [x for x in same if any(k in x[1] for k in SCHEDULE_KEYS) == scheduled]
    return (match or same)[0]


def ffn_share(group):
    num = den = 0
    for k in group["kernels"]:
        if k["layer"] in ("gate", "up", "down"):
            flops = k["forM"] * k["forK"] * k["forN"]
            den += flops
            num += (k["npuM"] if k["use"] else 0) * k["forK"] * k["forN"]
    return num / den


def add_4096(cfg):
    groups = cfg["kernels_gemm_chunked"]
    src = next(g for g in groups if g["prompt_len"] == 2048 and schedule_of(g) == [512] * 4 and "hetero_chunk_size_schedule" in g)
    new = copy.deepcopy(src)
    new["prompt_len"], new["hetero_chunk_size_schedule"], new["hetero_inflight"] = 4096, [512] * 8, 2
    base = [k for k in src["kernels"]]
    new["kernels"] = copy.deepcopy(base) + [dict(copy.deepcopy(k), chunk_id=k["chunk_id"] + 4) for k in base]
    at = next(i for i, g in enumerate(groups) if g["prompt_len"] == 4096 and "hetero_chunk_size_schedule" in g)
    groups.insert(at, new)
    cfg["chunking_scheduled"] = True


def main():
    src, out = sys.argv[1:3]
    import json5
    shipped = json5.load(open(src))
    cfgs = {"hm_1024": (ffn_only(shipped), 1024), "hm_2048": (ffn_only(shipped), 2048), "hm_4096": (ffn_only(shipped), 4096),
            "hs": (ffn_only(shipped), None), "hr": (shipped, 1024)}
    cfgs["hm_2048"][0]["chunking_scheduled"] = True
    add_4096(cfgs["hm_4096"][0])
    bad = False
    for name, (cfg, only) in cfgs.items():
        json.dump(cfg, open(f"{out}/{name}.json", "w"), indent=1)
        for length in ([only] if only else [1024, 2048, 4096]):
            i, g = select(cfg, length)
            sch = schedule_of(g)
            ids = sorted({k["chunk_id"] for k in g["kernels"]})
            ok = not name.startswith("hm_") or (set(sch) == {512} and ids == list(range(length // 512)))
            bad |= not ok
            print(f"{name} L={length}: group#{i} schedule={sch} inflight={g['hetero_inflight']} chunk_ids={len(ids)} "
                  f"FFN NPU share={ffn_share(g):.4f}{'' if ok else '  WRONG GROUP'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
