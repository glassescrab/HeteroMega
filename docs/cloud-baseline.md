# AUP cloud baseline runbook

## Status: 2026-10-13

Publication update, 2026-10-15: the compatibility changes are included in this
repository's source. The saved patch is for reproducing the port from the
starting commit; do not apply it again to a checkout that already contains it.
See [kernel-handoff.md](kernel-handoff.md) for the current teammate entry point.

**Current result:** the experimental direct-XDNA compatibility patch executes
real heterogeneous Llama inference: 512 successful NPU submissions and
512 successful timeline waits, zero submission/timeline failures. The fixed
1024-token workload generates the same eight greedy tokens as GPU-only.
Exact synthetic matrices also pass all eight row splits with zero error.
Random packed-W4A16 checks still fail; this is a functional run, not a validated
accuracy or performance baseline. See [runtime-compatibility.md](runtime-compatibility.md)
for the patch, commands, artifact requirements, limitations, and evidence.

The following October 12 setup/results are historical. Their initial context
failure and unchanged-runtime statements have been superseded by that port.

### Historical status: 2026-10-12

**October 12 result:** built HeteroMosaic with cloud compatibility adaptations and
completed a real-weight, full 32-layer Llama 3.1 8B GPU model run. The original
heterogeneous M-split benchmark failed NPU hardware-context creation with
`EINVAL`; a QoS-structure translation retry also failed. No successful
HeteroMosaic GPU-NPU execution or shared-buffer correctness is established.

The earlier official IRON NPU matmul and standalone HIP smoke checks passed.
They use different execution paths from HeteroMosaic's direct XDNA runtime.

Local source reference: `61714a3147f34857aa5dfef21a28e762777a2df0`.
The baseline-run request superseded the initial documentation-only scope.
Dependencies and real weights were installed/downloaded into separate cloud
directories. Two remote CMake files were adapted; model, kernels, scheduler and
direct-XDNA source files were unchanged. No system driver/kernel changes or
commits/pushes were made. Local implementation files remain unchanged.

## Actual baseline execution

Evidence is saved locally in [runs/2026-10-12-aup](runs/2026-10-12-aup/): full
logs, exact shell history, package versions, model/input/output records,
configuration, build patch, and the unsuccessful diagnostic adapter.

| Executed check | Result |
| --- | --- |
| Configure/build | Exit 0; `test_layout_hip`, `tensor_parallel_gemm_npu_gpu_sweepM`, and model Python extension built |
| Existing GPU layout test | Unpacked W4A16 GEMM and GEMV matched its BF16 references (`rtol=0.01`, `atol=0.1`); exit 0. Its source defines `TEST_UNPACKED_KERNEL`, so this is not a packed-kernel correctness test |
| Original heterogeneous sweep | 88 split entries failed context creation; four completed entries are GPU-only references, not heterogeneous successes; one GPU reference was interrupted by the 180-second timeout |
| Full GPU model | 291 parameter groups loaded, zero skipped; 1,024 input tokens and eight generated tokens; exit 0 |
| QoS translation retry | Context creation still failed; bounded at 90 seconds. This was a diagnostic experiment, not a successful port |

Model: `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4`, revision
`db1f81ad4b8c7e39777509fac66c652eb0a52f91`. Two safetensors shards were downloaded
with tokenizer/config files and merged by the existing frontend loader. The
matching tokenizer was loaded from that local snapshot; no gated Meta-repo
authentication was required. No AutoAWQ model runner was used.

The driver calls the original `LLaMA3W4A16Model` class with `max_seq_len=1536`
instead of its 16,512 default to bound scratch/KV/logit allocations on this
23 GiB machine. It keeps all 32 layers and original packed W4A16 kernels. A copy
of the shipped Strix Point config uses `heterogeneity=gpu`, `prompt_len=1024`,
`warmup=false`, `usePreSavedWeights=false`, and debug level 1. Direct safetensors
loading avoids the optional prepacked-weight download/preparation path.
The original GPU chunk size remains 2,048. This workload therefore uses one
GPU prefill chunk; it does not validate multi-chunk overlap.

The deterministic prompt is the first 1,024 tokenizer IDs of:
`("This experiment measures language model inference on heterogeneous processors. " * 200)
+ " Explain the purpose of this experiment."`
Input IDs are stored in `gpu-model-result.json`; their int64 byte SHA256 is
`2c11d2476f8b0d68744bec04b88ae434fa2c7f2e1f15a66f6db8785ec5e481c7`.
Greedy generation (`temperature=0`) returned
`[4221, 1646, 45478, 389, 98882, 37686, 13, 1115]`, decoded as
` language model inference on heterogeneous processors. This`.

**One cold run**, excluding construction/download/weight loading: wrapper wall
time 2.669836 s; runtime printed prefill 2.2232 s and post-prefill generation
0.426904 s. The runtime's label `Total Generation Time` excludes prefill;
use the synchronized wrapper wall time for the complete generation call.
Weight loading took 40.45 s. These are functional baseline observations, not
a repeated benchmark, TTFT study, accuracy/perplexity result, or speedup claim.

### Commands used

All commands below run in the AUP JupyterLab Linux terminal. Persistent locations:
`/notebooks/HeteroMosaic-baseline`, `/notebooks/heteromosaic-venv`,
`/notebooks/heteromosaic-libraries`, `/notebooks/heteromosaic-model`, and
`/notebooks/heteromega-baseline-logs`. `ironenv` was left intact.

```bash
python3 -m venv /notebooks/heteromosaic-venv
source /notebooks/heteromosaic-venv/bin/activate
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/rocm7.2
pip install pybind11 numpy json5 safetensors
pip install transformers==4.51.3 sentencepiece protobuf

git clone --filter=blob:none --no-checkout \
  https://github.com/glassescrab/HeteroMega.git /notebooks/HeteroMosaic-baseline
git -C /notebooks/HeteroMosaic-baseline sparse-checkout set src include py
git -C /notebooks/HeteroMosaic-baseline checkout \
  61714a3147f34857aa5dfef21a28e762777a2df0

mkdir -p /notebooks/heteromosaic-libraries
git clone --filter=blob:none --no-checkout https://github.com/amd/xdna-driver.git \
  /notebooks/heteromosaic-libraries/xdna-driver-05-19-25
git -C /notebooks/heteromosaic-libraries/xdna-driver-05-19-25 \
  sparse-checkout set src/include
git -C /notebooks/heteromosaic-libraries/xdna-driver-05-19-25 checkout \
  0e6d303b2cc2b3fe1cf10aba0acbf57a422588fb
```

For reproduction, copy the saved `torch211-hip-compat.hpp` into
`/notebooks/heteromega-baseline-logs/`, and apply `cloud-build.patch` to the fresh
pinned remote checkout with `git apply`. The patch changes two ROCm paths and
forces inclusion of that header. It aliases the removed `c10::hip::HIPStream`
and `HIPStreamGuard` type names to the ROCm wheel's corresponding CUDA-named
types, preserving the existing stream functions. No runtime source edits.

```bash
unset PYTHONPATH HSA_OVERRIDE_GFX_VERSION
export HOME_LIBS=/notebooks/heteromosaic-libraries
export HETEROMOSAIC_ROOT=/notebooks/HeteroMosaic-baseline
export ROCM_PATH=/opt/rocm-7.2.0
export LD_LIBRARY_PATH=/opt/rocm-7.2.0/lib:/opt/xilinx/xrt/lib
export TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1

cmake -S "$HETEROMOSAIC_ROOT" -B "$HETEROMOSAIC_ROOT/build" \
  -DCMAKE_HIP_ARCHITECTURES=gfx1150 \
  -DCMAKE_HIP_COMPILER=/opt/rocm-7.2.0/lib/llvm/bin/clang++ \
  -Dpybind11_DIR="$(python -m pybind11 --cmakedir)" \
  -DCMAKE_PREFIX_PATH=/opt/rocm-7.2.0 \
  '-DCMAKE_CXX_FLAGS=-isystem /opt/rocm-7.2.0/include' \
  '-DCMAKE_HIP_FLAGS=-isystem /opt/rocm-7.2.0/include --hip-path=/opt/rocm-7.2.0 --rocm-path=/opt/rocm-7.2.0' \
  '-DCMAKE_EXE_LINKER_FLAGS=-L/opt/rocm-7.2.0/lib -Wl,-rpath,/opt/rocm-7.2.0/lib' \
  '-DCMAKE_SHARED_LINKER_FLAGS=-L/opt/rocm-7.2.0/lib -Wl,-rpath,/opt/rocm-7.2.0/lib'
cmake --build "$HETEROMOSAIC_ROOT/build" -j2 --target \
  test_layout_hip tensor_parallel_gemm_npu_gpu_sweepM \
  unified_llm_w4a16_hetero_libtorch

timeout 180 "$HETEROMOSAIC_ROOT/build/bin/test_layout_hip"
```

Native gfx1150 was used with no graphics-version override. `-isystem`, library
and RPATH flags avoid mixing the container's HIP 5.7 system files with ROCm 7.2.
The repository's installation script was not run; no system packages were removed.

The heterogeneity test used these selectively retrieved artifact families:

```bash
git -C "$HETEROMOSAIC_ROOT" sparse-checkout add \
  hw_bins/npu2/8192x2048x2048/bf16_int4AWQ_bf16_M \
  hw_bins/npu2/8192x4096x4096/bf16_int4AWQ_bf16_M \
  hw_bins/npu2/8192x8192x8192/bf16_int4AWQ_bf16_M \
  hw_bins/npu2/8192x4096x14336/bf16_int4AWQ_bf16_M \
  hw_bins/npu2/8192x14336x4096/bf16_int4AWQ_bf16_K
timeout 180 "$HETEROMOSAIC_ROOT/build/bin/tensor_parallel_gemm_npu_gpu_sweepM" \
  --results_json=/notebooks/heteromega-baseline-logs/m-sweep.json
```

Copy the saved `download-model.py` and `run-model.py` into the log directory,
with `model-revision.txt` containing the pinned model revision, then:

```bash
python -u /notebooks/heteromega-baseline-logs/download-model.py
timeout 600 python -u /notebooks/heteromega-baseline-logs/run-model.py gpu \
  > /notebooks/heteromega-baseline-logs/gpu-model.log 2>&1
```

The small driver is saved verbatim in the evidence directory. It imports the
existing frontend, creates a config copy, bounds context capacity, constructs
the fixed input, and saves synchronized wall time and generated IDs/text.
It is used instead of the stock CLI because that CLI does not expose the
context-capacity constructor argument. It does not implement inference.
Full package pins and original command history are in the evidence directory.

### Remaining heterogeneous blocker

Both attempts reach `createHWctxt` in `src/npu_matmul_func/npu_matmul_func.cpp`
and fail `DRM_IOCTL_AMDXDNA_CREATE_CTX` with `EINVAL`, before NPU execution.
The original sweep's four `completed` records are GPU references only; do not
interpret its JSON counts or partial run as heterogeneous success.

The installed XDNA revision reported by XRT is
`bd02f5e75f7788dfbe0f3f716de928de1e7078f3` (2.26.0_20260818). Its UAPI adds
`user_start_col` to QoS and changes context names compared with the pinned 2025
header. A process-local ioctl adapter supplied the extended QoS with no requested
start column and zero padding. Context creation still failed. Thus the header
change is confirmed, but **the complete cause of EINVAL is unresolved**.
Kernel log access failed with `Operation not permitted`; no host permissions
or driver settings were changed to bypass this limitation.

Next: obtain provider kernel diagnostics for that ioctl and validate current
context/heap/tile arguments, or use a provider-managed host/VM with the pinned
XDNA stack. An older container XRT library alone does not downgrade the host's
kernel driver. Keep the successful GPU path and failed original run intact;
track any current-driver port separately. Do not run/tune the full heterogeneous
model until a packed W4A16 shared-buffer launch passes correctness.

## Connect

1. Open <https://dub.aupcloud.io/aipc-16> and enter the professor-provided token.
   Do not store the token in Git or in this runbook.
2. Select `mlir-aie:latest`, choose a session duration, and start the server.
3. In JupyterLab's Launcher, open **Terminal**. It starts in
   `/notebooks/mlir-aie` with `ironenv` active.
4. Read `/notebooks/README.ipynb` and `/notebooks/COMMITID.TXT`.

The supplied notebook says this is a Docker container; `/notebooks` persists
between launches but is not automatically backed up and can be removed after
token expiry. Keep reproducible results in the project separately. A transient
"server unavailable" dialog occurred; going through the hub URL restored the
same terminal/container. No SSH access was verified.

## Observed environment

| Item | Measured/observed | Baseline implication |
| --- | --- | --- |
| CPU/GPU | Ryzen AI 9 HX 370 / Radeon 890M; native `gfx1150` | Strix Point platform, wave32-capable GPU; kernel performance still untested |
| NPU | XRT identifies NPU Strix, `aie2p`, topology 6x8 | NPU2 device; official matmul execution passed |
| Devices | `/dev/kfd`, `/dev/dri/card0`, `/dev/dri/renderD128`, `/dev/accel/accel0` exposed | Both GPU and NPU available inside container |
| OS/kernel | Ubuntu 24.04.4 LTS, `6.17.0-42-generic` | Differs from README's recommended kernel 6.11 |
| Memory | About 23 GiB RAM, 8 GiB swap; about 20 GiB available during audit | Model/cache/GTT budget needs checking; not a 64+ GiB reference host |
| ROCm | `/opt/rocm-7.2.0`, HIP 7.2.26015 | Repository hardcodes `/opt/rocm-7.1.1` |
| System HIP headers | `/usr/include/hip` reports HIP 5.7 | Default compiler search can mix incompatible versions |
| XRT/XDNA | XRT 2.26.0; amdxdna 2.26.0.20260818; firmware 1.1.2.64 | Newer than repository's XRT 2.20/pinned 2025 driver source |
| Python Torch | `2.13.0+cpu`, `torch.version.hip=None` in `ironenv` | Cannot run this ROCm model; keep IRON environment intact |
| CMake | 4.4.2 | Meets documented minimum; project compatibility not tested |
| Disk | `/notebooks` about 307 GiB free at audit | Shared snapshot, not a guaranteed quota |
| MLIR-AIE | COMMITID lists `7e00b57955e108fe9d8e9419f5828a0c7e650858` | Use the installed checkout's examples, not assumptions about latest API |

## Executed smoke checks

From `/notebooks/mlir-aie`, the supplied official single-core matmul was built
and run with NPU2 selected:

```bash
mkdir -p /notebooks/heteromega-baseline-logs
make -C programming_examples/basic/matrix_multiplication/single_core \
  NPU2=1 run > /notebooks/heteromega-baseline-logs/npu-smoke.log 2>&1
```

Exit status 0, `PASS!`; M=K=N=512, tiles 32x32x32, input i16/output i32.
The example reported 2357 microseconds. This is only a functional smoke result,
not a HeteroMosaic benchmark or a stable/dedicated-machine performance estimate.

A separate 16-element HIP kernel wrote `i+1` and checked every returned value.
Default `hipcc` failed using old system headers; explicit `-I` and runtime-path
options alone did not fix it. `-isystem` fixed header selection, then explicit
library/RPATH selection fixed linking (`hipGetDevicePropertiesR0600` otherwise
unresolved). The working command was:

```bash
hipcc --hip-path=/opt/rocm-7.2.0 --rocm-path=/opt/rocm-7.2.0 \
  -isystem /opt/rocm-7.2.0/include \
  -L/opt/rocm-7.2.0/lib -Wl,-rpath,/opt/rocm-7.2.0/lib \
  --offload-arch=gfx1150 \
  /notebooks/heteromega-baseline-logs/hip_smoke.cpp \
  -o /notebooks/heteromega-baseline-logs/hip_smoke
/notebooks/heteromega-baseline-logs/hip_smoke
```

Result: `GPU HIP PASS: AMD Radeon Graphics (gfx1150), 16/16 correct`.
Diagnostic source and logs remain under `/notebooks/heteromega-baseline-logs`.
The GPU and NPU checks ran separately, not concurrently. No graphics-version
override was needed for this native HIP check.

## Initial baseline sequence (historical proposal)

The actual build/GPU run and remaining blocker above supersede this initial
sequence. Its prerequisite cautions still apply; steps are not all pending now.

1. **Resolve runtime choice before installing.** Prefer a provider-supported
   image matching HeteroMosaic's ROCm 7.1.1/XRT-XDNA recipe for reproduction.
   Alternatively evaluate the existing 7.2/2.26 image as a separately documented
   compatibility port. Do not downgrade the shared host kernel/driver or run
   `utils/new_setup.sh` blindly; it changes system packages and recreates a venv.
   Whether the old direct-ioctl runtime and precompiled PDIs work on this driver
   remains untested. IRON success does not answer that question.
2. **Use an isolated ROCm Python environment**, leaving `ironenv` intact.
   Match the chosen ROCm/PyTorch builds; the README pins Torch 2.10.0 with ROCm
   7.1. Ensure `torch.version.hip` is non-null and a GPU tensor check passes.
   Do not assume the existing CPU Torch can serve as the model's LibTorch.
3. **Stage pinned source and build prerequisites.** Pin the commit above;
   obtain the documented driver UAPI headers, LibTorch/ROCm dependencies and
   pybind11. Check `$HOME_LIBS`. Inspect large `hw_bins/npu2` artifacts before
   retrieving the whole repository. For the current image, CMake and setup
   hardcoded 7.1.1 paths need a deliberate adaptation; setting `ROCM_PATH` alone
   cannot override the root CMake assignment. Native gfx1150 worked for the
   smoke test; repository gfx1100 plus HSA override is a separate policy to
   validate, not silently substitute. Record all adaptations.
4. **Build and validate microbenchmarks first.** The documented sequence is
   `source utils/setup.sh`, then `cmake -S . -B build` and
   `cmake --build build -j4` after prerequisites are satisfied. These commands
   are not currently ready to run unchanged on this image. Validate GPU packed
   W4A16, then NPU packed W4A16, then a shared-buffer heterogeneous split. Use
   matching artifacts and verify launch status and numerical error. This gate
   catches direct-XDNA ABI and DMA-BUF issues before downloading a model.
5. **Only then run one fixed model workload.** Use separate GPU and original
   heterogeneous config copies, fixed weights/prompt/output length, and modest
   prefill length initially. Resolve model/tokenizer access and available memory
   before downloads. From `py/unified_llm_w4a16`, the documented GPU command is:

   ```bash
   python3 llama3_8b_w4a16_model.py \
     --config-path configs/configs_strixP_llama3_8b.json5 \
     --device cuda --text "What is the meaning of life?" --max-new-tokens 32
   ```

   The shipped config says `heterogeneity: gpu`. For GPU-NPU use a **copy** with
   `heterogeneity: hetero` and verified shapes/chunks/artifacts. `--backend hetero`
   alone is not evidence of NPU use. Frontend may fetch weights/tokenizer and
   packed caches, and `--prompt-test` can rewrite the selected config.
6. Record baseline outputs, selected paths, numerical checks, normal latency,
   software versions and machine contention before any persistent-FFN change.

**First development milestone:** reproducible HeteroMosaic packed W4A16 split
microbenchmark on this cloud, with numerical verification and confirmed use of
both devices/shared buffers. Full model generation follows that compatibility
gate; persistent FFN implementation follows the unchanged model baseline.

## References

- [AUP Learning Cloud](https://www.amd.com/en/corporate/university-program/learning-cloud.html)
- [Official IRON programming guide](https://github.com/Xilinx/mlir-aie/tree/main/programming_guide)
- [Official mini tutorial](https://github.com/Xilinx/mlir-aie/tree/main/programming_guide/mini_tutorial)
- Repository `README.md` and [project-plan.md](project-plan.md): baseline-specific
  setup and code map. Installed cloud README/Makefiles were used for smoke commands.
