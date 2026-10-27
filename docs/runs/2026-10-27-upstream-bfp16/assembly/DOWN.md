# Down projection: BFP16 result and remaining work

**Already implemented and measured:** package `fd67fbf` selects glassescrab's
BFP16-backed 8×8×8 MMUL for **both SwiGLU and down**. Down retains eight
columns/32 workers, original packed weight buffers, BF16 I/O and FP32 partials.
This follow-up audits the saved down artifacts and measurements; it makes no
new kernel change or hardware run.

The down operation is `[512,2560] × [2560,4096]`. DMA selects its K2560 slice
from the original full `[14336,4096]` packed weight buffer. The graph uses
M16 reuse four, one core activation buffer and a two-segment pipeline.

## Measured latency

These are down-stage measurements from the existing paired FFN experiments,
100 calls per arithmetic/order on HX370/default power:

| Interval | ABBA native → BFP16 ms | BAAB native → BFP16 ms |
|---|---:|---:|
| Down host launch-plus-wait | 7.223 → 4.732 | 7.228 → 4.791 |
| Down including BO I/O | 7.906 → 5.333 | 7.917 → 5.460 |
| Final CPU output unpack, separately timed | 1.685 → 1.576 | 1.682 → 1.647 |
| Down BO I/O through final unpack | 9.581 → 6.915 | 9.593 → 7.055 |

Launch-plus-wait falls **34.49% / 33.71%**. The last row takes medians of
per-call sums, not sums of medians. Wait intervals include runtime, DMA and
worker dependencies, not just matrix compute. Both projections change
arithmetic in these experiments, so down receives a different numerical Z;
this is not an isolated fixed-Z down-only ablation.

## Compiled instruction breakdown

The original whole-package [assembly audit](README.md) covers native and
BFP16 down ELFs. Down reuse four doubles the per-call M work relative to the
SwiGLU reuse-two example:

| Per K128/N32 half-call, M16 reuse4 | Native BF16 | BFP16 |
|---|---:|---:|
| Output register-block groups | 16 | 8 |
| Matrix MAC instructions | 8,192 | 512 |
| Steady MMUL bundles | 8,640 | 2,400 |
| Dequantized scratch written | 8 KiB | 8 KiB |
| Dequantized scratch read | 64 KiB | 32 KiB |
| A operands read | 32 KiB | 32 KiB |
| FP32 partials read + written | 8 + 8 KiB | 8 + 8 KiB |

The BFP16 loop uses `vconv.bfp16ebs8.fp32` and matrix `vmac.f` on `ex`
operands: four matrix MACs in a 20-bundle steady K8 body. Native has 32 MACs
in 36 bundles. BFP16 requires 512 operand conversions and 256 helper multiplies
per complete half-call, plus gather/shuffle work. Counts are decoded
instructions/bundles, **not measured cycles**. The steady-bundle totals exclude
prologues, tails, outer-loop control, dequantization and graph waits.

For core0,row2 in the retained BFP16 down disassembly, dequantization's low
half-loop is at `0x1730–0x1780` (lines1232–1246), followed by low MMUL at
`0x19b0–0x1a30` (lines1331–1352). High MMUL is at `0x1f10–0x1f90`
(lines1553–1574). The core1,row2 representative confirms the same counts.

**Code-confirmed schedule:** two M waves × eight N64 segments ×20 K128 groups
×two halves gives640 half-calls per worker and20,480 overall. That is
167,772,160 native matrix instructions versus10,485,760 BFP16 instructions.
Down executes no SiLU kernel. Each worker makes320 A/W acquisition pairs
and32 output acquisitions:21,504 core FIFO acquires and21,504 releases total.

Logical BFP16 local operand traffic across the launch is160 MiB of scratch
writes,640 MiB of scratch reads,640 MiB of A reads and320 MiB of FP32-partial
reads/writes. Separately, graph DMA schedules20 MiB of activation reads,
10.625 MiB of packed weights and4 MiB of output writes at shim interfaces.
Those are distinct logical interfaces, not measured DRAM traffic or bandwidth;
metadata, instruction fetch, graph init/finish and other accesses are excluded
from the local operand totals.

## What still costs time

**Code/assembly-confirmed:** each half is completely dequantized into its8 KiB
scratch before MMUL begins. That work, BFP16 operand conversion, A/C assembly
and per-K128 FP32 loads/stores remain. Down replays the input across its eight
N64 segments. A single16 KiB core activation buffer constrains buffering:
all32 down workers fit in61,952 B of64 KiB, leaving3,584 B. Another16 KiB A
buffer cannot simply be added. The selected MMUL has no accumulator spills;
maximum nested stack use is256 B within the4 KiB reservation.

**Measured host cost:** roughly0.66–0.67 ms for down BO I/O/host overhead
beyond its wait, then1.58–1.65 ms for final output unpack. The direct SwiGLU
output already avoids the Z-to-down input permutation; the remaining conversion
is final Y to row-major before the complementary GPU reduction.

**Proposed next targets:** scatter down output directly to row-major to remove
that final CPU unpack, then profile separate dequant/MMUL event regions before
redesigning conversion reuse or core buffering. Existing evidence does not
rank device dequantization, bank conflicts, conversion and FIFO stalls by time.
No further speedup is claimed here.

[down_breakdown.py](down_breakdown.py) reproduces the schedule/operand totals
and per-call timing summaries from retained evidence; its output is
[down_breakdown.json](down_breakdown.json). Existing numerical validation is
whole-branch/reference validation, not an additional standalone-down accuracy
claim. Original buffers remain unchanged throughout.
