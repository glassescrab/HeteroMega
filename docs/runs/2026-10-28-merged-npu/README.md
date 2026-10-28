# Single-dispatch merged NPU FFN

**Exploratory result, October 28, 2026:** a new single-dispatch NPU graph that
runs gate/up + SiLU and down on the same 32 workers completes the synthetic
M512/H4096/I14336 prefill FFN in **14.274 ms** and **14.585 ms** in two
reversed 100-sample confirmation blocks. Faithful native HeteroMosaic completes
the same blocks in **15.851 ms** and **15.874 ms**. The merged candidate is
**9.95%** and **8.12%** faster. A preceding repeat measured 11.1%/12.5%; the
retained confirmation uses the corrected NPU-partial validation and is the
result reported here. This is still a substantially larger margin than the
previous two-launch P4352 result (0.90%/1.05%).

This is an isolated synthetic complete-FFN latency result under explicit
`report` numerical policy, not whole-model prefill, TTFT, attention-overlap or
pretrained accuracy. Native and candidate both retain failed original
tolerances; structural and completion checks pass. The merged graph is an
experimental branch, not the production two-launch path.

## Measured comparison

Each job uses 5 warmups and 100 measured samples per mode. Block 0 runs native
then merged; block 1 runs merged then native. Every job has its own interleaved
all-GPU control.

| Block | Implementation | Own GPU control | Complete FFN | Native ÷ candidate |
| ---: | --- | ---: | ---: | ---: |
| 0 | Native HeteroMosaic, M256/M256 gate/up | 22.169 | **15.851** | — |
| 0 | Merged NPU P6400 + teammate GPU suffix | 22.331 | **14.274** | **1.1105** (9.95% lower) |
| 1 | Merged NPU P6400 + teammate GPU suffix | 22.275 | **14.585** | **1.0884** (8.12% lower) |
| 1 | Native HeteroMosaic, M256/M256 gate/up | 22.197 | **15.874** | — |

The candidate's GPU control is only 0.35–0.73% slower than native's, while its
complete FFN is 8.1–10.0% faster. The merged NPU branch is about
**12.47–12.72 ms** at P6400; the GPU suffix is about **13.5–13.8 ms** and
remains the critical path. The candidate still gets its win by shortening the
NPU branch enough to move a much larger channel share to the NPU (P6400 versus
P4352).

Raw evidence: [b0 native](b0_native.json), [b0 merged](b0_p6400.json),
[b1 merged](b1_p6400.json), [b1 native](b1_native.json). The files contain
every warmup/sample, both GPU controls, diagnostics, output hashes and
correctness records.

## Partition and parallelism

- **P6400 / 14336 = 44.64%** of intermediate channels on the NPU; the GPU owns
  **7936 / 14336 = 55.36%**. Both branches process all M512 rows.
- The NPU computes gate/up, SiLU×up and down for its channel prefix. The GPU
  computes the complementary gate/up and down suffix. The complete output is
  the sum of the two down partials.
- **One XRT launch**, not two: phase 1 runs gate/up + SiLU, phase 2 runs down.
  The same 32 workers (8 columns × 4 rows) execute both phases.
- The A/W ObjectFifos are **shared across phases**. Row-major A is used for x
  and row-major Z, so one memory-tile stream permutation serves both.
- One output join per column is **reused**: odd columns drain Z in phase 1 and
  Y in phase 2; even columns drain Y only. This avoids a second output join on
  the odd columns and fits the 64 KiB core memory budget.
- Z and Y output FIFO depths are 1 for this prototype; that is a memory-fit
  choice, not a proven optimum. Host input staging and an NPU-output H2D copy
  remain in the complete-FFN boundary.

The single-dispatch graph compiles at 64 KiB core memory. A naive version with
separate Z and Y joins overflowed the memory-tile DMA channels; a version with
two joins on odd columns overflowed core memory. The shared row-major join plus
depth-one output FIFOs is the working fit.

## Partition sweep

Five-sample exploratory runs with the same merged graph and teammate GPU suffix:

| NPU channels | NPU share | Complete FFN, ms |
| ---: | ---: | ---: |
| 4352 | 30.36% | 15.569 |
| 6144 | 42.86% | 14.184 |
| **6400** | **44.64%** | **13.867** |
| 6656 | 46.43% | 14.348 |

The 100-sample blocks above confirm P6400. P6656 makes the NPU/down side longer
again; P6400 is the best tested balance. These are exploratory sweep values, not
the headline paired comparison.

## Correctness

At P4352 the merged output is **bit-exact** to the existing two-launch
candidate for both alternating inputs:
[merged-vs-two-launch records](p4352_exact_compare.json) show
`merged_vs_two_launch_relative_l2: 0.0` and matching output hashes. This
establishes that the merged graph preserves the existing kernel arithmetic and
only changes launch/dataflow structure.

At P6400 both 100-sample jobs are `completed_with_accuracy_deviations` with
`accepted: true` under report policy. Native has 132 outside-tolerance checks
per job; the merged complete-output checks pass under report policy. The
validation records also check the NPU and GPU partials; six validation checks
fall outside the original tolerance. No accuracy equivalence is claimed.

The source and artifact contracts remain the standard upstream W4A16 group128
fixtures: full packed weight hashes and input hashes match across the native and
merged jobs. The merged NPU consumes the original 4,352-byte weight tiles; no
weight repacking.

## Reproduction

The working source is on `codex/npu-merged-kernel-parallel`. The new graph is
`npu/ffn/w4a16_merged_upstream.py`; the adapter/timer are
`experiments/ffn_partition/merged_npu.py` and
`experiments/ffn_partition/run_merged_partition.py`. The production two-launch
graph is unchanged.

Build the merged artifact and run the complete FFN:

```bash
export HETEROMEGA_ROCM_PATH=/opt/rocm-7.2.0 ROCM_PATH=/opt/rocm-7.2.0
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MAX_JOBS=2
export PATH=/notebooks/heteromega-ffn-venv/bin:$PATH
/notebooks/heteromega-ffn-venv/bin/python \
  -m experiments.ffn_partition.run_merged_partition \
  --m 512 --hidden 4096 --intermediate 14336 --npu-channels 6400 \
  --artifact-root /notebooks/HeteroMega-direct-output-20261027/artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --gpu-variant teammate --warmup 5 --iterations 100 \
  --output results/merged_p6400_confirmation.json
```

The merged artifact is cached under `artifacts/upstream_merged_bfp16_m512_h4096_p6400_*`.
The native comparison command is the same one used in the 2026-10-27 faithful
comparison, with `--mode latency --npu-rows 256 --accuracy-policy report`.

## Limits and next steps

- Isolated synthetic FFN only; no full-model prefill/TTFT or attention
  interference measurement.
- Report-policy numerical deviations; no accuracy or model-equivalence claim.
- The merged graph is a sibling experimental copy; production dispatch is still
  the two-launch path.
- The next optimization is a DMA-BUF/zero-copy output for the merged kernel to
  remove the remaining NPU-output H2D copy, then retune P. A deeper fused Z
  residency or down-weight prefetch is a further step, not demonstrated here.
- GPU-side follow-up experiments are in
  [2026-10-28-gpu-suffix](../2026-10-28-gpu-suffix/README.md): GEMM autotune
  selects the existing generic kernel, and a pre-dequantized PyTorch BF16 suffix
  is faster in isolation but slower under NPU concurrency. The follow-up
  role-specialized split-Z prototype is also rejected (19.191/21.588 ms versus
  13.867 ms); see [the split-Z report](../2026-10-28-split-z/README.md).
