# AUP runtime compatibility investigation

## Status, 2026-10-13

The direct-XDNA launch failures are resolved in an **experimental runtime port**
against source commit `61714a3147f34857aa5dfef21a28e762777a2df0`.
The packed W4A16 numerical gate remains open. Do not call this a validated
heterogeneous baseline or use its timings as a speedup result.

Publication update, 2026-10-15: these four-file changes are now included in the
repository source. The saved `runtime-compat.patch` remains a reproduction
artifact for the starting commit; do not reapply it to the updated source.
The later [profiling report](profiling-2026-10-14.md) records conditional timings
and explicitly retains the unresolved numerical gate.

A full 32-layer real-weight model run now has confirmed NPU execution and
matches the fixed GPU workload's eight generated tokens. This establishes
functional execution, not general model accuracy or numerical equivalence.

The cloud uses the previously documented ROCm 7.2/Torch 2.11 environment and
XDNA driver source `bd02f5e75f7788dfbe0f3f716de928de1e7078f3`. The old UAPI
headers remain pinned to `0e6d303b2cc2b3fe1cf10aba0acbf57a422588fb`.
No host kernel, driver, firmware, or IRON environment was changed.

## Measured causes and changes

1. **Device heap mapping alignment.** With current headers, an ordinary
   `mmap` of the 64 MiB heap led to context-creation `EINVAL`; an explicitly
   64 MiB-aligned mapping succeeded for 32- and 4-tile contexts. `alloc_heap`
   now reserves its own virtual-address range before replacing an aligned
   slice with the device mapping. It checks failures and cleans up the
   reservation/BO on failure. `MAP_FIXED` only replaces our own reserved pages.
2. **Reserved/padded configuration bytes.** A standalone probe using the
   baseline PDI passed context creation but failed CU configuration. Zeroing
   the CU parameters and allocating zeroed QoS storage rounded to eight bytes
   made that probe pass. The pinned QoS structure is 28 bytes; this driver
   reads 32. Column zero is suitable for the tested full-width 8-column PDIs.
   This is a targeted adaptation, not general UAPI version negotiation.
3. **Duplicate residency handles.** The first submission contained handles
   `[5,2,2,3]`: input and weights shared one HIP allocation/imported GEM BO.
   The driver's reservation locking rejected duplicates with `EALREADY`.
   Both command builders now compact the residency list to unique handles;
   logical tensor addresses in the command are preserved.
4. **Completion API.** Submission then succeeded, but the old WAIT_CMD ioctl
   returned `EOPNOTSUPP`. A shared helper first tries legacy WAIT_CMD and falls
   back only on `EOPNOTSUPP`/`ENOTTY` to the context's DRM timeline sync object,
   using the returned sequence number and an absolute monotonic deadline.
   Other errors propagate. Existing 500/800 ms timeout values are retained.

Changed files: `include/npu_matmul_func/npu_util.hpp`,
`include/npu_matmul_func/npu_matmul_func.hpp`,
`src/npu_matmul_func/npu_matmul_func.cpp`, and
`src/unified_llm_w4a16_hetero/npuSetup.cpp`. Model math, HIP/NPU kernels,
partition choices, and scheduling are unchanged by this patch.

## Numerical evidence

Cloud-only diagnostic copies of the M sweep use two timing iterations and one
warmup, with only the 2048 x 2048 x 2048 case enabled for focused tests.
The original benchmark remains the authoritative random-input test. These
diagnostic timings are not performance measurements.

- Original random scales/weights: NPU splits finish, but fail the existing
  `rtol=0.2, atol=0.2` check; first case maximum GPU/NPU difference is 1.5.
- An independent float matrix product of dequantized weights gives last-row
  maximum errors approximately 0.0624 for GPU and 1.2313 for NPU. NPU output
  is nonzero, ruling out the earlier hypothesis that no output was written.
  This reference uses the repository's dequantization helper; it is not yet
  an independent audit of the weight-packing permutation.
- Exactly representable scales (1/16), random weights/zeros: still fails;
  last-row errors approximately 0.0609 GPU versus 0.9592 NPU. Scale rounding
  alone does not explain the discrepancy.
- Constant quantized weight 9, zero point 8, scale 1/16, random activations:
  all eight NPU row splits (256 through 2048) pass existing tolerances, but
  maximum GPU/NPU error is 0.25. Last-row NPU/reference error is about 0.186.
- The same constant weights with activation 1/16 give the exact expected
  output 8 everywhere. All eight splits pass with **zero difference**, also
  covering NPU-only and concurrent GPU/NPU execution using imported buffers.
- The patched extension's GPU model regression uses the previous fixed
  1024-token input and generates identical eight token IDs. One cold
  generation call took 2.436990 s; no performance conclusion is drawn.
- With the required eight-column decode artifacts staged, full heterogeneous
  inference completed: two contexts, **512 successful EXEC_CMD submissions**,
  and **512 successful timeline waits**, zero failures in those APIs. Each
  legacy wait returned unsupported and used the fallback as designed. The
  input SHA and eight generated token IDs match GPU-only. One cold call took
  2.005948 s, with 512-token serial prefill chunks and one inflight slot.
  The instrumentation counts the whole process; it does not separate prefill
  and decode or provide per-operator hardware profiling.

The shipped down-projection GEMV config has `cpuN=1024, npuN=4096` for total
N=4096. Its existing validation reports `NPU+CPU N (5120) exceeds total N
(4096)` and falls back on that path. This was retained and recorded, not silently
fixed as part of the runtime port. Other configured NPU work did execute.

**Hypothesis, not verified:** the precompiled NPU kernel's intermediate
accumulation/rounding behavior may explain the random-input difference.
Keep tolerances unchanged until that behavior is understood. Do not hide
the failure by accepting only successful launch or benchmark exit status.

## Rejected command-format experiments

Instruction addresses were checked against the mapped instruction BO and
were intact on this host. Process-local experimental adapters changed the
old ERT_START_CU packet to ERT_START_NPU, using either tensor arguments alone
or the full register map. Both failed numerical checks (first-case maximum
difference 26.125). These adapters are **not** part of the source patch.
The original CU packet is retained; the exact-arithmetic pass supports it.

## Reproduction and evidence

Read [cloud-baseline.md](cloud-baseline.md) for environment setup and initial
CMake adaptations. Current remote source: `/notebooks/HeteroMosaic-baseline`;
diagnostics and logs: `/notebooks/heteromega-compat-2026-10-13`.
Downloaded raw evidence is under [runs/2026-10-13-compat/evidence/](runs/2026-10-13-compat/evidence/),
including `summary.json`, `hetero-model-8c.log`, model configs/results,
probe sources, test source variants, and intermediate patches. The earlier
`hetero-model.log` and `hetero-model-counted.log` used missing decode artifacts:
they completed through GPU fallback with **zero NPU submissions** and must
not be cited as heterogeneous execution evidence.
The local source patch is [runs/2026-10-13-compat/runtime-compat.patch](runs/2026-10-13-compat/runtime-compat.patch).

The patch builds with the previous cloud CMake setup:

```bash
cmake --build /notebooks/HeteroMosaic-baseline/build -j2 \
  --target tensor_parallel_gemm_npu_gpu_sweepM unified_llm_w4a16_hetero_libtorch
timeout 90s /notebooks/HeteroMosaic-baseline/build/bin/tensor_parallel_gemm_npu_gpu_sweepM \
  --results_json=/notebooks/heteromega-compat-2026-10-13/m-sweep-v3.json
```

The sweep is intentionally bounded; inspect individual `allclose` fields,
not just `status=completed`. Never reuse a diagnostic binary as the original
benchmark. Restore the original sweep source and rebuild first.

The model needs these additional paths in the sparse cloud checkout:

```bash
cd /notebooks/HeteroMosaic-baseline
git sparse-checkout add \
  hw_bins/npu2/8192x4096x1024/bf16_int4AWQ_bf16_M \
  hw_bins/npu2/1x4096x14336/bf16_int4AWQ_bf16_K_8c \
  hw_bins/npu2/1x4096x4096/bf16_int4AWQ_bf16_K_8c \
  hw_bins/npu2/1x14336x4096/bf16_int4AWQ_bf16_K_8c
gcc -shared -fPIC \
  -I/notebooks/heteromosaic-libraries/xdna-driver-05-19-25/src/include/uapi/drm_local \
  -I/usr/include/libdrm \
  /notebooks/heteromega-compat-2026-10-13/count_ioctls.c -ldl \
  -o /notebooks/heteromega-compat-2026-10-13/count_ioctls.so
timeout 180s env TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1 \
  LD_PRELOAD=/notebooks/heteromega-compat-2026-10-13/count_ioctls.so \
  python /notebooks/heteromega-compat-2026-10-13/run-model.py hetero
```

Use the environment exports in the cloud runbook first. The helper is a copy
of the saved October 12 model wrapper with its evidence directory changed.
It changes only the documented config fields and context capacity, preserving
the shipped partition/scheduling settings. The counter is observational and
can be omitted for normal runs; compilation is recorded in the raw evidence.
Folders ending only `_K` do not supply the selected `_K_8c` decode artifacts.
Missing artifacts can close the runtime's driver descriptor and allow GPU
fallback. Always check failures, selected paths, and actual NPU submissions.

Next: characterize NPU accumulation with a controlled float reference,
validate random packed W4A16, then validate real-weight heterogeneous model
output before persistent-FFN development.
