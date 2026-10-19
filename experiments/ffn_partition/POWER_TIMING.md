# NPU power check and FFN timing — HX370

Measured 2026-10-18 on Ryzen AI 9 HX370 / Radeon 890M / eight-column NPU2.
**The NPU reports `default`, not `performance`.** A fresh ordinary FFN run
measured **22.208 ms GPU-only versus 20.425 ms concurrent** at
M512/H4096/I14336/P512: **1.0873× speedup, or 8.03% lower latency**.
This remains a synthetic complete-FFN result, not whole-model prefill or TTFT.

## Power-mode evidence

`xrt-smi examine -d 0000:66:00.1 -r platform` reports eight columns and
`power_mode: default`. Attempts to configure `--pmode performance` failed
with `DRM_IOCTL_AMDXDNA_SET_STATE ... err=-13: Permission denied`, both as
UID 1003 and through sudo as UID 0. Performance mode was **not established**;
the precise host permission restriction was not diagnosed. No host driver
or kernel was changed.

The saved [attempt log](results/power/performance_attempt.txt) and
[initial query](results/power/before_mode_change.json) preserve the evidence.
Queries [before](results/power/default_before.json) and
[after](results/power/default_after.json) the ordinary run, and
[before](results/power/timeline_before.json) and
[after](results/power/timeline_after.json) the diagnostic, all report `default`.
These are boundary snapshots, not continuous clock/power measurements.
Electrical telemetry is unsupported in the returned platform report, so
power consumption, temperature and sustained clocks are not established.
Earlier [array8 results](ARRAY8_RESULTS.md) did not capture power mode and
must not be retrospectively labeled `default` or `performance` measurements.

## Ordinary complete-FFN comparison

The [new raw report](results/array8_default_m512_p512_hx370.json) uses the
unchanged ordinary runner, 50 samples per mode after three excluded warmups,
randomized mode order, and alternating inputs. All modes use the same seeded
synthetic unsigned W4A16 weights, group size 128 and BF16 activations.
CPU thread settings are OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1.

| Mode | Median ms | p10–p90 ms |
| --- | ---: | ---: |
| Original HeteroMosaic GPU FFN, no FFN offload | 22.208 | 21.905–22.523 |
| Concurrent GPU–NPU FFN | 20.425 | 19.965–21.176 |
| Same partition, serialized branches | 40.295 | 39.800–41.374 |

Concurrent latency is lower than its paired GPU control in all 50 iterations.
The concurrent NPU branch host-wall median is 18.220 ms; input staging is
0.256 ms, and output staging plus the boundary wait is 1.297 ms. These
individual medians are not additive. The full boundary runs from ready GPU
input to synchronized GPU output and includes staging, layouts, all four
NPU launches, waits and GPU reduction. Compilation, fixed-weight preparation,
and correctness readback are excluded. This run is a new observation on a
shared host, not evidence that changing power mode caused the difference
from the earlier 1.071× result.

All 150 timed invocations pass the fixed correctness gates. Changed, repeated
and zero inputs and both branch partials are checked separately; the run
records 456 successful NPU dispatches, including checks and warmups. Each
gate/up/down weight is uploaded once per constructed branch.

## Partition, kernels and reduction

**Code-confirmed:** the NPU owns intermediate channels `[0,512)` (3.57%);
the GPU owns `[512,14336)` (96.43%). Gate and up use matching N slices;
SiLU and multiply retain those channels; down consumes the matching K slice.
Each device produces an `[M,H]` partial. There is no full intermediate
concatenation. The GPU performs the final BF16 `torch.add` after waiting
for its own branch and the transferred NPU partial.

The GPU uses the unchanged `w4a16_gemm_fused_packed` dispatcher in
`src/hipkernels/w4a16_gemm_packed.cu` for three projections, plus separate
Torch BF16 SiLU and multiply operations. These are the original HeteroMosaic
kernels; teammate PR kernels are not integrated into these measurements.
The NPU launches gate, up, fused SiLU/multiply, and down through four XRT
contexts. Projections use `w4a16_prefill_reuse.py/.cc`, native BF16 MMUL with
FP32 accumulation, eight columns × four rows, multicast and up to two M16
tiles of weight reuse. Pointwise work uses `silu_mul.py/.cc` across eight
columns. Intermediates still cross host BO boundaries; the CPU permutes the
down input. Logical channel ownership does not imply on-chip FFN residency.

## Instrumented timing diagnostic

The separate [diagnostic report](results/timeline_m512_p512_array8.json)
contains 30 samples after three warmups. `profile_timeline.py` preserves the
operation order and mandatory input/final waits, adding HIP events and host
submission probes without per-stage GPU synchronization. Its wall median is
**20.925 ms**. Instrumentation can affect scheduling, so use the ordinary run
above for the speedup comparison.

GPU event spans and host API-call intervals have different meanings:

| GPU operation | HIP event median ms | CPU submission median µs |
| --- | ---: | ---: |
| Gate projection | 7.057 | 25.505 |
| Up projection | 6.247 | 2.965 |
| SiLU | 0.307 | 41.479 |
| Multiply | 0.445 | 18.295 |
| Down projection | 6.119 | 2.790 |
| Input GPU→host copy | 0.241 | 24.220 |
| NPU result host→GPU copy | 0.193 | 92.714 |
| GPU boundary reduction | 0.133 | 57.324 |

The entire GPU branch event median is **20.188 ms**. Host enqueue of the
branch, including event recording, is 174.247 µs. Event spans include device
scheduling, event overhead and possible submission gaps; they are not pure
arithmetic cycles. Submission intervals include Python/C++ runtime work and
must not be described as driver-only launch overhead. The reduction event
starts after both dependencies, so its 0.133 ms excludes waiting for them.

| NPU stage | CPU submission median µs | CPU wait median ms | Stage including host BO I/O median ms |
| --- | ---: | ---: | ---: |
| Gate projection | 93.808 | 4.359 | 5.007 |
| Up projection | 140.373 | 4.066 | 4.874 |
| Fused SiLU/multiply | 145.173 | 1.150 | 1.551 |
| Down projection | 65.249 | 4.127 | 5.015 |

NPU waits are host `wait(10000)` intervals, including scheduling, DMA and
execution effects; no NPU device-cycle timer is available here. The whole
NPU call, including input validation, has a 19.075 ms host median. CPU input,
down-input and output layout medians are 0.853, 0.091 and 0.905 ms. The final
output-stage host span is 1.072 ms and includes remaining GPU completion
waiting as well as staging and reduction; it is not a copy-only metric.

GPU events share one device clock; CPU and NPU-host offsets use
`perf_counter_ns` and are not calibrated to that clock. Do not overlay them
as an exact physical GPU/NPU execution timeline. Independent stage medians
also cannot reconstruct one invocation. All 30 diagnostic samples and 49
recorded correctness checks pass; 148 NPU dispatches complete. Maximum
explicit relative-L2 error is 0.003476 under the unchanged 0.02 limit.

**Measured implication:** matrix projections dominate GPU event time and
NPU host waits. The GPU boundary sum is a small event span in this diagnostic.
Launch/context sequencing and staged intermediates remain optimization
targets, but these measurements do not isolate pure context-switch cost,
physical shared-memory bandwidth, or attention interference. The next step
is to reduce NPU context transitions and staging, then retest complete FFN
latency and integrate with the existing prefill schedule. Performance-mode
comparison requires a host environment that permits and verifies the mode.

## Reproduction

Use the prepared runtime and ROCm environment in [README.md](README.md).
Query power mode immediately before and after each command, saving distinct
JSON files. The PCI address below is specific to this notebook:

```bash
/opt/xilinx/xrt/bin/xrt-smi examine -d 0000:66:00.1 -r platform \
  -f JSON -o /notebooks/power_before.json
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/notebooks/heteromega-ffn-venv/bin/python -m experiments.ffn_partition.run \
  --m 512 --hidden 4096 --intermediate 14336 --npu-channels 512 \
  --columns 8 --npu-design array8 --warmup 3 --iterations 50 \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/default_confirmation.json
/opt/xilinx/xrt/bin/xrt-smi examine -d 0000:66:00.1 -r platform \
  -f JSON -o /notebooks/power_after.json
```

For a separate instrumented run, use the same shape/options with module
`experiments.ffn_partition.profile_timeline`, `--iterations 30`, and a distinct
output JSON. Save a new pair of power queries around that diagnostic.
