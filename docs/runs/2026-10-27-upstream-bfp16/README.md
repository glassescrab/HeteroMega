# Direct-buffer BFP16 MMUL verification

**Measured:** glassescrab's BFP16-backed 8×8×8 MMUL reduces isolated
NPU-branch latency by **35.18% in ABBA and 34.61% in BAAB** versus the
optimized native-BF16 control. This is M512/H4096/I14336/P2560 prefill on
HX370/default power, eight columns and 32 workers. These results do not
establish combined GPU+NPU acceleration, full-model speedup or model accuracy.

The user's October 27 instruction selects BFP16 MMUL while retaining original
glassescrab weight buffers. The corrected TileFuse reference is pinned at
`121dd54abc68f84d89a7074372ebf82be2db62d5`,
`aie_kernels/aie2p/mix_int4_ATB.cc`. The prepared MLIR-AIE compiler is
`7e00b57955e108fe9d8e9419f5828a0c7e650858`.

## Implementation and comparison

**Code-confirmed:** `w4a16_prefill_upstream.cc` selects the four-accumulator
8×8×8 MMUL when `AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16=1`. The AIE API
converts BF16 operands internally for BFP16 computation. Flag0 retains native
4×8×8 MMUL. The direct 4,352-byte K128/N64 packed-weight dequantization body is
unchanged. No weights are repacked or concatenated. Local vector gathers and
scatters bridge existing 4×8 A/C blocks to internal 8×8 operands. C stays FP32
across all K128 groups and Y stays BF16. BFP16 reserves a 4 KiB stack and rejects
the native paired-M ablation; the native MMUL1 control retains 2 KiB.

Both profiles retain `combo_mmul1_row_major`: SwiGLU reuse2/Adepth2,
row-major input and down-A output; down reuse4/Adepth1; vector zero metadata;
MMUL M blocking1; two-segment pipeline; borrowed BO readback. BO staging and
final output unpacking remain. The same full original weight bytes and signed
input fixtures are used in both arithmetic modes.

Each order uses fresh subprocesses for the two excluded arithmetic references
and each timed block. Every child checks signed A, signed B, zero, repeat A;
timed children then perform five warmups and 50 measured calls. Same-arithmetic
outputs must match the reference exactly, including warmups. Cross-arithmetic
errors retain the original tolerances and explicit report policy. Missing
completions, nonfinite, stale, inconsistent, nonzero-on-zero, changed weights
or input bytes remain failures. Native controls remain strict.

| Order | Native median ms | BFP16 median ms | Reduction | Samples per arithmetic |
|---|---:|---:|---:|---:|
| [ABBA](arithmetic_abba.json) | 22.322063 | 14.469527 | 35.1784% | 100 |
| [BAAB](arithmetic_baab.json) | 22.404607 | 14.650269 | 34.6105% | 100 |

ABBA p10–p90 is 21.645–22.995 ms native and 13.763–14.986 ms BFP16.
BAAB p10–p90 is 21.865–22.796 ms native and 13.982–15.271 ms BFP16.
These are repeated calls in two experiments, not independent device trials.

The whole timer includes input validation/layout, BO writes/read/sync, both
launch/waits, and final output unpacking. Construction, fixed-weight uploads,
preflight, warmup, result snapshots, hashing and comparisons are excluded.
Host launch-plus-wait medians are:

| Stage | ABBA native ms | ABBA BFP16 ms | BAAB native ms | BAAB BFP16 ms |
|---|---:|---:|---:|---:|
| SwiGLU | 11.729349 | 6.512387 | 11.795128 | 6.592846 |
| Down | 7.223249 | 4.732201 | 7.227979 | 4.791240 |

These waits include runtime/device/DMA dependencies. They do not attribute
exact time to MMUL, dequantization or FIFO stalls. Static assembly evidence is
reported separately in [assembly](assembly/README.md).

## Numerical and execution evidence

All cases pass the original max-error and relative-L2 limits (`rtol=.03`,
`atol=.05`, relative L2≤.02; max error normalized by reference maximum).
BFP16 report mode was explicit and did not turn any tolerance failure into a
pass. The CPU reference uses BF16 dequantization/I/O with FP32 products; it is
not a bitwise BFP16 simulator.

| Report | Successful dispatches | Worst relative L2 vs CPU |
|---|---:|---:|
| [BFP16 smoke, five cases](bfp16_smoke.json) | 24 | 0.0167716662 |
| [BFP16 full shape](bfp16_model.json) | 8 | 0.0166669643 |
| [BFP16 P1152, offset128](bfp16_offset.json) | 8 | 0.0167297031 |
| [Native full-shape control](bf16_model.json) | 8 | 0.0037598080 |
| ABBA timing/checks/warmup | 488 | Separate native hardware reference |
| BAAB timing/checks/warmup | 488 | Separate native hardware reference |

Total: **1,024 successful NPU dispatches**, 400 timed invocations across both
arithmetic profiles and orders. Both timing reports pass every execution check.
BFP16 versus native hardware maximum relative L2 is **0.0166251988** and maximum
absolute difference **0.0030517578125**, within original bounds. Hardware
contexts are empty before and after; platform snapshots retain default power.

## Reproduction and artifacts

Remote isolated overlay: `/notebooks/HeteroMega-upstream-bfp16-20261027`.
All earlier overlays and measured baselines remain intact. Use the prepared
IRON Python with its existing XRT paths; no host driver/kernel changes were made.

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python -m experiments.ffn_partition.check_upstream --arithmetic bfp16 \
  --suite model --vector-zero --down-reuse 4 --down-activation-fifo-depth 1 \
  --swiglu-input-layout row_major --output-layout down_a --borrow-npu-readback \
  --artifact-root artifacts --output results/bfp16_model.json
# Repeat with --arithmetic bf16 and a new output path for the strict control.
# Smoke: --suite smoke; offset case: --suite model --channels 1152 --channel-start 128.
python -m experiments.ffn_partition.benchmark_upstream_arithmetic \
  --artifact-root artifacts --output results/arithmetic_abba.json \
  --bfp16-numerics report --order ABBA --rounds 1 --warmup 5 --iterations 50 --no-build
# Repeat with --order BAAB and a new output path.
```

[compiler-runtime-evidence.tar.gz](compiler-runtime-evidence.tar.gz) contains
raw runtime sources, original reports/logs, both full-shape compiler projects,
ELFs/disassembly, generated MLIR, binaries, manifests and environment metadata.
Its internal SHA256SUMS.json verifies 950 files. Test fixtures/model weights
and credentials are absent. [export_evidence.py](export_evidence.py) records
how it was assembled. Package selection uses the BFP16 model-shape artifacts
byte-for-byte; kernel-only PR #3 excludes this harness/evidence tree.

Independent [integrity audit](integrity_audit.json) verifies source/artifact
identities, all report counts and recomputed statistics, package build commands,
and exact native outputs against the previous selected package. Its
[script](integrity_audit.py) audits saved records; raw output arrays and
smoke/offset binaries were not exported, so those numerical errors are not
independently recomputed from tensors. The complete model-shape artifacts for
both arithmetic modes are retained. The snapshot predates the final host kernel
test edits; all compile/runtime sources match the current implementation.

Published kernel package: `fd67fbf40e9e2e1d06b58d365e4657e61aed050f`,
[PR #3](https://github.com/glassescrab/HeteroMega/pull/3), open and unmerged.

Local verification: 113 tests passed, plus 584 parametrized subtests. Host
scalar-shim tests validate indexing/routing and FP32 partial retention, not
BFP16 rounding. Device checks above establish the actual compiled execution.
