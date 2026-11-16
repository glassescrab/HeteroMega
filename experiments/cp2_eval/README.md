# Checkpoint 2 evaluation (AMD Ryzen AI HX 370, Llama-3.1-8B AWQ W4A16)

Scripts and HeteroMosaic configs behind the Checkpoint 2 results. They ran on the AUP notebook from a checkout of
this branch's code at `/notebooks/hm-cp2b`; results went to `/notebooks/hm-results/cp2/<stage>/`. Paths in the
scripts are those of that notebook (`common.sh` sets `SRC`, `RES` and the job directory).

Every timed cell is 6 processes x 5 repetitions in one randomized stage; rep 0 is dropped, a process value is the
median of reps 1-4, and the cell is the median of the processes (`cellmed.py STAGE`, run inside `RES`).
`v5_report.py RES STAGE` and `kab1_report.py RES STAGE` print the effective config of every process (selected config
group, gate/up/down NPU tokens per micro-batch, micro-batches in flight seen in the log, UNCACHED fallbacks).

| Result | Stage (`bash eval3.sh STAGE`) | Configs |
|---|---|---|
| Row A, 1024 tokens, 2 x 512, 1 in flight; kernel ablation | `kab1-1024` | `hm_1024.shipped.json` (author's entry) |
| Row B, 2048 tokens, 4 x 512, 4 in flight | `m4-2048` | `hm_2048.shipped.json` (author's entry), `hm_2048.json` (512/512/0) |
| Row C, 2048 tokens, 2 x 1024, 2 in flight | `m2b-2048` | `hs.json` (author's entry), `hso_2048.json` (1024/1024/0) |
| Row D, 4096 tokens, 2 x 2048, 2 in flight | `m2b-4096` | `hs.json` (author's entry), `hso_4096.json` (2048/2048/0) |
| Ablation: split unit x micro-batches in flight | `abl1-1024` | `hm_1024.json` (512/512/0), `hp_g0u0d512.json` (0/0/512) |
| Correctness (last-token KL, greedy tokens) | `quality.sh` | |
| Config-ranking check (11-16): settings S1-S4 = rows A-D, FFN-split candidates before / after the NPU kernel change | `rk1-1024` `rk2-2048` `rk3-2048` `rk4-4096`; smoke `smoke_rk.sh`, run `chain_rk.sh` | `make_rk_configs.py` (from `hr.json` and the rows' configs) |
| Per-micro-batch search with our NPU binaries (HeteroMosaic runtime) | `apmb1-L` `apmb2-L` `apmbc-L`, L = 2048, 4096 | `hm_ratio.py` pm patterns, `hm_bins.py config` |

`chain_*.sh` are the detached job scripts that ran these stages in order with smoke gates; `phi.sh` builds and checks
NPU channel counts above 8192 for the p sweep. Configs are generated from the author's `configs_strixP_llama3_8b.json5`
by `make_hm_configs.py`, `hm_ratio.py` and `make_v5_configs.py`; attention runs on the GPU in all of them.

The config-ranking stages run each cell on its own tree (`src=`: `/notebooks/hm-cp2b` = the reported code, original NPU binaries, old PDI cache
key; `/notebooks/hm-npualign` = PDI cache key with npuM x npuN, our NPU binaries in `hw_bins_ours/`). `rk_check.py` gates every such process
(selected group, schedule, in flight, GEMMs loaded per micro-batch, NPU files under the cell's tree, PDI contexts) and writes its config
fingerprint; `rk_report.py RES STAGE` lists the fingerprints with the cell medians. `bash eval3.sh STAGE --dry` prints the effective config of
every cell without running it.
