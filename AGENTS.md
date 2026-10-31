# HeteroMega session guide

## 2026-10-31 integrated GPU + NPU FFN

- Read `docs/ffn-teammate-testing.md`, `docs/ffn-deployment.md` and the latest
  `docs/progress.md` entry. The user authorizes committing/pushing the validated
  integration and teammate guide to origin/main. Preserve existing worktrees
  and teammate changes; no shared driver/kernel changes or credentials/weights.
- Build-time `HETEROMEGA_MERGED_FFN=ON`, runtime `HETEROMEGA_FFN_CONFIG=<JSON>`.
  Llama3 packed group128, M512/H4096/I14336/P6400 is the tested configuration.
  NPU owns a prefix and GPU a suffix through gate/up/SiLU/down; C++ sums the
  two outputs and the model adds one residual. Host staging, not zero-copy.
- Cloud builds and deployment checks complete: isolated30, GPU-attention
  model64/128 merged completions, native-attention128 merged +640 native calls
  for one/two inflight slots. Inspect retained evidence and native ioctl counts.
  The initial missing-root native run silently used GPU fallback and is invalid.
- NPU/combined numerical deviations are accepted under explicit report policy;
  preserve their error metrics and failed strict verdicts. GPU controls, finite/
  stale-output checks, launch/completion and guards remain strict. These jobs
  do not establish accuracy or a model speedup. Portable tests are not hardware
  proof. Existing evaluation batch methods do not yet include this new method.
- Unset HETEROMEGA_FFN_CONFIG in original baseline jobs; do not combine with
  HETEROMEGA_GPU_FFN=1. Decode/unsupported rows use the original FFN.
- Kernel/source history before this publication is retained on
  codex/npu-merged-kernel-parallel at e6ca183c; the required source dependencies
  and October31 deployment evidence are included here without the full earlier
  experiment-result archive. Pinned review/deployment worktrees remain intact.

## Start here

- Read `agent.md` for the current user-provided FFN-prefill plan and separately
  labeled review recommendations.
- Read `docs/project-plan.md` for the baseline architecture and build/run notes;
  its earlier broad research scope and milestones are historical.
- Read `docs/progress.md` for the latest verified state and open questions.
- Read `docs/kernel-handoff.md` for the teammate entry point and kernel priorities.
- Read `docs/profiling-2026-10-14.md` before optimization. Measured prefill is
  dominated by FFN matrix projections (about 68% including FFN pointwise/norm);
  down remains GPU-only, and two inflight chunks barely improve this workload.
  Current M-split outputs have no obligatory concatenate step. Distinguish
  synchronized diagnostic stages, ordinary latency, and overlapping host waits.
- Read `docs/cloud-baseline.md` and `docs/runtime-compatibility.md` before AUP
  cloud work. The experimental runtime port now executes real GPU-NPU model
  inference (512 successful NPU submissions/waits; fixed output matches GPU).
  Random packed-W4A16 numerical checks still fail; accuracy remains unvalidated.
  Evidence is in `docs/runs/2026-10-12-aup/` and `docs/runs/2026-10-13-compat/`.
- Read the upstream `README.md` before any environment setup. Its instructions
  target Linux/AMD hardware; this onboarding workspace is Windows/PowerShell.
- Initial baseline: `61714a3147f34857aa5dfef21a28e762777a2df0`
  (`updated readme (#3)`, 2026-09-04). Do not assume HEAD remains at this commit.

## Research scope

Current scope (2026-10-12): investigate persistent FFN intermediate-channel
partitions for heterogeneous GPU-NPU prefill within HeteroMosaic's existing
causal micro-batch schedule. Keep matching gate/up channels through activation,
gating, and down projection, then reduce partial outputs at the FFN boundary.
Measure whether savings survive interference with concurrently running attention.
Begin with one supported dense gated model and one available AMD platform.
Attention stays on its existing path; attention-head partitioning, decode
optimization, speculative decoding, and broader model support are deferred.
Speedup and hardware feasibility remain hypotheses.

`agent.md` preserves the user's current plan and supersedes the broader scope
in the September onboarding notes and `../Documents/CS 598 Proposal.pdf`.
The PDF remains a historical reference; no final-version status is asserted.
Assistant review suggestions in `agent.md` are labeled separately from the
user's plan. Follow later explicit user scope changes.

## Working rules

- The initial session is documentation-only: no implementation edits, dependency
  installation, model downloads, or commits/pushes. Follow later explicit user
  authorization when the project moves into development.
- The later 2026-10-12 request explicitly authorizes trying the cloud baseline,
  including isolated dependencies/model downloads and necessary compatibility
  investigation. Preserve baseline algorithms and record adaptations separately.
  It does not authorize changing the shared host kernel/driver or committing/pushing.
- The 2026-10-15 request explicitly authorizes committing and pushing the existing
  compatibility work, project documentation, and profiling evidence to
  `origin` (`glassescrab/HeteroMega`) for the kernel teammate. Preserve teammate
  changes and never publish cloud credentials or model weights. This does not
  authorize changing the shared host kernel/driver.
- Preserve existing work and upstream instructions. Inspect Git status first.
- Label findings **code-confirmed**, **documented but unverified**, **proposed**,
  or **measured**. Never describe a successful build, NPU launch, or speedup
  without an actual corresponding run and its evidence.
- Keep GPU-only and original HeteroMosaic baselines reproducible. Hold weights,
  quantization, prompts, output lengths, and decoding settings fixed.
- Do not infer NPU execution from `--backend hetero`, a config entry, or a
  firmware directory. Check the selected runtime path and successful completion.
- Distinguish logical partition ownership, shared DRAM buffers, and NPU on-chip
  residency. Persistent partitions do not automatically provide on-chip reuse.
- Check actual operations rather than comments: the Llama FFN uses SiLU, and
  `hetero_matmul_out_gemv_packed_M` actually divides output channels.
- Avoid running setup, tuning, or model scripts during read-only inspection;
  they can install packages, rewrite configs, or fetch weights/tokenizers.
- Update `docs/progress.md` after substantive work with changes, checks,
  limitations, and the next concrete step. Keep the plan aligned with scope.

## Key locations

- `py/unified_llm_w4a16/llama3_8b_w4a16_model.py`: frontend, weights, CLI.
- `src/unified_llm_w4a16_hetero/unified_llm_w4a16.cpp`: model/layer execution.
- `src/unified_llm_w4a16_hetero/hetero_compute.cpp`: per-operator splitting.
- `src/unified_llm_w4a16_hetero/npuSetup.cpp`: config, sharing, NPU dispatch.
- `src/npu_matmul_func/`: low-level XDNA contexts and command packets.
- `src/hipkernels/`, `src/cpu_avx_kernels/`: GPU and CPU kernels.
- `src/microbenchmarks/tensor_parallel_gemm_npu_gpu_sweep{M,K,N}.cpp`:
  split experiments; these are not persistent sublayer implementations.
- `hw_bins/npu2/`: shape-specific NPU artifacts. Exclude this large tree and
  vendored headers from broad source searches unless specifically needed.
