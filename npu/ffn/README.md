# Final NPU FFN prefill kernels

Eight NPU2 columns × four compute rows, W4A16 group128 with BFP16 matrix
compute and FP32 partial sums. Selected shape: **M512, H4096, P2560** NPU
intermediate channels (out of I14336).

| Stage | Generated MLIR | XCLBIN | Matching instructions |
|---|---|---|---|
| Gate + up + SiLU × up | [aie.mlir](prebuilt/swiglu_m512_k4096_p2560/aie.mlir) | [final.xclbin](prebuilt/swiglu_m512_k4096_p2560/final.xclbin) | [insts.bin](prebuilt/swiglu_m512_k4096_p2560/insts.bin) |
| Down projection | [aie.mlir](prebuilt/down_m512_k2560_n4096/aie.mlir) | [final.xclbin](prebuilt/down_m512_k2560_n4096/final.xclbin) | [insts.bin](prebuilt/down_m512_k2560_n4096/insts.bin) |

These are the exact binaries exercised on HX370 with NPU power mode `default`.
Each manifest records its shape, arithmetic and binary hashes. They compute
the NPU partial FFN; the caller runs complementary GPU channels and sums the
two down-projection outputs on the GPU. Whole-model integration is separate.

## Rebuild

Use the configured MLIR-AIE/IRON environment at
`7e00b57955e108fe9d8e9419f5828a0c7e650858`. From this directory:

```bash
mkdir -p build/swiglu build/down
python w4a16_swiglu.py -M 512 -K 4096 -P 2560 -co 8 \
  --max-reuse 2 --arithmetic bfp16 \
  --xclbin-path build/swiglu/final.xclbin \
  --insts-path build/swiglu/insts.bin --pdi-path build/swiglu/final.pdi
python w4a16_prefill_reuse.py -M 512 -K 2560 -N 4096 -co 8 \
  --max-reuse 2 --arithmetic bfp16 \
  --xclbin-path build/down/final.xclbin \
  --insts-path build/down/insts.bin --pdi-path build/down/final.pdi
```

The generators build the external C++ objects referenced by the MLIR.
`w4a16_prefill_bfp16.cc` is the selected projection kernel; `silu_mul.cc`
implements the fused pointwise step. `w4a16_prefill_reuse.cc` remains an
import dependency of the unchanged generators. BFP16 is selected explicitly.

## Runtime contract

XRT kernel name: `MLIR_AIE`. Launch arguments:
`(3, instruction_bo, instruction_bytes, A_bo, W_bo, Y_bo)`.
Instruction length is **bytes**, not words. Instruction BO uses group 1;
A/W/Y BOs use groups 3/4/5. Sync inputs to device, wait for completed
execution, then sync the output from device. Keep each XCLBIN/instruction pair
together. No separate PDI or standalone pointwise binary is needed at runtime.

| Stage | A bytes | W bytes | Y bytes |
|---|---:|---:|---:|
| SwiGLU | 4,194,304 | 10,977,280 | 2,621,440 |
| Down | 2,621,440 | 5,488,640 | 4,194,304 |

All buffers are compact, contiguous and little-endian:

- A: BF16 `[M/16, K/128, 4, 16, 4, 8]`, indexed as
  `[m_block, k_block, m_micro, k_micro, m_inner, k_inner]`.
- W: bytes `[N/32, K/128, 2144]`. Each tile has 2,048 unsigned-W4
  bytes, 64 BF16-scale bytes and 32 unsigned-zero bytes (zeros **0–15**).
  Q order is `[k_micro=16, n_micro=4, k_inner=8, n_pair=4]`;
  the low nibble is the even N lane. Scales/zeros follow logical N order.
  SwiGLU concatenates the packed gate weights followed by packed up weights.
- Y: BF16 `[M/16, N/32, 4, 4, 4, 8]`, indexed as
  `[m_block, n_block, m_micro, n_micro, m_inner, n_inner]`.
  For SwiGLU, output N is P2560, while combined weight N is 5120.

Repack SwiGLU output before down: for flat uint16 BF16 bits `z`, use
`ascontiguousarray(z.reshape(32,20,4,4,4,4,8).transpose(0,1,3,2,4,5,6)).reshape(-1)`.
Z passes through shared DRAM/host layout conversion between the two launches;
it does not stay on-chip through down. BFP16 numerical differences are expected.

Verify package integrity from this directory: `sha256sum -c SHA256SUMS`.
Attribution and license: [NOTICE](NOTICE) and [MLIR-AIE license](licenses/MLIR-AIE-LICENSE.txt).
