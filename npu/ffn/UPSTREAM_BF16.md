# Native BF16 with original glassescrab W4A16 buffers

The current requested path is `w4a16_upstream.py`: eight NPU columns, four
compute rows per column, native BF16 4×8×8 matrix multiplication and FP32
partial sums across K128 groups. BFP16 emulation is explicitly disabled.
The previous compact/BFP16 sources and measurements remain historical controls.

## Weight interface

Supply the original packed buffers from the corrected glassescrab TileFuse
producer at `121dd54abc68f84d89a7074372ebf82be2db62d5`:

- Full source logical W is K×N; K is divisible by 128 and N by 64.
- Each K128/N64 tile contains 4,096 packed unsigned INT4 bytes, 128 BF16 scale
  bytes and 128 zero-point bytes. Each N8 zero vector is repeated twice.
- N64 tiles are ordered by column modulo eight, then column within that stripe,
  then K128 group. INT4 low/high nibbles hold even/odd N lanes.
- The buffer size is `(full_K / 128) * (full_N / 64) * 4352` bytes.

Pass the **full source dimensions** even when computing a channel partition.
`--weight-k` and `--weight-n` describe that original buffer; `-K`, `-N`,
`--k-start` and `--n-start` select the logical region. K offsets align to 128;
N offsets align to 32. A partition never changes the packed buffer's strides.
Gate and up use separate original buffers; they are not concatenated.

Each worker acquires an original N64 tile and processes its owned N32 halves
using the same 8 KiB dequantization scratch and separate FP32 partial buffers.
Both halves owned by one worker share the input/weight transfer. A column
boundary splitting an N64 tile can cause two columns to read that tile; it
does not create a second packed host representation.

No compact-weight conversion, metadata rewrite or host weight reordering is
performed. The current XRT adapter still uploads the unchanged bytes into BOs
once; this is not a claim that the existing host allocation itself is imported
without a copy. Activations and outputs retain the previous compact BF16
layout, including the separate SwiGLU-to-down activation conversion.

## Build and call

In the configured MLIR-AIE environment at
`7e00b57955e108fe9d8e9419f5828a0c7e650858`, for M512/H4096/P2560 and full
intermediate width 14336:

```bash
python npu/ffn/w4a16_upstream.py --mode swiglu -M 512 -K 4096 -N 2560 \
  --weight-k 4096 --weight-n 14336 \
  --xclbin-path build/swiglu/final.xclbin \
  --insts-path build/swiglu/insts.bin --pdi-path build/swiglu/final.pdi
python npu/ffn/w4a16_upstream.py --mode projection -M 512 -K 2560 -N 4096 \
  --weight-k 14336 --weight-n 4096 \
  --xclbin-path build/down/final.xclbin \
  --insts-path build/down/insts.bin --pdi-path build/down/final.pdi
```

XRT launch inputs are `(A, gate_W, up_W, Z)` for SwiGLU and `(A, W, Y)` for
projection. The existing `MLIR_AIE` control/instruction arguments precede them;
instruction length is bytes. Verify the manifest's BF16 arithmetic, upstream
layout identifier, full source geometry, partition offsets and artifact hashes.
Old compact or BFP16 binaries are not interchangeable with this graph.

The experimental host adapter is
`experiments/ffn_partition/upstream_npu.py`. Wrap each existing flat contiguous
uint8 buffer in `UpstreamWeightBuffer(data, full_k, full_n)`, call
`build_upstream_artifacts(...)`, then construct `UpstreamNpuFFN(...)` and
pass BF16 uint16 input bits to `.run(...)`. It uploads fixed weights once.
It rejects unsupported storage rather than silently copying into another layout.

## Validation and scope

CPU tests independently enumerate upstream stripe order, metadata placement,
N32 halves, full-source K/N offsets, DMA streams and complete output coverage.
`experiments/ffn_partition/check_upstream.py` generates original-format test
fixtures directly and checks projection, fused SwiGLU and the complete NPU FFN
with signed inputs, changed inputs, exact zero and repeatability. Native BF16
uses the original strict tolerances. The script saves errors, successful
completion counts, input/output hashes and unchanged-weight checks.

Hardware results must be read from the corresponding saved report. A source
change or successful compile alone does not establish device correctness,
model accuracy or speedup. Per-segment runtime barriers differ from the old
graph, so previous latency measurements do not transfer to this design.
