# Adapting upstream execution into the persistent FFN partition

**Final result, October 28:** the selected native8/split-M32/preconvert-B
configuration with shared intermediate, imported HIP-owned output, P4352 and the
teammate GPU suffix completes the isolated M512/H4096/I14336 FFN in
**15.887/15.780 ms** in two reversed 100-sample blocks. Faithful native
HeteroMosaic completes the same blocks in **16.031/15.947 ms**. The candidate is
0.90%/1.05% faster; both blocks agree, but the margin is small and the
distributions overlap. Numerical deviations are retained under report policy.
See [the final DMA-BUF output report](../2026-10-27-dmabuf-output/README.md).

This report is being completed with hardware experiments on October 27, 2026.
All measurements use synthetic prefill FFN inputs, M512/H4096/I14336, on the
HX370/Radeon 890M/eight-column Strix system. They do not establish full-model
prefill or pretrained accuracy. Native HeteroMosaic stays unchanged and uses
explicit report policy, as requested; strict GPU and structural checks remain.

## Implemented experiments

**Code-confirmed:** the NPU still receives original 4,352-byte K128/N64 packed
weight tiles directly. No external NPU weight format or weight repacker was
introduced. Gate/up channel ownership persists through SiLU and multiplication,
and down computes the corresponding partial result before the GPU boundary sum.

- Row-major down-output DMA removes the CPU output permutation.
- A shared XRT BO connects SwiGLU output to down input. The producer completes
  before the consumer runs. There is no intermediate host read, write, or sync;
  this is shared DRAM, not on-chip residency across launches.
- Mapped final output avoids the BO.read copy. GPU staging and reduction remain
  included in ordinary timing.
- Native 8×8 A/C layouts remove the old 4×8 layout assembly from the matrix loop.
  BF16 partials round at each K128 boundary, following the related upstream
  strategy; this is an explicit arithmetic change, not a bit-preserving layout
  change. It enables larger reuse within tile SRAM.
- Runtime loops replace repeated identical graph bodies. DMA order and FIFO
  ownership stay fixed while compiled program memory is reduced.
- The teammate GPU adapter uses its merged gate/up projection and fused
  activation. The original GPU-only control is retained. The GPU suffix must
  still pass the original strict checks.
- The split-M32 experiment keeps one weight tile for M64, while two M32
  activation buffers allow prefetch. It removes the redundant BF16 up copy
  before SiLU and consumes local C directly.
- The independent preconvert-B experiment converts dequantized BF16 B into BFP
  scratch once and reuses it across M lanes. This conversion occurs on the NPU
  after the original packed buffer is consumed. It preserves BF16 dequantization
  rounding and the matrix instruction count.

All new graph, arithmetic and runtime choices are opt-in and recorded in cache
identities, manifests and execution metadata. Original native BF16 and BFP16
controls remain available. The source of the opaque native HeteroMosaic PDI has
not been proven to be the related TileFuse source; no such provenance is claimed.

## Intermediate measured results

These are exploratory results, not the final confirmation comparison.

| Variant | NPU channels | Median complete FFN, ms | Samples/mode |
| --- | ---: | ---: | ---: |
| Shared Z, mapped row-major Y, old FP32 partials | 2816 | 17.358 | 10 |
| Native8/BF16 partials, reuse4, original GPU | 2816 | 17.102 | 10 |
| Native8/reuse4, teammate GPU, ordinary block 0 | 3584 | 16.576 | 30 |
| Native8/reuse4, teammate GPU, ordinary block 1 | 3584 | 16.529 | 30 |
| Unchanged native HeteroMosaic, block 0 | — | 15.713 | 30 |
| Unchanged native HeteroMosaic, block 1 | — | 15.834 | 30 |
| Split-M32 prefetch, teammate GPU | 3584 | 16.058 | 10 |

The matched native8 comparison is still 4.4–5.5% slower than native. Exploratory
results from different processes are not paired causal ablations. GPU event
instrumentation is explicitly excluded from headline latency comparisons.

## Preserved failed attempts

The FP32-partial reuse4 build exceeded an up core's 64 KiB data memory by 512
bytes. Native8/BF16 partials resolved that data allocation limit, but the original
unrolled graph then overflowed program memory; runtime segment loops resolved
that separate failure. BFP preconversion initially used the wrong public MMUL
call form; the corrected API uses `aie::op_transpose` to mark already-transposed
block data, without another physical transpose. These failed logs are retained.

HIP registration of an XRT output mapping returned `invalid argument`. That path
is not a working GPU zero-copy result. The early native comparison also needed
an explicit path to the preserved driver headers after the notebook allocation
changed; the native library and driver were not modified.

## Final comparison and limits

The 100-sample paired result is in
[2026-10-27-dmabuf-output](../2026-10-27-dmabuf-output/README.md). The selected
configuration adds a shared SwiGLU/down intermediate, a GPU-owned DMA-BUF output
consumed directly by the GPU reduction, P4352, and the teammate GPU suffix. The
NPU branch is about 14.39 ms; a separate GPU-event diagnostic measured about
15.03 ms for the GPU suffix, making the GPU suffix the critical path. The
candidate and native both retain failed original numerical tolerances under
explicit report policy; structural checks pass. This is an isolated synthetic
FFN, not whole-model prefill/TTFT or pretrained accuracy.

The GPU-owned DMA-BUF input variant passed an H512/P512 correctness smoke but was
slower than host input staging (6.530 vs 5.431 ms), so it is not selected.
Preconvert-A was also slower (19.988 ms at P4352). The earlier 10-sample P4096/
P4352/P4608 sweep measured 15.879/15.432/16.080 ms; the 50-sample paired P4352
run was mixed, while the 100-sample confirmation favored the candidate in both
reversed blocks.
