# Final NPU FFN prefill kernels

Eight NPU2 columns × four compute rows. Native **BF16** 4×8×8 matrix
multiplication, unsigned W4 weights, K128 quantization groups and FP32
partial sums. BFP16 emulation is disabled.

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

These exact binaries pass signed/changed-input, zero and repeatability checks
on HX370 under the original strict numerical bounds. Five small-shape cases
and one model-shape case completed 32 NPU launches. Selected model-shape
outputs match the previous two-segment native-BF16 package bit for bit.

At HX370 default power, complete isolated NPU-branch median latency improved
**24.576→22.590 ms (8.08%)** in ABBA order and
**24.194→22.490 ms (7.04%)** in BAAB order. Each profile has 100 timed samples
per order. All timed/warmup outputs match the baseline exactly; the two
confirmation experiments completed 896 NPU launches including reference and
warmup. The timer includes host validation, activation handling, BO I/O, both
launch/waits and final output unpacking. Construction, fixed-weight upload and
checks are excluded. The optimized caller also borrows intermediate BO-read
views instead of copying them again; BO read/sync remain.

These are isolated NPU-branch results. Combined GPU+NPU prefill acceleration
and pretrained-model accuracy remain unvalidated. Synthetic correctness does
not establish model accuracy. Partition P2560 has not been retuned.

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
  --weight-k 4096 --weight-n 14336 --max-reuse 2 --segment-pipeline-depth 2 \
  --vector-zero --mmul-m-reuse 1 --activation-fifo-depth 2 \
  --input-layout row_major --output-layout down_a \
  --xclbin-path build/swiglu/final.xclbin \
  --insts-path build/swiglu/insts.bin --pdi-path build/swiglu/final.pdi
python w4a16_upstream.py --mode projection -M 512 -K 2560 -N 4096 \
  --weight-k 14336 --weight-n 4096 --max-reuse 4 --segment-pipeline-depth 2 \
  --vector-zero --mmul-m-reuse 1 --activation-fifo-depth 1 \
  --input-layout compact --output-layout compact \
  --xclbin-path build/down/final.xclbin \
  --insts-path build/down/insts.bin --pdi-path build/down/final.pdi
```

`--weight-k/--weight-n` describe the full original buffer. `-K/-N` and
`--k-start/--n-start` describe the selected region; K starts align to 128,
N starts to 32. `-N` means P for SwiGLU. The packaged binaries select start 0.
Arithmetic is fixed to native BF16; there is no BFP16 selector in this graph.
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
recorded in the manifest/cache identity. Experimental `--mmul-m-reuse 2`
reserves a 4 KiB stack: the original 2 KiB overflowed on full shapes. Even after
the fix it is about 2.2× slower because of heavy register spilling, so these
binaries use `--mmul-m-reuse 1` and 2 KiB stacks. SwiGLU reuse four is unsupported.

Verify integrity from this directory: `sha256sum -c SHA256SUMS`.
Each manifest identifies BF16 arithmetic, upstream weight layout, full source
geometry, selected slice and source/binary hashes. Earlier compact/BFP16
artifacts are incompatible. Attribution: [NOTICE](NOTICE) and
[MLIR-AIE license](licenses/MLIR-AIE-LICENSE.txt).
