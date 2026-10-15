# GPU/NPU kernel handoff

Updated 2026-10-15. This is the entry point for teammates developing kernels.
Starting upstream source: `61714a3147f34857aa5dfef21a28e762777a2df0`.
Runtime port commit: `20e4d3052ac21d95ae03f70ad916fab6c75de632`.
The repository now includes the tested experimental runtime compatibility port,
project plans, cloud reproduction instructions, profiling helpers and evidence.
No persistent FFN implementation or new GPU/NPU math kernel has been added.

## Read and reproduce

1. Read the [current scope](../agent.md) and [session rules](../AGENTS.md).
   The target is FFN prefill; attention stays on its existing path.
2. Follow [cloud-baseline.md](cloud-baseline.md) for the observed environment,
   build commands, model revision, input and GPU baseline. Then read
   [runtime-compatibility.md](runtime-compatibility.md) for the NPU port,
   required artifacts, validation commands and known failures.
3. Read the [profiling report](profiling-2026-10-14.md) and its
   [reproduction instructions](runs/2026-10-14-profile/README.md).
   Saved configs/results and diagnostic traces are in that run's `evidence/`.

Commands in these guides run on the Linux AUP host, not the Windows workspace.
The tested cloud source is `/notebooks/HeteroMosaic-baseline`, with its isolated
venv at `/notebooks/heteromosaic-venv`. It uses ROCm 7.2, Torch 2.11, Strix Point
`gfx1150` GPU and `aie2p` NPU. Cloud-specific CMake/Torch adaptations are saved
under `runs/2026-10-12-aup/`; they are not changes to the repository's CMake files.
An updated clone already contains the four runtime fixes: do not apply
`runtime-compat.patch` again. A historical checkout at the starting commit needs
that patch as well as the documented cloud build adaptations.

The cloud working tree contains tested local adaptations: do not blindly pull,
reset or overwrite it. Compare its diff with the saved patches first. Do not
copy credentials into Git; each teammate needs their own authorized cloud access.
Model weights and sibling `Documents/` references are outside this handoff.

## Code-confirmed integration points

| Area | Location and role |
| --- | --- |
| Model and weights | `py/unified_llm_w4a16/llama3_8b_w4a16_model.py`: frontend, model loading and CLI |
| Llama FFN and schedule | `src/unified_llm_w4a16_hetero/unified_llm_w4a16.cpp`: `forward_llama3_with_scratch`, projection dispatch and `generate`; gate/up futures complete before in-place `torch::silu_` and multiply, then down and residual |
| Existing operator partitions | `src/unified_llm_w4a16_hetero/hetero_compute.cpp`: `hetero_matmul_out_gemm_packed_M` and `_K`; M-split writes disjoint rows of a shared output, without an obligatory concatenation |
| GPU kernels | `src/hipkernels/`: packed W4A16 GEMM/GEMV and supporting layout kernels |
| NPU launch/configuration | `src/unified_llm_w4a16_hetero/npuSetup.cpp`: `get_split_type`, configuration selection, imported buffers and `npuMatmul_zero` |
| Direct XDNA runtime | `src/npu_matmul_func/` and `include/npu_matmul_func/`: hardware contexts, packets, unique residency handles and completion waits |
| NPU artifacts | `hw_bins/npu2/`: shape-specific precompiled artifacts; selected decode paths need `_K_8c` folders, not only `_K` |
| Split experiments | `src/microbenchmarks/tensor_parallel_gemm_npu_gpu_sweep{M,K,N}.cpp`; these do not preserve partitions across an FFN |

The runtime port changes heap mapping alignment, zeroed/padded configuration
storage, duplicate residency handles and legacy-wait fallback to DRM timeline
waits. It preserves the original math kernels, model computation and scheduling.
Keep these fixes when testing kernels on this cloud; they do not establish
general driver-version compatibility.

## Measured findings and open correctness gate

The October 14 workload uses Llama 3.1 8B AWQ INT4 weights, 32 layers, a fixed
1024-token input and eight greedy output tokens. Five timed calls follow one
excluded warmup for each normal-latency configuration.

- Matched GPU prefill median: **1780.2 ms**; heterogeneous serial: **1327.3 ms**.
  Two inflight chunks: **1316.6 ms**. These are conditional measurements on the
  experimental port; they are not validated accuracy/performance results.
- Synchronized heterogeneous prefill diagnostic: gate/up **437.1 ms**, down
  **422.2 ms**, SiLU/gating **49.4 ms**, FFN norm **9.0 ms**. The complete FFN
  accounts for **68.4%** of prefill. Down prefill is currently GPU-only.
- All 20 normal timed calls matched the fixed GPU output token IDs. NPU ioctl
  evidence confirms submissions and successful timeline completion.
- **Random packed-W4A16 tests still fail.** The first original sweep case has
  maximum GPU/NPU difference 1.5; an independent float product using the existing
  dequantization helper shows substantially larger NPU error. Constant exactly
  representable inputs/weights pass all eight tested row splits. Investigate
  packing, signed inputs, scale/zero metadata and arithmetic; the cause is open.
  Matching eight output IDs does not settle model accuracy. Do not loosen
  tolerances to make the discrepancy disappear.
- Existing down-decode configuration falls back, and Q decode uses CPU channels.
  Do not present decode as a pure GPU/NPU comparison. Host readiness/queue/wait
  sums overlap and are not additive stage latency or device utilization.

## Proposed kernel milestone

First resolve or precisely characterize the numerical discrepancy with a
controlled packed-matmul reference, including signed inputs and nonuniform
weights/scales/zeros. Preserve failing examples and state the numerical contract.
Then isolate one FFN with **M=512, hidden K=4096, intermediate I=14336** before
changing the model execution path.

For the first persistent-channel feasibility case, consider **4096 NPU / 10240
GPU intermediate channels**. Matching gate/up branches feed local SiLU and
multiply; down consumes the corresponding K slices and partial outputs are
summed once at the FFN boundary. The NPU branch's gate/up/down shapes would all
be 512x4096x4096, drawing on an already staged artifact family. This is a
proposal, not a validated layout, kernel or optimal ratio.

Agree on the branch contract before integration: logical M/K/N dimensions,
packed weight and quantization metadata layout, activation dtype/strides,
buffer ownership/lifetime, producer readiness and completion signaling.
Preserving channels does not imply retaining data in NPU on-chip memory.
Existing artifacts do not establish NPU-local SiLU/gating support or direct
consumption of a compact down-input slice; investigate both. Record any GPU
elementwise fallback and its transition cost explicitly.

Acceptance should include reference agreement at justified tolerances, unequal
channel ownership, correct boundary sum/residual handling, and repeated buffer
reuse with alternating inputs. Measure complete FFN latency, setup/repacking
cost and extra memory. Compare down placement separately from persistence with
the same splits and chunk schedule, then test interference with attention.
Persistent token-row ownership remains a useful challenger because it avoids
the channel split's boundary sum. Keep the baseline available throughout.
