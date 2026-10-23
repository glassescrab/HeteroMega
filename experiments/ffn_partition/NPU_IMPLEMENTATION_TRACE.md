# NPU implementation trace — 2026-10-22

## Conclusion and evidence boundary

**Measured:** at M512/H4096/I14336/P1792, most NPU branch time is inside the
two projection-containing graph executions, followed by CPU layouts and BO
staging. Submission itself is small. The fully staged NPU result is the last
dependency in 13/15 diagnostic samples, although the two branches are close
to balanced. Increasing the NPU allocation makes that tail worse.

**Code-confirmed:** the BFP16 adaptation improved the arithmetic microkernel
but retained the small M16/K128/N32 graph and external layout. The graph
replays activations for every local N tile, rereads weights over four token
waves, dequantizes the same weights on multiple workers/waves, and serializes
dequantization with matrix computation on each worker. All 32 compute tiles
are assigned work; assigned workers do not imply sustained compute occupancy.

**Compiled-binary confirmed:** representative gate, up and down worker ELFs
each contain **32 calls to the software `__floatunsisf` helper inside every
dequantization**. With the recorded schedule, this implies **2,752,512 helper
calls per FFN**. This is a specific, avoidable conversion cost and the first
small kernel experiment to try; its share of runtime is not yet measured.

**Not established:** whether AIE compute, dequantization, DMA, local-memory
bandwidth, register spills, or FIFO stalls dominate the execution interval.
The current host probes cannot answer that. This investigation reanalyzes
the saved hardware runs, traces source and disassembles existing binaries;
it does not present a new
device-cycle trace or a newly measured optimization.

Platform remains HX370/Radeon 890M, NPU power `default`. The performance-mode
request was denied by the host. Results concern an isolated synthetic FFN,
not full-model prefill or native heterogeneous HeteroMosaic.

## Call path and actual persistence

```text
GPU input X ── GPU branch: gate → up → SiLU×up → down ───────────────┐
     │                                                            │
     └─ HIP D2H → CPU input packing → XRT input BO write/sync       │
            → NPU graph 1: gate/up → adjacent-tile SiLU×up          │
            → Z BO sync/read → CPU Z-to-A layout → down BO write   │
            → NPU graph 2: down → Y BO sync/read → CPU unpack      │
            → pinned host copy → HIP H2D ──────────────────────────┤
                                                               GPU add
```

[`TimedFFN.run`](run.py#L61) queues GPU work before the host enters the NPU
path; blocking XRT waits therefore do not serialize GPU execution.
[`NPUBranch.run`](npu_backend.py#L445) executes the two NPU graphs
sequentially. Gate/up intermediates stay on-chip through the pointwise
operation. Z does not stay on-chip through down. Its full matrix is read
back, permuted, then written into a separate runner's BO.

Fixed weights are packed and uploaded once in the constructor
([source](npu_backend.py#L393)). They are still streamed from their BO into
the array repeatedly during inference. Persistent host BOs and persistent
logical channel ownership do not mean persistent on-chip weights.

## Measured time attribution

The table uses **means of disjoint per-sample components** from all 15
P1792 diagnostic samples. It accounts for the outer NPU call, not the full
concurrent FFN. Ordinary median FFN latency remains 18.754 ms. Summing
independent medians or adding overlapping GPU/NPU intervals is invalid.

| Outer NPU call component | Mean ms | Share |
| --- | ---: | ---: |
| SwiGLU host wait | 7.911 | 44.4% |
| Down host wait | 5.339 | 29.9% |
| CPU input/Z/output layout conversions | 2.372 | 13.3% |
| BO I/O and invoke-wrapper residual outside dispatch | 1.553 | 8.7% |
| XRT submission calls | 0.237 | 1.3% |
| Call-entry checks/bookkeeping outside inner timer | 0.374 | 2.1% |
| Other measured wrapper gaps | 0.045 | 0.3% |
| **Outer NPU call** | **17.831** | **100%** |

The 0.374 ms category includes the finite-input scan before the inner timer;
it is not an isolated scan measurement. The 1.553 ms category includes BO
write/read/sync, array copying and Python wrapper costs; it is not pure DMA.
[`dispatch_wait`](npu_backend.py#L316) includes submission plus completion
wait; the [diagnostic wrapper](profile_timeline.py#L71) separates those host
intervals. A wait includes device computation, DMA, stalls and runtime work.

Individual diagnostic medians are 0.966 ms input packing, 0.136 ms Z layout,
1.355 ms output unpack, and a 0.744 ms interval from SwiGLU wait completion
to down submission. HIP input/output copies take 0.244/0.175 ms. The GPU
reduction itself takes 0.155 ms after both dependencies are ready.

At P1792 the BO payload is 11.5 MiB per invocation: X write 4 MiB, Z read
and write 1.75 MiB each, Y read 4 MiB. HIP transfers add another 8 MiB.
These counts exclude CPU layout copies, instruction reads and array DMA.

### Which branch sets the boundary?

Both GPU-branch completion and NPU-output H2D completion are recorded with
HIP events on the same GPU clock
([source](profile_timeline.py#L203)). Their difference is meaningful even
though raw host and GPU clock origins are not calibrated.

| Diagnostic | Median NPU-result-ready minus GPU-branch-ready | NPU later |
| --- | ---: | ---: |
| BFP16 P1792 | +0.423 ms | 13/15 samples |
| BFP16 P2048 | +1.693 ms | 9/10 samples |
| BF16 P2048 | +7.058 ms | 10/10 samples |

At P1792 reduction starts only about 0.010 ms after the later dependency.
Consequently the small reduction is not the main tail. Optimizing the
NPU alone at fixed P1792 eventually leaves the GPU branch as the limit;
after substantial NPU improvements the partition should be retuned.

The ordinary P1792 confirmation's inner NPU median is 17.039 ms in the
serial schedule and 17.192 ms concurrent, about 0.9% higher. Complete FFN
latency falls from 37.894 to 18.754 ms with overlap. These data do not show
large GPU-induced NPU slowdown; they do not rule out internal memory stalls
or establish behavior with concurrent attention.

## Array schedule: where reuse is lost

At P1792, both graphs use eight columns × four rows, reuse two M16 tiles per
worker, and four sequential M128 waves. SwiGLU assigns even columns to gate
and odd columns to matching up plus pointwise; down uses all 32 workers.

The [activation tap](../../npu/ffn/prefill_schedule.py#L152) has an outer
`local_nb` dimension with **zero stride**, replaying the same activation
block for each local output-channel tile. Columns share the row stream by
multicast, but that does not remove this replay over time. The weight tap
is issued again for each wave.

| Source-derived quantity | Fused gate/up + SwiGLU | Down |
| --- | ---: | ---: |
| Local N32 tiles per worker | 14 | 16 |
| K128 groups per output tile | 32 | 14 |
| Unique activation bytes | 4 MiB | 1.75 MiB |
| Logical activation shim reads | **56 MiB (14×)** | **28 MiB (16×)** |
| Unique packed weights | 7.328125 MiB | 3.6640625 MiB |
| Logical weight shim reads | **29.3125 MiB (4×)** | **14.65625 MiB (4×)** |
| Worker dequantize/MAC calls | 57,344 | 28,672 |

The graphs request **127.96875 MiB of logical input DMA** for 16.7421875 MiB
of unique activation/weight data across the two graphs. These are logical
tap counts, not measured physical DRAM traffic, bandwidth or cache misses.

Each [SwiGLU wave](../../npu/ffn/w4a16_swiglu.py#L185) and
[down wave](../../npu/ffn/w4a16_prefill_reuse.py#L138) ends with
`task_group.finish()` awaiting that wave's output drains. The next wave's
feeds are scheduled afterwards. Double buffering operates within a wave;
cross-wave feed overlap is absent. The resulting bubble duration is unknown.

## Worker kernel: BFP16 is only part of the work

For each K128 step, the
[grouped kernel](../../npu/ffn/w4a16_prefill_bfp16.cc#L229) does:

1. Convert 32 zero points using a scalar loop.
2. Unpack and scale 4,096 W4 weights into an 8 KiB BF16 scratch buffer.
3. Run BFP16-backed 8×8×8 MMULs over two M16 activation tiles.
4. Read/write FP32 C partials, then return to the graph's FIFO loop.

Dequantization precedes MAC on the same worker. The current kernel does not
overlap these two phases. Across one FFN invocation there are **86,016** such
calls and **2,752,512 scalar zero-point conversions**. Reuse two is already
included in the four-wave schedule and must not divide these counts again.

### Actual compiled zero-point conversion

Through the notebook browser, the existing P1792 gate `(0,2)`, up `(1,2)`
and down `(0,2)` ELFs were disassembled with the prepared LLVM-AIE tool.
Each dequantize function contains 32 direct calls to `__floatunsisf`.
For example, the gate ELF has the helper at `0x1220` and calls at `0x3e4`,
`0x438`, `0x472`, `0x4a8`, and the remaining zero-point conversion sites.
The grouped accumulator calls that dequantize function once per K128 tile.

The source expression `bfloat16(128 + unsigned(zero_bytes[n]))` therefore
does substantially more than a cheap metadata load. The zero points are
four-bit unsigned values. For z in 0..15, BF16(128+z) is exactly the bit
pattern `0x4300 | z`; using validated bit construction or pre-encoded
metadata could remove the software numeric conversions. This is a proposed
change, not an implemented fix or a measured speedup. The previous incorrect
vector metadata path is why the conservative scalar code existed; validate
all zero values, scales, layouts and repeated execution when changing it.

The [compiler audit](results/bfp16_20261022/compiler_trace/audit.json) records
ELF/source/xclbin hashes and call examples. Downloaded disassembly is retained
alongside it. The remote xclbin files were rehashed and match both their
manifests and the saved P1792 profile. This ties the inspection to the measured
build, although it is not a runtime call/cycle counter. Stack accesses also
appear in the assembly; they alone do not prove spill-bound execution.

At the C++ semantic level, those calls write 672 MiB of dequant scratch,
read 1,344 MiB of that scratch, and read/write 672 MiB of FP32 partials across
the array. These are **on-chip semantic accesses**, not external DRAM bytes
or a claim that the compiler emits exactly those memory transactions.
The workload performs 22,020,096 logical 8×8×8 MMUL calls, 22.549 GFLOP
counting a multiply-add as two operations.

The [4×8-to-8×8 bridge](../../npu/ffn/w4a16_prefill_bfp16.cc#L123) also
assembles A/C vectors and splits C stores. The upstream M64/N64 scheduling
and native 8×8 layout were not adopted; this adaptation retained the existing
ABI and FP32 K-group boundaries. The fixed-P2048 experiment nevertheless
reduced SwiGLU wait by 32.5% and down wait by 22.0%, showing that changing
the projection implementation materially affects the execution interval.

Pointwise work runs on 16 up workers after their projections and gate
handoff. It can delay the slowest consumer of a multicast stream. The
current evidence does not isolate its contribution, FIFO wait cycles or
bank conflicts. Existing `event0/event1` bracket dequantization and MAC
together; they do not separate those costs or capture every FIFO wait.

## Priorities for the next optimization

These are **proposed experiments**, not measured speedups:

1. **Remove the software metadata conversions as a controlled ablation.**
   Replace the 32 integer-to-float helper calls with exact, validated BF16
   bit construction, then inspect assembly and compare unchanged P1792/P2048
   numerical checks and latency. This is narrower than rewriting the graph.
2. **Measure the worker phases.** Add separate device-cycle regions for
   dequantization, MAC, pointwise and FIFO acquisition, plus DMA/lock-stall
   counters. Inspect generated assembly for conversion cost and spills.
   Preserve an uninstrumented latency control: trace can perturb timing.
3. **Improve tile reuse and wave scheduling.** Reuse A across multiple N
   tiles, retain dequantized W across more M rows, and pipeline successive
   waves. Benchmark each independently. This targets repeated work inside
   the 74% host-wait portion, without assuming it is all memory bound.
4. **Remove host layout/staging where feasible.** Emit down-compatible Z,
   reuse/import BOs with verified synchronization, and emit output in the
   GPU consumer's layout. Z's permutation alone is only 0.136 ms; the
   larger 0.966/1.355 ms input/output layouts deserve attention too.

Do not simply change `max_reuse` to four. The current fused graph rejects
it. Its [raw memory estimator](../../npu/ffn/prefill_swiglu_schedule.py#L46)
gives BFP16 reuse-two upper bounds of 41,152 bytes per gate tile and 51,392
per up tile. The analogous reuse-four bounds are 65,728/82,112 bytes versus
65,536-byte local capacity. Shared gate pools are conservatively counted on
both tiles, and these bounds exclude alignment/spills. Larger reuse needs
a redesigned buffer lifetime/layout, not just larger FIFOs. Streaming
smaller A objects while retaining W/C is one candidate; optional BF16
partials would require separately recorded numerical and timing checks.

Launch-call tuning, eliminating the small GPU sum, or claiming bandwidth
saturation from host waits should not be the first response to this trace.

## Reproduce

Raw evidence is in the archive linked from [BFP16_RESULTS.md](BFP16_RESULTS.md).
After extracting the raw evidence and restoring the initial runtime plus final
harness exactly as described in its reproduction section, run in the same shell:

```bash
python experiments/ffn_partition/results/bfp16_20261022/trace_implementation.py \
  --source-root "$bfp16_source_root" \
  --output-dir /tmp/heteromega-bfp16-reproduced
```

The CPU-only script imports schedule helpers and hashes source files from the
explicitly selected source root. It checks every recorded source hash and full
plan, rejects mismatches and never falls back to the current checkout. It also
checks accounting identities and saved disassembly provenance. The command
writes `trace_summary.json` and `npu_cost_breakdown.png` to the temporary output
directory, preserving the recorded [derived JSON](results/bfp16_20261022/plots/trace_summary.json)
and [cost figure](results/bfp16_20261022/plots/npu_cost_breakdown.png).
No new kernel, hardware run, commit, push or PR is part of this analysis.
