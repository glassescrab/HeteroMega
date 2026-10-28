# Fused gate/up epilogue activation: rejected

**Tried, October 28, 2026:** the packed gate/up GEMM epilogue now computes
`SiLU(gate) * up` directly into the activation buffer, eliminating the separate
`silu_mul` kernel and the `[M, 2N]` gate/up global roundtrip. It is correct but
slower.

Measured on the merged P6400 FFN, 2 warmups + 5 samples per mode:

| GPU path | Concurrent FFN | Serial GPU+NPU | GPU-only control |
| --- | ---: | ---: | ---: |
| Separate gate/up + `silu_mul` | **13.867 ms** | 26.391 ms | 22.458 ms |
| Fused epilogue | 14.870 ms | 26.738 ms | 22.337 ms |

The fused path is **7.2% slower concurrent** and 1.3% slower serialized. Its
activation is **bit-exact** to the separate `silu_mul` path
([debug report](debug_epilogue.json): `exact: true`, zero mismatches), so this is
a performance rejection, not a numerical one.

## Why it loses

- The epilogue performs the `expf` and shared-memory gate/up pair reads inside
  each GEMM block's tail, serializing work that the standalone `silu_mul` did
  efficiently with vectorized `load8`/`store8`.
- Although the fused path removes the gate/up global write and activation read,
  that bandwidth saving is smaller than the lost epilogue efficiency.
- The existing separate activation kernel remains the better schedule.

## Scope and defaults

The fused epilogue is gated by `HETEROMEGA_GPU_FUSE_ACT=1`; default is 0, which
keeps the separate gate/up + `silu_mul` schedule. The new `linear` binding flag
defaults to false. No production default changed. The selected merged P6400
result remains [13.867 ms](../2026-10-28-merged-npu/README.md).

Further GPU work needs a different MMA/dequant schedule; epilogue fusion and
M-tile reuse have both been rejected.
