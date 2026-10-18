# Profiling reproduction and evidence

See [the report](../../profiling-2026-10-14.md) for interpretation and limits.
These commands run in the AUP Linux terminal, not Windows. No weights or packages
need to be downloaded; use the already established cloud environment in
[cloud-baseline.md](../../cloud-baseline.md) and
[runtime-compatibility.md](../../runtime-compatibility.md).

## Normal measurements

Copy the reusable scripts beside this README into a **fresh** cloud output
directory. The October 14 artifacts already exist and should be preserved.
Set `HETEROMEGA_PROFILE_DIR` to that fresh directory when rerunning the updated
runner/instrumenter. The exact older versions used on October 14 are also retained
in `evidence/`; later helper changes only add rerun safeguards/output-directory
selection and remove an unused, unmeasured configuration choice.

```bash
source /notebooks/heteromosaic-venv/bin/activate
unset PYTHONPATH HSA_OVERRIDE_GFX_VERSION LD_PRELOAD
export HOME_LIBS=/notebooks/heteromosaic-libraries
export HETEROMOSAIC_ROOT=/notebooks/HeteroMosaic-baseline
export ROCM_PATH=/opt/rocm-7.2.0
export LD_LIBRARY_PATH=/opt/rocm-7.2.0/lib:/opt/xilinx/xrt/lib
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1
# Choose a fresh directory and copy the updated scripts into it before running.
export HETEROMEGA_PROFILE_DIR=/notebooks/heteromega-profile-rerun
export OUT="$HETEROMEGA_PROFILE_DIR"
cd "$HETEROMOSAIC_ROOT"

for variant in gpu_native hetero_serial gpu_matched hetero_pipeline; do
  timeout 240s python "$OUT/profile_model.py" "$variant" \
    > "$OUT/$variant-baseline.log" 2>&1
done
```

Defaults are one excluded warmup and five measured generations per configuration.
The runner captures C++ output per call, checks the fixed input SHA, saves output
IDs and fallbacks, and records synchronized wall time plus runtime prefill/decode
timers. Each generation has eight output tokens but only seven decode iterations.

## Temporary diagnostics

Back up the current extension `.so` before modifying the cloud source; keep it
outside the build tree. `instrument_stages.py` backs up the model/NPU source into
the output directory, adds Llama-only stage boundaries and NPU host-phase timestamps,
and rejects reapplication to an instrumented model. It preserves model math.

```bash
python "$OUT/instrument_stages.py"
cmake --build build --target unified_llm_w4a16_hetero_libtorch -j2
gcc -shared -fPIC \
  -I/notebooks/heteromosaic-libraries/xdna-driver-05-19-25/src/include/uapi/drm_local \
  -I/usr/include/libdrm "$OUT/profile_ioctls.c" -ldl -o "$OUT/profile_ioctls.so"

for variant in gpu_matched hetero_serial hetero_pipeline; do
  trace=sync
  if [ "$variant" = hetero_pipeline ]; then trace=host; fi
  name="$variant-detail-$trace"
  timeout 240s env LD_PRELOAD="$OUT/profile_ioctls.so" \
    HETEROMEGA_IOCTL_LOG="$OUT/$name.ioctl.csv" \
    HETEROMEGA_NPU_TRACE="$OUT/$name.npu.csv" \
    python "$OUT/profile_model.py" "$variant" --trace "$trace" \
      --tag detail --repeats 2 > "$OUT/$name.log" 2>&1
done

name=hetero_serial-overhead-none
timeout 240s env LD_PRELOAD="$OUT/profile_ioctls.so" \
  HETEROMEGA_IOCTL_LOG="$OUT/$name.ioctl.csv" \
  HETEROMEGA_NPU_TRACE="$OUT/$name.npu.csv" \
  python "$OUT/profile_model.py" hetero_serial --tag overhead --repeats 2 \
    > "$OUT/$name.log" 2>&1

for variant in gpu_matched hetero_serial; do
  timeout 240s python "$OUT/profile_model.py" "$variant" \
    --tag kineto --repeats 1 --torch-profile > "$OUT/$variant-kineto.log" 2>&1
done
```

The Kineto pass executes one additional generation after its recorded calls.
Its GPU events are diagnostic, not additional normal latency samples.

## Analyze and restore

`analyze.py DIRECTORY` reads the raw results and produces `analysis.json` and
`baseline-summary.csv`. It also reads losslessly zipped raw GPU traces. `plot.py
DIRECTORY` makes the PNG/SVG figure with matplotlib. On this cloud the existing
`/home/mliraie/mlir-aie/ironenv/bin/python` supplies matplotlib; inference uses
the separate ROCm venv. No packages were installed for profiling.

NPU CSV columns, without a header, are:
`start_ns, created_ns, input_ready_ns, locked_ns, submitted_ns, done_ns, hw_index, inst_index`.
All clocks are monotonic. On this exact configuration, instruction indices 0–8
are prefill, 9 is gate decode, and 10 is the configured down GEMV that falls back.
Do not reuse that mapping blindly for another config; use its kernel-loading map.
The ioctl CSV has a header and includes setup and warmup as well as measured calls.
Unsupported legacy waits are expected; successful timeline waits establish completion.

After all profiling processes finish, restore `model-before-profiling.cpp` and
`npu-before-profiling.cpp` to their original source paths, ensuring their timestamps
are newer than the instrumented objects, then rebuild the extension. The session
also restored its saved baseline `.so` before the rebuild. `restore-status.json`,
`build-restored.log` and `source-status-after.txt` record restoration verification.
Do not reset to Git HEAD: that would discard the earlier compatibility work.

The large Chrome traces are stored as `evidence/gpu-kernel-traces.zip`; unzip them
locally to inspect with a trace viewer. GPU trace counts and categories support
the report, but synchronization/collection overhead and the recorded ROCTracer
duplicate-flow warning limit precise timing conclusions.
