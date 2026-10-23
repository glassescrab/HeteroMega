# Native HeteroMosaic W4A16 FFN comparison

**2026-10-21 status: implemented locally; hardware compilation and execution
are pending. No new latency, profile, or speedup is established.** The browser
connection is unavailable in this session, and the local machine has an NVIDIA
GPU without an AMD NPU or ROCm. The prepared AUP environment must be reconnected
to execute this experiment.

Local verification passes21 CPU tests, Python compilation, and the nine-job
dry plan. The existing packing tests require the experiment directory on
`PYTHONPATH`; no accelerator test was substituted with CPU execution.

The earlier 22.293 → 19.643 ms result compares our channel-partition FFN with
HeteroMosaic's GPU-only kernels. It does not compare against the native
HeteroMosaic GPU–NPU FFN. This experiment adds that missing baseline while
preserving the original kernels and dispatcher.

## Controlled workload

- Synthetic prefill FFN: M512, H4096, I14336, batch one, W4A16 group128.
- Same `contract.random_weights` seed12832, BF16-rounded scales, and two
  alternating inputs as the existing channel-partition experiment.
- Ready GPU input to synchronized GPU output; normalization, residual,
  attention, setup, packing/imports, references, and validation readback excluded.
- Native HeteroMosaic: original M-split gate/up, 256GPU +256NPU token rows;
  original GPU SiLU/multiply and GPU-only down. This is the recorded M512
  configuration, not a claim that all HeteroMosaic configurations use GPU down.
- HeteroMega: eight-column SwiGLU plus down, P1024 and P1152 intermediate
  channels on NPU; unchanged GPU kernels and GPU partial-output reduction.
- Each implementation retains its own all-GPU control. Ordinary jobs run in
  two blocks with variant order reversed; diagnostics are separate jobs.

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
GPU/NPU row regions. Two random inputs, zero, and repeated input produce84
explicit checks, including comparisons against the native all-GPU path.
Each timed call is also checked. The existing thresholds stay fixed:
`rtol=0.03`, `atol=0.05`, relative-L2 limit0.02.

The adapter refuses missing configurations, failed buffer imports, GPU fallback,
or failed NPU futures. It counts two successful NPU completions per native FFN;
the driver verifies exactly `2*(4 + warmup + iterations)` per native job.
These are completed runtime submissions, not hardware utilization counters.

If the historical native random-W4A16 numerical failure recurs, failing
per-stage/per-owner metrics are saved and the comparison stops. A numerically
invalid run cannot become a speedup result. Do not relax thresholds to finish
the performance table.

## Commands

Run from the repository root. These commands are prepared, not hardware-tested
in this session. Existing AUP runtime and compiler environments should be reused;
no driver, kernel, or system package changes are required by this harness.

CPU preparation, without Torch or accelerator access:

```bash
python -m experiments.ffn_partition.native_heteromosaic \
  --native-root . --prepare-only --output /tmp/native-ffn-prepared.json
python -m experiments.ffn_partition.compare_native \
  --plan-only --output-dir /tmp/native-ffn-plan
```

On AUP, first locate the existing model library under
`/notebooks/HeteroMosaic-baseline/build/py/unified_llm_w4a16/` and set
`HETEROMOSAIC_NATIVE_LIBRARY` to that actual `.so` path. Confirm its build
provenance and the selected native artifact files before execution.

```bash
export HETEROMEGA_ROCM_PATH=/opt/rocm-7.2.0
export ROCM_PATH=/opt/rocm-7.2.0
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export IRON_PYTHON=/home/mliraie/mlir-aie/ironenv/bin/python

/notebooks/heteromega-ffn-venv/bin/python \
  -m experiments.ffn_partition.compare_native \
  --native-root /notebooks/HeteroMosaic-baseline \
  --native-library "$HETEROMOSAIC_NATIVE_LIBRARY" \
  --driver-include /notebooks/heteromosaic-libraries/xdna-driver-05-19-25/src/include/uapi/drm_local \
  --artifact-root experiments/ffn_partition/artifacts \
  --npu-channels 1024,1152 --iterations 30 --diagnostic-iterations 10 \
  --blocks 2 --warmup 3 \
  --output-dir experiments/ffn_partition/results/native_comparison_01
```

Use a fresh output directory. The driver preserves commands, source hashes,
logs, raw reports, and NPU power snapshots before/after every process. It stops
on any failed job. It never changes power mode; optional
`--required-power-mode performance` requires an actually reported performance
mode. Earlier AUP runs reported `default`, and requests to change it failed.

## Profiling interpretation

- Ordinary native and HeteroMega medians/p10/p90 describe complete FFN calls.
  Native wall time includes the Python-to-C++ adapter call; its inner C++
  boundary is retained separately. Native uses one binding call, whereas the
  candidate retains its Python/XRT orchestration. That is a runtime difference
  included in the complete-path comparison, not isolated kernel performance.
- Native diagnostics synchronize gate/up, pointwise, and down boundaries.
  They perturb scheduling and must not supply the ordinary speedup headline.
- HeteroMega diagnostics retain separate GPU HIP event intervals, NPU host
  submission/wait intervals, staging, CPU layout, and reduction measurements.
  Their timing semantics differ from synchronized native stage intervals.
- A host NPU wait includes runtime, DMA, computation, stalls and completion.
  It is neither pure data movement nor a direct NPU hardware execution timer.
- Separate-process GPU controls expose drift but do not correct it. Power
  snapshots are boundary observations, not continuous clocks/thermal telemetry.
- A complete isolated FFN improvement would still require integration and
  measurement with the original attention/chunk schedule before claiming
  whole-model prefill or TTFT acceleration.
