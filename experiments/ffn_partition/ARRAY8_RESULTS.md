# Eight-column NPU FFN results — HX370

Measured 2026-10-18. **The NPU redesign is implemented and passes hardware
correctness.** At M512/H4096/I14336 with 512 NPU channels, a 50-iteration
confirmation measured **22.184 ms GPU-only versus 20.705 ms concurrent FFN**:
**1.071× speedup, or 6.67% lower latency**. The first 20-iteration run measured
22.198 versus 20.718 ms. This is a complete FFN microbenchmark gain; it does
not establish whole-model prefill, TTFT, or Max+ 395 performance.

**Power-mode limitation:** the runs below did not record NPU power mode.
A later query reports `default`; attempts to set `performance` were rejected
by the host. A fresh 50-sample run with `default` verified before and after
measured 22.208 versus 20.425 ms (1.0873×). See
[power evidence and per-device timing](POWER_TIMING.md) for that separate
run, launch diagnostics and GPU reduction timing. Do not assign the later
power reading retrospectively to these earlier measurements.

## What changed

The original NPU graph used one compute row per selected column. The default
now uses **eight physical columns × four rows = 32 workers**. Narrow N128
shards use two groups of four columns with different token rows, so all eight
columns remain active. Activations multicast horizontally; packed weights
multicast vertically; each worker reuses a dequantized weight tile across
up to two M16 blocks. FP32 accumulation, native BF16 multiplication and the
compact host ABI are preserved. See [the design](../../npu/ffn/ARRAY8.md).

The first build exposed the pinned DMA verifier's 512-element dimension
limit, despite its error saying 1023. The corrected quarter-chunk activation
schedule and memory-tile transpose compile and run; CPU permutation tests
verify the unchanged kernel layout. `--npu-design array8 --columns 8` is now
the default; `--npu-design legacy --columns 8` reproduces the original graph.
Neither the original graph nor existing hardware results were overwritten.

## Complete FFN measurements

All model-shaped runs use H4096/I14336, batch one, synthetic unsigned W4A16
weights with group128 and BF16 activations. Each mode uses the same canonical
weights and inputs. GPU-only means original HeteroMosaic GPU FFN kernels with
no NPU FFN offload. The two teammate PRs remain separate from this experiment;
keeping the GPU backend fixed isolates the NPU change.

Timing includes GPU-to-host staging, all four NPU launches, intermediate
readbacks/layout conversion, output staging, synchronization and GPU reduction.
Each row uses 20 samples per mode after two warmups, with randomized mode
order and alternating inputs. Values are medians in milliseconds.

| Prompt tokens M | NPU channels P | GPU-only | Concurrent FFN | NPU branch | Speedup vs GPU |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 512 | 5.821 | 12.102 | 11.335 | 0.481× |
| 128 | 2048 | 5.758 | 15.446 | 14.791 | 0.373× |
| 512 | 128 | 22.250 | 21.672 | 15.257 | 1.027× |
| 512 | 512 | 22.198 | 20.718 | 18.602 | 1.071× |
| 512 | 1024 | 22.249 | 23.884 | 22.375 | 0.932× |
| 512 | 2048 | 22.273 | 31.081 | 29.488 | 0.717× |
| 2048 | 512 | 89.159 | 88.644 | 38.660 | 1.006× |
| 2048 | 2048 | 87.806 | 89.351 | 84.129 | 0.983× |
| 4096 | 512 | 175.238 | 174.305 | 74.009 | 1.005× |
| 4096 | 2048 | 176.189 | 172.900 | 162.532 | 1.019× |

The best tested M512 allocation is P512 (3.57% of intermediate channels).
Its separate 50-sample run, after three warmups, confirms the same 1.071×
median ratio; concurrent beats its paired baseline in 49 of 50 iterations,
with improvement for both alternating inputs and both mode-order groups.
Larger allocations still make the NPU branch critical. At M128,
the tested allocations lose substantially; M2048/M4096 results are near parity,
with only a small 1.019× gain at M4096/P2048. Those small differences should not
be treated as a broad speedup claim. No single allocation is demonstrated to
improve every prompt length.

The observed M512 speedup exceeds a linear proportional-work estimate for a
3.57% offload. GPU slice shape/efficiency, cache behavior and clocks may also
contribute. No isolated GPU-suffix event measurement attributes that difference.

## Fresh legacy eight-column control

Both designs use the same eight-column setting and runtime environment.
Legacy has one compute row; array8 has four. Each configuration has its own
interleaved GPU-only control. Runs are sequential on a shared machine, so
cross-run ratios are descriptive rather than an isolated device-cycle result.

| P at M512 | Legacy NPU branch | Array8 NPU branch | Branch speedup | Legacy complete FFN | Array8 complete FFN |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 512 | 28.022 | 18.602 | 1.51× | 29.529 | 20.718 |
| 1024 | 46.358 | 22.375 | 2.07× | 47.910 | 23.884 |
| 2048 | 82.571 | 29.488 | 2.80× | 85.459 | 31.081 |

Legacy control GPU medians varied from 22.267 to 19.590 ms across allocations;
array8 M512 medians stayed around 22.2 ms. Use each run's own GPU baseline.
Earlier historical runs used different CPU thread settings and are not pooled
with these controls. All new runs set OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1.

## Remaining bottlenecks

At M512/P512, the initial run's NPU branch takes 18.602 ms. Summed projection
launch/wait intervals take 13.056 ms, SiLU launch/wait 1.303 ms, explicit BO I/O
outside dispatch 2.023 ms, and layouts 2.152 ms. Separate medians do not sum
exactly. Projection waits include DMA and runtime costs; they are not pure
matrix arithmetic. At P2048 they rise to 22.844 ms of a 29.488 ms branch.

The fixed-BO diagnostic compares repeated launches of one runner with cycling
through gate, up, SiLU and down. It uses no GPU, performs no timed input writes
or output readbacks, and validates exact output bits after each mode. Thirty
samples follow three warmups. Dispatch/wait medians are milliseconds:

| Stage | Repeated same context | Cyclic contexts | Ratio |
| --- | ---: | ---: | ---: |
| gate | 1.338 | 3.606 | 2.70× |
| up | 1.287 | 3.599 | 2.80× |
| silu_mul | 0.187 | 0.947 | 5.06× |
| down | 1.311 | 3.631 | 2.77× |

The cyclic host loop median is 11.838 ms. This establishes a large sensitivity
to launch/context sequencing; it does **not** isolate pure context-switch time.
Program state, caches, scheduling, clocks and fixed mode order can contribute.
Frozen stage inputs make this a dispatch diagnostic, not an FFN pipeline timing.

The next priority is to combine gate/up and pointwise work in one NPU program
and reduce context transitions, while retaining correct down-input ordering.
Host staging also matters: at M4096/P2048, layout conversions take 20.508 ms
and explicit BO I/O outside dispatch 22.174 ms. For small offloads on long
prompts, the final output-stage span largely waits for the GPU; it must not be
reported entirely as copy/reduction cost. Further C++ arithmetic tuning needs
separate dequantization/MMUL/stall measurements before assigning a compute or
DRAM-bandwidth bottleneck.

The schedule reduces logical weight shim payload by 8× and dequantization
calls by 2× at default R2, and activation shim payload by 8× for N widths
divisible by256. These are source-derived counts, not physical DRAM counters.
The complete FFN still uses four launches and host-staged intermediates;
there is no claim of full on-chip FFN residency or coherent GPU/XRT zero-copy.

## Validation and evidence

- 52 CPU tests pass: 26 NPU/packing/schedule tests and 26 experiment tests.
- Ten model-shaped array8 configurations, one repeated configuration, three
  fresh legacy controls and the small smoke test pass numerical validation.
- 939 timed complete-FFN invocations pass their fixed checks. Alternating,
  changed, repeated and all-zero inputs are checked; zero outputs are exact.
- 3,224 successful NPU dispatches are recorded by the FFN runs, plus 268 in
  the context diagnostic: **3,492 completed dispatches**. Every fixed weight
  is uploaded once per constructed branch. No CPU arithmetic fallback is used.
- Maximum recorded relative-L2 error among explicit FFN checks is 0.003589,
  below the unchanged 0.02 limit. These are synthetic bring-up thresholds,
  not model-accuracy validation.
- Kernel, graph and planner hashes in saved artifacts match the current
  sources. Every array8 projection manifest records eight columns, four rows
  and 32 workers. R4 remains unvalidated; the adapter selects at most R2.

Raw reports: [M128](results/array8_m128_h4096_i14336_hx370.json),
[M512](results/array8_m512_h4096_i14336_hx370.json),
[M2048](results/array8_m2048_h4096_i14336_hx370.json),
[M4096](results/array8_m4096_h4096_i14336_hx370.json),
[50-sample repeat](results/array8_repeat_m512_p512_hx370.json),
[legacy control](results/legacy8_control_m512_hx370.json),
[smoke](results/array8_smoke_hx370.json), and
[context diagnostic](results/context_m512_h4096_p512_array8.json).
[Derived analysis](results/array8_analysis.json) includes raw-report SHA256s;
[logs](results/logs) retain command output.

Hardware is Ryzen AI 9 HX370 / Radeon890M gfx1150 / NPU2, using the pinned
MLIR-AIE 7e00b579 toolchain, ROCm7.2, Torch2.11.0+rocm7.2 and NumPy1.26.4.
The notebook checkout is baseline61714a3 plus source overlays; local work is
on codex/ffn-partition-microbench. Source hashes, not the remote Git HEAD alone,
identify the tested changes. No model weights, drivers or shared runtime were
changed. This report preserves the measurements from the optimization turn;
publication and later measurements are tracked in `docs/progress.md`.

Reproduce from the initialized notebook terminal and prepared runtime:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/notebooks/heteromega-ffn-venv/bin/python -m experiments.ffn_partition.run \
  --m 512 --hidden 4096 --intermediate 14336 --npu-channels 512 \
  --columns 8 --npu-design array8 --warmup 3 --iterations 50 \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/array8_confirmation.json
/notebooks/heteromega-ffn-venv/bin/python -m experiments.ffn_partition.profile_contexts \
  --m 512 --hidden 4096 --npu-channels 512 --warmup 3 --iterations 30 \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/context_confirmation.json
```

See [the experiment README](README.md) for the ROCm environment setup and
numerical/timing contract. Change only `--npu-design legacy` for a legacy
control; keep weights, dimensions, environment and timing boundary fixed.
