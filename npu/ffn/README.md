# Final NPU FFN prefill kernels

Eight NPU2 columns × four compute rows. Native **BF16** 4×8×8 matrix
multiplication, unsigned W4 weights, K128 quantization groups and FP32
partial sums. BFP16 emulation is disabled.

These kernels accept the **original glassescrab TileFuse packed weight
buffers directly**. There is no weight repacking or gate/up concatenation.
Selected partition: M512, H4096, P2560 out of full I14336. This partition is
retained for compatibility testing; it has not been retuned for this design.

| Stage | Generated MLIR | XCLBIN | Instructions |
|---|---|---|---|
| Gate + up + SiLU × up | [aie.mlir](prebuilt/swiglu_m512_k4096_p2560/aie.mlir) | [final.xclbin](prebuilt/swiglu_m512_k4096_p2560/final.xclbin) | [insts.bin](prebuilt/swiglu_m512_k4096_p2560/insts.bin) |
| Down projection | [aie.mlir](prebuilt/down_m512_k2560_n4096/aie.mlir) | [final.xclbin](prebuilt/down_m512_k2560_n4096/final.xclbin) | [insts.bin](prebuilt/down_m512_k2560_n4096/insts.bin) |

These exact binaries passed signed/changed-input, zero and repeatability
checks on HX370. The selected FFN passed the original numerical bounds;
maximum observed relative L2 error was 0.003760. Seven test cases across
small/model shapes completed 40 NPU launches, including nonzero K/N slices,
paired halves, narrow N128 and an uneven P1152 partition. This establishes
synthetic NPU FFN correctness, not model accuracy or a new speedup claim.

## Original weight format

Pinned producer: glassescrab/mlir-aie
`121dd54abc68f84d89a7074372ebf82be2db62d5`,
`programming_examples/tilefuse/gemm_w4a16/test.cpp`.

- Full source logical weight shape: K×N; K is divisible by 128, N by 64.
- Each K128/N64 tile is **4,352 bytes**: 4,096 unsigned INT4 bytes,
  128 BF16-scale bytes, then 128 zero bytes. Every N8 zero vector is duplicated
  in place. Zero values are 0–15.
- Q order: `[k_micro=16,n_micro=8,k_inner=8,n_pair=4]`; the low nibble is
  the even N lane. Scale order is logical N. Zero order is `[8,2,8]`.
- Whole-buffer tile order: N64 column modulo eight, column within that stripe,
  then K128 group. This ordering is retained across partition selection.
- Full buffer bytes: `(K/128)*(N/64)*4352`. Full geometry is recorded in each
  manifest; never substitute the partition dimensions for it.

Workers process adjacent N32 halves of an original tile using one A/W
acquisition, one shared 8 KiB dequantization scratch and two FP32 partial
buffers. Column boundaries can cause a shared N64 tile to be read by two
columns. No second packed host representation is created.

## Rebuild

Use MLIR-AIE/IRON at `7e00b57955e108fe9d8e9419f5828a0c7e650858`.
From this directory:

```bash
mkdir -p build/swiglu build/down
python w4a16_upstream.py --mode swiglu -M 512 -K 4096 -N 2560 \
  --weight-k 4096 --weight-n 14336 --max-reuse 2 \
  --xclbin-path build/swiglu/final.xclbin \
  --insts-path build/swiglu/insts.bin --pdi-path build/swiglu/final.pdi
python w4a16_upstream.py --mode projection -M 512 -K 2560 -N 4096 \
  --weight-k 14336 --weight-n 4096 --max-reuse 2 \
  --xclbin-path build/down/final.xclbin \
  --insts-path build/down/insts.bin --pdi-path build/down/final.pdi
```

`--weight-k/--weight-n` describe the full original buffer. `-K/-N` and
`--k-start/--n-start` describe the selected region; K starts align to 128,
N starts to 32. `-N` means P for SwiGLU. The packaged binaries select start 0.
Arithmetic is fixed to native BF16; there is no BFP16 selector in this graph.

## Runtime contract

XRT kernel name: `MLIR_AIE`. Instruction length is **bytes**, not words.

- SwiGLU: `(3, instruction_bo, instruction_bytes, A_bo, gate_W_bo, up_W_bo, Z_bo)`.
- Down: `(3, instruction_bo, instruction_bytes, A_bo, W_bo, Y_bo)`.
- Instruction BO uses group 1. Tensor BO groups start at 3 in the listed order.
- Upload each original weight buffer once. Sync inputs, launch, check completed
  execution, then sync output. An unchanged BO upload is still a memory copy;
  direct format compatibility does not establish imported-buffer zero-copy.

| Buffer | SwiGLU bytes | Down bytes |
|---|---:|---:|
| A | 4,194,304 | 2,621,440 |
| Each original W | 31,195,136 (gate and up separately) | 31,195,136 |
| Output | 2,621,440 | 4,194,304 |

A and output remain compact little-endian BF16:

- A: `[M/16,K/128,4,16,4,8]`.
- Output: `[M/16,N/32,4,4,4,8]`, with N=P for SwiGLU.

The activation conversion before down remains: for flat uint16 Z, use
`ascontiguousarray(z.reshape(32,20,4,4,4,4,8).transpose(0,1,3,2,4,5,6)).reshape(-1)`.
This is an activation layout conversion, not weight repacking. Z goes through
shared DRAM between the two launches. The caller computes complementary GPU
channels and sums the two down partial outputs. Whole-model integration and
new GPU+NPU timing remain separate work.

Verify integrity from this directory: `sha256sum -c SHA256SUMS`.
Each manifest identifies BF16 arithmetic, upstream weight layout, full source
geometry, selected slice and source/binary hashes. Earlier compact/BFP16
artifacts are incompatible. Attribution: [NOTICE](NOTICE) and
[MLIR-AIE license](licenses/MLIR-AIE-LICENSE.txt).
