# TileFuse W4A16 adaptation for prefill FFN

## Current direct-buffer path — 2026-10-27

The subsequent [faithful native FFN comparison](../../docs/runs/2026-10-27-native-comparison/README.md)
measures our GPU+NPU path at 17.48–18.03 ms versus native HeteroMosaic at
15.81–15.89 ms. Native numerical failures are recorded under explicitly
authorized report policy; the native binary is unchanged. The NPU-branch gains
below therefore do not establish an advantage over native heterogeneous FFN.

The user's latest request selects glassescrab's BFP16 MMUL while preserving
original packed weight buffers. `w4a16_upstream.py --arithmetic bfp16` selects
8×8×8, four-accumulator MMUL in `w4a16_prefill_upstream.cc`, with the same
pinned upstream algorithm described below. `--arithmetic bf16` keeps the
native 4×8×8 control. Both use original **4,352-byte K128/N64 tiles**, unchanged
dequantization, BF16 external A/Y and FP32 C. No compact weight repacking is
performed. Internal A/C vector gathers/scatters bridge the existing 4×8 ABI.
BFP16 uses a 4 KiB stack and rejects the native paired-M MMUL ablation.

Selected dataflow remains eight columns/32 workers, SwiGLU reuse two with
row-major input and down-A output, down reuse four with one core A buffer,
vector zero metadata, and a two-segment pipeline. BFP16 arithmetic has its own
object/cache/manifest identity. `check_upstream --arithmetic bfp16` defaults
to report policy; original numerical verdicts and errors remain explicit,
while finite/repeat/zero/change/weights/completion failures still reject a run.

The sections below describe the earlier compact-weight adaptation and its
historical measurements. They do not establish performance of the new direct
buffer path. [Direct-buffer hardware evidence](../../docs/runs/2026-10-27-upstream-bfp16/README.md)
now records 1,024 successful dispatches and 34.6–35.2% lower NPU-branch median
latency versus the optimized native control. All original numerical tolerances
pass; worst relative L2 versus the CPU oracle is 0.0167717. This is not a
combined GPU+NPU or model-accuracy result.

The subsequent [direct-buffer GPU+NPU partition experiment](../../docs/runs/2026-10-27-upstream-partition/README.md)
measures complete isolated FFN latency, including GPU staging and reduction:
19.1–20.3% lower than matched GPU-only FFN kernels at M512/P2560–2816 in two
50-sample confirmations. All original tolerances pass. This additional result
still does not establish full-model prefill acceleration or pretrained accuracy.

## Historical compact-weight adaptation

**Code-confirmed:** the opt-in `--npu-arithmetic bfp16` path adapts the
W4A16 GEMM strategy from `glassescrab/mlir-aie` to HeteroMega's existing
eight-column prefill FFN graphs. It selects a separate C++ source; native
BF16 remains the default and its arithmetic source is unchanged.

This is an adaptation of the upstream microkernel strategy, not a copy of
the complete upstream array schedule. Source inspection does not establish
that this variant is faster, that its compiler allocation fits every shape,
or that it accelerates full-model prefill. Hardware evidence belongs in the
measurement section below.

## Upstream branch audit

The seven remote branch heads were inspected at their fetched revisions in
the 2026-10-22 session. These pins record that inspection; they are not
promises about future branch contents.

| Branch | Pinned head | Code-confirmed relevance |
| --- | --- | --- |
| `feature/update-mix-mm-int4-verification` | `121dd54abc68f84d89a7074372ebf82be2db62d5` | Cleaned TileFuse artifact, corrected unsigned W4A16 GEMM dequantization, optimized W4A16 GEMV and ablations; selected source. |
| `main` | `87a1f27699af2e079619f33a509b45e5d42b1763` | Earlier `mix_int4_ATB.cc`; the feature branch fixes its per-column scale/zero-point addressing. |
| `memory_optimizations` | `9fcd1efc35e8f3dac223a62b95e9791de2073a03` | Dense BF16/BFP16 GEMM and memory-layout work; not a packed-W4A16 replacement. |
| `bfp16` | `038b4941d26b344cdddb8759613425cc9d09a33a` | Direct block-float and mixed BF16/BFP16 dense GEMM examples, plus earlier mixed-precision experiments. |
| `int4_mix_precision` | `e259455f6d6f11727c41edd98c7bbf9cae4bf828` | Earlier signed-INT4 implementation with different metadata handling; superseded for this unsigned AWQ-style contract. |
| `mix_precision_with_en_st_re` | `f58186fd11b6f53589b06a0273ad9f34cac6caf5` | Earlier mixed INT8/stream-reuse work; does not supply the selected corrected W4A16 path. |
| `gemm_v` | `cce7c55ed95ad8163b2ebd8c31338bc8506ad008` | Earlier dense matrix/vector work; not the selected packed-W4A16 prefill GEMM. |

The selected source is
[`aie_kernels/aie2p/mix_int4_ATB.cc`](https://github.com/glassescrab/mlir-aie/blob/121dd54abc68f84d89a7074372ebf82be2db62d5/aie_kernels/aie2p/mix_int4_ATB.cc),
with the BFP16 compiler setting in
[`gemm_w4a16/makefile-common`](https://github.com/glassescrab/mlir-aie/blob/121dd54abc68f84d89a7074372ebf82be2db62d5/programming_examples/tilefuse/gemm_w4a16/makefile-common)
and the reference array topology in
[`whole_array.py`](https://github.com/glassescrab/mlir-aie/blob/121dd54abc68f84d89a7074372ebf82be2db62d5/programming_examples/tilefuse/gemm_w4a16/whole_array/whole_array.py).

**Why this head:** the newer GEMM fixes scales and zero points to index the
output-channel microtile, removes the incorrect transpose of their replicated
vectors, and fixes the zero-point region offset. Those are quantization/layout
corrections, distinct from the larger BFP16 arithmetic error accepted for the
current experiment. They should not be replaced with a looser tolerance.

**Documented but not independently verified:** the
[TileFuse ablation guide](https://github.com/glassescrab/mlir-aie/blob/121dd54abc68f84d89a7074372ebf82be2db62d5/programming_examples/tilefuse/ablation/README.md)
identifies the optimized W4A16 configurations and explains their reuse and
dataflow. The inspected branch files do not provide a comparable raw latency
dataset proving a best branch for HeteroMega's M512 FFN shapes. Older
`result.txt` files inspected contain matrix dumps rather than timing records.
Dense BFP16 throughput figures in the block-datatype examples use different
formats and shapes and cannot establish W4A16 FFN speedup.

## Arithmetic and buffer contract

**Code-confirmed:** [w4a16_prefill_bfp16.cc](w4a16_prefill_bfp16.cc) uses
`aie::mmul<8,8,8,bfloat16,bfloat16,accfloat>` with a four-accumulator, 2×2
expansion. The AIE API's
`AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16=1` flag enables BFP16 matrix
computation with BF16 input vectors. Both the selector's compile flags and
the C++ source require that setting; explicit zero is rejected. BFP16 is an
internal compute format here, not a new external weight or activation format.

| Property | Selected upstream GEMM | HeteroMega adaptation |
| --- | --- | --- |
| Full per-core tile | M64/K128/N64 | M16/K128/N32, with explicit M reuse |
| Arithmetic microtile | 8×8×8 through BFP16 MMUL | Same microtile and 2×2 expansion |
| Packed weight tile | 4,352 bytes | 2,144 bytes |
| Weight regions | 4,096 q bytes, 128 scale bytes, 128 duplicated zero bytes | 2,048 q bytes, 64 scale bytes, 32 zero bytes |
| Dequantized scratch | 128×64 BF16 | 128×32 BF16, 8,192 bytes |
| K-group partial storage | BF16 by the default upstream build | FP32 across every K128 group |
| Weight reuse | Stateful `DIV=2` across two M32 inputs | Explicit REUSE1/2/4 over independent M16 inputs |
| Graph/runtime | Upstream whole-array launch schedule | Existing HeteroMega array8/gate-up/SwiGLU schedules |

The compact external layout is unchanged:

- A: BF16 `[4,16,4,8]` within each M16/K128 tile.
- W: unsigned INT4 K8/N8 microtiles, low nibble for even local N, followed
  by BF16 per-column scales and one unsigned byte zero per column. Each
  K128 tile is one quantization group.
- C/Y: `[4,4,4,8]` within each M16/N32 output tile; C is FP32, Y is BF16.
- Grouped objects: independent A/C/Y tiles for each reuse lane. The same
  packed weight tile is dequantized once before processing those lanes.

The kernel gathers two existing 4×8 A blocks into an 8×8 input vector. It
gathers and scatters FP32 C the same way. B already uses K8/N8 blocks, so
the host packer, DMA taps, fused pointwise layout and down-input permutation
remain compatible. There is no change in logical channel ownership.

Dequantization retains HeteroMega's validated compact metadata loads and
computes `BF16((q-zero)*BF16(scale))`, equivalent to the corrected upstream
per-column formula. It does not reinterpret a 4,352-byte upstream tile as
our 2,144-byte tile. The implementation retains FP32 accumulation between
K groups and rounds to BF16 in `finish`; it has no hidden `g_counter` state.

[projection_arithmetic.py](projection_arithmetic.py) allocates a **4,096-byte
worker stack** for BFP16 and retains 2,048 bytes for native BF16. The upstream
Peano path reserves `0xD00` and warns that insufficient stack can silently
corrupt output. Our larger reservation is a precaution, not measured stack
usage. Actual compiler spills, memory placement and resource fit still need
inspection. The ordinary experiment caps reuse at two; fused SwiGLU rejects
reuse four even though the C++ grouped ABI supports it.

The selected kernel revision and compiler revision are separate: the
adapted kernel is pinned above, while the existing graph toolchain target
remains `7e00b57955e108fe9d8e9419f5828a0c7e650858`. Object names and build
contracts include arithmetic, source/helper hashes and reuse. Manifests
record compute format, upstream kernel revision and worker stack size.
BF16/BFP16 artifacts must not be substituted across these identities.

## FFN scope and GEMV

With `--fuse-swiglu`, matching gate/up partitions stay on their adjacent NPU
workers through SiLU and multiplication. The GPU handles its complementary
channels. Each device computes its down K-slice, and the **GPU sums the two
partial outputs**. BFP16 changes the NPU projections; the existing GPU kernels
and SiLU/multiply implementation are unchanged. Z still goes through host
staging and CPU layout conversion before the separate NPU down launch.

**Code-confirmed:** the latest upstream W4A16 GEMV uses
[`vm_mix_int4_64x8.cc`](https://github.com/glassescrab/mlir-aie/blob/121dd54abc68f84d89a7074372ebf82be2db62d5/aie_kernels/aie2/vm_mix_int4_64x8.cc)
with vector accumulation, not the BFP16 matrix-MMUL mechanism used by GEMM.
Its optimized graph distributes weights to four compute rows; the ablations
separate vector microkernel and dataflow improvements. This is relevant to a
future decode study, but the current task remains multi-token **prefill**.
No GEMV/decode implementation or speedup is claimed by this adaptation.

## Numerical reporting

The user explicitly accepted larger BFP16 numerical differences for this
performance investigation. `run.py`, `profile_timeline.py` and the partition
sweep select `report` accuracy policy by default for BFP16, while native BF16
defaults to `strict`. `--accuracy-policy strict` remains available.

Reporting does **not** widen the existing numeric limits or convert a failed
tolerance check into a passed check. Reports retain relative L2 error,
maximum error, tolerance status and a separate experiment-acceptance status.
Finite deviations can be recorded while timing continues. Nonfinite output,
invalid zero behavior, stale/nonresponsive output, inconsistent repeated
inputs, and missing or failed NPU completions remain execution failures.
GPU-only correctness controls continue to use strict checking.

These structural checks are not a proof of model accuracy. Accepted
performance data with reported numerical deviations must be labeled as such.
The earlier BF16 validation and speedups do not transfer to the BFP16 path.

## Build, latency and diagnostic commands

Run from the remote HeteroMega repository root after verifying the actual
AMD hardware, prepared environment and NPU power mode. These paths describe
the existing AUP setup; verify them rather than reinstalling the host driver.
Use fresh output directories and preserve failed attempts and compiler logs.

The runtime's `bin` directory must be on PATH so Torch can find Ninja; invoking
its Python by absolute path alone does not set PATH. Keep the initialized
IRON terminal's `PYTHONPATH` for `pyxrt`:

```bash
export PATH=/notebooks/heteromega-ffn-venv/bin:$PATH
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
```

Build a bounded fused smoke case without running the GPU or NPU:

```bash
/notebooks/heteromega-ffn-venv/bin/python -m experiments.ffn_partition.run \
  --m 128 --hidden 128 --intermediate 256 --npu-channels 128 \
  --npu-arithmetic bfp16 --fuse-swiglu --build-only \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --artifact-root experiments/ffn_partition/artifacts/bfp16 \
  --output experiments/ffn_partition/results/bfp16/smoke_build.json
```

After bounded execution checks, collect ordinary complete-FFN latency with
fresh GPU controls at both earlier BF16 candidate partitions:

```bash
/notebooks/heteromega-ffn-venv/bin/python -m experiments.ffn_partition.run \
  --m 512 --hidden 4096 --intermediate 14336 --npu-channels 1024,1152 \
  --npu-arithmetic bfp16 --fuse-swiglu --accuracy-policy report \
  --warmup 3 --iterations 30 \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --artifact-root experiments/ffn_partition/artifacts/bfp16 \
  --output experiments/ffn_partition/results/bfp16/latency_m512.json
```

Collect stage diagnostics separately, for example at P1152:

```bash
/notebooks/heteromega-ffn-venv/bin/python -m experiments.ffn_partition.profile_timeline \
  --m 512 --hidden 4096 --intermediate 14336 --npu-channels 1152 \
  --npu-arithmetic bfp16 --fuse-swiglu --accuracy-policy report \
  --warmup 3 --iterations 10 \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --artifact-root experiments/ffn_partition/artifacts/bfp16 \
  --output experiments/ffn_partition/results/bfp16/profile_m512_p1152.json
```

The earlier P1024/P1152 results are starting candidates, not a proven optimum
for BFP16. The complete-FFN timer includes staging, layout conversion,
launches, waits and GPU reduction. Diagnostic waits overlap other work and
include compute/runtime/DMA; they are not pure data movement. Instrumented
stage timings must remain separate from ordinary latency.

The GPU control in these commands uses original HeteroMosaic W4A16 **GPU**
kernels. It is not native HeteroMosaic's heterogeneous model scheduler. That
separate comparison remains described in
[NATIVE_COMPARISON.md](../../experiments/ffn_partition/NATIVE_COMPARISON.md).

## Measurement record

**Measured on 2026-10-22:** the BFP16 projections compile and execute in the
fused eight-column SwiGLU/down FFN on HX370, NPU mode `default`. Eight NPU
allocations were sampled at M512/H4096/I14336. P1792 (12.5%) measured
18.761 ms in refinement and **18.754 ms** in a 50-sample repeat, versus a
matched **22.349 ms GPU-only control**. This is 16.1% lower latency and 5.4%
lower than the fresh native-BF16 P1152 candidate (19.828 ms).

All ten successful reports pass the original numerical bounds despite the
report-only allowance: M512 maximum recorded relative L2 is 0.0172392.
There are 2,764 confirmed NPU completions and 1,694 timed invocations across
the recorded smoke, ordinary and diagnostic runs. These are isolated
synthetic FFN results; native heterogeneous HeteroMosaic and full-model
prefill are not established by these measurements.

See [the full results, allocation graphs, stage profiles and archive](../../experiments/ffn_partition/BFP16_RESULTS.md) for evidence, controls,
exact numerical errors, source identities, power observations and reproduction.
