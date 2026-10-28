# GPU M-reuse kernel experiment: rejected

**Tried, October 28, 2026:** a packed W4A16 GEMM variant computes **two 128-row
M tiles per block** (256x128 output, 512 threads) so each dequantized 128x128
weight tile is reused across twice as many rows. It is correct but slower.

Measured on the merged P6400 FFN, 2 warmups + 5 samples per mode:

| GPU kernel | Concurrent FFN | Serial GPU+NPU | GPU-only control |
| --- | ---: | ---: | ---: |
| Generic 128x128, 256 threads | **13.867 ms** | 26.391 ms | 22.458 ms |
| M-reuse 2, 256x128, 512 threads | 15.055 ms | 27.197 ms | 22.307 ms |

The M-reuse kernel is **8.6% slower concurrent** and 3.1% slower serialized.
The GPU partial strict checks pass; this is a performance rejection, not a
correctness change.

## Why it loses

- The M-reuse block halves weight dequantization but uses 512 threads and keeps
  the same ~43 KiB shared-memory footprint. Occupancy drops, and the extra warps
  do not recover the lost block-level parallelism.
- The A loads and synchronization double per block; the smaller grid and larger
  block make the shared-memory pipeline less effective.
- The existing 128x128/256-thread generic kernel remains the best tested
  packed-GEMM schedule on this iGPU.

## Scope and defaults

The variant is gated by `HETEROMEGA_GPU_MREUSE=2`; the default is 1, which keeps
the original generic kernel. The C++ template is dormant unless the flag is set.
No production default changed. Evidence and source are in this directory; the
selected merged P6400 result remains [13.867 ms](../2026-10-28-merged-npu/README.md).

Further GPU work needs a different microkernel direction (for example an
epilogue-fused SiLU/multiply or a lower-level MMA schedule), not a simple
M-tile reuse factor.
