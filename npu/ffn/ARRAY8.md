# Eight-column W4A16 prefill projections

**Status: compiled and executed on HX370.** This document describes
`w4a16_prefill_reuse.py`, its C++ kernel, and `prefill_schedule.py`. See the
[hardware results](../../experiments/ffn_partition/ARRAY8_RESULTS.md) for tested
shapes, correctness and complete-FFN performance. Here, **legacy** means this
directory's `w4a16_prefill.py`, which
uses one compute core per selected column; it does not mean the original
HeteroMosaic model baseline.

## Placement and reuse

The graph uses all eight NPU2 columns and compute rows 2–5: 32 workers.
For `C[M,N] = A[M,K] @ W[N,K].T`, tiles remain M16/K128/N32. Let
`Mb=M/16`, `Kb=K/128`, `Nb=N/32`, `Cn=gcd(8,Nb)`, and `G=8/Cn`.
`Cn` columns partition output channels; `G` column groups partition token
rows. Each column's four workers own different groups of M16 tiles.

An activation stream for each worker row broadcasts horizontally across
`Cn` columns. One packed weight stream per column broadcasts vertically
to four workers. A worker dequantizes each K128/N32 weight tile once and
uses it for `R` consecutive M16 tiles before releasing it. The default
chooses the largest `R` in {1,2} dividing `Mb/(4*G)`. Each output tile
retains its own FP32 accumulator across all K blocks. Four worker outputs
join in the column's memory tile and scatter into the compact output BO.

For **M128/N128**, `Cn=4`, `G=2`, and `R=1`: columns 0–3 and 4–7 own
different 64-token halves, while each group covers all 128 output channels.
All 32 workers remain active. For **M128/N256**, `Cn=8`, `G=1`, and `R=2`:
each worker handles two M16 tiles. Thus an M128 FFN with a 128-channel NPU
partition uses R1 for gate/up, but normally R2 for down when its output
hidden width is divisible by 256. The graph never silently substitutes
four physical columns for eight.

## Exact logical traffic

Define `T=Mb*Nb*Kb`. The following counts cover one projection, summed
across all streams. Host/shim bytes count scheduled payloads crossing the
NPU boundary, excluding protocol overhead and host/XRT synchronization.
They are **code-derived logical counts**, not measured DRAM transactions.

| Quantity | Legacy | Array8 |
| --- | ---: | ---: |
| Activation host/shim bytes | `4096*T` | `4096*T/Cn` |
| Packed-weight host/shim bytes | `2144*T` | `2144*T/(4*R)` |
| Output host/shim bytes | `1024*Mb*Nb` | unchanged |
| Weight dequantization calls across cores | `T` | `T/R` |
| Activation bytes consumed across cores | `4096*T` | unchanged |
| Packed-weight bytes consumed across cores | `2144*T` | `2144*T/R` |
| Runtime task groups | `Mb` | `Mb/(4*G*R)` |
| Matrix arithmetic, counting multiply/add separately | `2*M*N*K` | unchanged |

Horizontal multicast reduces activation host/shim reads by 8× when
`Cn=8`, or 4× when `Cn=4`. Vertical multicast plus R2 reduces weight
host/shim reads by 8×, but dequantization by only 2×: each of four cores
still dequantizes its received copy. R1 reduces weight host/shim reads by
4× without reducing the total dequantization count. These factors are
not latency speedups and exclude shared-memory interference.

The BO layouts and capacities are unchanged: A is BF16 `[Mb,Kb,2048]`, W
is uint8 `[Nb,Kb,2144]`, and C is BF16 `[Mb,Nb,512]`. Multicast does not
duplicate host BOs. Canonical weights and device-packed weights may still
coexist in application memory. Weights are replayed for subsequent M
groups; the complete model is not retained in NPU on-chip memory.

## DMA and numerical contracts

For each row stream the A shim tap is
`sizes=[localNb,4*Kb,R,512]`, `strides=[0,512,Kb*2048,1]`, where
`localNb=Nb/Cn`. It emits `[quarter,R,512]` within each grouped A object.
The memory-tile forward permutation restores `[R,2048]` using
`[(R,512),(4,R*512),(512,1)]`. This preserves the existing host
and C++ layouts without a host repack.

Two limits matter: shim ND wraps permit at most 1023 **32-bit words**,
while the pinned `aie.dma_bd` verifier additionally rejects dimensions
above 512 **elements** despite its diagnostic saying 1023. The final
512-element span satisfies that verifier, and `4*Kb<=512` under the K
bound. A memory-tile transform with a 1024-element dimension fails
compilation. Fixed shim endpoints use input channel 0 for A, input channel
1 for W, and output channel 0 for C. A memory tile needs at most six input
DMA channels and three output channels.

Arithmetic remains native BF16 multiplication with FP32 accumulation.
Unsigned int4 weights use K128 groups and dequantize as
`BF16((q-zero)*BF16(scale))`. Each output accumulates all K blocks in
FP32, then converts once to BF16 with round-to-nearest-even. The source
rejects BF16-to-BFP16 MMUL emulation. Reuse shares dequantization without
combining the accumulators of different token rows. Cross-device partial
rounding and final reduction still require separate FFN validation.

## Constraints and remaining costs

- M/K/N must be multiples of 128 and at least 128; M is at most 4096,
  and K/N at most 16384. Exactly eight columns and four rows are required.
  `localNb` must be at most 64. Some widths below N16384 therefore fail:
  N14208 uses four N-columns and would require 111 repeats.
- The CLI exposes maximum reuse 1/2/4, but the partition adapter selects
  maximum 2. R2's raw core buffers and 2KiB stack total about 38.2KiB;
  R4 approaches 64KiB before alignment or spills. Accepted dimensions
  are not evidence that every placement compiles or runs.
- Matrix arithmetic is unchanged. Dequantization, scratch-buffer traffic,
  DMA routing, multicast backpressure, and task-group synchronization
  remain potential costs; their importance requires measurement.
- The FFN adapter still runs gate, up, SiLU/multiply, and down as four
  launches. Intermediates pass through host DRAM, with CPU layout conversion
  before down. This projection graph does not fuse the complete FFN or
  establish coherent zero-copy GPU/XRT sharing.
- Measure complete FFN wall time, including staging, layout conversion,
  waits and reduction, before comparing against HeteroMosaic without FFN
  offload. Model prefill and attention interference remain separate checks.

## Pinned implementation references

All AMD references below use MLIR-AIE commit
`7e00b57955e108fe9d8e9419f5828a0c7e650858`:

- [Whole-array matmul topology and memory-tile transformations](https://github.com/Xilinx/mlir-aie/blob/7e00b57955e108fe9d8e9419f5828a0c7e650858/programming_examples/basic/matrix_multiplication/whole_array/whole_array.py).
- [AIE2P MMUL kernel patterns](https://github.com/Xilinx/mlir-aie/blob/7e00b57955e108fe9d8e9419f5828a0c7e650858/aie_kernels/aie2p/mm.cc).
- [IRON ObjectFifo forward/join and endpoint APIs](https://github.com/Xilinx/mlir-aie/blob/7e00b57955e108fe9d8e9419f5828a0c7e650858/python/iron/dataflow/objectfifo.py).
- [DMA dimension verifier](https://github.com/Xilinx/mlir-aie/blob/7e00b57955e108fe9d8e9419f5828a0c7e650858/lib/Dialect/AIE/IR/AIEDialect.cpp#L2449) and [word-based shim descriptor encoding](https://github.com/Xilinx/mlir-aie/blob/7e00b57955e108fe9d8e9419f5828a0c7e650858/include/aie/Dialect/AIEX/Utils/BdLowering.h).

See [PREFILL.md](PREFILL.md) for the packing contract and legacy runner,
and [the partition experiment](../../experiments/ffn_partition/README.md)
for complete-FFN timing boundaries. Legacy results remain separate from Array8.
