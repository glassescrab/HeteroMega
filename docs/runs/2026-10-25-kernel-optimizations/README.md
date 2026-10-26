# Native BF16 FFN optimization pass

**Measured:** the selected combination reduces isolated NPU-branch median
latency by **8.08% in ABBA order and 7.04% in BAAB order**, compared with the
preceding two-segment native-BF16 configuration. Outputs match exactly.
This is prefill at M512/H4096/I14336/P2560 on HX370/default power, using all
eight columns and 32 workers. It is not a GPU+NPU or whole-model speedup.

The user requested the remaining NPU optimizations before integration.
This pass evaluates vector zero metadata, M reuse, accumulator blocking,
DMA activation layouts and readback ownership. Native BF16 and original
glassescrab packed weight buffers are retained; no weights are repacked.
The original controls and failed bring-up evidence are preserved.

## Selected implementation

`combo_mmul1_row_major` selects:

| Option | SwiGLU | Down |
|---|---|---|
| M16 reuse | 2 | 4 |
| Core activation FIFO depth | 2 | 1 |
| Vector zero metadata | enabled | enabled |
| MMUL M blocking | 1: four accumulators | 1: four accumulators |
| Input layout | row-major | compact A |
| Output layout | down-A | compact C |
| Segment pipeline depth | 2 | 2 |
| Worker stack | 2 KiB | 2 KiB |

The caller borrows intermediate BO-read views, avoiding an additional NumPy
ownership copy. Final output is unpacked into an independent row-major array.
SwiGLU DMA gathers row-major input and scatters Z directly into the down-A
layout, eliminating two CPU permutations. BO write/read/sync remain, and Z
still traverses shared DRAM. This is neither continuous on-chip FFN residency
nor a shared-BO implementation. See the
[activation ABI and build commands](../../../npu/ffn/UPSTREAM_BF16.md).

**Code-confirmed:** down reuse four reduces its M waves from four to two,
weight DMA from 21.25 to 10.625 MiB and N32-half dequantizations from 40,960
to 20,480. Across the FFN, weight DMA falls 63.75→53.125 MiB and dequant calls
122,880→102,400. Activation DMA remains 60 MiB and projection arithmetic
32.212 GFLOPs. These are logical schedule counts, not measured DRAM bandwidth.
Only the down core A consumer becomes single-buffered; memory-tile/host A,
W and output buffering retain depth two.

## Ablations and selection

Each row is its own paired experiment; do not compare absolute values across
rows as if they were simultaneous. Initial ABBA tests use three warmups and
15 timed calls per block, giving 30 timed samples per profile.

| Candidate versus baseline | Baseline ms | Candidate ms | Reduction |
|---|---:|---:|---:|
| [Vector zero metadata](abba_vector_zero.json) | 23.862 | 23.837 | 0.11% |
| [Down reuse four](abba_downreuse4.json) | 23.736 | 23.805 | −0.29% |
| [Direct down-A output](abba_layout_down_a.json) | 23.843 | 23.612 | 0.97% |
| [Borrowed readback](abba_borrowed.json) | 24.182 | 23.848 | 1.38% |
| [Row-major input DMA](abba_row_major.json) | 24.143 | 22.801 | 5.56% |
| [Combination without row-major input](abba_combo_mmul1.json) | 23.801 | 22.978 | 3.46% |
| [Selected combination](abba_combo_mmul1_row_major.json) | 23.887 | 22.089 | 7.53% |
| [Paired M MMUL, repaired stack](abba_mmul_m_reuse2.json) | 24.212 | 53.425 | −120.66% |

Vector zero and down reuse alone have no convincing measured gain here.
The selected combination was therefore also compared directly against the
simpler row-major/direct-output/borrowed configuration. With five warmups and
25 calls per block, the combination wins **2.40%** in
[ABBA](select_staging_vs_combo_abba.json) and **2.68%** in
[BAAB](select_staging_vs_combo_baab.json), 50 samples per profile per order.
This supports selecting the combination; it does not identify each feature's
independent causal contribution or establish a globally optimal partition.

Longer final confirmations use five warmups and 50 calls per block:

| Order | Samples per profile | Baseline median ms | Selected median ms | Reduction |
|---|---:|---:|---:|---:|
| [ABBA](confirm_selected_abba.json) | 100 | 24.576387 | 22.589630 | 8.0840% |
| [BAAB](confirm_selected_baab.json) | 100 | 24.194170 | 22.489991 | 7.0438% |

ABBA p10–p90 ranges are 23.692–25.188 ms baseline and 21.954–22.956 ms
selected; BAAB ranges are 23.424–24.823 and 21.852–23.002 ms. These are
repeated calls within two experiments, not 400 independent experiments.
No confidence interval or GPU-interference generalization is asserted.

Each block runs in a fresh subprocess with fixed weights and the same two
signed synthetic inputs. A separate excluded A-reference block precedes it.
The timer covers the entire `UpstreamNpuFFN.run`: validation, host layouts,
BO I/O, both launches/waits and final unpacking. Construction, fixed-weight
uploads, warmup, hashing, output snapshots and comparisons are outside it.
Both profiles snapshot outputs after the timer. Wrong or nonfinite warmup
outputs prevent timing. Every timed output must match the control bitwise.

The selected host launch-plus-wait medians are approximately 11.7–11.8 ms
for SwiGLU and 7.2 ms for down. These remain the largest dependency intervals;
they are not kernel-only device cycles. This pass does not separate device
dequantization, MMUL, FIFO stalls or DMA time, and does not establish memory
bandwidth saturation.

## Correctness, rejected candidate and compiler evidence

[Selected smoke](v3_safe_smoke.json) and [model-shape](v3_safe_model.json)
checks pass the original strict CPU-reference bounds, finite output, exact
zero, repeated-A-after-changes, changed-input response and unchanged source
weights. Five smoke cases and the full shape complete 32 NPU dispatches.
They cover projection/SwiGLU/FFN, nonzero full-source offsets, paired N32
halves and a narrow N128 projection. Synthetic correctness does not establish
pretrained-model accuracy.

Worst strict-reference relative L2 across passing checks is 0.0040004822;
maximum absolute error is 0.0009765625. Independent [integrity audit](integrity_audit.json)
recomputes timing summaries/counters, resolves all 34 binary/instruction pairs
and source versions, and matches both benchmark inputs to the strict full-shape
oracle and previous pipeline outputs. The archived runtime sources match the
selected local implementation. One local test file has later test-only additions
not present in the remote source snapshot; that difference is recorded explicitly.

All 12 timing experiments pass exact output checks and recorded completion
counts. The final two confirmations alone complete 896 dispatches including
warmups/reference. Across all passing reports in this pass there are 2,672
completions. An additional eight completions belong to the retained failed
bring-up report and are **not correctness successes**. See [summary.json](summary.json).

The first eight-accumulator version passed a small case but produced
nonfinite full-shape outputs, including zero input:
[failed report](combo_model.json). Compiler inspection found its nested stack
needed 2,112 bytes versus the reserved 2,048. Four stores reached the first
A buffer. The full shape's larger main frame explains why the small smoke
case did not expose it. [Initial stack audit](stack_audit_v1.json) preserves
the exact addresses and instructions.

Experimental `--mmul-m-reuse 2` now reserves 4 KiB; the
[repaired full-shape check](v3_paired_model.json) passes. However, the paired
MMUL ablation is about **2.2× slower** and is excluded from the selected
binaries. Its actual loop spills accumulator state heavily. Four-accumulator
MMUL remains selected. This is compiler-confirmed spill evidence plus a
whole-branch timing regression, not a measured spill-cycle percentage.

The [final compiler audit](final_kernel_audit.json) verifies 192 ELF stack/buffer
placements and the bytes of 12 representative disassemblies. Selected
projection call chains use 256 bytes, with a maximum 704 bytes through the
separate SiLU call; both fit the 2 KiB reservation. Selected MMUL has zero
stack vector loads/stores in its K8 loop. The repaired paired ablation uses
2,176 bytes within 4 KiB but still has 128 stack vector loads and 128 stores
per K8 loop, versus 64 matrix MAC instructions.

Local verification completed **201 passing tests and one skip**: 77 NPU
tests and 125 experiment tests (one skipped). Coverage includes actual C++
kernel bodies in a host API shim, bit patterns, offset DMA enumeration,
layout coverage, stack reservation, cache identities, borrowed lifetimes and
benchmark rejection of output regressions. Local tests do not replace NPU
hardware execution.

## Reproduction and evidence

Remote overlay: `/notebooks/HeteroMega-kernel-opt-bf16-20261025`.
MLIR-AIE/IRON: `7e00b57955e108fe9d8e9419f5828a0c7e650858`;
Python 3.12.3, NumPy 1.26.4, pyxrt from `/opt/xilinx/xrt/python`.
Before/after platform snapshots report eight columns and **default** power.
After execution there are no active hardware contexts. Electrical telemetry
was unsupported; no power consumption was measured. No host driver or kernel
change was made. The directory date is local October 25; UTC runs are October 26.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.check_upstream \
  --suite model --output results/selected_model.json --artifact-root artifacts_v3 \
  --vector-zero --mmul-m-reuse 1 --swiglu-reuse 2 --down-reuse 4 \
  --swiglu-activation-fifo-depth 2 --down-activation-fifo-depth 1 \
  --output-layout down_a --swiglu-input-layout row_major --borrow-npu-readback
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.benchmark_upstream_optimizations \
  --artifact-root artifacts_v3 --output results/confirm_selected_abba.json \
  --profile-b combo_mmul1_row_major --order ABBA --rounds 1 --warmup 5 --iterations 50 --no-build
```

Repeat the second command with `--order BAAB` and a distinct output path.
The first command builds selected artifacts; build the baseline before
using `--no-build` on a new tree, or omit that flag. Recorded ablation,
selection and confirmation command JSONs retain the executed commands.
Graph defaults preserve the control; selecting the optimized profile is explicit.

The [main archive](kernel-opt-bf16-evidence-20261025.tar.gz) contains raw reports,
logs, all source upload versions, final sources, tested artifacts/manifests,
generated MLIR and ELFs. Its SHA256 is
`76ca2dccbbe9bda1b97535e750ae0ac400eee1b76d5af10042c1d8e8a539668d`
(11,020,877 bytes). Representative final disassembly is in the
[supplement](kernel-opt-final-disassembly.tar.gz), SHA256
`94e326b5a68dabd703b83a1bf5059cb43d2af76244c474d7820077fd4a0ede93`.
The [initial compiler archive](kernel-opt-v1-compiler-evidence.tar.gz), SHA256
`1d27d4f47902da625bf29791f08ed194449f9c482d57800cffaaede8868a56f7`,
preserves the failing 2 KiB configuration.

After extracting the main archive, replay the independent evidence audit
from the repository root:

```bash
python docs/runs/2026-10-25-kernel-optimizations/audit_evidence.py \
  /tmp/kernel-opt-bf16-evidence-20261025 --selected-dir prebuilt/selected \
  --previous-report docs/runs/2026-10-25-pipeline-bf16/pipeline_model.json \
  --archive-directory docs/runs/2026-10-25-kernel-optimizations \
  --output /tmp/rechecked-optimization-audit.json
```

Packaged MLIR is kept byte-for-byte as emitted by the compiler, including
its generated trailing whitespace. Authored source/document diffs are clean;
all package checksums pass.

The kernel-only PR uses the selected sources, generated MLIR, XCLBINs and
instructions. Harnesses and these reports remain on the local research branch.
Published package commit:
[`fc0b255`](https://github.com/glassescrab/HeteroMega/pull/3/commits/fc0b25585d5835e976302ac14910817f53a34cac),
22 files under `npu/ffn`, with all 21 payload checksums verified. The PR is
open and unmerged.
Further optimizations remain research work: dequant/MMUL overlap, broader N
reuse, SwiGLU reuse four with a new buffer allocation, device-phase tracing,
and retuning under actual GPU/attention interference. This pass does not
exhaust those redesigns or claim combined prefill acceleration.
