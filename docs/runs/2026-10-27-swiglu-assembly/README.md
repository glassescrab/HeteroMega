# First NPU launch: selected native-BF16 SwiGLU assembly

The strongest assembly-level explanation for the first launch's latency is
the volume of native-BF16 matrix instructions, followed by serialized W4
dequantization and repeated local-memory accesses. The selected MMUL loop
does not have accumulator spills. Exact time shares require a device trace;
this inspection does not convert instruction counts into measured cycles.

This report inspects the tested package `fc0b255`, M512/K4096/P2560, eight
columns and 32 workers. The first launch computes **both gate and up
projections, then SiLU(gate) × up**. Sixteen workers compute gate and sixteen
compute up; the latter also perform the pointwise operation. Down is a
separate second launch. No kernels or runtime settings changed for this audit.

## Measured boundary

The existing final ABBA/BAAB reports give first-launch host dispatch-plus-wait
medians of **11.810640 / 11.7303765 ms**. Including its BO I/O, the SwiGLU
stage medians are **12.497917 / 12.424878 ms**. These are host-observed
intervals containing device execution and synchronization, not isolated
MMUL/dequantization/FIFO cycle measurements. Fixed-weight uploads are outside
the timing. Row-major input handling is about 0.003 ms and the former Z
permutation is about 0.001 ms in this selected profile.

Gate/up projection arithmetic is `2 projections × 2 × 512 × 4096 × 2560`
= **21.47483648 GFLOPs**. Dividing by the measured launch/wait interval gives
about **1.82–1.83 effective TFLOP/s**, including all other work inside that
interval. This is not a peak hardware throughput figure.

## What the projection assembly does

Representative gate worker: `(column 0, row 2)`. Up worker `(1,2)` has the
same projection instruction structure, at different addresses.

| Gate-worker address | Work | Interpretation |
|---|---|---|
| `0x20d0` | `w4a16_prefill_reuse_accumulate_low` | One N32 half of an original N64 payload; two M16 reuse lanes |
| `0x2150–0x22c4` | W4 dequantization | Unpack nibbles, vector zero adjustment, scale, BF16 narrowing, scratch stores |
| `0x2300–0x2674` | Reuse/M/N loops and MMUL | Consume dequantized scratch; update local FP32 partial sums |
| `0x2490–0x25c0` | Repeated K8 MMUL body | 32 `vmac.f` instructions in 36 encoded instruction bundles |
| `0x26b0` | `w4a16_prefill_reuse_accumulate_high` | Repeat the same computation for the other N32 half |
| `0x2c90` | Finish | Narrow completed FP32 partials to BF16 |

For example, this is actual assembly in the repeated MMUL body, with encoded
bytes removed for readability:

```asm
24fc: vmac.f dm0, dm0, x8, x1, r1
2500: vmac.f dm2, dm1, x9, x6, r1
2504: vshuffle x9, x0, x0, r5 ; vmac.f dm1, dm3, x9, x5, r1
250c: vshuffle x2, x3, x3, r5 ; vmac.f dm4, dm4, x2, x6, r1
2514: vextbcstshfl.64 x8, x9, r22, r29 ; vmac.f dm0, dm0, x2, x5, r1
251c: vextbcst.128 x10, x6, #0x0
2520: vextbcst.128 x1, x5, #0x0
2524: vextbcstshfl.64 x8, x2, r22, r29 ; vmac.f dm2, dm2, x8, x10, r1
```

The four C++ `acc.mac(...)` operations in one K8 step lower to **32 native
`vmac.f` instructions**, eight per 4×8×8 matrix operation. The repeat also
contains 16 `vextbcst.128`, 16 `vextbcstshfl.64`, two `vshuffle` and six vector
load instructions. Many are bundled together with MAC instructions: summing
opcode counts does not give elapsed cycles. There are zero MMUL stack vector
loads/stores in this selected loop.

Per worker, four M waves × ten N64 segments × 32 K128 groups × two N32 halves
give **2,560 accumulate-half calls**. Each call executes two reuse lanes ×
four register blocks × 16 K8 steps × 32 `vmac.f` = **4,096 `vmac.f`**.
Thus the launch executes **335,544,320 projection `vmac.f` instructions
across the array**, or **10,485,760 per worker**. This count includes the
software-pipeline prologue/epilogue; it is not just the number of instructions
printed once in the repeated body.

W4 is a storage format here. The worker expands W4 into BF16 and performs
native floating-point MACs; it is not executing an INT4 matrix multiply.
This explains why a small packed weight buffer does not imply a proportionally
small amount of computation.

## Dequantization and local traffic

Representative instructions include `vldb.unpack`, `vunpack`, `vbor`,
`vsub.f`, `vmul.f`, BF16/FP32 conversions and `vst.conv.bf16.fp32`.
Vectorized zero metadata removes the old scalar lane-construction loop, but
it does not remove unpacking/scaling of the actual weight values.

The complete 8 KiB N32 scratch is produced **before** MMUL starts. The same
scratch is then reused for two M16 tiles; low and high halves run sequentially.
The two-segment DMA pipeline can overlap transfers with execution, but it does
not overlap dequantization and MMUL on a worker.

Across this launch, **81,920 half-tile dequantizations** expand 335,544,320
weight values. The same logical gate/up weights are dequantized repeatedly
across M tiles and workers. Source/assembly operand volumes are:

| Local operand traffic | Per accumulate-half call | Across the launch |
|---|---:|---:|
| Dequant scratch writes | 8 KiB | 640 MiB |
| Dequant scratch reads by MMUL | 32 KiB | 2,560 MiB |
| Activation operand reads by MMUL | 16 KiB | 1,280 MiB |
| FP32 partial-sum reads + writes | 8 KiB | 640 MiB |

These are local operand-access counts, excluding other traffic and not
physical DRAM measurements. Multicast and reuse make logical shim traffic
much smaller: **40 MiB activations and 42.5 MiB packed weights**, plus
2.5 MiB final Z. In particular, do not call the scratch-table totals host
weight movement or infer DRAM saturation from them.

FP32 accumulators persist in on-chip buffers across K128 groups, but are
loaded into vector registers and stored back for each group. Gate/up partitions
remain logically local; that does not keep all full-layer weights or activations
resident in one core.

## Pointwise and synchronization

The up worker's `silu_mul_bf16` is at `0x3120`; its repeated vector loop is
`0x3220–0x3330`. It clamps, forms LUT indices, gathers slope/intercept values,
does a linear sigmoid approximation, applies saturation masks, then performs
the two multiplies for `gate × sigmoid(gate) × up` with BF16 narrowing.
There is no scalar `exp`, division, reciprocal routine or external math call.

The LUT abstraction lowers with substantial pointer/state loads and stores,
and a 512-byte function stack frame; the coefficient banks are a separate
4 KiB allocation. Its 16-element loop has **71 encoded bundles**,
including 23 standalone NOPs, and 380 bytes of stack-object loads/stores through
derived pointers. This traffic is in addition to 64 bytes of gate/up reads,
32 bytes of output and 128 bytes of LUT gathers. It is an optimization
opportunity, not free work.
However, each up worker calls it only 80 times for 1,024 elements each:
5,120 vector iterations per up worker, versus 10.49 million projection
`vmac.f` instructions on that worker. Counts are different units and must
not be presented as a measured time ratio.

Each worker acquires A/W for a K128 group, computes both halves, then releases
those inputs. Only after all 32 K groups does gate publish its BF16 result.
Up then acquires the matching gate and output FIFO entries for SiLU/multiply.
Actual assembly has `acq`/`rel` instructions around these boundaries. It can
stall on input availability, its paired gate worker or output backpressure;
disassembly alone does not reveal how long any acquisition waited. The
graph executes 85,760 core acquisitions and as many releases, excluding
DMA-side locks, with 1,280 gate-to-up handoffs. There is no global core barrier
at each K step. Gate handoff uses producer-local memory readable by the
neighboring up core; it does not send the gate tensor through DRAM. Counts
describe completed workload, excluding the persistent cores beginning to wait
for a following invocation.

The selected four-accumulator kernel has no MMUL accumulator spills and fits
its 2 KiB stack. The previously tried eight-accumulator variant has a separate,
confirmed spill problem and was rejected; its slowdown must not be attributed
to the currently selected kernel.

## What to prioritize

The largest code-confirmed workload is native-BF16 projection MAC issue and
operand rearrangement. Next are repeated dequantization, scratch traffic and
K-group accumulator round trips. SiLU bookkeeping is smaller in repetition
count; FIFO/DMA stalls remain unmeasured. This ranking is a structural
interpretation, not a measured phase-percentage breakdown.

The next measurement should bracket dequantization and MMUL separately and
record lock/DMA stalls and device clock. Existing projection `event0/event1`
markers wrap dequantization plus MMUL together. A meaningful optimization
comparison would then test overlap/reuse or a tighter native-BF16 lowering
while avoiding the rejected accumulator-spill configuration. No such speedup
is asserted from this assembly inspection.

## Evidence identity

XCLBIN SHA256:
`2111b6f39da09f54e0a45fef20bf9ae923fd6a65e1a65f62e0525f6e2bea530a`.
Instructions SHA256:
`d0d731e3fa3880beccfa908b2213c9d125b05f6404d6eadbb1f07d4c9e5b0df5`.
Representative gate disassembly SHA256:
`7231758c77b3339bab81ab9dbe9add087fbb1f1e799cdf7de7f48fa89222a2eb`;
up disassembly SHA256:
`17572f9f85199f611890615549fa58fc24f5ae555a360512ad0cff5a98ad6802`.

[Assembly counts and timings](assembly_counts.json) record repeat-body
opcode counts and timing-report identities. The [projection audit](projection_assembly.json)
and [reproduction script](analyze_projection.py) verify prologue/repeated-body/
epilogue accounting for all four representative gate/up low/high routines.
The [pointwise audit](pointwise_assembly.json) verifies the SiLU instructions
against ELF bytes, including four NOPs hidden by the disassembler ellipsis.
To reproduce the projection audit, extract the preceding evidence archives
under `/tmp`, then run `python docs/runs/2026-10-27-swiglu-assembly/analyze_projection.py`. Full binaries and disassembly are
in the [previous optimization evidence](../2026-10-25-kernel-optimizations/README.md).
No new hardware run or kernel change was performed on October 27.
