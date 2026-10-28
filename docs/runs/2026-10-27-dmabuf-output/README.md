# Direct-buffer FFN with GPU-owned DMA-BUF output

**Measured, October 28, 2026 (UTC):** on the HX370/default system, the selected
HeteroMega FFN configuration completes the M512/H4096/I14336 synthetic prefill
FFN in **15.887 ms** (block 0) and **15.780 ms** (block 1). The unchanged native
HeteroMosaic implementation completes the same blocks in **16.031 ms** and
**15.947 ms**. The candidate medians are **0.90%** and **1.05% lower** in the two
reversed blocks. Both blocks therefore agree that the candidate is faster, but
the distributions overlap and the margin is small.

This is an isolated synthetic complete-FFN latency comparison, not whole-model
prefill, TTFT, attention-overlap or pretrained-accuracy evidence. Both paths
run under the explicit `report` numerical policy; original failed tolerances and
error magnitudes are retained. Structural, completion and buffer-integrity
checks remain strict. The result is a performance comparison with numerical
deviations, not a demonstrated accuracy equivalence.

## Measured comparison

Each job uses 5 warmups and 100 measured samples per mode. The block order is
native → candidate, then candidate → native. Every process has its own
interleaved all-GPU control. Medians are milliseconds.

| Block | Implementation | Own GPU control | Complete FFN | Candidate/native (native ÷ candidate) |
| ---: | --- | ---: | ---: | ---: |
| 0 | Native HeteroMosaic, M256 GPU + M256 NPU gate/up | 22.248 | **16.031** | — |
| 0 | HeteroMega P4352, DMA-BUF output, teammate GPU | 22.310 | **15.887** | **1.00907** (0.90% lower) |
| 1 | HeteroMega P4352, DMA-BUF output, teammate GPU | 22.365 | **15.780** | **1.01060** (1.05% lower) |
| 1 | Native HeteroMosaic, M256 GPU + M256 NPU gate/up | 22.258 | **15.947** | — |

The candidate's matched GPU control is 0.28–0.48% slower than native's control,
so the complete-FFN advantage is slightly larger than the raw control drift but
still below 1.5% in these blocks. The candidate p10 is lower in both blocks; the
p90 intervals overlap. This is not a claim of a broad or large speedup.

The 100-sample result resolves the earlier 50-sample P4352 run, which was mixed:
the candidate won one block and lost the other. That earlier report is retained
in [exploratory/dmabuf_comparison_summary_50.json](exploratory/dmabuf_comparison_summary_50.json).
The main 100-sample evidence is in [comparison_summary.json](comparison_summary.json)
and [comparison_manifest.json](comparison_manifest.json).

## Selected configuration

- P4352 of 14336 intermediate channels on the NPU; the complementary GPU suffix.
- Eight-column/four-row NPU, 32 workers, BFP16 native layout, split-M32 A
  prefetch and preconverted B. Original 4,352-byte packed weight tiles are
  consumed directly; no NPU weight repacking.
- Shared SwiGLU output/down input BO, row-major final NPU output, and an
  imported HIP-owned output BO consumed directly by the GPU reduction.
- Teammate three-kernel GPU suffix (merged gate/up, fused activation, down).
- Gate/up and down both overlap the GPU suffix. Ordinary timing includes input
  staging, both NPU launches, BO synchronization, the GPU suffix and the final
  reduction.

The NPU branch median is about 14.39 ms. The measured GPU suffix device time in
a separate 10-sample diagnostic was about 15.03 ms, so the GPU suffix is the
critical path at this partition. The 0.27 ms input staging and 0.44–0.48 ms
output/boundary interval are measured host spans and are not additive with the
NPU branch. A 100-sample P4352 run uses 436 NPU completions per candidate job;
the two candidate jobs complete 872 NPU dispatches. Native completes 218
successful dispatches per job, or 436 across the two blocks.

## Partition and variant evidence

A 10-sample exploratory sweep with the same selected options gives complete-FFN
medians of **15.879 ms** at P4096, **15.432 ms** at P4352, and **16.080 ms** at
P4608. P4352 is the selected region. This sweep is exploratory and is not the
paired headline comparison. See [exploratory/dmabuf_full_sweep.json](exploratory/dmabuf_full_sweep.json)
and its [log](exploratory/dmabuf_full_sweep_fixed.log).

Rejected variants are retained in [exploratory/exploratory_summary.json](exploratory/exploratory_summary.json):

- **Original GPU suffix, P4352:** 16.026 ms (20 samples); the teammate GPU
  suffix measured 15.693 ms in a separate 20-sample run. The teammate suffix is
  selected, but the runs are separate processes and are not a paired ablation.
- **Preconvert-A, P4352:** 19.988 ms (10 samples). The NPU branch grows to about
  18.69 ms; not selected.
- **GPU-owned DMA-BUF input, H512/P512 smoke:** 6.530 ms versus 5.431 ms for the
  output-only smoke. Correctness passed, but NPU swiglu/down waits increased
  enough to outweigh the removed host input copy. It remains an opt-in
  experiment and is not used by the selected configuration.

## Evidence and reproduction

The comparison audit is self-contained: [audit.py](audit.py) verifies the
manifest, report hashes, fixture identity, power mode, completion counts,
candidate upload/synchronization counts and the reported ratios; it writes
[audit.json](audit.json). Source and evidence hashes are listed in
[source_manifest.json](source_manifest.json).

Hardware: AMD Ryzen AI 9 HX370, Radeon 890M/gfx1150, eight-column Strix NPU,
ROCm 7.2, Torch 2.11.0+rocm7.2, Python 3.12.3. Every boundary observes NPU power
mode `default`; no host driver or kernel was changed. Cloud roots are
`/notebooks/HeteroMosaic-baseline-20261027` and
`/notebooks/HeteroMega-direct-output-20261027`.

To reproduce, use the configured ROCm/XRT/IRON environment and a fresh output
directory:

```bash
export HETEROMEGA_ROCM_PATH=/opt/rocm-7.2.0 ROCM_PATH=/opt/rocm-7.2.0
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MAX_JOBS=2
export PATH=/notebooks/heteromega-ffn-venv/bin:$PATH
export HETEROMEGA_XRT_PYBIND_INCLUDE=/notebooks/heteromega-pybind213-build/pybind11/include
/notebooks/heteromega-ffn-venv/bin/python \
  -m experiments.ffn_partition.compare_upstream_native \
  --native-root /notebooks/HeteroMosaic-baseline-20261027 \
  --native-library /notebooks/HeteroMosaic-baseline-20261027/build/py/unified_llm_w4a16/unified_llm_w4a16_hetero_libtorch.so \
  --driver-include /notebooks/HeteroMosaic-baseline-20261027/libraries/xdna-driver-05-19-25/src/include/uapi/drm_local \
  --native-accuracy-policy report \
  --artifact-root /notebooks/HeteroMega-direct-output-20261027/artifacts \
  --no-build-candidate --npu-channels 4352 \
  --shared-intermediate --bfp16-native-layout --split-m32-a --preconvert-b \
  --swiglu-reuse 4 --gpu-variant teammate --dmabuf-gpu-output \
  --iterations 100 --warmup 5 --required-power-mode default \
  --output-dir results/dmabuf_p4352_100_reproduction
```

The candidate artifacts and the XRT/HIP bridge are cached by source and
environment fingerprints. A cold run rebuilds them; setup is excluded from the
ordinary timing boundary. Run `python audit.py --evidence-dir . --output audit.json`
from this directory to recheck the evidence.

## Limits

- Synthetic fixed W4A16 group128 weights and BF16 inputs, not a model run.
- Both implementations retain numerical deviations under report policy; the
  candidate's original tolerance verdict is failed with 216 outside-tolerance
  checks in each 100-sample job. This does not establish model accuracy.
- Native timing includes its original wrapper and redundant readiness sync;
  candidate timing includes Python/XRT orchestration. Both retain their own GPU
  controls.
- The isolated FFN must still be integrated into the causal model schedule and
  measured against native with attention interference before any whole-model
  prefill or TTFT claim is possible.
