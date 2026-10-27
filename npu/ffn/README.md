# Final NPU FFN prefill kernels

Eight NPU2 columns × four compute rows. The selected binaries use
**BFP16-backed 8×8×8 MMUL** from glassescrab TileFuse, with BF16 I/O,
unsigned W4 weights, K128 quantization groups and FP32 partial sums.
`--arithmetic bf16` retains the native 4×8×8 control; `--arithmetic bfp16`
selects the packaged variant.

These kernels accept the **original glassescrab TileFuse packed weight
buffers directly**. There is no weight repacking or gate/up concatenation.
Selected partition: M512, H4096, P2560 out of full I14336. This partition is
retained for compatibility testing; it has not been retuned for this design.

The selected graph accepts row-major SwiGLU input and scatters its output
straight into the down projection's activation layout. Down reuses each weight
tile across four M16 lanes with a single core activation FIFO buffer; SwiGLU
retains reuse two. Vector zero-point metadata construction preserves exact
BF16 bits. Both stages retain the bounded two-segment DMA pipeline and the
four-accumulator MMUL path. These choices are explicit build options; baseline
controls remain available.

| Stage | Generated MLIR | XCLBIN | Instructions |
|---|---|---|---|
| Gate + up + SiLU × up | [aie.mlir](prebuilt/swiglu_m512_k4096_p2560/aie.mlir) | [final.xclbin](prebuilt/swiglu_m512_k4096_p2560/final.xclbin) | [insts.bin](prebuilt/swiglu_m512_k4096_p2560/insts.bin) |
| Down projection | [aie.mlir](prebuilt/down_m512_k2560_n4096/aie.mlir) | [final.xclbin](prebuilt/down_m512_k2560_n4096/final.xclbin) | [insts.bin](prebuilt/down_m512_k2560_n4096/insts.bin) |

The packaged model-shape binaries pass signed/changed-input, zero and
repeatability checks on HX370/default power under the original numerical
bounds. BFP16 correctness checks cover five small cases, M512/H4096/P2560
and a P1152 partition at offset128: 40 completed NPU launches. A rebuilt
native model-shape control adds eight successful launches. Worst BFP16
relative L2 versus the BF16 CPU oracle is **0.0167717**, below the unchanged
0.02 limit. Report mode retains numerical verdicts; these runs all passed.

With the same original weight bytes, layout/reuse options and synthetic
inputs, isolated NPU-branch median latency is **22.322→14.470 ms (35.18%)**
in ABBA order and **22.405→14.650 ms (34.61%)** in BAAB order. Each arithmetic
has 100 timed samples per order. Native/BFP16 have separate deterministic
references; all warmup/timed outputs match their own arithmetic exactly.
The two timing experiments completed 976 NPU launches including references,
structural checks and warmup. BFP16 versus native maximum relative L2 is
0.0166252; maximum absolute error is 0.00305176. Native output is unchanged.

The timer includes host validation, activation handling, BO I/O, both
launch/waits and final output unpacking. Construction, fixed-weight upload,
output snapshots and checks are excluded. SwiGLU host launch-plus-wait
falls from 11.729 to 6.512 ms in ABBA; this is not device-only compute time.
The caller borrows intermediate readback views; BO reads/synchronization remain.

These are isolated NPU-branch results. Combined GPU+NPU prefill acceleration
and pretrained-model accuracy remain unvalidated. Synthetic checks do not
establish model accuracy. Partition P2560 has not been retuned.

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
python w4a16_upstream.py --arithmetic bfp16 --mode swiglu -M 512 -K 4096 -N 2560 \
  --weight-k 4096 --weight-n 14336 --max-reuse 2 --segment-pipeline-depth 2 \
  --vector-zero --mmul-m-reuse 1 --activation-fifo-depth 2 \
  --input-layout row_major --output-layout down_a \
  --xclbin-path build/swiglu/final.xclbin \
  --insts-path build/swiglu/insts.bin --pdi-path build/swiglu/final.pdi
python w4a16_upstream.py --arithmetic bfp16 --mode projection -M 512 -K 2560 -N 4096 \
  --weight-k 14336 --weight-n 4096 --max-reuse 4 --segment-pipeline-depth 2 \
  --vector-zero --mmul-m-reuse 1 --activation-fifo-depth 1 \
  --input-layout compact --output-layout compact \
  --xclbin-path build/down/final.xclbin \
  --insts-path build/down/insts.bin --pdi-path build/down/final.pdi
```

`--weight-k/--weight-n` describe the full original buffer. `-K/-N` and
`--k-start/--n-start` describe the selected region; K starts align to 128,
N starts to 32. `-N` means P for SwiGLU. The packaged binaries select start 0.
BFP16 is explicit in these commands; use `--arithmetic bf16` for the native
control. Arithmetic is recorded in each object/cache/manifest identity.
Pipeline depth is recorded in the manifest. Depth one and two use distinct
compiled artifact identities; the packaged binaries use depth two.

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

Activations use little-endian BF16 bits:

- SwiGLU A: row-major `[M,H]`.
- SwiGLU Z and down A: `[M/16,P/128,4,16,4,8]`.
- Down Y: compact `[M/16,H/32,4,4,4,8]`.

The SwiGLU DMA writes the down-A layout directly; pass Z unchanged to down.
No CPU Z permutation is required. Z still traverses shared DRAM and the
current caller still reads and writes BOs between launches. This is not an
on-chip fused FFN or a shared-BO claim. Final Y must be unpacked into row-major
order before reducing it with the complementary GPU result. A borrowed
readback view is valid only until the same non-reentrant runner is reused;
materialize independent final Y before returning or overlapping calls.

To rebuild the prior two-segment control, omit `--vector-zero`, use reuse two
and activation FIFO depth two for both stages, and choose compact input/output.
`--segment-pipeline-depth 1` retains the older serial schedule. Each option is
recorded in the manifest/cache identity. Native-only experimental
`--mmul-m-reuse 2` reserves a 4 KiB stack: the original 2 KiB overflowed on full shapes. Even after
the fix it is about 2.2× slower because of heavy register spilling, so these
BFP16 binaries use `--mmul-m-reuse 1` and 4 KiB stacks. Native MMUL1 uses
2 KiB. BFP16 rejects MMUL2. SwiGLU reuse four is unsupported.

Verify integrity from this directory: `sha256sum -c SHA256SUMS`.
Each manifest identifies selected BFP16 arithmetic, upstream weight layout, full source
geometry, selected slice and source/binary hashes. Earlier compact-weight
artifacts are incompatible; native and BFP16 artifacts cannot be substituted. Attribution: [NOTICE](NOTICE) and
[MLIR-AIE license](licenses/MLIR-AIE-LICENSE.txt).
