# GPU-side suffix experiments

**Explored, October 28, 2026:** two GPU optimizations were tested against the
merged-NPU P6400 FFN. Neither improves the concurrent complete-FFN result. The
packed W4A16 teammate suffix remains selected.

Both experiments use the same M512/H4096/I14336 workload, P6400, 5 samples per
mode, and the merged single-dispatch NPU branch. The reference P6400 teammate
run is [13.867 ms concurrent](../2026-10-28-merged-npu/p6400_partition.json).
This is an isolated synthetic FFN comparison under report policy, not model
accuracy.

## 1. GEMM autotune

`HETEROMEGA_GPU_AUTOTUNE=1` recompiles the teammate GPU extension with
`AUTOTUNE=1`. The first call benchmarks the generic 128x128, K2048-special and
N64-general variants per packed shape and caches the winner.

| Shape | Generic | K2048-special | N64-general | Selected |
| --- | ---: | ---: | ---: | --- |
| gate/up K4096 M512 N15872 | **7.909 ms** | 8.885 ms | 9.084 ms | generic |
| down K7936 M512 N4096 | **3.980 ms** | 4.057 ms | 4.669 ms | generic |

The forced generic path was already optimal. The 5-sample complete FFN with
autotune on measured 14.517 ms versus the 13.867 ms teammate reference; the
difference is run variance, not a kernel change. Evidence:
[autotune log](autotune.log) and [report](autotune_p6400.json).
Default remains `AUTOTUNE=0`.

## 2. Pre-dequantized BF16 PyTorch suffix

`--gpu-variant torch_bf16` converts the complementary W4A16 suffix to contiguous
BF16 once (setup, excluded from timing) and runs three PyTorch BF16 matmuls plus
BF16 SiLU*up. The GPU-only strict control is unchanged.

| Suffix | Serialized GPU+NPU | Concurrent complete FFN |
| --- | ---: | ---: |
| Teammate packed W4A16 | 26.39 ms | **13.867 ms** |
| PyTorch BF16 pre-dequantized | **24.07 ms** | 14.805 ms |

The BF16 suffix is **2.3 ms faster in isolation** but **0.94 ms slower under
concurrent NPU execution**. Its BF16 weight traffic is about 4x the packed
W4A16 traffic, so it contends more with the NPU and the complete FFN loses.
Evidence: [torch BF16 report](torch_bf16_p6400.json). Default remains the
teammate packed suffix.

## Interpretation

The concurrent GPU suffix is not helped by simply using a faster-in-isolation
matmul. The packed W4A16 path's lower memory traffic matters when the NPU is
active. The remaining GPU lever is role specialization: move more gate/up to
the NPU (merged gate/up is efficient) while keeping **down on the GPU**, passing
the gate/up prefix Z across devices. That requires a gate/up-only merged NPU
graph and a GPU down with an external Z buffer. The current gate/up planner's
P<=8192 local-N cap limits the how far that split can go; extending it or
splitting the gate/up phase is a prerequisite for a larger win.

The role-specialized follow-up was then implemented and rejected: P8192 NPU
gate/up-only + GPU full down measured 19.191 ms (torch BF16) or 21.588 ms
(packed) versus 13.867 ms for the merged P6400 split. See
[2026-10-28-split-z](../2026-10-28-split-z/README.md). A packed-GEMM M-reuse-2
kernel was also correct but slower (15.055 versus 13.867 ms); see
[2026-10-28-gpu-mreuse](../2026-10-28-gpu-mreuse/README.md).

The present P6400 channel split therefore remains the selected configuration.
No production default was changed: autotune is opt-in
(`HETEROMEGA_GPU_AUTOTUNE=1`), and `torch_bf16` is an explicit CLI choice.
