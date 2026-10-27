# Faithful HeteroMosaic versus HeteroMega FFN

**Measured, October 27, 2026:** on HX370 at M512/H4096/I14336, native
HeteroMosaic completes the FFN in **15.81–15.89 ms**, while our direct-buffer
channel partitions take **17.48–18.03 ms**. Our implementation is **10.0–14.1%
slower than the native heterogeneous FFN** in the paired blocks. It still
reduces latency by 18.8–21.6% against its matched GPU-only control.

The user explicitly authorized timing a faithful HeteroMosaic implementation
regardless of numerical failures. These are implementation latency comparisons:
the original native binary and scheduling are unchanged, numerical errors are
retained, and native report policy permits timing. No accuracy equivalence is
asserted. This is an isolated synthetic **prefill FFN**, not a reproduction of
HeteroMosaic's whole-model paper numbers or TTFT.

## Ordinary complete FFN latency

Each row has 50 measured samples per mode after three warmups. The second block
reverses the order of fresh implementation processes. Every process interleaves
its own GPU-only control; candidate jobs also retain serial-partition controls.
All values below are medians in milliseconds. Comparisons use ordinary wall
samples, excluding the separate stage diagnostic.

| Block/order | Implementation | Own GPU-only control | Complete FFN | Relative to native in block |
| --- | --- | ---: | ---: | ---: |
| 0, first | Native HeteroMosaic, M256 GPU + M256 NPU gate/up | 22.267 | **15.811** | baseline |
| 0, second | HeteroMega, P2560 NPU channels | 22.214 | 18.034 | 14.06% slower |
| 0, third | HeteroMega, P2816 NPU channels | 22.229 | 17.681 | 11.82% slower |
| 1, first | HeteroMega, P2816 NPU channels | 22.295 | 17.481 | 9.99% slower |
| 1, second | HeteroMega, P2560 NPU channels | 22.447 | 17.669 | 11.18% slower |
| 1, third | Native HeteroMosaic, M256 GPU + M256 NPU gate/up | 22.381 | **15.893** | baseline |

Native reduces latency by about 29.0% against its own GPU control. Matched GPU
controls between native and each candidate differ by less than 0.4% within each
block, much less than the native/candidate gap. P2816 wins both new blocks,
but earlier runs reversed the P2560/P2816 ranking; this is not a global optimum.

Raw results and commands are in the
[manifest](results/faithful_comparison/comparison_manifest.json) and
[raw-sample summary](results/faithful_comparison/comparison_summary.json).
The summary retains `native_over_candidate_latency_ratio` and labels the
comparison `experimental_latency_with_numerical_deviations`; the separate
accuracy-validated speedup field remains unset. Numerical acceptance policy does
not alter the wall samples or this performance comparison.

## Faithfulness and controls

**Code-confirmed and build-audited:** the native library is rebuilt from pinned
HeteroMosaic source `61714a3147f34857aa5dfef21a28e762777a2df0`, with the recorded
four-file XDNA runtime compatibility port and two ROCm/Torch build adjustments.
Those adaptations change heap alignment, padded ioctl fields, duplicate BO
residency handling, completion waiting, ROCm paths and removed Torch type names;
they do not change model math, GPU/NPU kernels, partitioning or scheduling.

The thin binding calls the original config loader, shared HIP DMA-BUF import,
M-split dispatcher and GPU kernels from that compiled model library. It issues
original gate/up work, waits for their completion, performs GPU BF16 SiLU and
multiply, and runs original GPU down. Both projections use the original
`256x4096x14336_64x128x64_8c_bf16_int4AWQ_bf16` PDI/instruction pair. Native
NPU completions are counted only after actual successful futures; GPU fallback
is rejected. No host driver, kernel or firmware was changed.

The same native `.so` and binding hashes are present in the initial strict
failure, the report-policy smoke, both ordinary blocks and the diagnostic.
[Native build result](native_build_result.json) and
[source/patch provenance](native_build_provenance.json) identify the binary.
Its SHA256 is `6fa53d1cb6fd24e87a639b0d2f5a7d007d00eaac78fed45bca2af4a66b121b8b`.
The policy-only implementation is commit `1e30f8a`; binding, native library,
inputs, weights and timing boundaries did not change.

Both implementations receive identical synthetic unsigned W4A16 group128
weights, seed12832, and BF16 inputs, seed12833. Actual device weight hashes,
original packed-buffer hashes and input hashes match across all native and
candidate processes, including failed strict runs. The NPU candidate consumes
original 4,352-byte tiles directly, with eight columns/32 workers, BFP16 MMUL,
SwiGLU reuse2, down reuse4 and the selected DMA layouts. No NPU weight repacking
was added. GPU arithmetic/control checks remain strict.

Timing starts with ready GPU input and ends with synchronized GPU output.
Candidate GPU/host staging, XRT BO I/O, layouts, launches, waits and final GPU
partial-output sum are included. Setup, fixed-weight packing/import/upload,
CPU oracles and validation readbacks are excluded. Norm, residual, attention and
model scheduling are outside the workload. Native's Python-to-C++ dispatch and
redundant in-binding readiness sync remain included; its inner timer is also
recorded. Separate GPU controls expose these wrapper differences.

Hardware: AMD Ryzen AI 9 HX370, Radeon 890M/gfx1150, eight-column Strix NPU,
ROCm 7.2, Torch 2.11.0+rocm7.2, Python 3.12.3, NumPy 1.26.4. This is **not**
Ryzen AI Max+ 395. Every measurement boundary reports NPU power mode `default`;
final context snapshots show no active NPU contexts. The original native
M256/M256 split is a fixed reproduced configuration, not a fresh optimal
partition search for HeteroMosaic on this host.

## Where the time goes

The separate native diagnostic uses ten samples per mode, after three warmups,
with synchronization between stages. Its barriers perturb scheduling, so these
stage medians explain the paths and do not replace ordinary FFN latency.

| Synchronized stage | GPU-only, ms | Native heterogeneous, ms |
| --- | ---: | ---: |
| Both gate/up projections completed | 14.511 | 7.872 |
| SiLU and multiplication | 0.838 | 0.865 |
| GPU down projection | 7.044 | 7.010 |

Native gains about 6.64 ms at gate/up in this diagnostic. It retains full GPU
down; down is therefore still a large part of its FFN. Gate/up includes both
GPU and NPU completion and host futures, not isolated NPU compute cycles.
[Raw stage report](results/faithful_comparison/jobs/b0_native_diagnostic.json).

**Code-confirmed differences that guide the next optimization:** native
assigns half of each gate/up projection to NPU, or one-third of the three
projections' MACs. Our P2560/P2816 paths assign only 17.86%/19.64% of projection
MACs to NPU, leaving more work on the GPU. Native NPU writes disjoint row regions
straight into shared HIP gate/up outputs; it has no concatenate or final
partial-output sum. Our persistent channel ownership still stages intermediate
Z between separate NPU launches and copies the down partial back for GPU
reduction. It does not preserve Z on-chip across those launches.

**Measured host telemetry:** our concurrent NPU branch alone takes 14.70–15.52 ms,
almost as long as the native complete FFN. Output-layout conversion takes
0.97–1.40 ms; surrounding BO I/O takes about 0.68–0.75 ms per launch. The input
copy takes about 0.258 ms and the mixed final staging/reduction/GPU-wait interval
1.07–2.52 ms. These intervals nest or overlap and must not be added.
Paired concurrent/serial NPU wait ratios are only 1.001–1.031, so these data do
not support a large concurrency-induced NPU slowdown. Native wrapper overhead
is about 25 microseconds, far too small to explain the gap. See
[recomputed telemetry](analysis.json) and its [analysis script](analyze.py).

These differences do not by themselves quantify the cause of the gap. Candidate
NPU waits include runtime, DMA, compute and stalls. Its final boundary interval
also includes any unfinished GPU suffix, so it cannot be called pure transfer
cost. Nested/overlapping host intervals must not be added or subtracted to infer
GPU compute. The next useful work is to reduce host/XRT activation staging and
measure the GPU suffix with device events before changing the partition ratio
or claiming a specific hardware bottleneck.

## Numerical evidence retained

The initial strict run stopped, as did two fresh strict reproductions. The
subsequent explicit user instruction authorized report policy for faithful
native timing. All successful native report runs retain the original error
bounds and failed verdicts, while enforcing finite outputs, zero/change/repeat
checks, unchanged buffers and successful completion. No native arithmetic was
fixed or substituted to obtain the timings.

Native full-output relative L2 reaches 0.116976 with maximum absolute error
0.732421875 against the CPU oracle; native GPU-owned rows pass. Both 50-sample
native jobs retain 80 outside-tolerance checks out of 190. All candidate checks
pass the original bounds; worst NPU-partial relative L2 is 0.0172392. These error
magnitudes are reported, not used to block the authorized latency comparison.

Untimed probes give exact results for constant exact inputs and representative
one-hot q/zero/scale coordinates. Constant weights with signed random inputs
still fail; captured row vectors show identical columns and a one-sided negative
bias. None of 20 simple grouped nearest/truncate BF16-rounding models reproduces
the captured outputs. This narrows investigation toward arithmetic in reductions
but does not identify the compiled instruction causing it. See the
[projection probes](results/native_projection_diagnostic.json),
[captured row values](results/native_constant_vectors.json) and
[offline hypothesis analysis](rounding_analysis.json).

## Evidence and reproduction

The [audit](audit.json) passes all 1,194 exported file hashes, pinned source and
patch replay, native library/binding/PDI provenance, candidate artifacts,
fixture and buffer integrity, raw power snapshots, completion counts and
raw-sample summaries. It preserves each comparison's exact archived validator.
Across strict, report, candidate and untimed runs, **2,126 NPU dispatches
complete**. Hardware integrity success does not relabel numerical failures.
38 focused CPU tests pass for the native wrapper, comparison driver, projection
diagnostics and legacy strict controls.

- [Final hardware evidence](hardware-evidence.tar.gz): 6,521,672 bytes;
  SHA256 `2f45eab5bfd20a624c2e81b92ea7b147e3e7551823dd4bc9b5ffb4b8d12569dc`.
- [Earlier strict evidence](strict-hardware-evidence.tar.gz): 6,324,007 bytes;
  SHA256 `99923159a057dddef27527ecd8a3e8ebc68976b2e0d831fdc3d335bd720b8686`.
- [Pinned build payload](native-heteromosaic-baseline-20261027.tar.gz) includes
  exact original sources, PDI/instructions, pinned XDNA UAPI and bootstrap.
- Harness snapshots and later policy changes are preserved as separate archives
  and hash manifests; original failed and successful reports are not overwritten.

Cloud roots are `/notebooks/HeteroMosaic-baseline-20261027` and
`/notebooks/HeteroMega-native-comparison-20261027`. The candidate cache is
`/notebooks/HeteroMega-upstream-partition-20261027/artifacts`.
After extracting the build payload under `/notebooks`, build with
`bash /notebooks/native-heteromosaic-baseline-20261027/bootstrap.sh`.
Then, from the comparison overlay with the existing ROCm/XRT environment:

```bash
export HETEROMEGA_ROCM_PATH=/opt/rocm-7.2.0 ROCM_PATH=/opt/rocm-7.2.0
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MAX_JOBS=2
export PATH=/notebooks/heteromega-ffn-venv/bin:$PATH
/notebooks/heteromega-ffn-venv/bin/python \
  -m experiments.ffn_partition.compare_upstream_native \
  --native-root /notebooks/HeteroMosaic-baseline-20261027 \
  --native-library /notebooks/HeteroMosaic-baseline-20261027/build/py/unified_llm_w4a16/unified_llm_w4a16_hetero_libtorch.so \
  --driver-include /notebooks/HeteroMosaic-baseline-20261027/libraries/xdna-driver-05-19-25/src/include/uapi/drm_local \
  --native-accuracy-policy report \
  --artifact-root /notebooks/HeteroMega-upstream-partition-20261027/artifacts \
  --no-build-candidate --npu-channels 2560,2816 --iterations 50 --warmup 3 \
  --native-diagnostic --diagnostic-iterations 10 --required-power-mode default \
  --output-dir results/faithful_comparison_repeat
```

Use a fresh output directory. To audit locally, extract the final evidence
archive and run `python audit.py --evidence-dir EXTRACTED_DIR --output audit.json`.
No trained weights or model download is needed for this bounded experiment.
