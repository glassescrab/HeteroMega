# Native BF16 segment-pipeline experiment

**Measured:** keeping two N64 segments in flight reduced median latency of
the isolated NPU FFN branch by **3.11%** in ABBA order and **2.44%** in the
reversed BAAB confirmation. This is a small improvement with overlapping
latency distributions. It does not establish complete GPU+NPU prefill or
whole-model acceleration.

Runs used the AUP HX370, eight columns / 32 workers, native BF16, unchanged
glassescrab packed W4 buffers and fixed M512/H4096/I14336/P2560 geometry.
The isolated overlay was `/notebooks/HeteroMega-pipeline-bf16-20261025` with
MLIR-AIE `7e00b57955e108fe9d8e9419f5828a0c7e650858`, Python 3.12.3 and
NumPy 1.26.4. The directory date is local 2026-10-25; platform snapshots are
2026-10-26 UTC. [Before](platform_before.json) and [after](platform_after.json)
snapshots report power mode **default** and eight columns. Neither
[partition snapshot](partitions_before.json) reports an active context, including
[after execution](partitions_after.json). Electrical telemetry was unsupported;
power consumption was not measured. No host driver/kernel change was made.

## Change and control

**Code-confirmed:** `--segment-pipeline-depth 2` queues the next segment before
waiting for the oldest one. Output drains precede input fills, at most two
segments remain live, and all tasks complete before return. The window continues
across M-wave boundaries. `--segment-pipeline-depth 1` retains the serial
control. Both settings have distinct manifest and cache identities.

Core arithmetic, FIFO depths, buffers, transfer addresses and original weight
bytes remain unchanged. This change does not increase on-chip weight reuse or
overlap dequantization and MMUL inside a worker. The activation permutation
between SwiGLU and down remains. Earlier serial native-BF16 artifacts and checks
remain in [the previous evidence directory](../2026-10-25-upstream-bf16/README.md).
Earlier compact-weight/BFP16 timings are separate controls and must not be
assigned to this implementation.

## Timing evidence

Each A/B block used a fresh subprocess, fixed-weight upload, five warmup runs,
then repeated calls with the same two signed synthetic inputs. A is depth1;
B is depth2. The timer includes input validation, activation layouts, BO I/O,
both NPU dispatch/waits and output unpacking. Context creation, fixed uploads,
warmup, hashing and output comparisons are excluded. A separate serial reference
block precedes each experiment and is excluded from timing summaries.

| Report | Timed samples per depth | Serial median | Pipeline median | Latency reduction |
|---|---:|---:|---:|---:|
| [ABBA](pipeline_abba.json) | 50 | 24.7957 ms | 24.0239 ms | 3.1123% |
| [BAAB](pipeline_baab.json) | 100 | 25.1255 ms | 24.5116 ms | 2.4436% |

ABBA p10–p90 ranges are 23.8322–25.2272 ms serial and
23.2186–24.4581 ms pipelined. BAAB ranges are 24.4462–25.8651 ms serial and
23.9313–25.0570 ms pipelined. Raw times and per-block order are retained in
the reports. These are 300 timed branch calls, not 300 independent experiments.
`dispatch_wait_us` is a host launch-plus-wait interval, not a device-cycle or
kernel-phase measurement. No dequantization/MMUL/FIFO-stall attribution follows
from this experiment.

## Correctness and completions

| Report | Cases | Input runs | Successful NPU completions |
|---|---:|---:|---:|
| [Smoke](pipeline_smoke.json) | 5 | 20 | 24 |
| [Full shape](pipeline_model.json) | 1 | 4 | 8 |
| [Uneven partition](pipeline_odd.json) | 1 | 4 | 8 |
| ABBA, including warmup and reference | — | — | 248 |
| BAAB, including warmup and reference | — | — | 448 |
| Total | 7 correctness cases | 28 correctness runs | **736** |

All seven correctness cases pass the original strict bounds: `rtol=0.03`,
`atol=0.05`, relative L2 ≤ 0.02. Worst relative L2 is 0.00400048 and largest
absolute error is 0.0009765625. Finite output, exact zero, exact repeat after
changed/zero inputs, changed-input response and unchanged source weight bytes
all pass. Coverage includes full-source K/N offsets, paired N64 halves,
narrow N128, fused SwiGLU, a complete small FFN, the full model shape, and
M128/H512/I2048/P1152 at channel start128.

Every timed and warmup output matches its serial control exactly, and each
runner has the expected completion and fixed-weight-upload counts. Full-shape
inputs, weights and output hashes also match the previous serial package for
signed A, signed B, zero and repeated A; see
[previous_package_equivalence.json](previous_package_equivalence.json).
These synthetic checks do not validate pretrained-model accuracy.

Local checks: 63 NPU tests plus 114 experiment tests, **176 passed and one
skipped**. [summary.json](summary.json) provides machine-readable totals and
the original timing summaries.

## Reproduce

Run from the isolated overlay with its configured pyxrt/IRON environment;
no package installation or driver changes are required by these commands.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.check_upstream \
  --output results/pipeline_smoke.json --artifact-root artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python --segment-pipeline-depth 2
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.check_upstream \
  --suite model --output results/pipeline_model.json --artifact-root artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python --segment-pipeline-depth 2
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.check_upstream \
  --suite model --m 128 --hidden 512 --intermediate 2048 --channels 1152 --channel-start 128 \
  --output results/pipeline_odd.json --artifact-root artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python --segment-pipeline-depth 2
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.benchmark_upstream_pipeline \
  --output results/pipeline_abba.json --artifact-root artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --rounds 1 --order ABBA --warmup 5 --iterations 25 \
  --environment-note 'HX370; xrt-smi platform power_mode=default; isolated NPU branch'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.benchmark_upstream_pipeline \
  --output results/pipeline_baab.json --artifact-root artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python --no-build \
  --rounds 1 --order BAAB --warmup 5 --iterations 50 \
  --environment-note 'HX370; power_mode=default; reversed-order confirmation; isolated NPU branch'
```

Model geometry and seed251025 above are CLI defaults. Both variants receive
the same synthetic original-format packed bytes; the benchmark does not use
pretrained weights. Keep P2560 fixed when reproducing this comparison.

## Evidence identity and remaining work

[evidence.tar.gz](evidence.tar.gz) includes raw reports/logs, platform snapshots,
source snapshots, both depth1/depth2 model-shaped XCLBINs and instructions,
MLIR, core ELFs, manifests and build contracts. Its SHA256 is:

```text
0dabb910ce0392ec9e2b4dfbea959d3016ba4069834a799fbe110eeba3f2cdbe
```

The four standalone platform/partition JSON copies omit trailing blank lines;
their original bytes remain unchanged inside the archive.

The archive retains both `uploads/heteromega-pipeline-bf16-v1.tar.gz` and
`uploads/heteromega-pipeline-benchmark-v2.tar.gz`. Correctness ran before the
adapter's integer-only depth validation was tightened; the benchmark used the
second upload. The narrow change replaces the inline depth check with the
shared strict integer validator. The recorded adapter SHA256 values are
`5a2fff2b9a4dcadd1ee0f3270b8db1b1c1f26df13c675b0e5bfd178296c0d26b`
for correctness/v1 and
`239cda4d1584d2f4b6d500de3d4ecde3f4d6f01c0729861ca09a1c92da694513`
for benchmark/v2. Core kernel and graph sources were unchanged across these
runs. Use these recorded hashes and upload snapshots to reproduce each report.

[Independent integrity audit](integrity_audit.json) verifies manifests,
sources, counters and output equivalence. The
[SwiGLU](swiglu_mlir_audit.json) and [down](down_mlir_audit.json) MLIR audits
confirm unchanged compute/FIFO prefixes and DMA taps, at most two outstanding
tasks per channel and safe wait/free ordering. All 64 corresponding core ELF
pairs are byte-identical between depths. The [audit script](audit_mlir.py)
can be rerun on each extracted depth1/depth2 `aie.mlir` pair. Logical task
counts do not measure physical bandwidth or stall cycles.

The selected depth2 package is published in
[PR #3](https://github.com/glassescrab/HeteroMega/pull/3), commit `d628e48`.
This report, harness and raw evidence remain in the local research checkpoint;
the PR retains only the 21 kernel/package files.

**Proposed next step:** measure the complete GPU+NPU FFN with matching fixed
weights and compare against reproducible HeteroMosaic/GPU controls. P2560 has
not been retuned. Core-level phase profiling is still needed to decide whether
dequantization, local-memory traffic or arithmetic offers the next worthwhile
optimization.
