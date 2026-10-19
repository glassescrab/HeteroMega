# Complete-FFN partition measurements — 2026-10-18

For the subsequent eight-column/four-row redesign, see [ARRAY8_RESULTS.md](ARRAY8_RESULTS.md).
The measurements below preserve the original one-row NPU graph.

**No GPU–NPU allocation tested here demonstrated complete-FFN acceleration
over the original HeteroMosaic GPU FFN.** All ten model-shaped configurations
passed the implemented numerical checks. The closest result was M512 with
128 NPU channels and four columns: 27.192 ms concurrent versus 27.178 ms
GPU-only, an effectively tied result within the observed variation.

Concurrent execution was faster than executing the same two branches serially,
by 1.15–1.94× in median wall time. That control demonstrates a benefit from
allowing concurrency in this implementation; it does not establish an advantage
over the GPU-only baseline.

## Workload, machine, and timing

- AMD Ryzen AI 9 HX370, Radeon 890M (`gfx1150`), Strix NPU. These are **not**
  measurements of Ryzen AI Max+ 395.
- Linux `6.17.0-42-generic`, Python `3.12.3`, NumPy `1.26.4`,
  Torch `2.11.0+rocm7.2`, HIP `7.2.26015`, ROCm `/opt/rocm-7.2.0`.
  The notebook uses its preinstalled XRT and pinned MLIR-AIE/IRON revision
  `7e00b57955e108fe9d8e9419f5828a0c7e650858`.
- Bias-free SwiGLU with hidden width H4096 and intermediate width I14336;
  M is the number of prefill token rows. Weights are synthetic unsigned W4A16,
  group size 128, seed `12832`. Both devices and all allocations use slices
  of the same canonical weights and metadata. Input seed is `12833`.
  No checkpoint or complete model was loaded.
- Gate/up outputs, SiLU, multiplication, down partials, and the final sum have
  the BF16 boundaries specified in [README.md](README.md). Projection
  accumulation is FP32. The NPU owns the first P intermediate channels.
- Each allocation has **20 measured samples per mode after three warmups**.
  Baseline, serial, and concurrent modes are randomly interleaved with a
  reproducible order, alternating two inputs. Correctness is checked outside
  the timer after every warmup and measured invocation.
- The wall timer runs from a ready GPU-resident BF16 input to a completed
  GPU-resident BF16 output. It includes dynamic CPU staging allocations,
  layout conversions, GPU/host transfers, XRT BO I/O, all launches and waits,
  and the final GPU sum. Compilation, one-time setup allocations, fixed-weight
  packing/upload, CPU references, and validation readback are excluded.

The GPU baseline compiles the unchanged original
[`w4a16_gemm_packed.cu`](../../src/hipkernels/w4a16_gemm_packed.cu), followed by
separate BF16 SiLU and multiplication. The teammate's GPU PR #1 (`1b0023b`)
and evaluation PR #2 (`71c95d8`) were identified after these runs; neither is
part of these measurements. See [the PR-aware bottleneck analysis](BOTTLENECKS.md).
This is a complete
**FFN microbenchmark**, not a complete HeteroMosaic model/scheduler run,
end-to-end prefill latency, or TTFT measurement. Normalization, attention,
residual addition, and interference with other prompt chunks are excluded.

## All model-shaped results

Times are milliseconds, shown as **median [p10, p90]**. Percentiles describe
the observed samples, not confidence intervals. Each row has its own interleaved
GPU baseline. Speedup is that baseline median divided by concurrent median;
values below 1 mean slower than GPU-only. Columns is the requested maximum.

| M | Columns | P NPU channels | GPU baseline | Serial partition | Concurrent partition | Speedup |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 4 | 128 | 6.552 [6.274, 6.911] | 13.929 [13.202, 14.903] | 7.393 [6.915, 8.055] | 0.886× |
| 128 | 4 | 512 | 6.737 [6.201, 6.877] | 20.510 [20.149, 20.862] | 14.218 [13.578, 14.456] | 0.474× |
| 128 | 4 | 2048 | 6.833 [6.226, 7.106] | 46.971 [46.486, 47.998] | 40.584 [39.488, 42.073] | 0.168× |
| 512 | 4 | 128 | 27.178 [26.679, 27.411] | 44.591 [43.508, 45.037] | 27.192 [26.831, 27.629] | 0.999× |
| 512 | 4 | 512 | 27.441 [26.893, 63.625] | 71.774 [71.196, 100.014] | 44.424 [43.350, 67.815] | 0.618× |
| 512 | 4 | 2048 | 27.154 [26.709, 27.466] | 174.435 [173.090, 176.226] | 151.399 [150.934, 153.023] | 0.179× |
| 512 | 8 | 128 | 27.096 [26.831, 27.333] | 42.789 [42.094, 43.679] | 27.358 [27.166, 27.552] | 0.990× |
| 512 | 8 | 256 | 27.309 [26.672, 59.740] | 45.904 [44.709, 74.236] | 27.619 [27.156, 69.094] | 0.989× |
| 512 | 8 | 512 | 27.359 [26.930, 74.100] | 54.279 [53.053, 82.385] | 28.048 [27.124, 67.802] | 0.975× |
| 512 | 8 | 1024 | 27.455 [26.868, 82.473] | 73.642 [71.201, 104.980] | 45.687 [44.739, 55.236] | 0.601× |

For the eight-column/P128 case, gate/up actually use four columns because P128
contains only four N32 tiles. Down and SiLU use eight columns. The other
eight-column cases use eight columns for all stages. P128, P256, P512, P1024,
and P2048 represent 0.893%, 1.786%, 3.571%, 7.143%, and 14.286% of I14336.

Raw evidence, including all samples and artifact manifests:

- [M128, four columns](results/ffn_m128_h4096_i14336_hx370.json).
- [M512, four columns](results/ffn_m512_h4096_i14336_hx370.json).
- [M512, maximum eight columns](results/ffn_m512_h4096_i14336_c8_hx370.json).
- [Machine-readable summary](results/summary.csv).

Shared-host variability is visible and retained. In M512/four-column/P512,
iterations 14–19 slow down across baseline and partitioned modes; the baseline
reaches 82.431 ms. Several eight-column runs also have broad upper tails.
No clock, power, temperature, or external-load measurements identify the cause.
Warmups and interleaving reduce some biases but do not establish statistical
significance or eliminate common disturbances. In particular, the 14 µs median
gap for M512/four-column/P128 is far too small to interpret as a meaningful
difference. No samples were removed to obtain these tables.

## What limits the current implementation

The NPU branch preserves logical channel ownership but stages intermediate
activations through host memory between four launches: gate, up, fused
SiLU/multiply, and down. Weights stay in their XRT BOs. This is not on-chip
persistence or GPU/XRT zero-copy sharing.

Representative medians from concurrent runs, in milliseconds:

| M / max columns / P | Complete NPU host branch | Gate with host I/O | Up with host I/O | Down with host I/O | SiLU with host I/O | C→A layout conversion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 512 / 4 / 128 | 16.340 | 4.614 | 4.032 | 4.236 | 0.756 | 0.040 |
| 512 / 4 / 512 | 42.346 | 13.380 | 12.804 | 12.919 | 0.855 | 0.076 |
| 512 / 4 / 2048 | 148.438 | 47.859 | 47.726 | 48.316 | 2.155 | 0.088 |
| 512 / 8 / 128 | 14.627 | 4.330 | 3.944 | 3.172 | 1.034 | 0.022 |
| 512 / 8 / 256 | 16.768 | 4.580 | 4.481 | 4.811 | 1.183 | 0.038 |
| 512 / 8 / 512 | 26.039 | 7.530 | 7.234 | 7.541 | 1.175 | 0.078 |
| 512 / 8 / 1024 | 43.686 | 13.473 | 13.246 | 13.229 | 1.318 | 0.058 |

The projection path dominates larger NPU allocations. The observed reduction
in P512 NPU branch time with eight columns is substantial, but its complete
FFN still does not beat GPU-only. Removing the small C→A permutation alone
would not close the larger gaps. These stage intervals include host I/O and
completion waits; they do not isolate arithmetic, NPU DMA, or hardware
utilization. Medians of individual stages need not sum to a median total.

For small allocations, the NPU can finish while GPU work remains outstanding.
For example, M512/four-column/P128 has a median 10.058 ms in the output-staging
and boundary-wait interval; this includes waiting for the GPU branch. It must
not be reported as 10.058 ms of transfer or reduction overhead. No per-device
hardware timeline or memory-bandwidth counter was collected.

## Correctness and compatibility evidence

The CPU suite has **20 passing tests**, covering paired weight/metadata slices,
asymmetric and endpoint allocations, exact native-layout conversion, numerical
metrics, GPU packing, staged NPU composition, and rejection of invalid readback
buffers. CPU tests do not replace hardware execution.

The three model-shaped reports contain **329 passing detailed comparisons**
and **600 checked timed invocations**. They validate both branches and the
combined FFN against CPU references and the original GPU baseline, including
changed input, zero input, and return to the first input. Every warmup is also
checked. The largest detailed maximum absolute error is `0.03125`; the largest
relative L2 error is `0.003654145`. Fixed limits are relative L2 `0.02` and
maximum absolute error `0.05 + 0.03*max(abs(reference))`; all-zero references
require exact-zero output. These synthetic checks do not establish model
accuracy or token/logit agreement.

Each of the ten allocations records **216 successful NPU dispatches**, for
2,160 across the model-shaped runs. This includes validation, warmup, and timed
calls, with four dispatches per NPU invocation. Recorded gate/up/down weight
upload counts remain exactly one throughout each allocation.

The [small synchronized diagnostic](results/diagnostic_small.json) passes all
15 stage/layout/combined checks. Native down output and the returned logical
matrix agree exactly, and the C→A permutation preserves SiLU output exactly.
NPU SiLU differs from the ideal BF16 reference by up to `0.0625`, with relative
L2 `0.002773046`, within the fixed limits. This diagnostic is correctness
evidence, not a performance run. The earlier
[small FFN smoke test](results/smoke_hx370.json) also passed but uses earlier
adapter/runner revisions and is excluded from the model-shaped timing table.

An initial [failed smoke test](results/failed_numpy25_smoke_hx370.json) exposed
a readback ABI incompatibility between the notebook's prebuilt `pyxrt` and
NumPy `2.5.4`: `BO.read` presented zero-stride byte arrays, corrupting interpreted
outputs despite successful NPU completion. Pinning the isolated runtime to
NumPy `1.26.4` restored valid contiguous byte arrays and passing stage/FFN
checks. The adapter now rejects malformed dtype, shape, or zero/negative-stride
readback before reinterpretation, with a regression test. No tolerance was
relaxed. The failed run is retained as rejected evidence. This fix does not
resolve or explain HeteroMosaic's separately documented original direct-DRM
random-W4A16 numerical discrepancy.

## Source provenance

All three model-shaped runs record identical experiment source hashes, verified
against the current local source files. The original GPU GEMM hash is
`bc5f0480bb322c9a76217ab0e4805bf6d8aea26156a6971e160af3901792575a`, matching
both baseline commit `61714a3147f34857aa5dfef21a28e762777a2df0` and the inspected
`origin/main`. The NPU projection C++ hash is
`090e87845395f730b580be537c7da5f11c0f53eaee110b28786e362cdfd32ba2`; SiLU C++ is
`1863c3ab0cb4be00c0ced57223d172da2706969d1329d7785e9a78c4dea167fc`.
Full graph, adapter, binary, and instruction identities are in the JSON files.

The measured remote checkout reports old HEAD `61714a3`, branch
`codex/npu-ffn-mlir-aie`, and untracked source overlays. That Git HEAD alone
does not identify the experiment; use the recorded hashes and dirty status.
Do not substitute the local integration branch HEAD for remote run provenance.

## Reproduction

Start in the notebook's initialized IRON terminal so its `PYTHONPATH` exposes
`pyxrt`; activate the isolated ROCm runtime and run from `/notebooks/HeteroMega`:

```bash
source /notebooks/heteromega-ffn-venv/bin/activate
export HETEROMEGA_ROCM_PATH=/opt/rocm-7.2.0
export ROCM_HOME=/opt/rocm-7.2.0 ROCM_PATH=/opt/rocm-7.2.0
export LD_LIBRARY_PATH=/opt/rocm-7.2.0/lib:/opt/xilinx/xrt/lib:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=4
export MAX_JOBS=2
python -c 'import torch, numpy, pyxrt; print(torch.__version__, numpy.__version__)'
```

The printed versions must include Torch `2.11.0+rocm7.2` and NumPy `1.26.4`.
Use the [setup notes](README.md#running-on-the-amd-notebook) if the runtime is
not prepared. The three measured configurations were:

```bash
python -m experiments.ffn_partition.run \
  --m 128 --hidden 4096 --intermediate 14336 --npu-channels 128,512,2048 \
  --columns 4 --warmup 3 --iterations 20 --seed 12832 \
  --artifact-root experiments/ffn_partition/artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/ffn_m128_h4096_i14336_hx370.json

python -m experiments.ffn_partition.run \
  --m 512 --hidden 4096 --intermediate 14336 --npu-channels 128,512,2048 \
  --columns 4 --warmup 3 --iterations 20 --seed 12832 \
  --artifact-root experiments/ffn_partition/artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/ffn_m512_h4096_i14336_hx370.json

python -m experiments.ffn_partition.run \
  --m 512 --hidden 4096 --intermediate 14336 --npu-channels 128,256,512,1024 \
  --columns 8 --warmup 3 --iterations 20 --seed 12832 \
  --artifact-root experiments/ffn_partition/artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/ffn_m512_h4096_i14336_c8_hx370.json
```

The next performance work is to improve the NPU projection path and reduce
staging/launch costs, then repeat this complete-FFN comparison. Model integration
must preserve HeteroMosaic's attention and causal chunk schedule, validate real
outputs, and measure complete prefill before any end-to-end model acceleration
claim is justified.
