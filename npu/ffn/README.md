# NPU FFN kernel bring-up

For the selected single-dispatch graph **inside the model**, start with
[GPU + NPU FFN testing](../../docs/ffn-teammate-testing.md). Its selected
`w4a16_merged_upstream.py` and `w4a16_prefill_upstream.cc` path consumes original
4352-byte packed tiles. Older compact formats and two-launch paths below are
separate experiments; do not substitute them into the deployment manifest.
Historical bulk evidence remains on the pinned source branch e6ca183c.

This directory adds editable MLIR-AIE/IRON sources to the HeteroMosaic
baseline. A complete host-staged GPU–NPU FFN microbenchmark is available in
[experiments/ffn_partition](../../experiments/ffn_partition/README.md). Whole-model
Llama prefill acceleration remains unvalidated.

Current development targets **multi-token prefill projections**. The default
FFN experiment now uses [eight columns and four compute rows](ARRAY8.md),
with multicast and weight reuse. See
[PREFILL.md](PREFILL.md) for the tiled W4A16 matrix-multiply design, compact
buffer ABI, build commands, and correctness checks. The scalar single-token
and activation examples below preserve the earlier bring-up work.
Hardware results for 128/512/2048/4096-token projections are recorded in
[PREFILL_VALIDATION.md](PREFILL_VALIDATION.md).

The optional `--npu-arithmetic bfp16` experiment adapts the corrected TileFuse
W4A16 GEMM from the latest relevant `glassescrab/mlir-aie` branch. It retains
the existing compact ABI, eight-column graphs and on-chip SwiGLU fusion.
See [the branch audit, arithmetic contract and measurements](BFP16_ADAPTATION.md).
Native BF16 remains the default; BFP16 reports numerical deviations explicitly.

## Environment

Validated environment and measurements are recorded in [VALIDATION.md](VALIDATION.md).
The AUP notebook supplied for development is **Ryzen AI 9 HX 370 / Strix**, with
an AIE2P NPU (`npu2`), not the planned Ryzen AI Max+ 395 evaluation machine.
Keep their performance results separate.

The code targets MLIR-AIE revision
`7e00b57955e108fe9d8e9419f5828a0c7e650858`, supplied by the notebook's
`ironenv`. It requires NumPy and `ml_dtypes`, and device runs require `pyxrt`.
Use the preconfigured Jupyter terminal. Do not apply the inherited root
README's kernel/GRUB/driver installation steps to the managed notebook.

The checkout is `/notebooks/HeteroMega`; `/notebooks` persists across sessions
while the AUP token remains valid. Credentials are not stored in this repo.

## Build and run

From this directory, in the supplied MLIR-AIE environment:

```bash
# One full Llama-3.1-8B intermediate vector; also supports smaller local shards.
make length=14336 tile_size=1024 cols=1
python run_silu_mul.py --json results/silu_mul_14336_hx370.json

# A small, single-token W4A16 projection tile, built from source.
make -f Makefile.w4a16 K=128 N=64
make -f Makefile.w4a16 run K=128 N=64
```

`build/final.xclbin.json` and the W4 equivalent contain compiled shapes and
artifact hashes. Runners validate them before allocating device buffers;
rebuild when changing dimensions. Each build emits an XCLBIN, instruction
binary, and PDI. Generated hardware binaries stay out of Git.
Both IRON graphs include the C++ source hash in their compile-time arguments:
the pinned JIT otherwise can reuse a whole-design cache entry after an
external C++ kernel changes. Manifests identify the intended toolchain
revision, not an automatically detected installed revision.
External object filenames also include the source hash and tile dimensions;
the pinned explicit-output compiler otherwise reuses an existing `.o`
in `final.prj` without checking whether its source or `-D` dimensions changed.

The XRT harness reuses allocations, but explicitly synchronizes input and
output BOs. Its reported dispatch/wait time includes NPU DMA and compute and
excludes BO input/output synchronization, allocation, and compilation. It is
not isolated core latency, FFN latency, TTFT, or end-to-end inference latency.

CPU-only checks, from the repository root:

```bash
python -m unittest discover -s npu/ffn -v
python npu/ffn/run_w4a16_linear.py --self-test
```

## Numerical and partition contracts

- Activations and weight scales are **BF16**, consistent with the inherited
  BF16/int4 kernels. W4A16 here does not mean IEEE FP16 activations.
- `silu_mul.cc` consumes already-projected gate and up arrays. It computes
  `BF16(BF16(SiLU(gate)) * up)`, retaining the baseline's intermediate BF16
  rounding. A 128-segment direct sigmoid LUT replaces the coarse native
  tanh approximation; narrowing uses round-to-nearest-even. Inputs below
  -16 use sigmoid zero and inputs at/above 16 use one. The finite input
  smoke tests include gates from -64 to 64. The approximation is checked against that staged
  reference, with single-round error also reported.
- `w4a16_linear.cc` is a scalar, single-core correctness implementation of
  `M=1`, group size 128. It dequantizes each weight to BF16, accumulates in
  FP32, and returns BF16. K is a multiple of 128 and N a multiple of 64;
  compile-time FIFO limits reject larger shapes. It is not optimized and
  cannot directly run a full 4096×14336 Llama projection.
- The portable weight layout is output-major `[N, K/2]` uint8: even K in the
  low nibble, odd K in the high nibble; scales and zeros are `[N, K/128]`.
  Dequantization is `(q - zero) * scale`. The W4 runner packs three regions:
  quant bytes, little-endian BF16 scales, and one uint8 zero per group.
- `reference.py` keeps matching gate/up output-channel slices local through
  activation/multiply and consumes matching down-projection K slices.
  Its CPU oracle reduces FP32 down partials before final BF16 rounding;
  the device linear prototype returns BF16 partials. Real cross-device
  reduction needs separate error validation. Host algebra tests do not
  establish bitwise model equivalence.

## Integration work remaining

1. Profile the validated [tiled prefill projection](PREFILL.md) to separate
   dequantization, matrix arithmetic, and DMA costs. Add on-chip weight reuse
   and connect checkpoint loading to its packed layout.
2. Connect gate/up, local activation, and sliced down projection within the
   NPU graph. The current standalone activation crosses host/device BO
   boundaries; it does not yet prove persistent intermediate locality.
3. Adapt to HeteroMosaic's packed layout and runtime. Its 128×64 tiles occupy
   4352 bytes (4096 quantized weight bytes, 128 BF16 scale bytes, and 128
   duplicated-zero bytes) and have an eight-way column interleave. These
   are not interchangeable with the portable layout above.
4. Integrate shared buffers and cross-device synchronization. Shared physical
   DRAM does not itself guarantee identical weight layouts, no temporary
   copies, or coherent GPU/NPU access. The inherited runtime uses DMA-BUF
   import, GPU events, and an NPU mutex; this isolated harness uses XRT.
5. Select one aligned asymmetric FFN ratio offline, compare CPU/GPU reduction,
   then run the fixed Llama-3.1-8B-Instruct evaluation on Max+ 395. Check
   numerical error and greedy-token agreement before reporting speedups.

The inherited FFN launch sites are in
`src/unified_llm_w4a16_hetero/unified_llm_w4a16.cpp`; buffer import and NPU
submission are in `npuSetup.cpp`; per-operator splits and temporary assembly
are in `hetero_compute.cpp`. Existing NPU PDIs remain untouched.

## Source references

- [Pinned MLIR-AIE SwiGLU example](https://github.com/Xilinx/mlir-aie/tree/7e00b57955e108fe9d8e9419f5828a0c7e650858/programming_examples/ml/swiglu)
- [Pinned AIE2P kernels](https://github.com/Xilinx/mlir-aie/tree/7e00b57955e108fe9d8e9419f5828a0c7e650858/aie_kernels/aie2p)
- [HeteroMosaic baseline](https://github.com/glassescrab/HeteroMega/tree/61714a3147f34857aa5dfef21a28e762777a2df0)

Adapted MLIR-AIE portions retain their Apache-2.0 WITH LLVM-exception
attribution. The inherited project's licenses and notices remain applicable.
