# Prefill GPU–NPU FFN partition experiment

This microbenchmark measures the complete bias-free SwiGLU FFN from a ready
GPU input to a ready GPU output. It compares the original HeteroMosaic GPU
FFN with a channel-partitioned GPU–NPU implementation and a serialized control.
The purpose is to establish whether an unequal NPU allocation reduces actual
FFN wall-clock latency after staging, synchronization, and reduction costs.
The [legacy results](RESULTS.md) cover the original one-row NPU graph.
The default now uses the [eight-column, four-row design](../../npu/ffn/ARRAY8.md);
its [measured results](ARRAY8_RESULTS.md) are recorded separately to preserve
the original controls. A later 50-sample M512/P512 run measured 1.0873x
complete-FFN speedup on HX370 with NPU mode `default` verified before and
after. Performance-mode configuration was rejected by the host. See
[power checks and device/launch timing](POWER_TIMING.md); other prompt
lengths and allocations have important limits.

The opt-in combined gate/up projection and denser ratio sweep are documented
in [fusion results and operation graphs](FUSION_RESULTS.md). The separate
projection path remains available as the default comparison.

`--fuse-swiglu` extends that fusion through SiLU and multiplication, keeping
gate/up intermediates in adjacent NPU tile memory. It uses two NPU launches:
SwiGLU, then down. See the [architecture](../../npu/ffn/SWIGLU.md) and
[hardware validation and latency comparison](SWIGLU_RESULTS.md).

For the measured `M512/H4096/I14336` workload, the three-launch
`--fuse-gate-up` control has a competitive P768–896 region. The newer
two-launch path's working candidate is `--fuse-swiglu --npu-channels 1152`;
retain P1024 as a close alternative. A 50-sample confirmation measured
19.643 ms versus 22.293 ms GPU-only (1.1349x) on HX370 in `default` mode.
Fresh controls, stage graphs and the separate repeat are in
[SWIGLU_RESULTS.md](SWIGLU_RESULTS.md). Other prompt lengths and the actual
model schedule need retuning; these measurements do not establish a global
optimum.

This is **prefill only**. It does not execute attention, normalization, residual
addition, an entire decoder layer, or model inference. FFN latency here is not
end-to-end prefill latency or time to first token.

## Computation and comparison paths

For input `X[M,H]`, gate/up weights have shape `[I,H]` and down weights have
shape `[H,I]`. The NPU owns the prefix of `P` intermediate channels; the GPU
owns `[P,I)`. Both devices compute matching gate/up channel slices, local
SiLU and multiplication, and a down projection over those same channels.
The two `[M,H]` down partials are summed once on the GPU.

| Path | FFN execution | Purpose |
| --- | --- | --- |
| GPU baseline, `P=0` | Full gate/up, SiLU/multiply, and down on the GPU | HeteroMosaic FFN without NPU offload |
| Concurrent partition, `0<P<I` | GPU branch enqueued while the NPU branch executes, followed by completion and reduction | Measured heterogeneous FFN latency |
| Serialized partition, same `P` | Same branch kernels and data handling with branch execution serialized | Control for the effect of allowing concurrent work |

The GPU adapter builds the existing
[`w4a16_gemm_packed.cu`](../../src/hipkernels/w4a16_gemm_packed.cu) source
unchanged, with separate BF16 SiLU and multiplication. It uses the full
intermediate width for the baseline and compact sliced weights/buffers for a
GPU partition. This is an isolated FFN built from HeteroMosaic's original GPU
kernels, not a run of its model scheduler.

The teammate's GPU PR #1 (`1b0023b`) and evaluation PR #2 (`71c95d8`) have now
been reviewed; they are not part of the saved hardware measurements. See
[the bottleneck and integration analysis](BOTTLENECKS.md). Preserve the original
GPU baseline when adding that implementation as another comparison.

## Timing boundary

Every timed invocation begins with the same BF16 input ready on the GPU and
ends only when its complete BF16 output is ready on that GPU.

Included in heterogeneous wall time:

- Input staging from GPU to host and the NPU's packed activation layout.
- Dynamic XRT BO writes, reads, and synchronization.
- All gate/up, SiLU/multiply, and down launches and completion waits.
- Intermediate layout conversion, NPU output staging back to GPU, and the
  final partial-output sum.
- GPU completion needed to make the result usable by a following layer.

Compilation, one-time setup allocations, weight generation, initial
packing/upload of fixed weights, input preparation, and correctness-reference
evaluation are setup costs outside the timer. Device buffers and fixed weights
are reused across invocations. CPU staging-buffer allocations performed during
an invocation are inside its timer. The NPU branch uploads fixed weights once
during preparation: three BOs normally, or two with combined gate/up.

Report measured complete-invocation samples and their median, p10, p90, and
range. A dispatch/wait interval is a host interval, not a hardware cycle count.
Never calculate concurrent latency as the maximum of separately measured branch
times. Allowing concurrency does not itself prove device overlap or acceleration.
Warmups are excluded from the reported timing samples. Fine-grained diagnostic
intervals must not be added together to reconstruct overlapping wall time.

## Current NPU path and its limits

By default each NPU FFN invocation performs four actual launches: gate, up, fused
SiLU/multiply, and down. It uses the source-built MLIR-AIE kernels under
[`npu/ffn`](../../npu/ffn/PREFILL.md). There is no CPU arithmetic fallback.

This first adapter stages intermediate BF16 activations through host memory
between launches. The CPU converts the projection output layout to the down
projection input layout using an exact permutation of uint16 bits:

- Projection output: `[Mb,Nb,mm4,nm4,mi4,ni8]`, with `Mb=M/16`, `Nb=P/32`.
- Down input: `[Mb,Kb,mm4,km16,mi4,ki8]`, with `Kb=P/128`.

The permutation groups four N32 tiles into one K128 tile. Pointwise SiLU and
multiplication can operate directly in the packed projection-output order.

Channel ownership persists logically through the branch. The default path
stages intermediates through host memory; `--fuse-swiglu` keeps gate/up outputs
on-chip through pointwise work, but still stages Z before down.
GPU and XRT buffers are separate allocations
with explicit staging. Shared physical DRAM does not make this adapter zero-copy.
Fixed backend-specific packed weights also occupy memory in addition to the
canonical host representation; report that storage instead of claiming no
replication.

The common experiment requires `M`, `H`, and `I` to be positive multiples of
128, with each at least 128. `P` is a multiple of 128 in `[0,I]`; zero and full
NPU ownership are valid contract endpoints. The NPU compiler additionally
requires `M<=4096`, projection K/N at most 16384, and at most 64 N32 tiles per
N column. The default `--npu-design array8 --columns 8` requires all eight
physical columns and uses four compute rows per column (32 workers). Narrow
N128 shards split token rows between two groups of four columns. Horizontal
activation multicast, vertical weight multicast, and up to two M16 blocks of
weight reuse retain the existing host ABI. Planner and source hashes bind each
compiled artifact to its schedule.

Use `--npu-design legacy --columns 8` to reproduce the original one-row graph.
Only in legacy mode is `--columns` a maximum that may be reduced to a divisor
of the output tile count. The old source and artifact directories are preserved.

### Opt-in combined gate/up projection

`--fuse-gate-up` combines the two NPU projections into one array8 graph with
`N=2P`. It concatenates the existing packed gate/up weights once during setup;
quantization metadata and BF16/FP32 arithmetic are unchanged. All eight columns
and four compute rows remain active. Columns 0–3 compute gate and columns 4–7
compute up; output DMA writes two separate compact `[Mb,P/32,512]` BOs directly.
No CPU split/compaction of a wider output is needed.

The complete NPU branch has three launches: combined gate/up, SiLU/multiply,
and down. Two fixed weight BOs replace three (the total packed weight payload
is unchanged). One redundant input BO upload is removed. Intermediates still
pass through host buffers, and CPU down-input reordering remains. This is
projection fusion, not on-chip fusion of the complete FFN or SiLU epilogue.

The combined graph currently supports `128<=P<=8192`, aligned to128, with the
other array8 limits unchanged. For P divisible256, internal activation DMA
payload is unchanged versus two separate projections. For P=128 modulo256,
the original graph uses two groups of four columns, while the combined graph
uses one eight-column group: horizontal multicast also reduces logical input
DMA payload. At M128 this can additionally change M reuse from1 to2. Treat
these as mapping changes as well as launch changes; they are source-derived
traffic counts, not hardware DRAM measurements.

The original path remains the default. Run a matched ratio sweep with separate
ordinary and instrumented measurements using the prepared notebook environment:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python -m experiments.ffn_partition.sweep_partition \
  --m 512 --npu-channels 128,256,384,512,640,768,896,1024,1536,2048,4096,7168 \
  --iterations 30 --diagnostic-iterations 10 --warmup 3 \
  --required-power-mode default \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output-dir experiments/ffn_partition/results/fusion_sweep_m512
```

Each ordinary job interleaves its own GPU-only, serialized and concurrent
controls. Fused/unfused process order alternates between ratios. The driver
checks unchanged correctness thresholds, actual NPU completion counts, fixed
weight uploads, and power-mode snapshots before/after each job. It never changes
power settings. Use a new directory for new measurements; `--resume` requires
the same configuration and measurement source hashes. `--plan-only` writes a
reviewable command manifest without running hardware.

Generate static shareable figures from saved evidence with matplotlib:

```bash
python -m experiments.ffn_partition.plot_partition_sweep \
  experiments/ffn_partition/results/fusion_sweep_m512 \
  --m 512 --output experiments/ffn_partition/results/fusion_figures
```

The plotter preserves ordinary latency versus instrumented diagnostics, GPU
event intervals versus NPU host waits, and separate repeated runs. Bands show
sample p10–p90 ranges, not confidence intervals. The selected ratio is the best
tested point for that workload; it is not an exhaustive or global optimum.

## Numerical contract and checks

Both adapters receive slices of the same deterministic canonical unsigned-int4
weights, BF16-rounded scales, and integer zero points. Quantization groups span
128 K elements. Each projection dequantizes to BF16, accumulates in FP32, and
rounds its output to BF16. SiLU is rounded to BF16 before multiplication; the
product is rounded again. Each down partial is BF16 before the boundary sum,
which is also rounded to BF16.

The CPU contract supplies two references: an unpartitioned FFN and a partitioned
FFN modeling the additional down-partial rounding. They need not be bitwise
identical. The NPU SiLU kernel is an approximation; numerical validation is
still required for the composed FFN and its final reduction.

Correctness checks use finite outputs, a fixed relative-L2 bound, and a fixed
tensor-normalized maximum-error bound. Defaults are relative L2 at most `0.02`
and maximum absolute error at most `0.05 + 0.03*max(abs(reference))`.
An all-zero reference requires exact zero output. These are explicit synthetic
bring-up thresholds, not model-accuracy evidence, and are never adapted to make
a failing run pass.

CPU checks cover unequal slices and metadata, both single-device endpoints,
alternating/zero inputs, corrupted quantization lanes, partial rounding, and
the layout conversion for every uint16 bit pattern. Run them from the repository
root:

```bash
OPENBLAS_NUM_THREADS=1 python -m unittest discover \
  -s experiments/ffn_partition -p 'test_*.py' -v
```

## Running on the AMD notebook

The prepared notebook runtime is `/notebooks/heteromega-ffn-venv`, with
Torch `2.11.0+rocm7.2`, **NumPy `1.26.4`**, `ml_dtypes`, and `ninja`. Start in an initialized
IRON terminal and preserve its `PYTHONPATH`, which exposes the installed
`pyxrt`, when activating this environment:

```bash
source /notebooks/heteromega-ffn-venv/bin/activate
export HETEROMEGA_ROCM_PATH=/opt/rocm-7.2.0
export ROCM_HOME=/opt/rocm-7.2.0 ROCM_PATH=/opt/rocm-7.2.0
export LD_LIBRARY_PATH=/opt/rocm-7.2.0/lib:/opt/xilinx/xrt/lib:${LD_LIBRARY_PATH:-}
export MAX_JOBS=2 OPENBLAS_NUM_THREADS=4
python -m pip install 'numpy==1.26.4'
python -c 'import torch, numpy, ml_dtypes, pyxrt; print(torch.__version__, numpy.__version__)'
```

The NumPy pin is required for this notebook's prebuilt `pyxrt`. With NumPy
`2.5.4`, an actual BO read returned a uint8 array with zero stride, repeating
the first byte instead of exposing the buffer. Copying that array silently
corrupts readback; successful NPU dispatch does not validate it. NumPy `1.26.4`
restored valid readback and the small composed-FFN correctness checks passed.
The adapter accepts signed or unsigned one-byte integer buffers and rejects
zero/negative strides, other dtypes, and incorrect byte count or shape before
interpreting output. Restart Python after changing NumPy.
This pin applies to the isolated runtime; preserve the separate IRON environment.

The runtime needs the AMD GPU and NPU exposed by the host. Pass `--iron-python`
the separate interpreter containing the pinned MLIR-AIE/IRON revision
`7e00b57955e108fe9d8e9419f5828a0c7e650858`. The GPU extension requires the
HIP compiler and headers. `HETEROMEGA_ROCM_PATH` can select their installation.

From the repository root, start with a small shape that still exercises an
unequal partition and multiple quantization groups:

```bash
python -m experiments.ffn_partition.run \
  --m 128 --hidden 256 --intermediate 512 --npu-channels 0,128 \
  --columns 8 --npu-design array8 --warmup 2 --iterations 20 \
  --artifact-root build/ffn_partition \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/small_m128_h256_i512.json
```

After hardware correctness passes, test model-shaped projections and several
unequal allocations using the same canonical weights:

```bash
python -m experiments.ffn_partition.run \
  --m 128 --hidden 4096 --intermediate 14336 --npu-channels 0,128,512,2048 \
  --columns 8 --npu-design array8 --warmup 2 --iterations 20 \
  --artifact-root build/ffn_partition \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/modelshape_m128_h4096_i14336.json
```

Change the interpreter path if the environment differs. Add `--build-only`
to prepare artifacts without running the timed experiment. Artifact directories
and manifests bind geometry and graph/kernel source hashes to compiled binaries;
incompatible or stale builds must be rebuilt. Kernel compilation and GPU
extension compilation can take substantially longer than a measured invocation.

For a numerical failure, run `python -m experiments.ffn_partition.diagnose`
with the same shape, one NPU channel count, artifact root and IRON interpreter.
It saves stage comparisons and raw arrays as JSON/NPZ, including XRT readback
dtype and strides. This diagnostic is synchronized and supplies no performance
measurement. The normal benchmark stops on a failed correctness check.

For per-stage GPU event spans and CPU launch/wait intervals, run the separate
instrumented diagnostic. It preserves required dependencies without adding
per-stage GPU waits; its latency is not an ordinary speedup measurement:

```bash
python -m experiments.ffn_partition.profile_timeline \
  --m 512 --hidden 4096 --intermediate 14336 --npu-channels 512 \
  --columns 8 --npu-design array8 --warmup 3 --iterations 30 \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output experiments/ffn_partition/results/timeline_confirmation.json
```

Record `xrt-smi` power-mode queries immediately before and after each run;
[POWER_TIMING.md](POWER_TIMING.md) gives the query and interpretation. CPU
and GPU clocks are not calibrated to each other, NPU waits are host intervals,
and independent medians cannot form an exact cross-device timeline.

## Interpreting results and next integration step

The available prior NPU measurements characterize standalone projections on
Ryzen AI 9 HX370, not Ryzen AI Max+ 395. They exclude host staging and do not
predict a complete-FFN speedup. This experiment must record the actual hardware,
software, shape, allocation, numerical errors, and measured timing samples.
The [results report](RESULTS.md) records complete-FFN measurements on that
machine. Whole-model prefill latency remains unmeasured for this implementation.

The existing HeteroMosaic operator M-split can write directly to disjoint regions
of shared output. There is no mandatory concatenation cost to assume removed.
Comparisons against its optimized heterogeneous model path remain separate from
the GPU-FFN-without-offload baseline here; its previously documented random
packed-W4A16 numerical discrepancy remains a correctness gate for that path.

If a partition improves complete FFN latency, the next test is an opt-in path
inside the original causal micro-batch schedule, holding attention, weights,
quantization, and chunk sizes fixed. Measure attention interference and actual
complete-prefill latency with output/logit checks before claiming model-level
acceleration or TTFT improvement.
