# HeteroMega progress

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
