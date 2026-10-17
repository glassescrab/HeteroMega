# GPU FFN slice (`kernels/gpu`)

The GPU half of a persistent intermediate-channel FFN split (scope: [agent.md](../../agent.md), [kernel handoff](../../docs/kernel-handoff.md)).
The GPU owns intermediate channels `[0, s)` of one Llama FFN layer (H = 4096, I = 14336). The NPU owns `[s, 14336)`.
Each device computes `Y = (SiLU(X W_gate[:, slice]) * (X W_up[:, slice])) W_down[slice, :]`. The two partial outputs are summed once at the FFN boundary: `x += Y_G + Y_N`.
The handoff's proposed feasibility split, 4096 NPU / 10240 GPU channels, is `s = 10240`.

> **Status: proposed.** The HIP and C++ code has **not been compiled or run** on the AUP cloud yet. CPU-side checks pass (see [Checks done](#checks-done)). It does not change the HeteroMosaic build, model path, kernels or baseline.

## What is here

| File | Purpose |
|---|---|
| `include/heteromega/gpu_ffn.hpp` | Public API |
| `src/pack_w4a16.cpp` | Packs a W4A16 matrix, or one device's channel slice of an FFN layer, into the HeteroMosaic tile layout |
| `src/gpu_ffn.cpp` | `gpu_ffn_slice_forward`: gate/up GEMM → SiLU-and-multiply → down GEMM, on one HIP stream |
| `src/silu_mul.cu` | SiLU-and-multiply kernel (bf16, fp32 math) |
| `src/residual_add.cu` | Boundary sum on the GPU (R-GPU): `x += y_g + y_n` |
| `src/residual_add_cpu.cpp` | Boundary sum on the CPU (R-CPU): same math, AVX-512 with scalar fallback |
| `tests/test_gpu_ffn.cpp` | Correctness tests: level 1 (each kernel vs fp32) and level 2 (`Y_G + Y_N` vs the unsplit FFN) |
| `bench/bench_gpu_ffn_slice.cpp` | GPU slice latency for a grid of M and `s` |
| `bench/bench_ffn_ablation.cpp` | Each GPU change measured alone, against HeteroMosaic's FFN order on the same weights, plus a dense bf16 reference |
| `bench/bench_reduce.cpp` | R-GPU vs R-CPU latency |
| `bench/bench_bandwidth.cpp` | GPU streaming-read bandwidth, alone or next to an NPU load |
| `tools/check_packing.py` | CPU check of the layout and the split math (numpy only) |

## GPU branch contract

The handoff asks to agree on these items before integration. This is what the GPU side implements (**code-confirmed**, not yet run):

| Item | GPU side |
|---|---|
| Logical shapes | `x_norm` [M, 4096]. gate/up packed as one [4096, 2n] matrix (columns `[0, n)` gate, `[n, 2n)` up). down packed as [n, 4096]. `Y_G` [M, 4096]. n = channels of the slice |
| Weight layout | HeteroMosaic packed layout, the same one the NPU artifacts read: 128 × 64 tiles of 4352 bytes, ordered by tile column % 8, then tile column, then tile row |
| Quantization metadata | Per tile: 64 bf16 scales, then 64 int8 zeros stored twice (128 bytes). Group size 128 = tile height |
| Activation dtype and strides | bf16, row-major, contiguous. For M > 1 the input storage must hold `padded_rows(M)` rows (multiple of 128), because the GEMM reads whole 128-row tiles |
| Buffer ownership | The caller owns `x_norm`, `Y_G` and the scratch `GpuFfnBuffers` (allocate once for the largest M; reuse across layers and calls) |
| Readiness and completion | `gpu_ffn_slice_forward` enqueues 3 kernels (plus one copy if `x_norm` is not padded) on the given HIP stream and does not synchronize. The caller records an event. `residual_add2` must start only after both `Y_G` and `Y_N` are complete |
| Boundary sum | `residual_add2(x, y_g, y_n)`: fp32 math, one bf16 rounding. `y_n` can be bf16 or fp32 |
| Split points | Multiples of 128 work. Multiples of 512 (8 tile columns) keep each slice a tile subset of the full packed buffer |

Numerical contract of the tests, against an fp32 reference computed from the same quantized weights:

- Matmuls and the FFN (levels 1 and 2): `max|got − ref| / max|ref| ≤ 1e-2`, relative L2 error ≤ 1e-2, cosine ≥ 0.9999.
- SiLU-and-multiply and the boundary sum (one bf16 rounding): the same max limit, relative L2 error ≤ 5e-3, cosine ≥ 0.99999.

Inputs are random signed values. Weights, scales (0.002 to 0.02) and zeros (6 to 9) are nonuniform. These are the controlled packed-matmul conditions that the handoff asks for to investigate the open NPU mismatch. The GPU tests check the GPU half only.

## Design notes

- The GPU and the NPU read the **same** packed layout. One packer serves both devices.
- Tiles are ordered by column group (tile column % 8). A channel slice is therefore not a contiguous range of the full packed buffer. `pack_ffn_slice` packs each device's slice on its own.
- `down` of a slice is a K-slice: rows `[begin, end)` and quantization groups `[begin/128, end/128)`.
- The GEMM and GEMV are HeteroMosaic's `w4a16_gemm_fused_packed` and `w4a16_gemv_fused_packed` from `src/hipkernels/`. This project compiles them from those sources and does not change them.
- The GEMM reads whole 128-row tiles of its input. Only its output writes check `M`. HeteroMosaic pads the same way (`M_padded` in `hetero_compute.cpp`).
  - `GpuFfnBuffers` rounds its rows up to a multiple of 128.
  - If `x_norm` is not padded, `gpu_ffn_slice_forward` first copies it into `GpuFfnBuffers::x_pad` (one `hipMemcpyAsync`). Pass a padded `x_norm` to skip the copy.
  - `packed_linear` refuses an unpadded input for M > 1.
- The benchmarks enqueue all timed iterations back to back and read the events after the loop. A sync in the loop would add the host launch time to each kernel time.

## Build (AUP cloud)

Use the environment of [cloud-baseline.md](../../docs/cloud-baseline.md): the ROCm 7.2 venv with Torch 2.11, native `gfx1150`, no graphics-version override.

1. Set the environment:
   ```bash
   source /notebooks/heteromosaic-venv/bin/activate
   unset PYTHONPATH HSA_OVERRIDE_GFX_VERSION
   export ROCM_PATH=/opt/rocm-7.2.0
   export LD_LIBRARY_PATH=/opt/rocm-7.2.0/lib:/opt/xilinx/xrt/lib
   ```
2. Configure from the repository root. Check that CMake prints `ROCm: /opt/rocm-7.2.0` and `HIP architectures: gfx1150`:
   ```bash
   cmake -S kernels/gpu -B build/gpu
   ```
3. Build. Keep `-j` small: each HIP file includes LibTorch, and the machine has 23 GB of RAM:
   ```bash
   cmake --build build/gpu -j4
   ```

Notes:

- This is a separate CMake project. It does not need `HOME_LIBS`, the XDNA headers or the cloud CMake patch of the root build.
- The tests and benchmarks call `c10::hip::getCurrentHIPStream()`. Torch 2.11 renamed the HIP stream types but kept this function (see `docs/runs/2026-10-12-aup/torch211-hip-compat.hpp`), so no compat header should be needed. **Documented but unverified** until the first build.

## Run

1. Run the CPU check (any machine):
   ```bash
   python3 kernels/gpu/tools/check_packing.py
   ```
2. Run the GPU tests. Start with `--quick` (M ∈ {1, 37, 128}, `s` = 7168). The first line shows the device, its architecture and the free GPU memory:
   ```bash
   ./build/gpu/bin/test_gpu_ffn --quick
   ```
3. Run the full tests (M ∈ {1, 37, 128, 512, 2048}, `s` ∈ {512, 7168, 10240, 13824}). They need about 2 GiB of GPU memory:
   ```bash
   ./build/gpu/bin/test_gpu_ffn
   ```
4. Measure the GPU slice latency. Defaults: M ∈ {1, 128, 512, 2048, 4096}, `s` from 1024 to 13312 in steps of 1024, plus 14336 (GPU only). For the handoff's isolated FFN, use M = 512:
   ```bash
   ./build/gpu/bin/bench_gpu_ffn_slice --m 512 --s 10240,14336 > gpu_slice.csv
   ```
5. Measure what each change gives. Variants: HeteroMosaic order (`hm`), one gate/up GEMM (`merged`), plus the fused SiLU-and-multiply (`fused`), and a dense bf16 `torch::mm` reference (`dense`):
   ```bash
   ./build/gpu/bin/bench_ffn_ablation --m 1,128,512,2048 --s 10240,14336 > ablation.csv
   ```
6. Compare the two boundary-sum options:
   ```bash
   ./build/gpu/bin/bench_reduce > reduce.csv
   ```
7. Measure GPU bandwidth alone. Then run it again while an NPU load runs:
   ```bash
   ./build/gpu/bin/bench_bandwidth --seconds 10
   ```

## Checks done

Run on macOS (no AMD GPU) on 2026-10-06:

| Check | Result |
|---|---|
| numpy packer == line-by-line numpy translation of HeteroMosaic `_pack_weights_packed` (byte equal) | PASS |
| Emulated HeteroMosaic GEMV addressing on full, N-slice, K-slice, and `start_col` | PASS |
| FFN split, `Y_G + Y_N` == full FFN, 3 split points | PASS |
| C++ packing loop (`pack_w4a16.cpp`) == numpy packer (byte equal), 3 shapes | PASS |
| R-CPU scalar path == numpy round-to-nearest-even; inf and NaN kept | PASS |
| R-CPU AVX-512 path, x86_64 syntax check | PASS (not run) |
| CMake configure, HIP/C++ compile, GPU tests and benchmarks | **not executed** |

`src/hipkernels/` in this repository is unchanged from upstream `61714a3`, where these checks were made.

## Known limits

- HeteroMosaic's GEMV (M = 1) accumulates in fp16. Long K (the `down` slice) can lose precision. This also affects the baseline.
- The GPU partial `Y_G` is bf16, because the HeteroMosaic kernels write bf16. `residual_add2` also accepts an fp32 `Y_N`.
- `residual_add2_cpu` needs CPU tensors (for example pinned host memory). Where `Y_G` and `Y_N` live is an integration decision.
- `pack_ffn_slice` needs `begin` and `end` to be multiples of 128.
- `GpuFfnBuffers::allocate` takes `hidden` (H) for `x_pad`. This adds `padded_rows(max_M) × H × 2` bytes (32 MiB for max M = 4096).
- Not integrated into `unified_llm_w4a16.cpp`. The model path is unchanged.

## Next steps

1. Build and run `test_gpu_ffn` (quick, then full) on the AUP cloud. Record the result in `docs/progress.md`.
2. Run `bench_gpu_ffn_slice --m 512 --s 10240,14336` for the isolated FFN of the handoff milestone.
3. Agree with the NPU side on the `Y_N` dtype and the readiness signal before integration.
4. Stretch: fuse SiLU-and-multiply into the gate/up GEMM epilogue.
