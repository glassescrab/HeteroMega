# HeteroMega agent continuation guide

## Latest optimization — 2026-10-25: reuse and DMA activation layouts

The user requested **"do all other optimizations first"** before combined
GPU+NPU integration. This pass evaluated vector zero metadata, down M reuse,
MMUL accumulator blocking, row-major input DMA, direct down-A output DMA and
borrowed readback. Native BF16, eight columns/32 workers and original packed
glassescrab weight buffers are retained. No weight repacking is introduced.

Selected profile: `combo_mmul1_row_major` in
`experiments/ffn_partition/benchmark_upstream_optimizations.py`. SwiGLU uses
reuse2/Adepth2/row-major input/down-A output; down uses reuse4/Adepth1/compact
input/output. Both enable vector zero metadata, retain MMUL M blocking1,
2 KiB stacks and segment depth2. Host readback is borrowed; final output is
independent. **The activation ABI changed**: Z already has down-A layout,
so do not apply the previous CPU permutation. BO I/O still occurs.

**Measured HX370/default power:** versus the preceding two-segment control,
median NPU-branch latency is 24.576→22.590 ms (ABBA, 8.08% lower) and
24.194→22.490 ms (BAAB, 7.04% lower), 100 timed samples/profile/order.
All outputs match exactly. The combination beats the simpler DMA-only
configuration by 2.4–2.7% in both orders. This remains an isolated NPU-branch
result, not combined GPU+NPU/full-model acceleration or model accuracy.

The experimental eight-accumulator MMUL overflowed its original 2 KiB stack
on full shapes. A conditional 4 KiB stack fixes correctness, but heavy
register spills make it about 2.2× slower. It is not selected. Keep the failed
report separate from successful evidence. Passing reports complete 2,672
dispatches; the retained failed report has eight further completions.
Local tests: 201 passed, one skipped. Runtime sources/artifacts and exact
output equivalence were independently audited.

Read `docs/runs/2026-10-25-kernel-optimizations/README.md` and
`npu/ffn/UPSTREAM_BF16.md`. Research branch:
`codex/native-bf16-reuse-optimizations`; isolated cloud overlay:
`/notebooks/HeteroMega-kernel-opt-bf16-20261025`. Earlier overlays/controls
remain intact. Kernel-only PR #3 is managed in `../HeteroMega-kernels`;
do not push research harnesses or evidence into it. Device-phase tracing,
dequant/MMUL overlap, larger N reuse and SwiGLU buffer redesign remain open;
this pass does not exhaust those research changes. Integration stays deferred
until this optimization checkpoint is delivered.

Published kernel package: `fc0b25585d5835e976302ac14910817f53a34cac` in
[PR #3](https://github.com/glassescrab/HeteroMega/pull/3), 22 files under
`npu/ffn` including the new DMA-output helper. All 21 payload checksums pass.
Generated MLIR is retained byte-for-byte, including compiler whitespace.
The PR description documents the new activation ABI and measured limits;
the PR remains open and unmerged.

## Latest optimization — 2026-10-25: two-segment native BF16 pipeline

The user authorized implementing the proposed segment pipeline. The selected
graph now defaults to `--segment-pipeline-depth 2`; explicit depth 1 preserves
the serial schedule. Both keep native BF16, original upstream weight buffers,
identical compute/FIFO definitions and transfer addresses. At most two
segments are outstanding, with the oldest retired before submitting a third.
This pipelines DMA scheduling, not dequantization and MMUL within a worker.

**Measured on HX370/default power:** NPU-branch median including host layouts
and BO I/O improved 24.796→24.024 ms (ABBA, 50 samples/schedule) and
25.126→24.512 ms (BAAB, 100 samples/schedule): 3.1% and 2.4% reductions.
Outputs are bit-identical to the serial control. Seven correctness cases and
both timing experiments completed 736 NPU dispatches. This is a modest
isolated NPU-branch gain with overlapping timing distributions, not a
GPU+NPU/full-model speedup or model-accuracy result.

Read `docs/runs/2026-10-25-pipeline-bf16/README.md` for raw evidence and
reproduction. The new timing entry point is
`python -m experiments.ffn_partition.benchmark_upstream_pipeline`.
Remote overlay: `/notebooks/HeteroMega-pipeline-bf16-20261025`; earlier
overlays and serial package are preserved. The kernel-only PR remains in
`../HeteroMega-kernels`; keep reports/harnesses in the local research branch.
Published as `d628e482e00ae0dd044db0da513b4448f6c84f24` in
[PR #3](https://github.com/glassescrab/HeteroMega/pull/3). Full experiment
checkpoint: local branch `codex/native-bf16-segment-pipeline`.

## Latest direction — 2026-10-25: native BF16, original upstream weights

The user requested **"we dont want repacking and go back to BF16"** and
clarified **"Accept glassescrab weight buffers directly"**. This supersedes
the BFP16 selection for the final package. Activation layout conversion was
explicitly outside that clarification; do not conflate it with weight packing.

The new `npu/ffn/w4a16_upstream.py` graph uses native BF16 4×8×8 MMUL,
FP32 K-group partials, and all eight columns / 32 workers. It consumes original
striped K128/N64/4352-byte weight payloads, selecting slices with the **full
source dimensions**. Gate/up have separate original weight BOs. N32 halves
owned by one worker share an A/W acquisition and 8 KiB scratch. BF16 is fixed
in this graph; BFP16 emulation is explicitly zero. Existing compact/BFP16
graphs and measurements remain controls, not the newly selected interface.

Read `npu/ffn/UPSTREAM_BF16.md` and
`docs/runs/2026-10-25-upstream-bf16/README.md`. The new host adapter is
`experiments/ffn_partition/upstream_npu.py`; correctness entry point is
`python -m experiments.ffn_partition.check_upstream`. This adapter uploads
existing packed bytes once without converting/concatenating them. BO upload
copies and the Z-to-down activation permutation still occur.

**Measured correctness on HX370:** seven cases, 28 input runs, 40 completed
NPU dispatches; all strict numerical, finite, zero, repeat, changed-input and
unchanged-weight checks pass. Worst relative L2 is 0.00400048. This includes
M512/H4096/I14336/P2560 and a nonzero-offset P1152 partition. Native BF16
package binaries and generated MLIR match the selected report/source hashes.
No new GPU+NPU latency, whole-model speedup or model-accuracy claim is made.
Per-segment barriers differ, so old timing results do not transfer.

The remote overlay is `/notebooks/HeteroMega-upstream-bf16-20261025`.
Earlier remote checkouts and baselines were preserved. Published in
[PR #3](https://github.com/glassescrab/HeteroMega/pull/3) as
`4749d927d50bf1c5cd03f4310f72fd9669f23640`; the final package still contains
only 21 files under `npu/ffn`. Continue the kernel-only PR in
`../HeteroMega-kernels`. Full implementation, tests and evidence are saved
locally on `codex/native-bf16-upstream-weights`; do not push full research
history, test harnesses or evidence archives into that PR. Branch and package
statements in the dated entries below describe earlier checkpoints.

## Previous package checkpoint — final kernels only in PR #3

The user asked to reduce the PR to final MLIR code and needed XCLBINs.
PR #3 now has one commit, `8622dbee423ba8e13ee3e1f166799f6201d0bc28`,
adding only 21 files under `npu/ffn`: unchanged build sources, two generated
MLIR graphs, tested SwiGLU/down binaries and matching instructions for
M512/H4096/P2560, manifests, checksums, licenses and a short ABI/build README.
The clean package worktree is `../HeteroMega-kernels`, branch
`codex/npu-ffn-final-package`, tracking the PR branch
`origin/codex/npu-bfp16-prefill-optimizations`.

This original workspace now uses local backup branch
`codex/ffn-full-experiment-backup-20261022` and preserves the full experiment
history. Do not push this backup into PR #3 or reintroduce its reports,
benchmarks, plots and handoff files. Existing artifact hashes match and all
48 NPU CPU tests pass against the packaged modules; packaging did not rerun
hardware. Historical broader PR descriptions below are superseded.

## Current authorization — 2026-10-22: optimization and PR

The user explicitly requested **"make some optimizations and make a PR"**.
This supersedes the PR pause in the historical entries below. The current
branch is `codex/npu-bfp16-prefill-optimizations`. Preserve the prior native
comparison preparation and teammate GPU/evaluation changes from main.
The branch is pushed and [PR #3](https://github.com/glassescrab/HeteroMega/pull/3)
is open. Continue review or new experiments there; do not create a duplicate PR.

The bounded optimizations are exact BF16 bit construction for W4 zero-point
metadata, removing software integer-to-float conversions, and borrowed
read-only BO readback views inside the non-reentrant NPU branch. XRT read/sync
and layout staging remain. `--owned-npu-readback` reproduces the extra NumPy
ownership copy. Native BF16 arithmetic remains the default control.

Hardware verification runs in `/notebooks/HeteroMega-opt-20261022`, with the
old kernel and owned-copy control in `/notebooks/HeteroMega-opt-control-20261022`.
The original BFP16 overlay is preserved. Use source hashes rather than the
copied remote Git HEAD to identify what ran. The notebook currently reports
NPU power mode `default`, not `performance`.

Read [OPTIMIZATION_RESULTS.md](experiments/ffn_partition/OPTIMIZATION_RESULTS.md)
for the final measured configurations and reproduction. P2560 with explicit
`--borrow-npu-readback` confirms at 18.337/18.393 ms versus old-best 18.845 ms;
owned P2560 is 18.800 ms. Borrowing is partition-dependent and remains opt-in.
The old/new kernel outputs are bit-identical in the separate hardware check.
All 13 reports pass original bounds. Latest main's GPU/evaluation work is
merged. These remain isolated FFN results; no full-model acceleration is
established. The historical uncommitted/PR-paused statements below no longer
describe the current authorization or branch.

Historical BFP16 analysis must use its archived source: extract
`initial-runtime.tar.gz` then `final-harness.tar.gz`, and pass `--source-root`
to the analysis scripts. They deliberately reject the changed current kernel.

## Latest analysis — 2026-10-22: NPU bottleneck trace

Read [NPU_IMPLEMENTATION_TRACE.md](experiments/ffn_partition/NPU_IMPLEMENTATION_TRACE.md)
before further tuning. Existing P1792 diagnostics attribute 74.3% of the
outer NPU call to the two execution waits, 13.3% to CPU layouts and 8.7% to
BO I/O/wrapper residual; submission is 1.3%. The staged NPU result is usually
the last GPU-visible dependency. Source analysis finds 14×/16× activation
replay, four sequential M waves and 86,016 dequantize/MAC calls per FFN.
These logical counts do not establish memory bandwidth saturation. The next
device trace must separate dequant, MMUL, FIFO/lock and DMA costs; current
event markers combine dequant and MAC. Improve reuse/buffering before simply
raising the NPU share. No kernels or recorded benchmark results changed in
this analysis, and PR creation remains paused.

The compiled gate/up/down ELFs additionally reveal 32 `__floatunsisf` software
conversion calls per dequantization (2.75 million per FFN by the schedule).
Inspect the saved compiler audit and try exact BF16 zero-metadata bit
construction as the first bounded ablation. The conversion's actual time
share is not yet measured; retain the old path as a control.

## Latest update — 2026-10-22: TileFuse BFP16 adaptation

The latest user request is to inspect all current branches of
`glassescrab/mlir-aie`, adapt the optimized W4A16 kernels to the FFN, and
accept the larger BFP16 arithmetic differences for this performance study.
This takes priority over historical strict-tolerance blocking below. Prefill
remains the scope; the upstream GEMV was inspected but decode is deferred.

Read [BFP16_ADAPTATION.md](npu/ffn/BFP16_ADAPTATION.md) for all seven pinned
branch heads, the selected corrected TileFuse source at `121dd54abc68f84d89a7074372ebf82be2db62d5`,
ABI/stack/cache contracts, commands, and measurement evidence. The new
`--npu-arithmetic bfp16` selector preserves the existing eight-column fusion
schedule and uses 8×8×8 BFP16-backed matrix operations. Native BF16 is still
the default. BFP16 defaults to reporting numerical deviations; original
thresholds and their pass/fail status remain recorded. Nonfinite, zero,
stale-output, repeatability and NPU-completion failures still stop the run.

Browser access was restored in this session. The prepared AUP environment
is usable again. Experiments run in an **isolated overlay** at
`/notebooks/HeteroMega-bfp16-20261022`; the earlier remote checkout and
baselines were preserved. The overlay retains the remote base Git history,
not the local checkpoint history; use recorded source hashes to identify its
actual code. Runtime PATH must include `/notebooks/heteromega-ffn-venv/bin`
for Ninja; invoke experiment entry points using `python -m`.

A fresh power switch attempt was denied with error 13; power is still
`default`. Never label these runs `performance`. The small fused BFP16
FFN and model-shaped runs now execute on hardware; current results and
limitations are recorded in the adaptation document and `docs/progress.md`.
The confirmed BFP16 candidate is P1792 (12.5%): 18.754 ms versus 22.349 ms
GPU-only, and 5.4% lower than fresh BF16 P1152. All 147 CPU tests and all
ten hardware reports pass the original bounds. Raw reports, build contracts,
source snapshots and graphs are in
[the BFP16 results](experiments/ffn_partition/BFP16_RESULTS.md).
The native baseline checkout/library were absent at their previously recorded
paths in this restarted notebook.

The native HeteroMosaic heterogeneous comparison remains a separate task:
the current FFN control uses its original **GPU-only** W4A16 kernels.

All new work is uncommitted. Preserve earlier uncommitted comparison files.
PR creation remains paused; this request does not authorize publishing.
The handoff below records the preceding state and is historical wherever it
conflicts with this update, especially its browser blocker and accuracy gate.

## Resume here — 2026-10-22

This handoff summarizes the user's latest requests and the verified state at
the end of the session. The original user-provided research plan is preserved
below. Its October 12 status statements are historical; use this handoff and
`docs/progress.md` for current implementation/measurement status.

### Active task and authorization

The latest implementation request is: **"Use w4a16 kernels compare with
HeteroMoasic, do the profilings."** Resume actual correctness and profiling
against native HeteroMosaic's GPU–NPU FFN, rather than stopping at a source
comparison or rerunning only its GPU kernels.

- Scope is **prefill FFN only**, initially M512/H4096/I14336, W4A16 group128.
  Keep attention unchanged; decode and attention partitioning are deferred.
- The user requested an eight-column NPU design, fused gate/up, further
  pointwise fusion, partition sweeps, and complete FFN latency. Those earlier
  implementations and measurements are already checkpointed; reuse them.
- Implementation, cloud experiments, necessary adapter fixes, and profiling
  are authorized. Preserve baselines and teammate changes. Do not change the
  shared host kernel/driver or publish credentials/model weights.
- **PR creation remains paused** by the user's explicit request. The latest
  checkpoint was local; do not assume permission to publish the new harness.
  This handoff request itself does not request a commit or push.
- Earlier slide requests are secondary to the outstanding profiling. Do not
  update slides with results that have not been measured.

### Git state to preserve

Snapshot: branch `codex/ffn-partition-microbench`, HEAD
`740c45516d4e5e4ea5f95032f254522af09a92c5`
(`Checkpoint fused NPU FFN kernels and partition measurements`). Recheck Git
status and HEAD before editing; this is not a guarantee about a future checkout.

**The native comparison is uncommitted local work**, added after that checkpoint:

| File under `experiments/ffn_partition/` | Purpose |
| --- | --- |
| `native_heteromosaic.py` | Native W4A16 baseline, canonical inputs/weights, references, correctness and profiling |
| `native_heteromosaic_bindings.cpp` | Thin binding to an existing native HeteroMosaic shared library |
| `compare_native.py` | Fresh native versus P1024/P1152 experiments, GPU controls, power queries and evidence validation |
| `test_native_heteromosaic.py` | Six CPU contract/preparation checks |
| `test_compare_native.py` | Four CPU orchestration/evidence checks |
| `NATIVE_COMPARISON.md` | Full run instructions and measurement limitations |

`docs/progress.md` also has an uncommitted October 21 entry. This handoff adds
documentation changes to `agent.md`, `AGENTS.md`, and `docs/progress.md`.
Do not discard untracked files, reset the checkout, or overwrite the notebook
checkout wholesale. The remote Git history was not synchronized to the local
checkpoint; inspect local and remote state independently before transferring.

### What has actually been verified

**Measured earlier on HX370/Radeon 890M, NPU power mode `default`:** our
two-launch on-chip SwiGLU FFN at P1152 took **19.643 ms**, versus its matched
**22.293 ms GPU-only control** (1.1349x, 11.9% lower latency) in the confirmation
run. P1024 was nearly tied; retain both candidates. These are synthetic isolated
FFN measurements, not full-model prefill, TTFT, or Ryzen AI Max+395 results.
Evidence: [SWIGLU_RESULTS.md](experiments/ffn_partition/SWIGLU_RESULTS.md).

**Critical baseline distinction:** the 22.293 ms control uses original
HeteroMosaic GPU kernels, with all FFN channels on GPU. It is **not** native
HeteroMosaic GPU–NPU execution. Our four-, three-, and two-launch NPU variants
are all HeteroMega implementations; none is a native HeteroMosaic baseline.

**Code-confirmed architecture:**

| Path | Gate/up | SiLU × up | Down / final output |
| --- | --- | --- | --- |
| Recorded native M512 HeteroMosaic | 256 GPU + 256 NPU token rows, full intermediate width | GPU, full shared tensors | GPU down; disjoint row outputs need no concatenate or partial sum |
| HeteroMega SwiGLU | Matching intermediate-channel partitions, all token rows on each device | Local to each branch; fused on-chip on NPU | Matching down K-slices on GPU/NPU; **GPU adds the partial outputs** |

Native HeteroMosaic uses imported shared GPU allocations and direct XDNA.
Our prototype uses XRT and host staging. Its gate/up→pointwise intermediates
stay on-chip, but **Z is still read back, permuted on CPU, and uploaded to the
separate down graph**. Shared physical memory does not imply shared BOs or
on-chip residency. Larger native HeteroMosaic configurations also offload down;
the GPU-only-down statement is specific to the recorded M512 configuration.

**Locally verified for the new comparison:** 21 CPU tests pass; Python
compilation, config preparation, and a nine-job dry plan pass. **The new C++
binding has not been compiled or linked on ROCm, and no new native comparison
has run on hardware.** Do not promote prepared status to measured status.

### Last blocker and environment

The last browser checks returned `{"apps":[],"browsers":[]}` and
`No browser is available`. Asking the app to open AUP returned `queued`.
This establishes only that **no browser was exposed to that session**; the
underlying cause and notebook availability were not established. Recheck the
available browser tools/surfaces in the next session before declaring a blocker.
The user was asked to open the notebook in the desktop browser and use
`@Browser`. No reconnection was verified before this handoff.

The local workspace is `/home/adam/Documents/ChatGPT/HeteroMega` on Linux,
with an Intel CPU/NVIDIA RTX4090 and no AMD NPU or ROCm. It can run CPU checks,
not substitute for the requested AMD hardware measurements.

Previously prepared cloud locations, **to verify after reconnecting**:

| Resource | Location |
| --- | --- |
| AUP notebook | `https://dub.aupcloud.io/aipc-16` |
| HeteroMega checkout | `/notebooks/HeteroMega` |
| Native HeteroMosaic checkout | `/notebooks/HeteroMosaic-baseline` |
| FFN runtime Python | `/notebooks/heteromega-ffn-venv/bin/python` |
| Native baseline Python | `/notebooks/heteromosaic-venv/bin/python` |
| MLIR-AIE compiler Python | `/home/mliraie/mlir-aie/ironenv/bin/python` |
| ROCm | `/opt/rocm-7.2.0`, native `gfx1150` |
| Pinned XDNA headers | `/notebooks/heteromosaic-libraries/xdna-driver-05-19-25/src/include/uapi/drm_local` |
| Original model library directory | `/notebooks/HeteroMosaic-baseline/build/py/unified_llm_w4a16/` |

The user's notebook credential is intentionally not copied into repository
documentation. Use the authorized session/login flow. Keep the prepared
environments and compiled artifacts; read the cloud runbooks before setup.

### Next steps, in order

1. Read `AGENTS.md`, this handoff, `docs/progress.md`, and
   [NATIVE_COMPARISON.md](experiments/ffn_partition/NATIVE_COMPARISON.md).
   Inspect Git status. For hardware work also read `docs/cloud-baseline.md`,
   `docs/runtime-compatibility.md`, and `docs/profiling-2026-10-14.md`.
2. Reconnect/discover the browser and open AUP. Inspect remote files, running
   jobs, available GPU/NPU, software versions, and NPU power before launching.
   Previous attempts to switch `default`→`performance` were authorized but
   denied even as root; **performance mode was never established**. Do not
   change the host driver or mislabel another default-mode run.
3. Transfer the uncommitted comparison files to the HeteroMega notebook
   checkout while preserving its changes. Locate the actual native model
   `.so`, pinned headers, and original M256 gate/up artifacts. Set
   `HETEROMOSAIC_NATIVE_LIBRARY` to the real library path. Check ABI/exports,
   source/build provenance, and hashes; the adapter links that library rather
   than compiling a replacement native runtime. Fix adapter build issues if
   found, keeping kernel math and baseline partitioning unchanged.
4. Run the bounded native correctness check first (M512/H4096/I14336,
   NPU rows 256; a few iterations suffice initially). The adapter checks 84
   combinations of gate/up/output, row ownership, random/zero/repeated inputs,
   and GPU comparisons. It rejects fallback and failed futures, and requires
   two successful NPU completions per native FFN call.
5. **If native random-W4A16 checks fail, save and diagnose the failure.** This
   problem was already present in the original runtime port. Matching packed
   bytes, successful launches, or matching a few generated tokens does not
   establish numerical correctness. Keep `rtol=0.03`, `atol=0.05`, and the
   relative-L2 limit 0.02; do not widen them to produce a speedup claim.
6. After the numerical gate passes, run the exact commands in
   `NATIVE_COMPARISON.md`: native M-split, fused P1024/P1152, each with GPU
   controls, 30 ordinary samples and separate 10-sample diagnostics after
   three warmups. Two reversed-order ordinary blocks plus diagnostics make
   nine jobs. Use a fresh output directory; the driver currently has no
   resume flag and stops on the first failure. `--plan-only` also creates a
   manifest, so use a different directory for the subsequent hardware run.
7. Validate raw reports, counters, unchanged inputs/weights, source/binary
   hashes and before/after power snapshots. Preserve logs/failed attempts.
   Download results to the local repository. Produce a latency comparison
   graph with variability and separate stage/device profiling figures;
   plot generation for this new comparison is still outstanding.
8. Report measured results and actual bottlenecks, including negative results.
   Update `docs/progress.md` and this handoff. Full-model prefill integration
   with unchanged attention/chunk scheduling follows the isolated comparison;
   it has not been done. Keep PR creation paused.

### Timing and correctness pitfalls

- Ordinary complete FFN latency uses ready GPU input→completed GPU output,
  including orchestration, staging, waits, layouts and final reduction where
  present. Setup/packing/uploads and validation readback stay outside timing.
- The native adapter records outer Python-call `wall_us` plus inner
  `binding_wall_us`. Its separate diagnostics synchronize gate/up, pointwise,
  and down. HeteroMega's diagnostic uses GPU HIP events and host probes without
  those added stage barriers. Do not treat those stage columns as identical
  timing semantics or substitute diagnostic totals for ordinary latency.
- **NPU wait is not pure data movement:** it includes runtime, DMA, compute,
  stalls and completion. Host/GPU clock origins are not calibrated; overlapping
  intervals and independent stage medians cannot be added into an exact total.
- The earlier full-model native profiles are provisional because original NPU
  numerical validation remains open. Their real weights and synchronized
  measurement context differ from the new isolated synthetic benchmark.
- Native packing uses the existing independently tested byte packer. Native
  C++ weight setters assume transposed metadata relative to canonical
  `[N,K/128]`; do not replace direct packed-byte input casually.
- The native runtime owns process-global configs, imports and contexts. Use a
  fresh process per job and keep imported tensors alive. A library hash does
  not prove source-to-binary correspondence; retain build evidence.
- Do not assume the teammate GPU PR kernels are integrated: these controlled
  experiments still use the original HeteroMosaic GPU kernels.

### Local checks already run

From the repository root, the following test invocation passed 21 tests. It preserves any
existing `PYTHONPATH` while supporting the older packing tests' direct imports:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH="$PWD/experiments/ffn_partition:$PWD${PYTHONPATH:+:$PYTHONPATH}" \
python -m unittest \
  experiments.ffn_partition.test_compare_native \
  experiments.ffn_partition.test_native_heteromosaic \
  experiments.ffn_partition.test_gpu_packing \
  experiments.ffn_partition.test_sweep_partition -v
```

`native_heteromosaic --prepare-only` writes `prepared_not_executed` status;
`compare_native --plan-only` writes planned jobs. Neither is hardware evidence.
See the runbook for exact CLI commands. For concise background, also read
`docs/checkpoint-2026-10-18-ffn-fusion.md` and `npu/ffn/SWIGLU.md`.

---

# Historical HeteroMega agent reference plan

Saved 2026-10-12 at the user's request. The user-provided plan below is preserved
verbatim. It is the current planning reference for the narrowed FFN-prefill
study; attention-head partitioning and decode optimization are deferred.
A later explicit user instruction or final proposal can revise this scope.

Read `AGENTS.md` for repository working rules, `docs/project-plan.md` for the
baseline code/build map, and `docs/progress.md` for actual progress. The plan's
future work instructions do not mean those steps have been executed or that
saving this file authorizes implementation in the current documentation task.

## Review recommendations (assistant suggestions, not user requirements)

These refinements were proposed during review; retain them for consideration
without treating them as independently approved scope changes:

1. Time-box an early NPU SiLU/gating and buffer-layout feasibility check.
   Distinguish a full NPU-local branch from one using GPU elementwise fallback.
2. Where meaningful, isolate persistence with identical channel splits, kernels,
   weights, and chunk schedules; separately compare against optimized original
   HeteroMosaic. Document unavoidable differences between the controlled paths.
3. Treat persistent token-row partitioning as an important challenger: it avoids
   the partial-output sum required by channel partitioning. Do not turn it into
   a second large implementation project without evidence that this is needed.
4. Validate correctness at every step: reference algebra, packed slices, device
   execution, concurrency, then model integration. Preserve quantization metadata
   and test repeated buffer reuse with alternating inputs.
5. Define FFN timing boundaries independently of the existing G2 stage. Separate
   host readiness/queue/submit/wait intervals from actual device execution;
   reproduce scheduler release times in representative overlap experiments.
6. Keep allocation selection as a stretch goal unless measured winners change
   across workloads by more than measurement variability.

Suggested first milestone: one representative FFN shape, one valid unequal
split, a correctness reference, an NPU capability/layout assessment, and
measurements of the unchanged baseline when target hardware is available.
No runtime feasibility, correctness, or speedup is established yet.

## User-provided plan

You are helping develop **HeteroMega**, a semester research project built on HeteroMosaic.

Repository: https://github.com/glassescrab/HeteroMega  
Upstream: https://github.com/UIUC-ChenLab/heteroMosaic

Work in the existing checkout. Read repository instructions and inspect its current state before making changes. Preserve existing work and use the repository’s established build and development practices.

## 1. Research objective

Investigate whether **preserving tensor partitions across an entire feed-forward network (FFN) sublayer** improves heterogeneous GPU–NPU LLM prefill.

HeteroMosaic already supports heterogeneous operation allocation, GEMM partitioning, and causal micro-batching that overlaps work from different prompt chunks. Our extension must account for that existing scheduling behavior.

The central research question is:

> When do persistent FFN partitions reduce execution costs enough to improve end-to-end prefill, and when does GPU participation in the FFN interfere with concurrently executing attention?

Do not assume the proposed implementation will be faster. Establish the baseline behavior and bottleneck through code inspection and measurements.

Initial scope:
- Dense, gated FFNs supported by the existing runtime.
- Prefill as the primary target.
- One supported model and one available AMD platform initially.
- Attention remains on its existing execution path.

Defer attention-head partitioning, speculative decoding, and broader model support until the FFN study is working.

## 2. Proposed FFN computation

For a gated FFN:

U = X W_up  
V = X W_gate  
Z = SiLU(V) ⊙ U  
Y = Z W_down

Partition the intermediate feature dimension into GPU and NPU portions.

For each device i:

Z_i = SiLU(X W_gate,i) ⊙ (X W_up,i)  
Y_i = Z_i W_down,i

Combine at the FFN boundary:

Y = Y_GPU + Y_NPU

The up and gate projections use matching output-feature partitions, corresponding to N-splits. The down projection consumes those partitions along its reduction dimension, corresponding to a K-split.

The intended property is that intermediate channels retain their ownership and compatible layout between these operations. This does not require intermediates to remain in on-chip memory.

Handle model-specific biases, residual connections, activation functions, and quantization metadata correctly. Apply any down-projection bias once after combining partial outputs.

## 3. Phase one: audit the existing implementation

Trace one model’s prefill path from dispatch through attention and FFN execution. Identify the actual files and functions responsible for:

- Up, gate, and down projections.
- Activation and elementwise gating.
- GEMM split dimensions and ratios.
- Packed weight layouts and quantization metadata.
- Intermediate buffers, strides, and ownership.
- GPU–NPU synchronization and output combination.
- Micro-batch dependencies and dispatch.
- NPU queue management and configuration reuse.
- Existing profiling, tuning, and benchmark infrastructure.

Answer these questions with concrete code references:

1. Does the runtime already preserve any partitions across FFN operators?
2. Where are full intermediates assembled, converted, or synchronized?
3. Do split outputs already write directly into shared output buffers?
4. Can existing kernels consume feature partitions without repacking?
5. How does an FFN allocation interact with attention from another micro-batch?
6. What operations can execute efficiently on the NPU, including SiLU and gating?
7. Which existing configuration is the strongest relevant baseline?

Distinguish findings from assumptions. If persistent channel partitioning already exists, characterize it and revise the proposed extension around a demonstrated missing capability.

Record a concise architecture map and project plan in repository documentation, following existing conventions.

## 4. Phase two: establish instrumentation and baselines

Reuse existing tracing where possible. Add only missing instrumentation needed to measure:

- Complete FFN latency.
- Projection and activation/gating latency.
- Intermediate assembly, conversion, and reduction.
- Dependency waits and synchronization.
- GPU and NPU execution intervals.
- Attention–FFN overlap.
- End-to-end prefill latency.

Separate host enqueue time from device execution time. Identify asynchronous completion correctly. Label estimates of memory traffic as estimates rather than hardware measurements.

Establish these comparison configurations where supported:

A. Original HeteroMosaic with its existing optimized configuration.  
B. Single-device FFN allocation within the existing runtime.  
C. Existing operation-level tensor partitioning.  
D. Persistent token-row partitioning across the FFN, if not already covered by the baseline.  
E. Proposed persistent intermediate-channel partitioning.

Avoid duplicate configurations when two labels describe the same implementation.

First measure the existing configurations before introducing the new execution path.

## 5. Phase three: implement a minimal persistent FFN path

Add an opt-in execution mode that preserves the original path as the default and fallback.

Start with one model, one supported shape family, and one valid split ratio. Then extend to a small ratio sweep aligned with backend tiling and quantization constraints.

Requirements:
- Matching intermediate-channel ownership for up and gate projections.
- Correct local activation and gating.
- A down projection that consumes each partition directly.
- Correct combination of partial outputs.
- Explicit dependency handling across both devices.
- Compatible packed weight and metadata access.
- No runtime repacking that silently dominates the measured result.
- No full intermediate assembly between projections unless required; document any such requirement.

If the NPU cannot execute local activation/gating efficiently, inspect available kernel capabilities before designing a new kernel. Quantify any fallback transition and its cost. Do not describe an execution path as fully device-local if it moves NPU intermediates to the GPU.

Separate one-time setup costs from inference costs. Measure additional memory capacity, including any duplicated or repacked weights.

## 6. Phase four: verify correctness

Compare against the original runtime using identical weights, quantization, inputs, and model semantics.

Check:
- FFN outputs with tolerances appropriate to the numerical format.
- Several valid ratios, aligned shapes, and supported boundary cases.
- Single-device endpoints where the interface supports them.
- Complete prefill outputs or logits.
- Multiple micro-batches with the existing dependency schedule.
- Absence of races, stale reads, and duplicate bias/residual application.

Expect floating-point differences from changed reduction order. Report the tolerance and observed error; do not require bitwise equality without justification.

Use focused tests that catch partition, layout, and synchronization errors.

## 7. Phase five: evaluate overlap and end-to-end behavior

Run three levels of experiments:

1. **Isolated FFN:** determine whether persistent partitions improve complete sublayer latency and identify the reason.
2. **Concurrent attention and FFN:** use representative attention work from the same model and micro-batch schedule. Measure both stage latencies and the time until both finish.
3. **Complete prefill:** compare the extension with the strongest original HeteroMosaic configuration.

For each comparison:
- Hold model, precision, prompt, and relevant runtime settings constant.
- Include warm-up and repeated measurements.
- Report central tendency and variability.
- Record device, software versions, power settings, and relevant thermal conditions.
- Separate fixed-schedule comparisons from results after tuning.
- Give both the baseline and extension comparable tuning opportunities.

Measure a small representative range of prompt lengths and micro-batch sizes before expanding the sweep.

Primary metric: **end-to-end prefill latency**, or TTFT if the benchmark includes producing the first token.

Supporting metrics:
- Complete FFN latency.
- Overlapping interval completion time.
- Attention slowdown caused by FFN GPU participation.
- Synchronization and intermediate handling costs.
- Memory footprint.
- Energy per prefill if suitable measurement hardware is available.

Do not claim success based only on individual GEMM speedups.

## 8. Phase six: add allocation selection only if justified

If measurements show predictable differences between configurations, implement a small policy selecting among single-device, persistent token-row, and persistent channel execution.

Use measured costs for the complete FFN and its competing attention work. Integrate with the existing scheduler rather than replacing causal micro-batching.

Begin with an offline lookup or simple selection rule. Avoid a large new scheduler until the evidence warrants it.

Compare the policy against:
- The strongest fixed allocation.
- The existing HeteroMosaic allocation/tuning approach.
- A measured best configuration over the evaluated candidates.

Use separate calibration and evaluation workloads where practical.

## 9. Research claims and decision points

Treat these as hypotheses:

- Persistent partitions reduce meaningful FFN boundary costs.
- Those savings survive backend layout and reduction overhead.
- The best FFN allocation changes with overlapping attention.
- Selecting the allocation improves complete prefill over a strong tuned baseline.

If isolated FFN performance improves but prefill worsens, investigate interference rather than presenting a kernel gain as an end-to-end gain.

If internal boundary costs are negligible, revise the motivation.

If existing code already provides the mechanism, focus on a demonstrably missing capability or document that the original hypothesis does not hold.

Keep the related-work distinction precise:
- GPU–NPU tensor partitioning is established.
- Megatron’s paired projection partitioning is established.
- HeteroMosaic’s contention-aware micro-batch scheduling is established.
- Our potential contribution is the measured benefit and selection of coordinated sublayer partitions within that schedule.

## 10. Working style and first-session deliverables

Proceed autonomously with inspection, documentation, instrumentation, implementation, and supported validation. Ask only when a missing hardware resource or consequential unresolved design choice blocks progress.

Never fabricate benchmark results. If suitable hardware is unavailable, complete the code audit, build checks, applicable correctness tests, and reproducible benchmark commands. Clearly identify measurements still requiring hardware.

For the first session:
1. Audit the repository and trace the FFN execution.
2. Document whether the proposed mechanism already exists.
3. Identify the concrete implementation changes and kernel dependencies.
4. Establish baseline commands and add focused instrumentation if feasible.
5. Recommend the smallest initial experiment based on the actual code.

At each milestone, report:
- What changed or was learned.
- Evidence supporting the conclusion.
- Checks completed.
- Remaining limitations.
- The next concrete step.

Keep implementation changes reviewable and avoid unrelated refactoring.
