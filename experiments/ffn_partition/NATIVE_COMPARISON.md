# Native HeteroMosaic W4A16 FFN comparison

**Measured on HX370, October 27:** native HeteroMosaic takes 15.81–15.89 ms
versus 17.48–18.03 ms for our P2560/P2816 channel partitions at M512/H4096/I14336.
Our path is 10.0–14.1% slower than native in the paired blocks, while still
beating matched GPU-only controls. Numerical failures are retained under the
explicitly authorized native report policy. The same native binary and binding
are verified across strict and report runs. [Results, stage profile, evidence
and reproduction](../../docs/runs/2026-10-27-native-comparison/README.md).
38 focused CPU tests pass; the final evidence audit verifies 1,194 files and
2,126 completed NPU dispatches.

The user explicitly authorized timing the faithful HeteroMosaic implementation
despite numerical failure. Native report mode changes acceptance policy only;
the native kernels, binding, dispatcher and timing boundary remain unchanged.
Original numerical errors and tolerance failures remain part of the evidence.

The [measured direct-buffer FFN result](../../docs/runs/2026-10-27-upstream-partition/README.md)
compares HeteroMega with matched GPU-only kernels. This experiment adds the
native heterogeneous HeteroMosaic baseline, preserving its original kernels
and dispatcher.

## Controlled workload

- Synthetic prefill FFN: M512, H4096, I14336, batch one, W4A16 group128.
- Fixed `contract.random_weights` seed 12832, BF16-rounded scales, and two
  alternating inputs. Full original packed-weight and input hashes must match
  across admitted processes before a comparison is reported.
- Ready GPU input to synchronized GPU output. Candidate staging, NPU BO I/O,
  activation layouts, both NPU launches, synchronization and GPU reduction
  are included. Setup, fixed-weight uploads/imports, CPU references and
  validation output readback are excluded, as are norm, residual and attention.
- Native HeteroMosaic: original M-split gate/up, 256 GPU + 256 NPU token rows;
  original GPU SiLU/multiply and GPU-only down. This is the recorded M512
  configuration, not a claim that all HeteroMosaic configurations use GPU down.
- HeteroMega: eight-column/32-worker SwiGLU plus down, P2560 and P2816
  intermediate channels on NPU, using the selected direct-buffer BFP16 MMUL
  and reuse/DMA options. The NPU consumes full original 4,352-byte weight tiles
  without repacking; the complementary GPU branch uses original GPU kernels.
- Each implementation retains its own interleaved all-GPU control; candidate
  jobs also retain a serial-partition control. Six ordinary jobs run in fresh
  processes: native/P2560/P2816, then P2816/P2560/native. An optional native
  stage-diagnostic job runs separately afterward.

The native adapter links an existing HeteroMosaic model shared library and calls
its original config loader, DMA-BUF import, M-split dispatcher, and GPU GEMM.
It does not reconstruct the native runtime using our XRT staging implementation.
Packed weights are prepared by the existing independently tested byte packer;
the native GPU and NPU receive the same packed bytes.

The native library hash and source hashes are recorded separately. A binary
hash alone does not prove which source produced it; retain the original build
records. Both paths must use compatible ROCm/Torch installations.

## Correctness and execution evidence

`native_heteromosaic.py` checks gate, up, and complete FFN output against the
independent BF16 reference, both across the whole tensor and separately on the
GPU/NPU row regions. Two random inputs, zero, and repeated input produce 84
explicit checks, including comparisons against the native all-GPU path.
Every warmup and timed call is checked, with full metrics and output hashes
retained. Zero, repeat and changed-input checks reject stale or broken execution.
Original host and actual GPU input/packed-weight hashes are checked before and
after execution. The existing thresholds stay fixed:
`rtol=0.03`, `atol=0.05`, relative-L2 limit `0.02`.

The adapter refuses missing configurations, failed buffer imports, GPU fallback,
or failed NPU futures. It counts two successful NPU completions per native FFN;
the driver verifies exactly `2*(4 + warmup + iterations)` per native job.
These are completed runtime submissions, not hardware utilization counters.

Native HeteroMosaic defaults to strict accuracy. Explicit
`--native-accuracy-policy report` admits faithful native timing despite numerical
deviations, while all GPU controls remain strict. The BFP16 candidate also uses
explicit report policy. Both retain original tolerance verdicts and error
magnitudes; nonfinite, stale, changed-weight or completion failures still reject
the run under either policy.
Each candidate process must complete `8 + 2*(warmup + iterations)` calls to each
of its two NPU stages and upload each fixed gate/up/down buffer exactly once.

In native strict mode, a numerical failure preserves the report and stops the
comparison by default. In native report mode, accepted numerical deviations use
status `completed_with_accuracy_deviations` and do not block timing. If native
or candidate numerical tolerances fail, the comparison retains an explicitly
labeled experimental latency ratio with both numerical verdicts and leaves
`speedup_vs_native` unset. This is a faithful-implementation performance
comparison, not evidence of numerical equivalence or model accuracy.

`--keep-going` can collect remaining independent jobs after an execution or
acceptance failure, but the final exit remains nonzero. A failed native job
still suppresses native/candidate comparisons; accepted report-mode numerical
deviations do not. Numerical thresholds themselves remain unchanged.

## Commands

Run from the repository root. These faithful native timing commands have
executed on the cloud host. Reuse the configured AUP runtime and compiler environments;
this harness does not require host driver or kernel changes.

CPU preparation, without Torch or accelerator access:

```bash
python -m experiments.ffn_partition.native_heteromosaic \
  --native-root . --prepare-only --output /tmp/native-ffn-prepared.json
python -m experiments.ffn_partition.compare_upstream_native \
  --native-root . --artifact-root experiments/ffn_partition/artifacts \
  --no-build-candidate --native-accuracy-policy report --native-diagnostic \
  --plan-only --output-dir /tmp/native-ffn-plan
```

On AUP, set `NATIVE_ROOT` to the pinned native checkout,
`HETEROMOSAIC_NATIVE_LIBRARY` to its verified model `.so`, and
`NATIVE_DRIVER_INCLUDE` to its matching headers directory containing
`amdxdna_accel.h`. Set `UPSTREAM_ARTIFACT_ROOT` to the direct-buffer candidate
cache. Retain the native build records, library hash and selected PDI/instruction
hashes; a source checkout alone does not establish binary provenance.

```bash
export HETEROMEGA_ROCM_PATH=/opt/rocm-7.2.0
export ROCM_PATH=/opt/rocm-7.2.0
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
/notebooks/heteromega-ffn-venv/bin/python \
  -m experiments.ffn_partition.compare_upstream_native \
  --native-root "$NATIVE_ROOT" \
  --native-library "$HETEROMOSAIC_NATIVE_LIBRARY" \
  --driver-include "$NATIVE_DRIVER_INCLUDE" \
  --native-accuracy-policy report \
  --artifact-root "$UPSTREAM_ARTIFACT_ROOT" --no-build-candidate \
  --npu-channels 2560,2816 --iterations 50 --warmup 3 \
  --native-diagnostic --diagnostic-iterations 10 \
  --required-power-mode default \
  --output-dir experiments/ffn_partition/results/native_comparison_01
```

The two reversed blocks are fixed. Omit `--native-diagnostic` for ordinary jobs
only. Omit `--native-accuracy-policy report` to retain the strict default.
`--no-build-candidate` validates the existing cache without compiling;
to build or refresh it, replace that flag with `--iron-python "$IRON_PYTHON"`,
where the variable names the configured IRON interpreter. ROCm/PyXRT execution
still uses the main runtime interpreter.

Use a fresh output directory. The driver saves commands, source hashes, logs,
raw reports, report hashes, and NPU power snapshots before/after every process.
It observes power mode without changing it; the example requires the previously
observed `default` mode. Different observed modes suppress the cross-process
comparison. Summary fixture-match fields cover successfully admitted reports;
they do not validate a failed native run.

## Profiling interpretation

- Ordinary native and HeteroMega medians/p10/p90 describe complete FFN calls.
  Native wall time includes the Python-to-C++ adapter call and a conservative
  redundant readiness sync inside the binding; `binding_wall_us` is retained
  separately. Candidate timing uses `TimedFFN` with Python/XRT orchestration.
  These different wrappers and their own GPU controls must remain visible;
  the comparison measures complete paths, not isolated kernel performance.
- Native diagnostics synchronize gate/up, pointwise, and down boundaries.
  They perturb scheduling and must not supply the ordinary speedup headline.
- Candidate ordinary reports retain host NPU branch, submission/wait, staging
  and layout measurements. These spans overlap concurrent GPU work, and the
  output-boundary span can include waiting for it. Do not add them to infer
  device-only phase durations or compare them directly with native synchronized
  stage diagnostics. This driver does not schedule candidate diagnostic jobs.
- A host NPU wait includes runtime, DMA, computation, stalls and completion.
  It is neither pure data movement nor a direct NPU hardware execution timer.
- Separate-process GPU controls expose drift but do not correct it. Power
  snapshots are boundary observations, not continuous clocks/thermal telemetry.
- A complete isolated FFN improvement would still require integration and
  measurement with the original attention/chunk schedule before claiming
  whole-model prefill or TTFT acceleration.
