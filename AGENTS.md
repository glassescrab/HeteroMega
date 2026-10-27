# HeteroMega session guide

## Start here

- Read the **2026-10-22 optimization/PR update at the top of `agent.md` first**
  and `npu/ffn/BFP16_ADAPTATION.md` for the latest upstream adaptation,
  arithmetic policy, hardware evidence and remaining comparison work.
  The original user-provided
  FFN-prefill plan and separately labeled review recommendations follow it.
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
  target Linux/AMD hardware. The original onboarding used Windows/PowerShell;
  the current local handoff uses Linux without an AMD NPU. Verify the actual
  execution environment rather than assuming either has suitable hardware.
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
- The latest 2026-10-22 request, "make some optimizations and make a PR",
  authorizes implementation, cloud verification, commits, pushing the branch
  and creating a PR. It supersedes the earlier PR pause. Preserve teammate
  changes and the recorded baselines; shared host kernel/driver changes remain
  outside scope.
- Label findings **code-confirmed**, **documented but unverified**, **proposed**,
  or **measured**. Never describe a successful build, NPU launch, or speedup
  without an actual corresponding run and its evidence.
- Keep GPU-only and original HeteroMosaic baselines reproducible. Hold weights,
  quantization, prompts, output lengths, and decoding settings fixed.
- The 2026-10-22 user request accepts larger BFP16 numerical differences for
  the experimental prefill performance study. Use explicit BFP16/report mode;
  retain error magnitudes and original tolerance pass/fail. Structural execution
  failures remain failures. Preserve native BF16 and strict GPU controls.
  This supersedes historical instructions that block all BFP16 timing on the
  previous error tolerance; it does not establish model accuracy.
- The 2026-10-27 user request explicitly allows timing native HeteroMosaic
  despite numerical failures, provided its implementation is faithful. Use
  explicit native report policy; preserve the original kernels, dispatcher,
  packed weights and timing boundary, and retain numerical errors and original
  tolerance verdicts. Numerical differences do not block this performance
  comparison. Execution, stale-output and buffer-integrity failures still fail;
  GPU controls remain strict. This supersedes the earlier native accuracy gate.
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
