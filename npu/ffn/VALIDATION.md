# NPU bring-up validation

Run on 2026-10-14 at 03:31 UTC (2026-10-13 in America/Chicago), through the
provided AUP JupyterLab browser session. The source checkout is on branch
`codex/npu-ffn-mlir-aie`, based on HeteroMosaic commit `61714a3`.

## Observed platform

- AMD Ryzen AI 9 HX 370 with Radeon 890M, Strix AIE2P NPU, topology 6×8.
- Ubuntu 24.04.4, Linux `6.17.0-42-generic`, XRT `2.26.0`.
- Installed MLIR-AIE checkout: `7e00b57955e108fe9d8e9419f5828a0c7e650858`.
- These are **HX 370 bring-up results**, not results for the planned Max+ 395.

## Results

All 20 hardware correctness cases passed, along with repeated-output checks.
The [machine-readable summary](results/hx370_validation.json) records source
hashes and tolerances. Complete per-case reports and compiled artifacts remain
in `/notebooks/HeteroMega/npu/ffn/{results,build*}` on the notebook.

| Kernel | Geometry | Cases passed | Max absolute error | Median dispatch + wait |
|---|---|---:|---:|---:|
| Fused BF16 SiLU×up | 14,336 elements, tile 1024, 1 column | 4/4 | 0.125 | 160.122 µs |
| Fused BF16 SiLU×up | 2,048 elements, tile 1024, 1 column | 4/4 | 0.125 | 98.378 µs |
| Fused BF16 SiLU×up | 14,336 elements, tile 512, 4 columns | 4/4 | 0.125 | 92.434 µs |
| Scalar W4A16 linear | M=1, K=128, N=64 | 4/4 | 0 | 917.787 µs |
| Scalar W4A16 linear | M=1, K=256, N=64 | 4/4 | 0 | 1,723.981 µs |

SiLU cases: normal inputs, a dense gate sweep over [-16,16], zero gates,
and selected tails through ±64. Reference uses staged BF16 SiLU rounding;
pass condition is `abs(error) <= 0.02 + 0.04*abs(reference)`. This does not
establish Llama-level numerical correctness or exact sigmoid equivalence.

W4A16 cases: nonzero output-channel slice, zero activations, quantized weights
equal to their zero points, and a nonzero input-channel slice for down
projection. Tolerances were `rtol=0.01, atol=0.001`; tested outputs matched
the BF16 reference exactly. The two K sizes exercise one and two quantization
groups. No actual checkpoint weights were used.

SiLU timings use 20 repeated launches; W4 uses 2 warmups then 10 launches.
They include dispatch, NPU DMA/compute, and wait, but exclude BO input/output
synchronization and setup. They are single-session observations without
frequency control or a GPU baseline. They are not evidence of FFN/LLM
acceleration. W4 is deliberately scalar and remains an optimization target.

Local host validation also passed 10 unit tests, six W4 output-slice packing
cases, and one FP32 down-partial algebra case. Python syntax checks and
`git diff --check` passed.

## Reproduction

In the notebook's preconfigured `ironenv`:

```bash
cd /notebooks/HeteroMega/npu/ffn
make length=14336 tile_size=1024 cols=1
python run_silu_mul.py --json results/silu_mul_14336_hx370.json

make length=2048 tile_size=1024 cols=1 build_dir=build_silu_2048
python run_silu_mul.py --xclbin build_silu_2048/final.xclbin \
  --insts build_silu_2048/insts.bin --json results/silu_mul_2048_hx370.json

make length=14336 tile_size=512 cols=4 build_dir=build_silu_4col
python run_silu_mul.py --xclbin build_silu_4col/final.xclbin \
  --insts build_silu_4col/insts.bin --json results/silu_mul_14336_4col_hx370.json

make -f Makefile.w4a16 K=128 N=64
python run_w4a16_linear.py -K 128 -N 64 \
  --xclbin build_w4a16/final.xclbin --insts build_w4a16/insts.bin \
  --rtol .01 --atol .001 --json results/w4a16_k128_n64_hx370.json

make -f Makefile.w4a16 K=256 N=64 build_dir=build_w4a16_k256
python run_w4a16_linear.py -K 256 -N 64 \
  --xclbin build_w4a16_k256/final.xclbin --insts build_w4a16_k256/insts.bin \
  --rtol .01 --atol .001 --json results/w4a16_k256_n64_hx370.json
```

The initial native-tanh activation failed numerical checks and was replaced
with a direct sigmoid LUT. Explicit convergent BF16 rounding fixed W4 errors.
Two compiler cache hazards were addressed with source-hash specialization
and content/dimension-addressed object filenames. Successful results above
were collected after rebuilding those objects.

The full persistent FFN graph, HeteroMosaic integration, GPU/NPU reduction,
Max+ 395 profiling, Llama correctness, and end-to-end comparisons remain to
be implemented and evaluated; see [README.md](README.md).
