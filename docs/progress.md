# HeteroMega progress

## 2026-10-28 — single-dispatch merged NPU FFN

**Measured:** an experimental single-dispatch NPU graph now fuses gate/up+SiLU
and down on the same 32 workers. With P6400 and the teammate GPU suffix, two
reversed 100-sample confirmation blocks complete the synthetic M512/H4096/I14336
FFN in **14.274 ms** and **14.585 ms**, versus faithful native HeteroMosaic
**15.851 ms** and **15.874 ms**. The merged candidate is **9.95%/8.12%** faster.
An earlier repeat measured 11.1%/12.5%; the retained confirmation uses corrected
NPU-partial validation. Matched GPU controls are 22.331/22.275 ms versus native
22.169/22.197 ms, so the candidate control is only 0.35–0.73% slower; the FFN
advantage is not control drift.

The merged graph keeps the same 32 workers (8 columns × 4 rows) for both
phases, reuses the A/W ObjectFifos, uses row-major x/Z, and reuses one output
join per column for Z in phase 1 and Y in phase 2. It is **one XRT launch**
instead of two. The NPU branch is 12.47–12.72 ms at P6400; the GPU suffix is
13.5–13.8 ms and remains the critical path. A five-sample sweep measured
15.569/14.184/13.867/14.348 ms at P4352/6144/6400/6656; P6400 is selected.

At P4352 the merged output is **bit-exact** to the existing two-launch candidate
on both alternating inputs. At P6400 the complete-output and partial checks are
accepted under explicit report policy; six validation checks fall outside the
original tolerance. Native has 132 outside-tolerance checks per 100-sample job.
This remains an isolated synthetic FFN result, not whole-model prefill/TTFT,
attention interference or pretrained accuracy.

The merged graph is an experimental sibling of the production two-launch path;
`npu/ffn/w4a16_upstream.py` is unchanged. Full source, job JSONs, exact-compare
records, sweep data and reproduction are in
[docs/runs/2026-10-28-merged-npu](runs/2026-10-28-merged-npu/README.md). Branch:
`codex/npu-merged-kernel-parallel`. Changes are committed only; no push/PR.

Next: add a DMA-BUF/zero-copy output to the merged kernel to remove the remaining
NPU-output H2D copy, then retune P around 6400. Deeper on-chip Z residency and
down-weight prefetch remain unproven follow-ups.

## 2026-10-28 — DMA-BUF output P4352 beats faithful native FFN

**Measured:** the selected HeteroMega configuration completes the synthetic
M512/H4096/I14336 prefill FFN in **15.887 ms** and **15.780 ms** in two reversed
100-sample blocks. Unchanged native HeteroMosaic completes the same blocks in
**16.031 ms** and **15.947 ms**. Candidate medians are **0.90%** and **1.05%**
lower; both blocks agree, but the distributions overlap and the margin is small.
Matched GPU-only controls are 22.310/22.365 ms versus native's 22.248/22.258 ms,
so the candidate's own GPU control is 0.28–0.48% slower. The complete-FFN
advantage is therefore small and must not be generalized.

The selected configuration is P4352 NPU channels, eight columns/32 workers,
BFP16 native layout, split-M32 A prefetch, preconverted B, shared SwiGLU/down
intermediate, row-major final output, imported HIP-owned output BO and the
teammate three-kernel GPU suffix. The NPU branch median is about 14.39 ms; a
separate GPU-event diagnostic measured about 15.03 ms for the GPU suffix. The
GPU suffix is the critical path at this partition. Input staging (0.27 ms) and
the output/boundary interval (0.44–0.48 ms) are host spans and are not additive
with the NPU branch.

Both implementations run under the explicit `report` numerical policy and retain
failed original tolerances: native has 132 outside-tolerance checks per 100
samples in block 0; each candidate job has 216. Structural, completion and
buffer-integrity checks pass. This is an isolated synthetic complete-FFN latency
comparison, not whole-model prefill/TTFT, attention interference, or pretrained
accuracy. The candidate completes 436 NPU dispatches per job; native completes
218. No host driver/kernel changes were made.

Rejected variants are retained: the original GPU suffix was 16.026 ms at P4352
(20 samples); preconvert-A was 19.988 ms (10 samples); a GPU-owned DMA-BUF input
passed an H512/P512 smoke but was slower (6.530 versus 5.431 ms for output-only)
because NPU input reads became slower. The 10-sample partition sweep gave 15.879
ms at P4096, 15.432 ms at P4352, and 16.080 ms at P4608; the earlier 50-sample
paired P4352 run was mixed, which the 100-sample confirmation resolves.

[Full report, evidence, audit and reproduction](runs/2026-10-27-dmabuf-output/README.md).
Cloud root: `/notebooks/HeteroMega-direct-output-20261027`. Branch:
`codex/shared-buffer-ffn-optimization`. Changes are committed only; no push/PR.

Next: integrate this FFN into the causal model schedule and measure attention
interference before any whole-model prefill or TTFT claim. Further gains require
shortening the GPU suffix or improving NPU efficiency enough to shift the
partition balance; input DMA-BUF staging is not the bottleneck.

## 2026-10-27 — faithful native HeteroMosaic FFN comparison

**Measured:** native HeteroMosaic completes M512/H4096/I14336 FFN in
15.81–15.89 ms, versus 17.48–18.03 ms for HeteroMega P2560/P2816, across two
reversed blocks with 50 samples per mode. Our channel partition is 10.0–14.1%
slower than the native heterogeneous FFN here; it still beats its matched
GPU-only controls by 18.8–21.6%. Native gains about 29.0% versus its own GPU
control. This replaces the earlier missing-native-baseline comparison, not
the preserved GPU-only measurements.

The user explicitly authorized faithful native timing despite numerical
failure. Native report mode retains errors and original failed tolerances;
GPU controls and execution/buffer-integrity checks stay strict. The original
native library, binding and timing body are byte-identical across policies.
Both paths use identical original packed buffers and inputs. Native's complete
output relative L2 reaches .116976; candidate checks all pass. This is a latency
comparison of the implementations, not a model-accuracy result.

The native baseline is rebuilt from pinned 61714a3 with only saved runtime/build
compatibility fixes. Its M256/M256 gate/up split writes shared HIP buffers and
keeps down on GPU. A separate synchronized profile gives gate/up 14.511→7.872 ms,
pointwise .838→.865 ms, and down 7.044→7.010 ms. Our concurrent NPU branch alone
is 14.70–15.52 ms, plus remaining staging/GPU-completion/reduction. Native offloads
33.3% of projection MACs, versus our 17.9–19.6%. Host spans overlap; their values
do not identify device-cycle or bandwidth shares.

The audit verifies 1,194 files, native source/patch/binary provenance, identical
fixtures, power snapshots and 2,126 completed dispatches across all retained
runs. 38 focused CPU tests pass. Hardware remains HX370/Radeon 890M/Strix,
NPU default mode. No host driver/kernel changes or kernel-only PR changes.
Research branch: `codex/native-heteromosaic-ffn-comparison`; report-policy code
commit 1e30f8a. [Full report and reproducible evidence](runs/2026-10-27-native-comparison/README.md).

Next: reduce candidate host/XRT activation staging and measure GPU suffix
execution with device events; then retest against this faithful native baseline.
Whole-model prefill/TTFT and attention interference remain unmeasured here.

## 2026-10-27 — direct-buffer GPU + NPU partition measured

**Measured:** complete M512/H4096/I14336 prefill FFN latency is 17.72–17.95 ms
versus 22.18–22.23 ms with matched HeteroMosaic GPU-only FFN kernels, across
two reversed-order confirmation runs with 50 samples/mode/partition. P2560
and P2816 deliver 1.236–1.255× speedup (19.1–20.3% lower latency); their
ranking reverses, so no unique optimum is established. Six allocations were
tested. Input/output GPU staging, both NPU launches, layouts, waits and final
GPU reduction are all inside the complete FFN timing boundary.

The new `experiments/ffn_partition/run_upstream_partition.py` passes full
original 4352-byte-tile buffers unchanged to the eight-column BFP16 NPU
adapter and prepares the GPU complement from identical canonical W4A16
values. It retains strict GPU controls and BFP16 report policy, per-call
completion/upload counters and exact original-weight hashes. All 3702
numerical checks pass, with worst relative L2 .0172392 on an NPU partial;
confirmation complete-output relative L2 is at most .0080541 vs the CPU
oracle. Independent audit verifies 1656 completed NPU dispatches, 3094
archived file hashes, 14 NPU artifact pairs and the GPU build provenance.
All 29 focused CPU tests pass.

The notebook initially denied GPU access; a normal idle-server restart
restored device allocation. No host driver/kernel changes were made. Hardware
is HX370/Radeon890M/Strix in NPU `default` mode. Isolated overlay:
`/notebooks/HeteroMega-upstream-partition-20261027`; implementation commit
`f3e109e`, branch `codex/upstream-gpu-npu-partition`. Kernel-only PR #3 is
unchanged. [Results, evidence, commands and limitations](runs/2026-10-27-upstream-partition/README.md).

This is an isolated FFN comparison, using staged original GPU kernels. The
teammate's fused GPU frontend, native heterogeneous HeteroMosaic baseline,
attention overlap, real-weight accuracy and full-model prefill remain separate
work. Next: integrate P2560 as a starting point into the existing causal
prefill schedule, then measure whether the gain survives attention interference.

## 2026-10-27 — down-specific BFP16 audit

The request to apply the same treatment to Down is already covered by package
`fd67fbf`: both projections use BFP16. A saved-artifact audit confirms down's
reuse-four path, 8,192→512 matrix instructions and 8,640→2,400 steady MMUL
bundles per half-call, no accumulator spills and 61,952 B SRAM allocation.
Existing down launch-plus-wait medians are 7.223→4.732 ms and 7.228→4.791 ms
(34.49%/33.71% lower). Final CPU Y unpack still takes 1.58–1.65 ms in BFP16.
These are stage measurements from paired FFN runs, not a fixed-Z standalone
down ablation or device-phase cycle measurements. No new kernel/hardware run
was made. [Down breakdown and reproducible counts](runs/2026-10-27-upstream-bfp16/assembly/DOWN.md).
Direct row-major down-output DMA is the next proposed host-overhead target;
device conversion/dequant/stall shares still require profiling.

## 2026-10-27 — glassescrab BFP16 MMUL with original buffers

The latest user direction supersedes the native-only arithmetic selection.
The direct-weight kernel now offers explicit BFP16-backed 8×8×8 MMUL from
the pinned corrected TileFuse source, preserving original 4,352-byte weights,
eight columns/32 workers, BF16 I/O, FP32 partials and the selected reuse/DMA
optimizations. Native BF16 remains the default strict control. BFP16 has its
own compile/cache/manifest identity and a 4 KiB stack.

**Measured:** at M512/H4096/I14336/P2560 on HX370/default, isolated NPU-branch
median latency improves 22.322→14.470 ms (35.18%, ABBA) and 22.405→14.650 ms
(34.61%, BAAB), 100 samples/arithmetic/order. First SwiGLU launch-plus-wait
falls 11.729→6.512 ms; these are host waits, not device-only cycle timings.
All numerical and structural checks pass across 1,024 completed NPU dispatches.
Worst BFP16 relative L2 versus the CPU oracle is 0.0167717 against .02; cross
arithmetic versus native is .0166252, maximum absolute error .00305176.
Local checks pass 113 tests plus 584 subtests. Compiler/runtime sources,
artifacts, raw reports, assembly and reproduction are in
[runs/2026-10-27-upstream-bfp16](runs/2026-10-27-upstream-bfp16/README.md).

The research branch is `codex/upstream-bfp16-mmul`; isolated cloud overlay is
`/notebooks/HeteroMega-upstream-bfp16-20261027`. Previous baselines remain.
The kernel-only package stays in `../HeteroMega-kernels`, PR #3. No GPU code,
model scheduler, driver or kernel was changed. Next: evaluate the complementary
GPU branch, boundary reduction and attention interference using this BFP16
package, then retune the partition. NPU-only timing is not full-model speedup
and synthetic checks are not pretrained-model accuracy.

Published kernel package: `fd67fbf40e9e2e1d06b58d365e4657e61aed050f` in
[PR #3](https://github.com/glassescrab/HeteroMega/pull/3), open and unmerged.
The package has 22 files under `npu/ffn`; all 21 payload checksums pass.

## 2026-10-27: first-launch assembly breakdown

- **Inspected, no kernel changes or new hardware run:** selected `fc0b255`
  SwiGLU gate/up ELFs for M512/H4096/P2560 and their actual disassembly.
  Existing measured first-launch host dispatch/wait is 11.73–11.81 ms;
  including BO I/O it is 12.42–12.50 ms.
- **Compiler-confirmed:** each native BF16 4×8×8 API MAC lowers to eight
  `vmac.f`; four API MACs form 32 instructions in a 36-bundle repeated K8
  body. Prologue/loop/epilogue accounting gives 335,544,320 projection
  `vmac.f` across 32 workers, 10,485,760 per worker, with no selected MMUL
  accumulator spills. Gate/up arithmetic is 21.475 GFLOPs.
- **Code/compiler-confirmed:** 81,920 half-tile dequantizations finish before
  their MMUL work. Logical local scratch traffic is 640 MiB written and
  2,560 MiB read; FP32 partial sums are loaded/stored at every K128 boundary.
  These local operand counts are not DRAM traffic or measured bandwidth.
- **Secondary cost:** SiLU uses a vector linear LUT without scalar exp/libm
  or reciprocal calls, but its 16-element loop has 71 encoded bundles and
  repeated stack-object bookkeeping. There are 5,120 such iterations per
  up worker. FIFO locks and DMA can also stall; no phase percentages follow
  from assembly counts. Native BF16 MAC volume is the strongest structural
  explanation, with serialized dequant/scratch work adding overhead.
- **Next measurement:** split dequant/MMUL event regions and record device
  clock plus FIFO/DMA stalls before claiming a cycle breakdown. Existing
  markers combine dequantization and MMUL. [Assembly report](runs/2026-10-27-swiglu-assembly/README.md).

## 2026-10-25: native BF16 reuse and activation-layout optimization pass

- **Implemented:** vector zero metadata, down M reuse four with core A FIFO
  depth one, row-major SwiGLU input DMA, direct down-A output DMA and borrowed
  readback. The selected profile keeps four MMUL accumulators, native BF16,
  all eight columns and unchanged original packed W4 bytes. Activation layout
  ABI changes are documented; BO reads/writes and final output unpack remain.
- **Measured:** selected NPU-branch median 24.576→22.590 ms (ABBA, 8.08%) and
  24.194→22.490 ms (BAAB, 7.04%), each 100 samples/profile. Both orders use
  fresh subprocess blocks, fixed inputs/weights, excluded warmup/reference and
  exact output comparisons. The combination also beats the simpler staging
  configuration by 2.4–2.7%; vector zero/down reuse alone show no convincing
  benefit. All measurements use HX370/default power, M512/H4096/I14336/P2560.
- **Measured correctness:** selected smoke/model checks pass strict bounds,
  finite/zero/repeat/changed-input and unchanged-weight checks (32 dispatches).
  All 12 benchmark reports pass bitwise controls. Across passing reports,
  2,672 dispatches complete; the retained failed bring-up report has eight
  additional completions that are not correctness successes. Worst strict
  relative L2 is 0.0040004822; maximum absolute error 0.0009765625.
- **Compiler-confirmed/rejected:** eight-accumulator MMUL overflowed 2 KiB
  on full shapes. A 4 KiB conditional stack fixes correctness, but the repaired
  variant is about 2.2× slower due to heavy spills. Selected MMUL remains1.
  Down reuse halves its weight/dequant replay; these are logical counts, not
  measured physical bandwidth or a kernel-phase timing breakdown.
- **Verified:** 201 local tests pass, one skips. Independent audit resolves
  34 artifact pairs/source versions, recomputes summaries and completion
  counts, and matches benchmark outputs to the strict prior full-shape oracle.
  Selected runtime sources match the cloud snapshot; one test-only file has
  later local test additions. Previous baselines and failed evidence remain.
- **Published:** kernel-only [PR #3](https://github.com/glassescrab/HeteroMega/pull/3)
  updated at `fc0b255`, with 22 files and 21 verified payload checksums.
  Selected binaries/MLIR match the cloud evidence exactly. Full research code
  and reports remain on local `codex/native-bf16-reuse-optimizations`.
- **Scope/next step:** this completes the bounded optimization pass before
  integration. It does not establish combined GPU+NPU or whole-model speedup.
  Device-phase tracing, dequant/MMUL overlap, larger N reuse and a SwiGLU
  buffering redesign remain research work. Retune partitions under real
  attention/GPU overlap when integration resumes.
  [Evidence and reproduction](runs/2026-10-25-kernel-optimizations/README.md).

## 2026-10-25: bounded pipeline for original-weight BF16 segments

- **Implemented:** keep two successive DMA task groups in flight, including
  across M-wave boundaries. Queue each segment's output drains before fills;
  wait for and free the oldest group before submitting a third. No change to
  C++ arithmetic, core buffers, FIFO depths, weight bytes or DMA addresses.
  `--segment-pipeline-depth 1` retains the serial control; depth 2 is the
  selected default. Manifests and cache identities include the depth.
- **Measured correctness:** all seven strict-reference cases pass (40 NPU
  completions), covering model shape, uneven partitions and source offsets.
  Full-shape outputs match the preceding package exactly. ABBA/BAAB timing
  runs also require exact control outputs, finite data, successful completion
  and one-time unchanged-weight uploads. Total: 736 completed dispatches.
- **Measured performance:** HX370/default-power isolated NPU-branch median
  24.796→24.024 ms in ABBA (50 samples per schedule), and 25.126→24.512 ms
  in BAAB confirmation (100 per schedule): 3.1% and 2.4% lower latency.
  Timings include activation layouts/BO I/O; setup, weight uploads, warmup,
  hashing and comparisons are excluded. Each block uses a fresh subprocess.
- **Verified locally:** 63 NPU tests pass; 114 experiment tests complete with
  one skip (176 pass total). Tests cover output ownership, bounded in-flight
  groups, drain-before-fill ordering, tail/wave transitions, cache separation
  and detection of bitwise output regressions.
- **Compiler/artifact verified:** compute/FIFO MLIR prefixes and DMA taps
  match between depths; all 64 corresponding core ELF pairs are byte-identical.
  The emitted runtime submits twice as many tasks before its first await,
  stays within two live tasks/channel and six logical descriptors/shim, and
  awaits output completion before freeing descriptors. All four binary pairs
  and source identities match their recorded manifests.
- **Published:** kernel-only [PR #3](https://github.com/glassescrab/HeteroMega/pull/3)
  updated at `d628e48`; it still contains only 21 files under `npu/ffn`.
  Full harness/evidence is checkpointed locally on
  `codex/native-bf16-segment-pipeline` and is excluded from the PR.
- **Limits/next step:** timing distributions overlap; do not generalize this
  modest isolated-branch improvement to full GPU+NPU prefill. Dequantization
  and MMUL remain serial inside each worker, and weight/activation replay
  remains. Profile those phases next, then evaluate the selected schedule
  under actual GPU/attention overlap and retune the partition.
  [Evidence and reproduction](runs/2026-10-25-pipeline-bf16/README.md).

## 2026-10-25: native BF16 consuming original upstream weights

- **User scope:** return to native BF16 and accept glassescrab's existing
  packed weight buffers directly. The clarification concerns weights;
  SwiGLU-to-down activation conversion remains outside this change.
- **Implemented:** `w4a16_prefill_upstream.cc` and `w4a16_upstream.py` consume
  the original striped K128/N64/4352-byte payloads, with separate gate/up
  buffers and full-source K/N strides for partition selection. Native 4×8×8
  BF16 is explicitly selected before AIE headers; partials remain FP32. All
  32 workers are retained. A worker processes its N32 halves from one A/W
  acquisition with shared 8 KiB scratch and separate partial accumulators.
  A column ownership boundary can reread a shared N64 tile without repacking.
- **Implemented host path:** `upstream_npu.py` accepts original buffer
  descriptors, validates BF16/layout/source/artifact identity, and uploads
  fixed bytes once. It performs no weight conversion or concatenation.
  Existing compact/BFP16 experiment paths remain reproducible controls.
- **Measured correctness:** seven cases and 28 input runs completed 40 NPU
  dispatches on HX370. Strict numerical, finite, changed-input, exact-zero,
  repeatability and unchanged-weight checks all pass. Worst relative L2 is
  0.00400048 (limit 0.02); largest absolute error is 0.0009765625. Selected
  M512/H4096/I14336/P2560 FFN relative L2 is at most 0.00375981. Nonzero K/N
  slices, paired N64 halves, narrow N128, fused SwiGLU, complete FFN, and an
  uneven P1152 partition were exercised.
- **Verified locally:** 59 NPU tests pass; 111 partition tests complete with
  one existing skip. Source/manifest identities and selected binary hashes
  match the downloaded evidence. Both MLIR graphs assign 32 cores across
  eight columns with 2048-byte stacks. Package checksums pass.
- **Published:** [PR #3](https://github.com/glassescrab/HeteroMega/pull/3)
  updated with commit `4749d92`, retaining only 21 kernel/package files.
  Full research changes and evidence are checkpointed locally on
  `codex/native-bf16-upstream-weights` and are not part of the kernel-only PR.
- **Limits/next step:** synthetic NPU correctness only. BO upload copies and
  activation staging remain; no new end-to-end GPU+NPU speedup or model
  accuracy is established. P2560 is retained, not retuned. Benchmark the new
  graph's per-segment schedule and partition ratio before quoting latency.
  [Contract](../npu/ffn/UPSTREAM_BF16.md) and
  [hardware evidence/reproduction](runs/2026-10-25-upstream-bf16/README.md).

## 2026-10-25: glassescrab W4A16 compatibility re-audit

- **Code-confirmed:** a fresh check of all seven `glassescrab/mlir-aie`
  branch heads leaves the corrected reference at
  `121dd54abc68f84d89a7074372ebf82be2db62d5`. Our BFP16 projection matches
  its unsigned W4, BF16 activations/scales, per-output-channel K128 groups,
  low-even/high-odd nibble order and BF16 `(q - zero) * scale` dequantization.
  Both enable BFP16-backed 8×8×8 MMUL with four accumulators.
- **Intentional differences:** upstream uses N64 weight tiles of 4,352 bytes
  with duplicated zero metadata and eight-column-striped host tile order;
  ours uses compact N32 tiles of 2,144 bytes. Buffers require repacking.
  Upstream's default BF16-output kernel rounds partial sums after each K128
  call; ours retains FP32 partials until final BF16 output. Tile geometry,
  explicit M reuse and fused FFN scheduling also differ. This is an adaptation,
  not a drop-in binary interface or a claim of bit-identical GEMM results.
- **CPU-verified:** all 48 existing NPU tests pass. An additional independent
  transcription of the upstream host packer and kernel metadata addressing
  at K384/N1024 checked 393,216 dequantized weights, including multiple K
  groups, striped column tiles and varying scales/zeros. Its BF16 weight
  values are bit-identical to the compact kernel-layout model and logical
  reference. This checks layout/dequantization, not hardware BFP16 MMUL.
- **Package-verified:** PR #3 still points to `8622dbe`; all 20 package hashes
  pass, packaged source identities match this workspace, and manifests match
  the archived measured artifacts. Packaged arithmetic is explicitly BFP16;
  the native BF16 experiment control remains a separate path. No new device
  execution, direct upstream-versus-ours hardware comparison or PR change.
  Next comparison, if exact upstream numerical parity is required, must use
  matched output/partial precision and the respective host layouts.

## 2026-10-22: PR narrowed to final kernels and required binaries

- User requested final MLIR code and needed XCLBINs only. PR #3 was replaced
  with one commit (`8622dbe`), 21 files entirely under `npu/ffn`.
- Package includes nine unchanged source dependencies, two generated MLIRs,
  SwiGLU/down XCLBINs and instruction pairs for M512/H4096/P2560, manifests,
  SHA256SUMS, license/notice and a concise build/runtime contract.
- **Verified:** both pairs match the measured artifact hashes; generated
  graphs each contain 32 cores across eight columns; source identities match;
  all 48 existing NPU CPU tests pass against packaged modules. No new device
  execution or performance claim from repackaging.
- Full research work remains on local backup branch
  `codex/ffn-full-experiment-backup-20261022`. The minimal PR worktree is
  `../HeteroMega-kernels`; continue package review there. GPU/model runtime
  integration remains a separate next step.

## 2026-10-22: BFP16 dequantization optimization published

- **Implemented and compiler-confirmed:** construct exact BF16 zero-point
  metadata bits in place of scalar integer-to-float conversions. Gate/up/down
  worker ELFs contain 32→0 `__floatunsisf` call sites per dequantizer. Compact
  W4A16 ABI, eight columns, BFP16 MMUL and native BF16 control remain intact.
- **Measured at fixed P2048 with owned readback:** ordinary FFN median
  19.320→18.671 ms; diagnostic NPU call 18.634→15.965 ms. This exposes the GPU
  as the later dependency. Waits still combine device execution, DMA and stalls.
- **Measured selected configuration:** P2560 plus experimental borrowed
  readback confirms at 18.337 and 18.393 ms (50 samples each), versus the old
  P1792 confirmation at 18.845 ms and fresh GPU-only controls 22.450/22.304 ms.
  The observed gain is 2.4–2.7% over the old best, with overlapping sample
  distributions. Owned P2560 measures 18.800 ms. Borrowing has no universal
  benefit, so owned readback stays default and `--borrow-npu-readback` opts in.
- **Verified:** 13 reports pass original bounds, 2,468 NPU completions,
  1,485 timed invocations; a separate 16-completion old/new comparison is
  bit-identical on two random inputs, zero and repeat. 158 local CPU tests
  pass across NPU, partition and teammate evaluation suites. All 101 archived
  file hashes match. Both power snapshots remain `default`.
- **Scope:** synthetic isolated FFN, not native heterogeneous HeteroMosaic or
  full-model prefill/TTFT. Native adapter remains prepared but unmeasured.
  Latest main (teammate GPU/evaluation PRs) is merged without source changes
  to those components. Current request explicitly authorizes commit/push/PR,
  superseding the historical pause. Branch: `codex/npu-bfp16-prefill-optimizations`.
  Published as [PR #3](https://github.com/glassescrab/HeteroMega/pull/3).
- [Optimization report and reproduction](../experiments/ffn_partition/OPTIMIZATION_RESULTS.md).
  Next restore native comparison and test the selected FFN within actual
  prefill/attention scheduling.

## 2026-10-22: NPU implementation bottleneck trace

- **Reanalyzed measured evidence:** P1792's outer NPU call averages 17.831 ms:
  74.3% in SwiGLU/down host waits, 13.3% CPU layouts, 8.7% BO/invoke-wrapper
  residual and 1.3% submission. These are additive per-sample means, not a
  sum of independent medians. On the shared GPU-event clock, the staged NPU
  result arrives 0.423 ms later than the GPU branch at the median and is late
  in 13/15 samples. Reduction is only 0.155 ms. Serial versus concurrent inner
  NPU medians differ by 0.9%; large GPU-induced contention is not established.
- **Code-confirmed:** all 32 compute tiles are assigned work, but activations
  replay 14 times in gate/up and 16 times in down; weights replay across four
  sequential M128 waves. Logical input DMA totals 127.969 MiB for 16.742 MiB
  unique A/W data. The kernel executes 86,016 dequantize/MAC calls, serializing
  preparation and computation. The BFP16 adaptation retains small tiles,
  FP32 K-group feedback and the 4×8 external layout rather than adopting the
  upstream larger-tile schedule. Logical traffic is not measured DRAM traffic.
- **Analysis, not new hardware timing:** no separation of device compute,
  dequantization, DMA and FIFO/lock stalls is claimed. Next split device event
  regions, improve A/W reuse and wave overlap, then remove host layout/BO
  staging and retune the partition. Raising fused reuse to four requires a
  buffer redesign; raw SRAM bounds exceed capacity.
- **Compiled-binary confirmed via notebook:** disassembled existing P1792
  gate/up/down worker ELFs. Each dequantization contains 32 software
  `__floatunsisf` calls: 2,752,512 calls per FFN implied by the schedule.
  Rehashed xclbins match the recorded profile. Saved audit/disassembly for
  reproducibility. First bounded ablation: replace scalar zero metadata
  conversion with validated exact BF16 bit construction; runtime savings
  remain unmeasured. Stack accesses alone do not establish a spill bottleneck.
- Source-linked report and reproducible CPU analysis:
  [NPU implementation trace](../experiments/ffn_partition/NPU_IMPLEMENTATION_TRACE.md).
  Kernel behavior and prior evidence remain unchanged; no commit, push or PR.

## 2026-10-22: TileFuse BFP16 FFN adaptation measured

- **Implemented:** audited all seven heads of `glassescrab/mlir-aie` and selected
  the corrected TileFuse W4A16 GEMM at `121dd54abc68f84d89a7074372ebf82be2db62d5`.
  Added opt-in BFP16-backed 8×8×8 projections to the existing array8, fused gate/up
  and fused SwiGLU graphs. Compact W4/BF16 ABI, FP32 K-group partials, eight
  columns, GPU kernels and final GPU reduction remain intact. BFP16 stacks
  are 4096 bytes; caches/manifests distinguish arithmetic and source revisions.
  Upstream GEMV was inspected (vector accumulation); decode remains deferred.
- **User-authorized numerical policy:** larger BFP16 deviations may be reported
  while profiling proceeds. Existing tolerance pass/fail and errors remain
  visible; finite output, zero/repeat/changed-input checks and successful NPU
  completion remain required. GPU controls stay strict. Native BF16 remains
  the default and its arithmetic source is unchanged.
- **Measured on HX370/default:** eight NPU allocations at M512/H4096/I14336
  place the best sampled point at P1792 (12.5%). Refinement measured 18.761 ms;
  a 50-sample repeat measured **18.754 ms versus 22.349 ms GPU-only** (1.1917×,
  16.1% lower latency). A fresh BF16 P1152 control measured 19.828 ms with an
  almost identical GPU control; selected BFP16 is 5.4% lower. This is isolated
  synthetic FFN latency, not full-model prefill/TTFT or native heterogeneous
  HeteroMosaic speedup.
- **Profiled:** at fixed P2048, SwiGLU host wait fell 12.625→8.516 ms and down
  wait 7.481→5.833 ms. Submission costs remain around tenths of a millisecond.
  At P1792 the GPU branch is 18.162 ms and outer NPU call 17.848 ms in separate
  diagnostics. Host layouts/staging remain; waits are not pure DMA/compute.
- **Verified:** ten successful reports, 2,764 completed NPU submissions and
  1,694 timed invocations; every numerical check stays within original bounds.
  M512 maximum recorded relative L2 is 0.0172392. All 147 CPU tests pass,
  including rendering; 97 archived evidence hashes were verified. Failed
  initial command/PATH setup attempts are preserved separately.
- Browser access returned. Work ran in `/notebooks/HeteroMega-bfp16-20261022`,
  preserving the earlier notebook checkout. Performance-mode configuration
  again failed with permission error 13; all power snapshots report `default`.
  The native baseline checkout/model library were absent at their recorded
  paths, so that separate comparison still needs re-establishment.
- Evidence and reproducible graphs: [BFP16 results](../experiments/ffn_partition/BFP16_RESULTS.md).
  Source/ABI and branch audit: [adaptation](../npu/ffn/BFP16_ADAPTATION.md).
  Next integrate the measured candidate with real prefill/attention scheduling
  and restore the native heterogeneous baseline. No commit, push or PR.

## 2026-10-22: continuation handoff

- Added a current continuation guide at the top of `agent.md`, preserving the
  original user-provided plan below it. It records the active native W4A16
  profiling request, branch/checkpoint, uncommitted adapter files, prior measured
  results, local-only validation, unresolved browser access, cloud locations,
  run sequence, correctness gates, profiling caveats, and paused PR creation.
- Updated `AGENTS.md` to point incoming agents to that handoff and distinguish
  the current Linux environment from historical Windows onboarding. This is
  documentation-only work; no new hardware measurement or commit was made.

## 2026-10-21: native W4A16 FFN comparison prepared; hardware access blocked

- User requested actual W4A16 profiling against native HeteroMosaic. Added a
  bounded adapter that links the existing native model library and uses its
  original shared-buffer M-split gate/up, GPU pointwise and GPU down for the
  recorded M512/H4096/I14336 configuration. Original runtime and kernel sources
  are unchanged. HeteroMega's prior GPU-only comparison remains separate.
- Added matched canonical weights/inputs, stage and row-owner correctness
  checks, refusal of GPU fallback, successful NPU completion counters, and
  separate ordinary/diagnostic runs. The comparison driver schedules fresh
  native and P1024/P1152 SwiGLU jobs with reversed ordering, GPU controls,
  before/after power queries, and raw evidence validation.
- **Locally verified only:** 21 CPU tests pass (ten new tests plus existing
  packing/sweep checks) for configuration,
  numerical reference/input contracts, failure reporting, job planning and
  evidence checks. CPU preparation and the nine-job dry plan also pass. These
  do not compile the C++ binding or execute hardware.
- **Blocked:** the browser tool reports no available browser, preventing access
  to the authorized AUP notebook. The local host has no AMD NPU or ROCm. No new
  hardware profiling, native accuracy result or speedup is claimed. Reconnect
  AUP, compile the thin adapter against the existing compatible library, pass
  the numerical gate, then run the prepared comparison. Details and commands:
  [native comparison](../experiments/ffn_partition/NATIVE_COMPARISON.md).

## 2026-10-18: fusion checkpoint and cleanup

- User authorized a local checkpoint of the validated gate/up and on-chip
  SwiGLU work. Source, tests, raw results, power snapshots, compiler audit,
  plots and nested benchmark logs are included; no new hardware run or
  implementation change is part of checkpointing. Push/PR remain paused.
- Removed the completed upload's transport-only checksum manifest and
  redundant local transfer/scratch copies. Preserved scientific provenance,
  the source-only baseline archive, interrupted-run evidence, compiled
  kernels and reusable environments.
- Resume from [the checkpoint guide](checkpoint-2026-10-18-ffn-fusion.md).
  The next model experiment is actual prefill integration and attention
  interference; direct Z layout/shared-BO handoff remains a separate proposal.

## 2026-10-18: on-chip gate/up and SwiGLU fusion

- **Implemented and hardware-validated:** opt-in `--fuse-swiglu` computes
  gate/up projections plus SiLU/multiply in one eight-column/four-row graph,
  followed by the existing down graph. This reduces NPU launches from three
  to two. Adjacent gate/up column pairs retain gate intermediates on-chip;
  all 32 workers perform projections and 16 also perform pointwise work.
  Existing BF16 boundaries and arithmetic kernels are unchanged. Z still
  passes through host memory and CPU layout conversion before down. GPU
  kernels and the final GPU partial-output reduction are unchanged.
- **Measured correctness:** small M128/H128/P128 and model-shaped
  M512/H4096/P384,P896 checks pass all 180 checks, including 24 exact
  cross-variant BF16 Z/full-branch comparisons. Every runner and fixed-weight
  upload count matches; 60 NPU launches complete. Maximum explicit relative-L2
  error is 0.003556 under unchanged tolerance. The interrupted first full-size
  attempt remains separately recorded with zero checks; the notebook server
  stopped for an unknown reason. The retry and fresh controls use the restarted
  container, with NPU mode `default` verified before/after.
- **Compiled-artifact confirmed:** 661 checks of the small build verify shared
  gate buffers in adjacent tile memory, no gate DMA, and A/W on the two inbound
  DMA channels. Static data plus reserved stack occupies 39,104 bytes per gate
  core and 45,248 bytes per up/pointwise core. This is not a runtime memory or
  bank-contention measurement. Local validation passes 102 CPU tests.
- **Measured complete FFN:** a fresh seven-allocation comparison at
  M512/H4096/I14336, followed by a reversed-order four-allocation repeat,
  places the two-launch path's best sampled point at P1152 (8.04% NPU).
  It takes 19.657 ms versus its 22.474 ms GPU-only control in the main sweep
  (1.1433x), and 19.643 versus 22.293 ms in the 50-sample confirmation
  (1.1349x). This is 1.86%/2.99% lower latency than each round's retuned
  three-launch minimum at P896. P1024 is only 0.17% slower in confirmation;
  retain the 1024–1152 region, not a claim of a unique or global optimum.
- **Measured diagnostic:** at P1152, NPU host branch time falls from 20.802
  to 18.830 ms; the new GPU branch HIP duration is 18.941 ms and final GPU
  reduction is 0.149 ms. Fusion mainly improves the projection/pointwise
  frontend. Larger shares remain NPU-limited; small shares can remain
  GPU-limited and do not consistently benefit. Host waits are not pure DMA
  or device compute time, and diagnostic medians must not be added to infer
  ordinary concurrent latency. The 36 jobs pass all 2,600 timed checks;
  5,525 NPU completions include these jobs, warmups and exact-only checks.
- The previous 26 measurement sources are archived with matching hashes;
  separate-projection and combined gate/up controls remain available.
  Architecture, raw evidence and fresh comparison results are recorded in
  [SWIGLU_RESULTS.md](../experiments/ffn_partition/SWIGLU_RESULTS.md) and
  [SWIGLU.md](../npu/ffn/SWIGLU.md). HX370/default mode and synthetic FFN
  remain the limits; no whole-model prefill, attention-interference or
  Max+395 result is established. Next integrate the candidate region into
  the real prefill schedule. Direct Z layout emission/shared-BO handoff is
  a separate proposed optimization. No commit, push or PR in this turn.

## 2026-10-18: combined gate/up and partition sweep

- **Implemented and hardware-validated:** `w4a16_gate_up.py` computes matching
  gate/up slices in one wider GEMM on eight columns and four rows. Columns 0–3
  produce gate and 4–7 produce up, with compact output buffers written directly
  by DMA. The unchanged BF16/FP32 compute kernel is reused. `--fuse-gate-up`
  reduces NPU FFN launches from four to three; the separate-projection control
  remains available. Weights upload once, and input uploads drop from two to
  one. Intermediates still pass through host DRAM; this is not on-chip full-FFN
  fusion. GPU performs the final partial-output reduction.
- **Measured:** expanded the earlier coarse split coverage to 12 NPU channel
  counts from 128 through 7168, with fused/unfused comparisons, then added
  P1152 and repeated the best region. M512/H4096/I14336 is fixed, with original
  HeteroMosaic GPU kernels, canonical weights/inputs, randomized execution order
  and a matched GPU-only control in each process. Ordinary latency (30 samples
  in the main sweep, 50 in confirmations) is separate from instrumented stages.
- **Measured:** the initial best fused P896 takes 19.948 ms versus 22.272 ms
  GPU-only (1.1165×), while the initial best unfused P512 takes 20.537 ms
  (1.0897×). Longer confirmation favors P768 (19.783 ms) over P896 (20.108 ms).
  Two final blocks with candidate order reversed put P768/P896 at
  19.997/19.944 ms and 20.023/20.003 ms. These results support a competitive
  768–896 region (5.36–6.25% NPU), not a unique or exhaustive optimum. P896 is
  a practical candidate; retain P768 for subsequent prefill integration.
- **Measured diagnostic:** at fused P896 the GPU branch is 19.779 ms, with
  projections accounting for 96.2% of its HIP event duration. The NPU host
  call is 18.324 ms and GPU reduction is 0.142 ms. Larger NPU shares become
  completion/staging limited. At some fixed splits, fusion shortens NPU work
  but increases complete-FFN latency; scheduling interaction is plausible,
  not isolated causal proof. Host waits include runtime/DMA/compute/stalls;
  they are not pure data-movement or kernel execution measurements.
- Validation: 77 CPU tests pass. All 62 main/confirmation jobs pass, with 3,850
  timed calls and 2,046 explicit numerical checks. The independent M512 exact
  comparison at P128/384/512/896 passes another 160 checks, including bit-exact
  fused versus separate gate, up and complete NPU outputs for alternating,
  zero and repeated inputs. These runs total 11,380 successful NPU completions
  including warmups and correctness-only calls. All report/power/source hashes
  match; the report records counts and retained evidence in detail.
- **Limits:** HX370/Radeon 890M, verified NPU `default` throughout; the host
  rejected the previously authorized performance-mode change. This is a
  synthetic complete-FFN microbenchmark, not whole-model prefill/TTFT or
  Max+395 validation. Teammate GPU PR kernels remain outside this controlled
  comparison. All-NPU and every legal intermediate split were not measured.
- Evidence, reproduction, latency curves, per-stage graphs and independent-run
  comparison: [FUSION_RESULTS.md](../experiments/ffn_partition/FUSION_RESULTS.md).
  Next: integrate the candidate region into the actual prefill schedule and
  measure attention interference and end-to-end prefill against the unchanged
  baseline. PR creation remains paused; no commit or push in this turn.

## 2026-10-18: NPU power verification and device/launch timing

- **Measured:** XRT reports NPU mode `default`, eight columns, at PCI address
  `0000:66:00.1`. Configuration to `performance` was rejected with err=-13
  both as UID 1003 and sudo UID 0. Performance mode is not established; no
  driver/kernel changes were made. Queries before and after both new runs
  remain `default`. Earlier benchmark files did not capture power mode.
- **Measured ordinary FFN:** M512/H4096/I14336/P512, 50 samples per mode
  after three warmups, gives 22.208 ms GPU-only versus 20.425 ms concurrent:
  1.0873× / 8.03% lower latency. All 50 paired iterations improve; all 150
  timed calls pass correctness. The serialized control is 40.295 ms. This
  uses original HeteroMosaic GPU kernels and remains a synthetic complete-FFN
  result, not whole-model prefill, TTFT or a performance-mode comparison.
- Added separate `profile_timeline.py` instrumentation. **Measured diagnostic:**
  30 samples give 20.925 ms instrumented wall time; the GPU branch HIP event
  median is 20.188 ms and GPU boundary reduction is 0.133 ms after dependency
  waits. GPU gate/up/down event medians are 7.057/6.247/6.119 ms. NPU gate/up/
  down CPU wait medians are 4.359/4.066/4.127 ms; fused SiLU/multiply waits
  1.150 ms. Separate CPU submission intervals are recorded for both devices.
- HIP events include scheduling and event overhead; NPU waits are host spans,
  and CPU submission calls are not driver-only launch cost. CPU/GPU clock
  origins are not calibrated and stage medians are not additive. Ordinary
  latency and instrumented diagnostics remain separate. The NPU path still
  uses four contexts and host staging; GPU performs the final partial sum.
- Validation: the ordinary run records 456 successful NPU dispatches and the
  diagnostic 148; all 30 diagnostic samples and 49 checks pass, maximum
  explicit relative-L2 error 0.003476 under unchanged 0.02 tolerance. Fixed
  gate/up/down weights upload once. The existing 52 CPU tests were rerun and
  passed before adding the diagnostic. Raw evidence and reproduction are in
  `experiments/ffn_partition/POWER_TIMING.md` and `results/power/`.
- Next: reduce NPU context transitions and intermediate staging, measure
  complete FFN again, then integrate with the prefill schedule. A verified
  performance-mode comparison requires host permission to change the mode.

## 2026-10-18: eight-column/four-row NPU prefill redesign

- **Implemented and hardware-validated:** added `w4a16_prefill_reuse.py/.cc`
  and the CPU-only `prefill_schedule.py`. The graph uses all eight columns
  and four rows (32 workers), horizontal activation multicast, vertical weight
  multicast and up to two M16 blocks of dequantized-weight reuse. N128 shards
  split token rows across two four-column groups. Host packing and native
  BF16/FP32 accumulation remain unchanged. The default backend is `array8`;
  `--npu-design legacy` preserves the original one-row graph and artifacts.
- Corrected the pinned DMA verifier's 512-element dimension constraint using
  quarter-chunk shim transfers and a memory-tile permutation. Added exact
  address/layout tests and schedule hashes; manifests require 32 workers.
- **Measured on HX370:** M512/H4096/I14336/P512 complete FFN improved from
  22.198 ms GPU-only to 20.718 ms concurrent (20 samples). An independent
  50-sample repeat measured 22.184 versus 20.705 ms: 1.071x speedup / 6.67%
  lower latency. Includes all staging, four NPU launches, waits and reduction.
  This uses original HeteroMosaic GPU kernels; teammate PRs were not merged.
- Fresh legacy eight-column controls show NPU-branch medians of 28.022,
  46.358 and 82.571 ms at P512/1024/2048; array8 takes 18.602, 22.375 and
  29.488 ms. Shared-host variation remains; each run retains its GPU control.
- All tested prompt lengths 128/512/2048/4096 pass numerical checks. Small
  prefill loses to GPU-only; long prompts are near parity, with at most a
  1.019x gain among tested M4096 allocations. No whole-model prefill/TTFT or
  Max+395 acceleration is established.
- **Measured diagnostic:** cycling four initialized XRT contexts takes
  2.70–2.80x the repeated-same-context projection dispatch medians; SiLU is
  5.06x. This includes context/program/cache/scheduling effects, not isolated
  context-switch time. Next prioritize fewer launches/context transitions and
  resident intermediates; retain complete-FFN correctness/timing checks.
- Validation: 52 CPU tests; 939 passing timed FFN invocations; 3,492 completed
  NPU dispatches including the context diagnostic. Maximum recorded explicit
  relative-L2 error is 0.003589 under unchanged 0.02 tolerance. Fixed weights
  upload once. Source hashes match tested artifacts; no arithmetic fallback.
- Evidence and reproduction commands: `experiments/ffn_partition/ARRAY8_RESULTS.md`;
  architecture/traffic: `npu/ffn/ARRAY8.md`. Raw JSON, logs and derived analysis
  are saved locally and on the notebook. No commit/push in this turn.

## 2026-10-18: teammate PR review and FFN bottleneck analysis

- Located and fetched open PR #1 (`1b0023b`, GPU FFN) and PR #2 (`71c95d8`,
  evaluation). PR #2 contains #1 by verified Git ancestry; its separate diff
  is six evaluation/documentation files. The previous ordinary-branch check
  missed these PR refs. No PR was merged or published during this review.
- **Code-confirmed:** PR #1 can provide the GPU branch through its lower-level
  slice API. Its activation uses a different BF16 rounding boundary, and its
  model partial-split switch still omits the NPU output. GPU and our MLIR-AIE
  NPU packed layouts differ. The PR's FFN ablation also generates independent
  weights for several variants; retain shared canonical weights for fair tests.
- **Code-confirmed:** PR #2 depends on #1 and supplies existing model controls,
  not the complete new GPU+NPU path. Its default runner still performs decode;
  strict prefill requires one-token warmups and measurements. Its five CPU
  tests were rerun from the pinned stack and passed.
- **Measured, derived from existing raw data:** at M512/P2048/four columns,
  median summed projection dispatch/waits are 142.320 ms and account for 95.9%
  of NPU branch time. Explicit BO I/O and layouts outside those waits are only
  about 2.145 and 2.405 ms. The complete GPU baseline is 27.154 ms. These host
  waits include DMA/runtime costs and are not pure compute times.
- **Code-confirmed:** the graph uses one GEMM worker per column and repeats
  weight DMA/dequantization for every M16 block (32 times at M512). Larger
  tiles/reuse and additional compute rows are concrete optimization candidates,
  but their gains and the compute/DMA/stall breakdown remain unmeasured.
- Added `experiments/ffn_partition/BOTTLENECKS.md`, a CPU-only analysis script
  and derived JSON with report hashes. Corrected the old missing-PR wording.
  No new hardware runs or kernel changes; old measurements still use original
  GPU kernels. Next: controlled PR backend integration, strict-prefill runner,
  projection instrumentation/reuse improvements, then complete-FFN retesting.

## 2026-10-18: prefill FFN partition microbenchmark

- User requested a GPU–NPU FFN partition experiment against HeteroMosaic
  without FFN offload. Created local branch `codex/ffn-partition-microbench`
  and merged published `origin/main` (`24bb066`), preserving existing NPU work.
  The fetched remote advertised only `main`; the teammate's separate new GPU
  FFN implementation has not yet been located. Requested its branch/commit.
- **Code-confirmed:** added `experiments/ffn_partition/` with an adapter around
  unchanged HeteroMosaic packed GPU kernels, matching channel slices through
  gate/up/SiLU/down, a four-launch MLIR-AIE/XRT NPU branch with persistent
  weight BOs, GPU boundary reduction, and concurrent/serialized comparisons.
  The original model runtime and GPU kernel source remain unchanged.
- Timing runs from ready GPU input to synchronized GPU output, including
  NPU host staging, dynamic allocations, layout conversions, transfers and
  waits. Setup packing/upload and compilation are excluded. This is complete
  FFN latency, not whole-model prefill or TTFT. The NPU path retains logical
  partitions but stages intermediates in host DRAM and is not zero-copy.
- **Measured checks:** CPU contract/packing/backend regression tests pass. Hardware
  validation uses fixed synthetic W4A16 weights, an independent CPU reference,
  branch partial checks, changed/zero/repeated inputs, and unchanged fixed
  tolerances. Performance results require these gates to pass first.
- Notebook setup uses isolated `/notebooks/heteromega-ffn-venv` with
  Torch 2.11.0+rocm7.2, NumPy 1.26.4, ml_dtypes and ninja; existing IRON environment
  and host drivers are unchanged. Native `gfx1150` compilation is forced to
  avoid Torch's default all-architecture list failing rocWMMA's target check.
  **Measured compatibility issue:** the prebuilt XRT Python binding with
  NumPy 2.5.4 returned zero-stride byte arrays, silently repeating the first
  byte. The composed FFN correctly failed its numerical gate. Pinning NumPy
  1.26.4 restored correct readback and the small composed FFN passed. The
  backend rejects malformed byte views before interpreting BF16 values.
  The available machine is HX370/Radeon 890M, not Max+ 395.
- **Measured:** ten model-shaped configurations pass: `H=4096`, `I=14336`,
  `M=128/512`, four-column maximum with `P=128/512/2048`, plus `M=512`
  eight-column maximum with `P=128/256/512/1024`. Each uses three excluded
  warmups and 20 samples per mode, with randomized mode order and alternating
  inputs. All 600 recorded invocations pass validation. The 2,160 NPU
  dispatches in these runs complete; each fixed weight is uploaded once.
- **Measured:** no tested allocation beats GPU-only median FFN latency.
  Best four-column `M=128` result is 7.393 ms versus 6.552 ms GPU-only
  (0.886x). At `M=512`, `P=128` is effectively tied: 27.192 versus 27.178 ms
  (0.999x). Eight-column allocations range from 0.601x to 0.990x. Concurrent
  execution improves over the same serialized partition, but that is a
  separate comparison. Some samples show large common slowdowns; retain
  them and do not assign a cause without load/clock/temperature evidence.
- NPU projection stages dominate large partitions. For four columns,
  `M=512/P=2048`, gate/up/down host intervals including I/O are approximately
  47.86/47.73/48.32 ms; SiLU is 2.16 ms and down-input reorder is 0.088 ms.
  These are not pure device compute measurements. Output-stage diagnostics
  include GPU completion waiting, not just copy/reduction cost.
- **Validated:** 20 CPU regressions pass; the additional hardware stage
  diagnostic passes all 15 checks. Model-shaped reports contain 329 detailed
  checks plus the 600 timed-invocation checks. Their source hashes match local
  files, and the original GPU kernel hash matches both upstream baseline and
  fetched main. Cloud execution used the old baseline checkout with source
  overlays, recorded explicitly by its Git status and source hashes.
- Raw JSON, logs, a CSV summary and reproduction/report instructions are under
  `experiments/ffn_partition/`. Next: obtain the teammate GPU implementation,
  improve NPU projection throughput and intermediate residency, then repeat
  the complete-FFN comparison. Attention interference and whole-model prefill
  remain subsequent measurements; no model-level acceleration is established.
## 2026-10-18: local evaluation runner on GPU PR #1

- Based on GPU PR #1 at `1b0023b`; preserves the earlier evaluation checkout.
- Full plan lists Main A/B/C and paired GPU/NPU sanity checks, including pending endpoints.
- Reuses synchronized `generate(1)` timing, adds prompt prefixes and the original
  heterogeneous backend, and batches methods/lengths in alternating process order.
- CSV reports median/range, token agreement and GPU activation. New persistent
  GPU+NPU FFN and channel-ratio sweeps await the NPU integration; no new hardware
  results are asserted. Commands and measurement limits: [evaluation](evaluation.md).
- User reviewed the complete evaluation scope and authorized a follow-up PR to #1.
- Mac validation: five CPU tests plus CLI command previews and synthetic
  JSON-to-CSV checks; AMD execution remains untested in this change.

## 2026-10-17: GPU P0/P1 work (`kernels/gpu/`, branch `gpu-p0p1`)

All runs on the AUP cloud (HX 370, Radeon 890M `gfx1150`, ROCm 7.2, Torch 2.11).
Details and tables: [kernels/gpu/README.md](../kernels/gpu/README.md#results-2026-10-17-hx-370).

- **Executed, pass:** `test_gpu_ffn` quick and full, 0 failed. New checks:
  `slice_packed_ffn` byte-equal to `pack_ffn_slice` (20 cases), `GpuFfnModel`
  bit-equal to the prefix path, prefix GEMM/GEMV blocks vs fp32.
- **Repeated measurements (G1):** `bench_ffn_ablation` 5 rounds, shuffled order,
  GPU clock/power/temperature per row. Per-round ratio to HeteroMosaic's order:
  fused SiLU-and-multiply about −2 % at every M; merged gate/up GEMM 0 % at
  M ≥ 128; `gemv_w4a16` −13 to −14 % of the decode FFN. Round 0 of each run was
  up to 10 % slower (package 51 to 53 W, GPU about 2.3 GHz, for about 50 s).
- **Bandwidth (G2, CPU as the second agent):** GPU alone 95.9 GB/s; GPU + 8 CPU
  threads 67.6 + 27.1 GB/s. The sum stays at 93 to 97 GB/s. **Not measured with
  the NPU** (needs the NPU side).
- **One weight copy, two split points (G3):** `kInterleaved` gate/up layout and
  `FfnSliceWeights::prefix`; same latency as a separately packed slice.
- **GEMM (G4):** AUTOTUNE kept `generic` in all 24 FFN shapes, so it gives
  no gain. `generic` is compute-bound at 9.1 to 9.5 TFLOPS from M = 128. Static
  ISA count of its K loop: 64 WMMA, 756 other VALU (about 10 per unpacked
  weight, incl. a software fp32 → bf16 rounding) and 487 LDS instructions per
  wave per K step. Proposed fix (not implemented): exact integer weights
  `0x4300 | q` into WMMA with zero/scale applied per K step, and B-fragment order
  in LDS. `rocprofv3` aborts with Torch in the process, so no counters.
- **Decode GEMV (G5):** new `gemv_w4a16` (fp32 accumulation): per layer at
  s = 14336, 1.090 → 0.979 ms; 93 to 96 GB/s.
- **Model integration (G6):** `slice_packed_ffn`, `GpuFfnModel`, and a switch in
  `forward_llama3_with_scratch` (CMake `-DHETEROMEGA_GPU_FFN=ON`, environment
  `HETEROMEGA_GPU_FFN=1`). **Executed end to end with real weights**
  (`kernels/gpu/tools/aup_model_ffn.sh`, Llama 3.1 8B AWQ INT4, GPU-only,
  1024-token prompt, 64 new tokens, 2 processes × 3 repetitions per mode, order
  OFF ON ON OFF):
  - **Correct (measured):** all 4 processes give the 8 reference greedy tokens
    of `docs/runs/2026-10-12-aup/gpu-model-result.json`; all 12 repetitions give
    the same 64 tokens with and without the switch.
  - Prefill 1.801 → 1.781 s (−1.1 %), decode 16.49 → 18.09 tokens/s (+9.7 %).
  - Peak allocation 8.94 to 9.32 GiB in both modes (probably set while loading;
    not measured).
  - With the backend's seeded random weights (timing only): prefill 1.739 →
    1.712 s, decode 16.86 → 18.14 tokens/s, peak 6.68 → 8.21 GiB.
  - The build used the installed XDNA 2.26 UAPI header, renamed to the 2025 names
    by the script (`SYSTEM_XDNA_HEADER=1`; GPU-only). The Python extension needs
    ROCm's `-L` in `CMAKE_MODULE_LINKER_FLAGS`; without it, it linked HIP 5.7 from
    `/lib/x86_64-linux-gnu` next to HIP 7.2 and crashed or found no device.
- `src/hipkernels/w4a16_gemm_packed.cu`: new `w4a16_gemm_fused_packed_tiles`
  entry point, K-loop bound fix for K prefixes in the K2048 kernel, `#ifndef`
  guard on `AUTOTUNE`. Existing entry points are unchanged in behavior.

## 2026-10-16: GPU FFN-slice module proposed (`kernels/gpu/`)

- Added `kernels/gpu/`, a separate CMake project for the GPU half of the
  persistent intermediate-channel FFN split: slice packer, gate/up GEMM,
  SiLU-and-multiply and down GEMM on one HIP stream, boundary sum on the GPU or
  the CPU, tests and benchmarks. It compiles the existing `src/hipkernels/`
  packed GEMM/GEMV unchanged. Root build, model path and baseline are unchanged.
- **Code-confirmed:** the GPU branch contract (shapes, packed layout, metadata,
  dtype/strides, buffer ownership, completion) is in `kernels/gpu/README.md`.
  Tests include the proposed 4096 NPU / 10240 GPU split and M=512.
- **Executed (macOS, no GPU, 2026-10-06):** numpy and C++ packers are byte-equal
  to a line-by-line translation of `_pack_weights_packed`; emulated GEMV
  addressing on slices and `Y_G + Y_N` == full FFN for 3 split points pass.
- **Not executed:** CMake configure, HIP/C++ compile, GPU tests or benchmarks on
  the AUP cloud. No performance or GPU numerical result is claimed.
- Next: build and run `test_gpu_ffn` in the `cloud-baseline.md` environment,
  then `bench_gpu_ffn_slice --m 512 --s 10240,14336`.

## 2026-10-15: GitHub kernel teammate handoff

- User explicitly requested committing/pushing the work so the GPU/NPU kernel
  teammate can refer to it. Remote `origin/main` was checked before publication
  and still pointed to starting commit `61714a3147f34857aa5dfef21a28e762777a2df0`.
- Prepared separate runtime-port and documentation/evidence commits. Added
  `docs/kernel-handoff.md` and README entry links; preserved upstream setup.
  Runtime port commit: `20e4d3052ac21d95ae03f70ad916fab6c75de632`.
  Saved plans, cloud instructions, compatibility evidence, profiling report and
  reproduction helpers are included. Earlier dated references to uncommitted
  changes describe historical session state.
- No new math kernels, persistent-FFN implementation, dependencies or model
  downloads were introduced for this handoff. Cloud-only build adaptations
  remain documented reproduction artifacts. Shared-host drivers were untouched.
- Checks: source patch matches the saved tested compatibility patch; whitespace
  checks pass for runtime edits and maintained Markdown. Preserved user-plan
  Markdown hard breaks and raw evidence retain their original whitespace.
  Text/archive credential scans and local Markdown link checks passed; saved
  cloud screenshots were visually reviewed. Prior cloud build/run evidence is
  retained; no fresh GPU/NPU run is implied by publication.
- Next: coordinate kernel buffer/packing/completion contracts, investigate the
  random packed-W4A16 numerical mismatch, then implement an isolated FFN shape
  and separate down-placement benefits from persistent-partition benefits.

## 2026-10-14: stage profiling and bottleneck report

- User authorized profiling latency/stages/bottlenecks to guide project work.
  Reused AUP hardware, weights, dependencies and the October 13 compatibility
  port. HEAD still `61714a3147f34857aa5dfef21a28e762777a2df0`.
- **Measured:** four configurations, one excluded warmup plus five timed calls
  each, full 32 layers, fixed 1024-token input and eight greedy output tokens.
  Median prefill: GPU native chunks 1745.1 ms, GPU matched 512-token chunks
  1780.2 ms, heterogeneous serial 1327.3 ms, same partitions/two inflight chunks
  1316.6 ms. All 20 measured baseline calls matched prior GPU token IDs.
  Conditional timing results only; numerical fidelity remains unvalidated.
- **Measured:** serial heterogeneous decode loop 439.9 ms for seven steps,
  versus GPU matched 415.3 ms. Complete generation medians 1766.8 vs 2196.7 ms.
  Two inflight chunks improve complete latency only 0.3% on this workload.
  Final repetitions supersede an early commentary impression of a regression.
- Added temporary cloud-only Llama FFN substage scopes and NPU host-phase
  timestamps; existing tracer captures decode too because its guard lives
  through `generate`. Separate phase by sequence length. Two measured traced
  calls per diagnostic after warmup; an untraced instrumentation pass checks
  overhead. Added timed-ioctl interposer and separate Torch/Kineto GPU traces.
- **Measured:** synchronized serial prefill 1340.8 ms: gate/up 437.1 ms, down
  422.2 ms, SiLU/gating 49.4 ms, FFN norm 9.0 ms; FFN total 917.7 ms (68.4%).
  G1 158.5 ms, attention 158.0 ms, O/layout/residual 95.0 ms. Stage barriers
  add about 1% to prefill but 10% to decode; pipeline host intervals are not
  comparable device-completion measurements.
- **Measured:** 288 prefill +224 gate-decode NPU submissions per generation;
  successful submit/timeline waits. Untraced serial prefill host sums: command
  build 18.9 ms, readiness polling 1171.9 ms, mutex queue 0.5 ms, submission
  3.2 ms, completion wait 587.1 ms. Pipeline readiness/queue sums rise to
  2602.3/181.5 ms while completion stays 589.4 ms. These overlap, are not
  additive latency or hardware utilization, and are not all removable overhead.
- **Code-confirmed/measured:** active prefill down is GPU-only; M-split uses
  shared output regions, not a mandatory concat. Down decode's invalid
  cpuN+npuN causes 224 warnings/fallbacks per generation; Q decode also uses
  CPU channels. Do not describe the decode comparison as purely GPU/NPU.
- Saved report, PNG/SVG figure, normal summary CSV, configs/results, raw
  stage/host/ioctl traces, kernel tables and losslessly zipped GPU traces in
  `docs/profiling-2026-10-14.md` and `docs/runs/2026-10-14-profile/`.
  Reproduction scripts and restoration checks are included. No packages were
  installed; used the existing IRON matplotlib only for the report figure.
- Restored cloud model/NPU source from pre-profile snapshots and restored its
  baseline module, then rebuilt the ordinary extension successfully. Hash/content
  checks passed. No profiling instrumentation was added to local implementation
  files; the earlier four-file compatibility patch remains uncommitted. No host
  driver/firmware changes, inference algorithm changes, commits or pushes.
- Next: resolve numerical mismatch; isolate a 512x4096x14336 FFN and test down
  placement before attributing gains to persistence. A proposed feasibility
  partition is 4096 NPU /10240 GPU channels using staged NPU shape families,
  with activation/layout/packing correctness still to establish. Preserve a
  token-row comparison and measure readiness/queueing with controlled schedules.

## 2026-10-13: direct-XDNA runtime port and confirmed GPU-NPU model run

- User explicitly authorized resolving cloud compatibility. Source HEAD remains
  `61714a3147f34857aa5dfef21a28e762777a2df0`; changes are uncommitted.
- **Measured:** explicitly aligned device-heap mapping resolves context EINVAL.
  Zeroed padded QoS/CU parameters resolve PDI configuration failure; unique BO
  residency handles resolve submission EALREADY; DRM timeline waits resolve
  unsupported legacy WAIT_CMD. Changed four runtime/header files locally and
  in the cloud, preserving model math, kernels, splits and scheduling.
- **Executed:** patched M sweep and model-extension builds, exit 0. Original
  random-weight sweep now submits/completes NPU work but fails existing
  numerical tolerance (first shape max difference 1.5). An independent float
  product puts the larger error on the NPU side. Exact scales alone do not fix
  it; intermediate accumulation/rounding is a hypothesis, not a confirmed cause.
- **Executed:** cloud-only short diagnostic sweep, 2048 cubed: exact activation
  1/16, qweight 9, zero point 8, scale 1/16 => output exactly 8. Eight row splits
  from NPU M=256 to 2048 pass with zero error, including concurrent shared-buffer
  GPU-NPU work and NPU-only execution. Random activations with those constant
  weights pass loose existing tolerances but have max difference 0.25.
- **Executed:** full GPU model regression, same fixed 1024-token input and eight
  greedy tokens as October 12; one cold generation call 2.436990 s.
- **Executed:** true heterogeneous model run with shipped 512-token serial
  chunk schedule, same weights/input/output settings. Two contexts; 512 NPU
  submissions and 512 timeline waits succeeded, zero submission/timeline
  failures. Generated token IDs match GPU-only; cold wall time 2.005948 s.
  This is functional evidence, not a repeated speedup or accuracy result.
- Found/corrected sparse artifact staging: GEMV needs `_K_8c` folders. Earlier
  apparent hetero model success actually used GPU fallback (zero submissions)
  after missing files disabled the driver. Preserve those logs as rejected
  evidence. Existing down-GEMV cpuN+npuN=5120>4096 warning/fallback remains;
  the other NPU paths are confirmed by counts.
- Rejected START_NPU packet adapters after worse numerical results. Retained
  original START_CU encoding. Restored the cloud sweep source after temporary
  diagnostics; its original-benchmark rebuild is recorded separately.
- Saved raw probe/build/model logs, source variants, configs/results and patches
  locally in `docs/runs/2026-10-13-compat/evidence/`; current source patch is
  `docs/runs/2026-10-13-compat/runtime-compat.patch`. Updated session instructions,
  plan, cloud runbook and `docs/runtime-compatibility.md`. Host/IRON unchanged;
  no commits/pushes. Cloud session expired during a stalled browser call;
  recovered persistent files through a new session.
- Next: characterize NPU numerical behavior without relaxing checks, establish
  random packed-W4A16 correctness and broader real-weight accuracy, and make
  setup failures explicit before persistent-FFN implementation/performance work.

## 2026-10-12: baseline build and real-weight GPU model run

- User explicitly requested running HeteroMosaic, authorizing isolated cloud
  dependency installation, model downloads, and compatibility investigation.
- Created a separate ROCm PyTorch environment (2.11.0+rocm7.2) and pinned source
  checkout in `/notebooks`; kept IRON environment and host drivers intact.
- **Executed:** CMake configure and build of GPU layout test, original M-split
  sweep, and Python model extension; exit 0 after two CMake path adaptations
  and a build-time alias header for renamed Torch HIP stream/guard types.
  No inference/kernel/scheduler/runtime source changes.
- **Executed:** existing GPU layout test; unpacked GEMM/GEMV matched references.
  Its source selects unpacked mode; this is not packed-kernel numerical validation.
- **Executed:** original heterogeneous sweep, bounded at 180 s. 88 split entries
  failed NPU context creation (`EINVAL`), four GPU reference entries completed,
  and a fifth GPU reference was interrupted. No successful heterogeneous result.
- **Executed:** full 32-layer Llama 3.1 8B AWQ GPU inference with pinned real
  model/tokenizer revision `db1f81ad4b8c7e39777509fac66c652eb0a52f91`; loaded 291
  parameter groups, zero skipped. Fixed 1,024-token input, context capacity 1,536,
  eight greedy generated tokens; synchronized generation-call wall time
  2.669836 s in one cold run, excluding construction/weight loading. Exit 0.
  Not a statistical performance or model accuracy/perplexity study.
- **Executed:** process-local extended-QoS adapter retry; still `EINVAL`, bounded
  at 90 s. Confirmed installed XDNA UAPI differs; complete cause remains unresolved.
  Kernel log access is unavailable inside the container.
- Saved exact commands, patch, adapter/driver sources, configs, package pins,
  fixed input/output IDs, and logs locally in `docs/runs/2026-10-12-aup/`.
  Updated `docs/cloud-baseline.md` with reproducible setup and execution steps.
- Local implementation unchanged; source HEAD still
  `61714a3147f34857aa5dfef21a28e762777a2df0`; no commits/pushes.
- Next: provider kernel diagnostics/current-XDNA compatibility work or matching
  host stack; validate original packed shared-buffer NPU launch before full
  heterogeneous inference or persistent-FFN implementation.

## 2026-10-12: AUP cloud access and device smoke checks

- Authenticated to the supplied AUP cloud and opened a JupyterLab terminal in
  the `mlir-aie:latest` environment. Credentials were not saved to the repository.
- Observed Ryzen AI 9 HX 370/Radeon 890M (`gfx1150`), NPU Strix (`aie2p`),
  exposed GPU/NPU devices, Ubuntu 24.04.4/kernel 6.17.0-42, ROCm 7.2 and XRT 2.26.
- **Executed:** official MLIR-AIE single-core i16/i32 matmul, M=K=N=512,
  `make ... NPU2=1 run`; exit 0 and `PASS!`.
- **Executed:** scratch HIP kernel on gfx1150; 16/16 outputs correct. Fixed its
  build invocation to select ROCm 7.2 headers/libraries instead of stale system
  HIP 5.7. No installed files or repository implementation were changed.
- Existing `ironenv` Torch is `2.13.0+cpu`; GPU tensor check failed because it
  has no HIP support. Separate ROCm PyTorch is required for HeteroMosaic.
- Saved connection steps, version differences, working smoke commands and the
  staged baseline procedure in `docs/cloud-baseline.md`. Remote diagnostic
  source/logs are under `/notebooks/heteromega-baseline-logs`; example generated
  its build artifacts. One transient connection error recovered through hub.
- **Not executed:** HeteroMosaic configure/build, W4A16 kernels, DMA-BUF sharing,
  concurrent GPU-NPU tests, model generation, or performance baseline. No
  dependencies installed, weights downloaded, commits/pushes, or implementation
  edits. HEAD still `61714a3147f34857aa5dfef21a28e762777a2df0`.
- Next: resolve supported runtime/image versus a documented 7.2/XDNA 2.26 port;
  establish isolated ROCm Torch; validate original packed W4A16 GPU/NPU split
  with correctness and sharing before full-model downloads or FFN changes.

## 2026-10-12: revised plan saved for future sessions

- Saved the complete user-provided plan verbatim in repository `agent.md`, with
  provenance and separately labeled assistant review recommendations.
- Current planning scope is FFN prefill on one model/platform; attention remains
  on its existing path. Attention partitioning, decode optimization, speculative
  decoding, and broader model support are deferred.
- Updated AGENTS to read `agent.md` and marked the earlier project-plan scope
  and milestones as historical. Preserved the existing architecture/build notes.
- Implementation remains unstarted. HEAD remains
  `61714a3147f34857aa5dfef21a28e762777a2df0`; documentation remains uncommitted.
- Verification: checked saved plan against the supplied text and inspected Git
  status. No implementation, dependency, model, build, or benchmark changes.
- Next step when development is requested: use `agent.md` for the audit,
  NPU activation/layout feasibility investigation, and baseline experiment.
  The September next-session list below is historical where it differs.

## 2026-09-18: repository onboarding and scope capture

**Status:** documentation prepared; implementation and hardware validation have
not started. No performance or numerical correctness result has been reproduced.

### Starting state

- Repository: `C:/Users/pangq/Desktop/HeteroMega/HeteroMega`, branch `main`.
- Starting HEAD: `61714a3147f34857aa5dfef21a28e762777a2df0`,
  `updated readme (#3)`, authored 2026-09-04.
- Origin: `https://github.com/glassescrab/HeteroMega.git`;
  upstream: `https://github.com/UIUC-ChenLab/heteroMosaic.git`.
- Working tree was clean before documentation changes. No existing AGENTS.md
  was found in the workspace/repository or checked ancestor locations.
- Reference PDFs live in sibling `../Documents/`, outside Git. The supplied
  proposal matches the user's goal; whether it is the final version is unknown.
- Session host is Windows/PowerShell; target execution recipe is Linux/AMD.

### Completed

- Read README, build/setup files, Llama frontend/bindings, main model execution,
  quantized linear dispatch, heterogeneous compute helpers, NPU config/import/
  launch code, and relevant M/K/N microbenchmark and tuning locations.
- Read the complete one-page proposal and relevant Megatron-LM/HeteroMosaic
  sections; visually checked the proposal and key architecture figures.
- Created repository `AGENTS.md`, `docs/project-plan.md`, and this log. Added a
  small outer-workspace `../AGENTS.md` entry point to identify the nested repo.
- Recorded documented commands, source-based corrections, reuse opportunities,
  feasibility gates, and a small first development milestone in the plan.

### Findings that affect the research

- Existing code supports operator splits plus causal chunk scheduling. Preserve
  both in the original baseline and control scheduling in causal comparisons.
- Main Llama attention and FFN pointwise work are GPU-side. Persistent device
  ownership across those operations is not implemented in the inspected path.
- M-split GEMM writes into a shared output; do not assume every operator performs
  a gather. K-split stages/copies and sums; N-split benchmark explicitly assembles.
- N-split GEMM is benchmarked but lacks a dedicated model dispatch branch.
- NPU execution uses shared DMA-BUF handles and a mutex-protected submit/wait
  path. KV caches are currently excluded from XDNA buffer import.
- Shipped Strix Point Llama config selects GPU. README's config filename and
  model example differ from the actual frontend; see plan before running.
- Existing traces can either perturb execution with synchronization or omit
  device completion timing. Fine-grained overhead evidence needs more work.

### Verification and boundaries

Static source/path checks only. No setup/build/model/benchmark/tuning script was
run. No dependencies installed, weights/tokenizers downloaded, implementation
files modified, PDFs moved, or commits/pushes made. Documentation links/anchors
and final Git diff/status were checked. Reference-render scratch images are in
the app visualization directory, outside the Git repository.

### Next session

1. Read AGENTS and the plan; incorporate a later final proposal if supplied.
2. Identify the target Ryzen AI system and available Linux runtime/NPU kernel
   generation tools. Do not treat documentation as a successful setup.
3. When implementation is authorized, implement M1: synthetic FFN partition
   metadata/reference correctness harness with unequal channel splits and one
   boundary sum, plus a shape/layout compatibility audit. No model needed.
4. Record actual commands/results and calibration tolerances here. Hardware
   FFN integration and NPU attention remain subsequent work, not completed work.
