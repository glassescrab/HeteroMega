#!/usr/bin/env python3
"""v5 rows C/D (11-15): hso_<L>.json = hs.json (the author's full config) with, in the 2-in-flight fixed-chunk group of prompt_len L
(2048: chunk 1024, 4096: chunk 2048), gate/up npuM = the whole micro-batch (use=true) and down off (npuM 0, use=false) on every chunk.
Nothing else changes.   make_v5_configs.py CFGDIR"""
import copy, json, sys
from pathlib import Path
d = Path(sys.argv[1]); base = json.loads((d / "hs.json").read_text())
for L, cs in ((2048, 1024), (4096, 2048)):
    cfg = copy.deepcopy(base); hit = 0
    for g in cfg["kernels_gemm_chunked"]:
        if g["prompt_len"] == L and g.get("hetero_chunk_size") == cs and "hetero_chunk_size_schedule" not in g and g.get("hetero_inflight") == 2:
            hit += 1
            for k in g["kernels"]:
                if k["layer"] in ("gate", "up"): k["npuM"], k["use"] = cs, True
                elif k["layer"] == "down": k["npuM"], k["use"] = 0, False
            print(L, cs, sorted((k["chunk_id"], k["layer"], k["npuM"], k["use"]) for k in g["kernels"] if k["layer"] in ("gate", "up", "down")))
    assert hit == 1, (L, hit)
    (d / f"hso_{L}.json").write_text(json.dumps(cfg, indent=1))
