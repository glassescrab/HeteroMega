# HeteroMega project plan

> **2026-10-14 profiling update:** [profiling-2026-10-14.md](profiling-2026-10-14.md)
> records repeated baselines, FFN stages and NPU wait phases. The FFN accounts
> for about 68% of diagnostic prefill, and GPU-only down projection is a major
> remaining cost. Prioritize numerical fidelity, an isolated FFN/down-placement
> ablation, and then a controlled persistence experiment. This does not establish
> that intermediate assembly is the baseline bottleneck.

> **2026-10-13 runtime update:** the uncommitted compatibility port executes
> GPU-NPU Llama inference on AUP, with counted NPU submissions and matching
> fixed-workload tokens. Random packed-W4A16 checks still fail. Read
> [runtime-compatibility.md](runtime-compatibility.md) and the latest progress
> entry before development; establish numerical fidelity before FFN changes.

> **2026-10-12 scope update:** [../agent.md](../agent.md) is the current
> user-provided plan, focused on persistent FFN partitions for prefill and
> attention-FFN interference within the existing micro-batch schedule.
> Attention partitioning and decode optimization are deferred. The September
> scope, research milestones, and future-work directions below are preserved
> as historical context and are superseded by that plan. The baseline code map
> and build notes remain useful static-inspection references, not verified runs.

## Scope and evidence

As of 2026-09-18, this is an onboarding plan based on static inspection, not a
validated implementation or performance result. Baseline Git commit:
`61714a3147f34857aa5dfef21a28e762777a2df0` (`updated readme (#3)`).
Origin: <https://github.com/glassescrab/HeteroMega.git>.
Upstream: <https://github.com/UIUC-ChenLab/heteroMosaic.git>.

**Scope reference:** `../../Documents/CS 598 Proposal.pdf`, titled
"HeteroMega: Asymmetric GPU-NPU Tensor Parallelism on AI SoCs". Its final-version
status is unconfirmed. A later final proposal is authoritative. The proposal
targets one Ryzen AI system, Llama-3.1-8B-Instruct, batch size one, complete GQA
groups with local KV-cache slices, and matched FFN channel partitions. It calls
for NPU attention/elementwise support and separate offline-selected attention
and FFN ratios. Exact hardware, kernel toolchain, and ratios remain undecided.

**Question:** Does preserving partitions across a sublayer reduce intermediate
assembly and synchronization enough to improve end-to-end inference relative
to independently partitioned operators and the existing graph scheduler?
Keep model weights, quantization, and decoding settings fixed. Measure fixed
prompt/output workloads across context lengths: total inference latency,
time to first token (TTFT), decode tokens/s, sublayer latency, intermediate
movement, and synchronization. A negative performance result is informative.

## Current architecture (code-confirmed)

This is a custom inference runtime, not Megatron-LM or a generic graph compiler.
Python handles tokenization/configuration and quantized weight preparation;
pybind11 calls a LibTorch C++ model; HIP executes GPU kernels; Linux XDNA driver
ioctls submit precompiled NPU matmul artifacts. CPU AVX GEMV paths also exist.
PyTorch's `cuda` device name denotes the ROCm GPU in this project.

```text
Python frontend -> pybind11 -> UnifiedLLMW4A16Impl::generate / forward
  embedding -> [RMSNorm -> Q/K/V linears -> RoPE + KV-cache update
    -> attention -> O linear -> residual
    -> RMSNorm -> gate/up linears -> SiLU(gate) * up -> down linear
    -> residual] x layers -> final norm -> LM head -> token selection
                     |
         QuantizedLinearImpl::forward
           GPU HIP / heterogeneous split / NPU matmul / CPU decode
```

For the intended `cuda` execution, attention, RoPE, cache writes, normalization,
residuals, and FFN SiLU/multiply remain GPU-side in the inspected Llama path.
Projection functions return futures where host/NPU work is asynchronous; the
model waits before consuming the full logical result. A future wait is not
necessarily a whole-GPU barrier; GPU dependencies also use stream ordering.
Even the `npu` mode selects NPU linear operators, not an entirely NPU model.

Prefill uses GEMM; single-token calls use GEMV. `forward_llama3_chunked` can
divide prefill into causal token chunks and optionally pipeline scratch slots
on HIP streams. Per-layer KV-ready events order dependent chunks. This is
existing graph-level overlap, so the baseline must not be described as only
independent operator partitioning. Decode follows the non-chunked path.

For `C[M,N] = X[M,K] W[K,N]` (logical weight orientation):

- **M-split GEMM:** GPU and NPU compute different token rows, writing directly
  into regions of the shared output. There is no mandatory concatenate copy.
- **K-split GEMM:** partitions input features; the current function allocates
  input staging/partial-output tensors, copies slices, waits for NPU work, and
  adds partial results. It can also split the K0 contribution by M.
- **N-split:** a standalone GEMM benchmark repacks output-column weight slices,
  launches both devices, then copies both outputs into a full result. The
  model's `QuantizedLinearImpl::forward` has no dedicated N-split GEMM branch;
  the config loader's `split_type=-2` does not by itself supply that behavior.
- **Decode:** `hetero_matmul_out_gemv_packed_M` is misleadingly named: its
  implementation divides N among NPU/CPU/GPU. There is also a K-split path.

`import_dma_buf_to_xdna` exports HIP allocations through HSA DMA-BUF and imports
them as XDNA buffer handles. Registered pointers are cached. `npuMatmul_zero`
polls a HIP input-ready event, acquires a global NPU mutex, submits an XDNA
command, and waits for completion. Thus host launches can overlap GPU work,
but this helper serializes NPU executions. Shared memory does not eliminate
DDR traffic, layout conversion, dependencies, or contention. KV caches are
currently explicitly skipped by `import_all_weights_to_xdna`.

## Code reading map

Line anchors refer to the starting commit; use symbols if the source moves.

| Location | Functions / reason to read |
| --- | --- |
| `py/unified_llm_w4a16/llama3_8b_w4a16_model.py:678` | `LLaMA3W4A16Model`, `_load_quantized_weights`, `_prepare_presaved_weights`, `main`; defaults are 32 Q heads, 8 KV heads, head dimension 128, hidden 4096, FFN 14336, group size 128. |
| `src/unified_llm_w4a16_hetero/python_bindings.cpp:11` | `PYBIND11_MODULE`, exposed constructor, `forward`, `generate`, weight-loading methods. |
| `src/unified_llm_w4a16_hetero/unified_llm_w4a16.cpp:862` | `QuantizedLinearImpl::forward`: packed/unpacked, GEMM/GEMV, device dispatch. |
| Same file, `:2105`, `:2152`, `:2298`, `:3780` | `forward`, `forward_llama3_chunked`, `forward_llama3_with_scratch`, `generate`; main integration points. |
| `include/unified_llm_w4a16_hetero/unified_llm_w4a16.hpp:13` | Attention modes, `GET_TRACES`, scratch/model classes. Mode 2 uses SDPA for initial prefill, flash attention for later chunks, custom HIP decode attention. |
| `src/unified_llm_w4a16_hetero/hetero_compute.cpp:111`, `:282`, `:449`, `:633` | Packed M/K GEMM and GEMV implementations, copies, reductions, futures. |
| `src/unified_llm_w4a16_hetero/npuSetup.cpp:666`, `:1051`, `:1139` | `read_npu_config`, `get_split_type`, `load_npu_kernels`; keys include M/K/N, projection kind, chunk ID. |
| Same file, `:1831`, `:1913`, `:2000` | `npuMatmul_zero`, `import_dma_buf_to_xdna`, `import_all_weights_to_xdna`. |
| `src/npu_matmul_func/npu_matmul_func.cpp` | `createHWctxt`, `createInstctxt`, `create_cmd_packet`; `.pdi`/instruction loading and driver interface. |
| `src/unified_llm_w4a16_hetero/helper.cpp` | Quantized safetensors/bin loaders, unpacking, `initialize_dummy_weights`. |
| `src/hipkernels/` | Packed W4A16 GEMM/GEMV, RoPE, RMSNorm, embedding, LM head, decode attention. |
| `src/microbenchmarks/tensor_parallel_gemm_npu_gpu_sweepN.cpp:401` | `run_split_once`, `prepare_point_state`: N partitioning and output assembly. K/M companion benchmarks and `test_layout_*` provide validation starting points. |
| `py/unified_llm_w4a16/_hetero_tune.py`, `_benchmark_heteroMosaic.py` | Existing tuning/benchmark automation; inspect before use, as they generate or rewrite configs/results. |

## Build and run (documented; NOT executed here)

The supported recipe is Linux/AMD-specific. README documents Ubuntu 24.04.4,
kernel 6.11.0-26, large GTT settings, ROCm 7.1.1 at `/opt/rocm-7.1.1`, AOCL,
XRT/XDNA packages, and driver source at
`$HOME_LIBS/xdna-driver-05-19-25` pinned to
`0e6d303b2cc2b3fe1cf10aba0acbf57a422588fb`. Use the README for prerequisite
installation details; none were installed or validated in this session.
HIP kernels target gfx11/wave32; README excludes CDNA wave64.

After prerequisites, the README sequence is:

```bash
# On the target Linux machine, from the repository root.
export HOME_LIBS="/path/to/your/libraries"
cd utils
source new_setup.sh
# Open a fresh terminal and return to the repository root.
export HOME_LIBS="/path/to/your/libraries"
source utils/setup.sh
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

`new_setup.sh` installs/removes system packages and recreates `rocmPytorch` in
its working directory; it is not a read-only environment check. Requirements
pin torch 2.10.0, torchvision 0.25.0, torchaudio 2.10.0 from the ROCm 7.1 index.
CMake finds active Python Torch first, then `$HOME_LIBS/libtorch_7.1.0`.
README requests CMake >=3.25; root CMake declares 3.18 and enables HIP. Follow
the README's >=3.25 requirement pending a real build; do not assume the setup
script enforces it. CMake selects gfx1151 for the recognized AI Max+ 395 CPU
name, otherwise gfx1100, unless `CMAKE_HIP_ARCHITECTURES` is supplied.

The extension lands in `build/py/unified_llm_w4a16/`; executables in `build/bin/`.
The frontend adds the extension directory to its import path.

```bash
# From repo root, in a configured Linux shell. Future execution only.
hf auth login  # if required for the chosen model/tokenizer
cd py/unified_llm_w4a16
python3 llama3_8b_w4a16_model.py \
  --config-path configs/configs_strixP_llama3_8b.json5 \
  --device cuda --text "What is the meaning of life?" \
  --max-new-tokens 32
```

Source-confirmed corrections/caveats:

- README's `configs_strixP_llama3.json5` does not exist; the file above does.
  Passing a nonexistent config can create a GPU-default file automatically.
- This Strix Point config currently says `"heterogeneity": "gpu"`; the command
  above is a GPU baseline. `--backend hetero` names the extension, not actual
  GPU-NPU execution. For a later heterogeneous run, use a separate config with
  `"heterogeneity": "hetero"`, appropriate shapes/chunks, and matching artifacts.
- The actual CLI model default is
  `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4`, unlike the README's
  unquantized model example. The tokenizer has a separate default. Running the
  frontend may download files and create packed caches. Dummy weights do not
  by themselves prevent tokenizer access.
- `--prompt-test` can update `prompt_len` in the selected config. Use copies for
  experiments. Exact config lookup/handles must be checked; fallback behavior
  differs by path and is not proof the NPU ran.
- No Windows or CPU-only end-to-end build/run has been verified. CLI accepting
  `--device cpu` is not evidence of a complete CPU-only model path.

## HeteroMega design (proposed, not implemented)

Use the GEMM convention above, independent of physical packed/transposed layout.
For device d and matching channel subset I_d:

```text
G_d = X W_gate[:, I_d]; U_d = X W_up[:, I_d]
H_d = SiLU(G_d) * U_d
Y_d = H_d W_down[I_d, :]
Y = Y_GPU + Y_NPU
```

Keep `H_d` partitioned through down projection: N-split first projections,
K-split final projection. Never sum gate/up partials after applying SiLU to a
K-split input: nonlinear activation makes that algebra incorrect.
For attention, assign complete GQA groups (4 Q heads per KV head in this Llama
configuration), partition Q/K/V outputs consistently, retain RoPE/cache/attention
within each branch, and sum matching O-projection contributions. The logical
boundary reduction need not be a distributed all-reduce; a shared-memory sum
is a candidate. Place residual/norm after reduction, initially on the GPU.

Reuse the frontend, model skeleton, quantization/layout helpers, HIP kernels,
XDNA sharing/launch infrastructure, N/K microbenchmarks, and baseline scheduler.
Add explicit sublayer partition metadata, reusable branch buffers, matching
weight slices, N-split model dispatch, branch-local consumers, and boundary
completion/reduction. Preserve the existing execution mode for comparisons.
Avoid rewriting the scheduler before the partitioned sublayer is validated.

## Feasibility gates and evaluation

1. **NPU kernels/toolchain:** the inspected tree supplies precompiled matmul
   artifacts, but no NPU attention or SiLU/multiply implementation or obvious
   regeneration pipeline. Establish access to kernel sources/compiler and
   valid artifact generation before promising full NPU-local sublayers.
2. **Shapes/layouts:** N-split gate/up and K-split down artifact directories exist
   for Llama-sized matrices, but compatible paired shapes, strides, instruction
   variants, and successful launches remain unverified. Existing K-split kernels
   may expect full-input strides rather than compact branch input. Packed tiles
   are 128x64 with quantization group size 128; runtime GEMV loading also requires
   positive `npuN` divisible by 2048. Head/group-aligned splits must satisfy actual
   backend constraints, not just the algebra.
3. **Attention:** support dynamic activation-by-activation matmuls, softmax,
   causal masks, RoPE scaling, growing KV length, and NPU-visible cache slices.
   Existing weight-only W4A16 linears do not establish these capabilities.
   With 8 KV groups, group ownership is discrete, not a continuous ratio.
4. **Synchronization/lifetime:** audit HIP-to-XDNA readiness, partial-output
   zeroing/completion, pointer registration/offsets, scratch reuse, and error
   propagation. Several model consumers use `future.wait()` without checking the
   returned status. Do not weaken dependencies to obtain apparent speedups.
5. **Measurement:** M splits need no explicit gather; quantify actual copies,
   allocation, reductions, host waits, NPU queue time, and DDR contention.
   Existing G1/A/G2 traces are coarse host timestamps. `trace_sync_stages=true`
   inserts device synchronizations; false does not give precise device completion
   times. Measure normal latency separately from intrusive profiling. Existing
   printed prefill time excludes token selection, so define TTFT explicitly.
6. **Fairness/correctness:** compare GPU-only, original HeteroMosaic, and the new
   path; add a controlled per-op-versus-persistent ablation with identical splits
   and chunk policy. Test prefill and decode independently, cache continuation,
   and fixed token counts (EOS can shorten `generate`). Calibrate BF16/W4A16
   tolerances against a reference; do not adopt the N/K sweep's 0.20/0.20
   tolerances as model-level acceptance criteria. Report numerical errors and
   later logits/perplexity alongside performance.

## First milestone and sequence

**M1 (recommended): one synthetic FFN partition contract and correctness harness.**
No model downloads or full decoder changes. Start with small group-aligned
dimensions and deterministic tensors; compare a full FFN against two unequal
channel branches, preserving each intermediate through down projection and
performing one final sum. Use CPU/GPU reference execution as available and label
it as emulation, not GPU-NPU performance. Include M=1 and M>1, mismatched gate/up
partition rejection, and at least two valid ratios. Agree numerical tolerances
before quantized tests. Acceptance: reference agreement, explicit shape/ownership
metadata, no concatenated hidden intermediate, and a documented NPU shape/layout
compatibility audit for the intended hardware follow-on.

Then: establish the Linux hardware baseline; port the single FFN branch path
using existing N/K kernels plus validated NPU elementwise support; instrument
assembly/waits and compare with per-op execution. Add GQA-group attention and
cache tests after the FFN path works. Finally integrate both sublayers, tune
separate ratios, restore/evaluate chunk scheduling, and measure end-to-end.
M1 alone neither proves NPU feasibility nor answers the performance hypothesis.

## Reference organization

Keep project-owned plans, progress, and a future final proposal in repository
`docs/` so they travel with code. Recommend a `docs/references.md` bibliography
with source links/versions and local-paper locations; keep bulky third-party
PDFs outside Git unless there is a specific archival/distribution reason.
No reference files were moved in this session.

Current local references, relative to this file:

- `../../Documents/CS 598 Proposal.pdf`: current scope; SHA256
  `7928a15b9c4a5d2e58c51a9bf8d2011cc78e4852cf42dbc260b78055449e1570`.
- `../../Documents/Megatron-LM.pdf`: Section 3 / Figure 3, paired projection
  partitioning and boundary reductions. Llama's SwiGLU/GQA adaptation is ours.
- `../../Documents/HeteroMosaic.pdf`: Sections 2 and 5, especially Figure 5 and
  Section 5.1; graph scheduling and M/K/N split tradeoffs. Its performance claims
  are paper results, not measurements reproduced in this checkout.
