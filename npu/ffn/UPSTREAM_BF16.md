# Native BF16 with original glassescrab W4A16 buffers

The current requested path is `w4a16_upstream.py`: eight NPU columns, four
compute rows per column, native BF16 4×8×8 matrix multiplication and FP32
partial sums across K128 groups. BFP16 emulation is explicitly disabled.
The previous compact/BFP16 sources and measurements remain historical controls.

The selected experimental profile is `combo_mmul1_row_major`: vectorized
zero-point loads, the original four-accumulator MMUL, SwiGLU M reuse 2,
down-projection M reuse 4, row-major SwiGLU input and output already arranged
for the down projection. The host adapter borrows BO readback views. These
choices are explicit options; graph and adapter defaults retain the controls.

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
without a copy. `--vector-zero` reads the original duplicated N8 zero-point
metadata with vector loads. It changes neither the packed bytes nor the
native BF16 dequantization arithmetic.

## Selected activation interface

| Stage | Input A buffer | Output buffer |
|---|---|---|
| SwiGLU | Row-major BF16 `[M,H]` | Native down-A BF16 `[M/16,P/128,4,16,4,8]` |
| Down | The SwiGLU output in that native A layout | Compact C BF16 `[M/16,H/32,4,4,4,8]` |

For `--input-layout row_major`, the shim gathers K128 pieces from the original
row strides and memory-tile DMA permutes them into the existing core A layout.
`--output-layout down_a` scatters the unchanged SwiGLU worker stream directly
into the down-input layout. The selected adapter therefore skips the CPU input
packing and SwiGLU-to-down permutation. Its final compact-output-to-row-major
conversion remains, and `.run(...)` still returns BF16 uint16 `[M,H]`.

Both launches retain BO writes, reads and synchronization. Z is host-staged
between launches; the new layout does not establish continuous on-chip
residency. `copy_output_bits=False` avoids the additional ownership copy by
borrowing readback views until they are consumed. The adapter remains
non-reentrant; these are not persistent output views or a zero-copy weight ABI.

## Build and call

In the configured MLIR-AIE environment at
`7e00b57955e108fe9d8e9419f5828a0c7e650858`, for M512/H4096/P2560 and full
intermediate width 14336:

```bash
python npu/ffn/w4a16_upstream.py --mode swiglu -M 512 -K 4096 -N 2560 \
  --weight-k 4096 --weight-n 14336 \
  --vector-zero --mmul-m-reuse 1 --max-reuse 2 --activation-fifo-depth 2 \
  --input-layout row_major --output-layout down_a --segment-pipeline-depth 2 \
  --xclbin-path build/swiglu/final.xclbin \
  --insts-path build/swiglu/insts.bin --pdi-path build/swiglu/final.pdi
python npu/ffn/w4a16_upstream.py --mode projection -M 512 -K 2560 -N 4096 \
  --weight-k 14336 --weight-n 4096 \
  --vector-zero --mmul-m-reuse 1 --max-reuse 4 --activation-fifo-depth 1 \
  --input-layout compact --output-layout compact --segment-pipeline-depth 2 \
  --xclbin-path build/down/final.xclbin \
  --insts-path build/down/insts.bin --pdi-path build/down/final.pdi
```

XRT launch inputs are `(A, gate_W, up_W, Z)` for SwiGLU and `(A, W, Y)` for
projection. The existing `MLIR_AIE` control/instruction arguments precede them;
instruction length is bytes. Verify the manifest's BF16 arithmetic, upstream
layout identifier, full source geometry, partition offsets, input/output
layouts, reuse, FIFO depth, MMUL mode, stack reservation and artifact hashes.
Old compact or BFP16 binaries are not interchangeable with this graph.

The preceding commands build the selected profile. To retain the original
native-BF16 control, omit `--vector-zero` and use `--max-reuse 2`,
`--activation-fifo-depth 2`, `--mmul-m-reuse 1`, `--input-layout compact` and
`--output-layout compact` for both stages. These remain their default values.
Pipeline depth defaults to 2; depth 1 retains the earlier serial schedule.

## M reuse and MMUL controls

`--max-reuse 4 --activation-fifo-depth 1` lets a down worker reuse each
dequantized N32 half over four M16 tiles. This reduces M waves from four to
two at M512. Only the core-consumer A FIFO becomes single-buffered; host and
memory-tile A buffers retain depth two. The estimated down-worker buffer
total, including the selected 2 KiB stack, is 59,904 bytes. Compilation,
memory placement and hardware checks remain necessary for another shape.
The effective reuse may be smaller than the requested maximum when M is small.

For M512/H4096/P2560 at channel start 0, the following are **code-confirmed
logical counts**, not measured physical bandwidth:

| Stage | Activation DMA | Packed-weight DMA | N32-half dequantizations | Projection arithmetic |
|---|---:|---:|---:|---:|
| SwiGLU, reuse 2 | 40 MiB | 42.5 MiB | 81,920 | 21.475 GFLOPs |
| Down control, reuse 2 | 20 MiB | 21.25 MiB | 40,960 | 10.737 GFLOPs |
| Down selected, reuse 4 | 20 MiB | 10.625 MiB | 20,480 | 10.737 GFLOPs |

Across the FFN, packed-weight DMA falls from 63.75 to 53.125 MiB and
dequantization calls from 122,880 to 102,400. Activation DMA remains 60 MiB:
the input is replayed ten times for SwiGLU and eight times for down.
Projection arithmetic remains 32.212 GFLOPs; SiLU and host work are excluded
from that arithmetic count. The input/output DMA layout options remove CPU
permutations without reducing these NPU transfer volumes.

The experimental `--mmul-m-reuse 2` pairs M16 lanes in an eight-accumulator
register block to share B loads. Compiler inspection found substantial
register spills and an overflowing nested call chain with the original
2 KiB stack. This mode now reserves 4 KiB, but it was slower in the ablation
and is not selected. `--mmul-m-reuse 1` retains the original four-accumulator
kernel and 2 KiB stack. Both preserve native BF16 and FP32 partial sums.

SwiGLU reuse 4 is currently rejected because its extra activation, accumulator,
gate and output storage needs a separate buffering redesign. Larger N reuse,
dequantization/MMUL overlap and partition retuning remain open optimizations.

## Segment pipeline

`--segment-pipeline-depth 2` keeps at most two successive N64 segments in
flight. Every segment queues its output drains before its activation and
weight fills. The runtime waits for and frees the oldest group before
submitting a third; the window continues across M-wave boundaries. Changing
pipeline depth alone leaves FIFO depths, core buffers, arithmetic and transfer
addresses unchanged; the other tuning options are independent.
Completion of a segment's output drains proves its input transfers are done
before their descriptors are reused. All groups are drained before return.

`--segment-pipeline-depth 1` reproduces the serial schedule for comparison.
Depth is part of the artifact manifest and cache identity. Two in-flight
segments require at most two tasks per DMA channel and six live shim buffer
descriptors in this graph. This does not increase core-local weight reuse or
overlap dequantization with MMUL inside an individual worker.

The experimental host adapter is
`experiments/ffn_partition/upstream_npu.py`. Wrap each existing flat contiguous
uint8 buffer in `UpstreamWeightBuffer(data, full_k, full_n)`, call
`build_upstream_artifacts(...)`, then construct `UpstreamNpuFFN(...)` and
pass BF16 uint16 input bits to `.run(...)`. It uploads fixed weights once.
It rejects unsupported storage rather than silently copying into another layout.

Use the same selected options when building and constructing the adapter:

```python
selected = dict(segment_pipeline_depth=2, swiglu_reuse=2, down_reuse=4,
                swiglu_activation_fifo_depth=2, down_activation_fifo_depth=1,
                vector_zero=True, mmul_m_reuse=1,
                swiglu_input_layout="row_major", output_layout="down_a")
build_upstream_artifacts(m, hidden, channels, gate, up, down, artifact_root,
                         python_executable=iron_python, **selected)
runner = UpstreamNpuFFN(m, hidden, channels, gate, up, down, artifact_root,
                       copy_output_bits=False, **selected)
y_bits = runner.run(x_bits)
```

`x_bits` is a contiguous row-major uint16 view of BF16 values; a noncontiguous
input requires the adapter's explicit contiguous staging copy. Borrowed
readback is a host option, not an XCLBIN argument. The benchmark harness names
the complete configuration `combo_mmul1_row_major`.

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
model accuracy or speedup. Compare tuning profiles on the same build and
inputs; previous compact/BFP16 latency measurements do not transfer. The
selected isolated NPU configuration still needs comparison under actual
GPU/attention overlap before claiming heterogeneous prefill acceleration.
