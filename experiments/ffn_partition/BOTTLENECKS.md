# Prefill FFN bottlenecks and the two teammate PRs

**Update:** the eight-column/four-row NPU redesign is now implemented. See
[the new measurements and remaining bottlenecks](ARRAY8_RESULTS.md). The analysis
below preserves the original one-row graph and PR review as historical evidence.

Reviewed 2026-10-18. **The current NPU projection path is the first optimization
target.** Small offloads remove too little GPU work to cover the added costs;
larger offloads make the NPU slower than the complete GPU FFN. This conclusion
uses the existing HX370 measurements, not a new run of the teammate's code.

## PR stack and evidence boundaries

Both PRs are open and have been fetched locally:

| PR | Pinned head | Role |
| --- | --- | --- |
| [#1: GPU FFN](https://github.com/glassescrab/HeteroMega/pull/1) | `1b0023bbe09616f720665e983634ddd50784137a` | GPU channel-slice implementation, fused pointwise operation, model hook, tests and profiling tools |
| [#2: evaluation](https://github.com/glassescrab/HeteroMega/pull/2) | `71c95d83ec09bd2c1da08edeec968013b95acf47` | Prefill runner and evaluation plan; its head includes PR #1 |

Git ancestry confirms PR #1 is an ancestor of PR #2. The evaluation-only diff
contains six files. Integration order is #1 then #2; do not independently apply
both full diffs. Local refs are `origin/pr/1` and `origin/pr/2`. No PR was merged
or published during this analysis. The earlier check of ordinary remote
branches missed the PR refs; the teammate code is now identified.

**Measured here:** the [existing ten-configuration experiment](RESULTS.md),
using original HeteroMosaic GPU kernels and our host-staged MLIR-AIE NPU branch.
**Documented by the teammate, not rerun here:** PR #1's hardware results.
**Code-confirmed:** the contracts and graph structure described below.
**Calculated:** traffic requests and proportional-work examples, not hardware
counters. PR #2's five CPU tests were rerun and all passed. No new hardware
latency, model accuracy, or end-to-end acceleration is claimed by this review.

## What the measured critical path says

All rows below use M512/H4096/I14336. P is the number of NPU channels.
Times are medians in milliseconds. Projection wait is formed by summing the
three host launch-and-wait intervals within each sample, then taking a median.

| Max columns | P | Full GPU FFN | NPU branch | Projection launch/wait sum | Complete concurrent FFN |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 128 | 27.178 | 16.340 | 11.818 | 27.192 |
| 4 | 512 | 27.441 | 42.346 | 38.047 | 44.424 |
| 4 | 2048 | 27.154 | 148.438 | 142.320 | 151.399 |
| 8 | 128 | 27.096 | 14.627 | 10.227 | 27.358 |
| 8 | 256 | 27.309 | 16.768 | 12.667 | 27.619 |
| 8 | 512 | 27.359 | 26.039 | 21.348 | 28.048 |
| 8 | 1024 | 27.455 | 43.686 | 38.877 | 45.687 |

At four columns/P2048, projection waits occupy **95.9% of NPU branch time**
(median of per-sample shares). Explicit host BO work outside dispatch/wait is
2.145 ms, the three layout conversions total 2.405 ms, and SiLU dispatch/wait
is 1.558 ms. These separately computed medians need not sum exactly.
Removing only those external staging/layout costs would leave approximately
142 ms of projection launch/wait intervals against a 27 ms GPU FFN. Improving
intermediate residency is useful, but is not sufficient at this allocation.

The waits include NPU DMA, scheduling, and host/runtime overhead. They do not
identify pure matrix arithmetic time or prove a compute or bandwidth limit.
Four separate XRT contexts are constructed for gate, up, SiLU and down; their
context-switch costs have not been isolated.

The small allocations have the opposite problem. P128 is only 0.893% of the
intermediate channels. Under an optimistic model in which GPU time scales
linearly with channels and offload has zero cost, it saves only about 0.24 ms
from a 27 ms FFN. P512 removes 3.571% and saves about 0.98 ms. The corresponding
model-only speedups are 1.009x and 1.037x. These are not measured hardware bounds:
real GPU kernels can scale nonlinearly with shape.

At eight columns/P128, the NPU branch takes 14.627 ms, but the recorded final
output-stage interval is 12.030 ms because it also waits for the GPU. That
interval combines CPU output copying, H2D transfer, event waits, reduction and
host synchronization; calling all 12 ms a copy or reduction cost would be wrong.

Increasing four to eight columns at P512 reduces NPU branch time
**42.346 to 26.039 ms**, and concurrent FFN time **44.424 to 28.048 ms**.
That is a useful improvement, but still loses to its 27.359 ms GPU control.
At P128, gate/up use only four columns even when the maximum is eight because
there are only four N32 tiles. These comparisons are from separate runs and
retain the shared-host variability described in [RESULTS.md](RESULTS.md).

## Why the current NPU graph is expensive

The source establishes the following repeated work; its individual contribution
to measured latency still needs device tracing:

1. **Only one arithmetic worker per column.**
   [Graph placement](../../npu/ffn/w4a16_prefill.py#L95) puts each worker on
   `Tile(i, 2)`. Four/eight columns mean four/eight GEMM workers; the graph does
   not spread work over the other compute rows.
2. **Limited weight and activation reuse.** The loop order is
   `[M16, N32, K128]`. [DMA taps](../../npu/ffn/w4a16_prefill.py#L103) reread
   each packed weight tile for every M16 block and repeat A for each N32
   output tile. M512 therefore streams each weight tile 32 times. Fixed weight
   BO uploads happen once, but internal DMA reads do not.
3. **Repeated dequantization and accumulator traffic.**
   [The C++ kernel](../../npu/ffn/w4a16_prefill.cc#L102) dequantizes 4,096
   weights into an 8 KiB BF16 scratch before every tile accumulation. At M512
   this repeats 32 times for each unique weight tile. Each K128 call also
   loads/stores a 512-element FP32 accumulator, about 4 KiB of logical local
   accesses. FP32 accumulation persists across K in local memory, but is not
   held in registers across all K calls.
4. **Scheduling and sublayer boundaries.** FIFOs have depth two, while the
   [runtime sequence](../../npu/ffn/w4a16_prefill.py#L113) finishes a task group
   for each M16 block. The [FFN adapter](npu_backend.py#L300) then serially
   completes four launches with host intermediates between them. Compiler
   initiation intervals and FIFO stalls have not been measured.

For one projection, let `T = (M/16)(K/128)(N/32)`. The current graph requests
`4096*T` bytes of A, `2144*T` bytes of W, and `2*M*N` output bytes. These are
logical graph payloads, not measured external DRAM traffic.

For M512/H4096/P512, the three projections together have only **3.141 MiB**
of unique packed weights, but request **100.5 MiB** of weight payload and
**192 MiB** of activation payload, plus 5 MiB of projection outputs. Separately,
host BO writes/reads total 15 MiB, before layout copies and GPU transfers.
At P2048 the unique weights are 12.563 MiB, with 402 MiB of repeated weight
payload and 768 MiB of activation payload. These quantities must not be added
and labeled DRAM-counter readings: caches, the memory hierarchy and repeated
software copies determine actual physical traffic.

## What the GPU PR changes, and what it does not establish

PR #1 provides a useful reusable GPU branch: one merged gate/up projection,
one fused SiLU/multiply kernel, and down projection on one stream. Its
[reported prefill ablation](https://github.com/glassescrab/HeteroMega/blob/1b0023bbe09616f720665e983634ddd50784137a/kernels/gpu/README.md#L70-L93)
shows approximately 2% benefit from pointwise fusion and little benefit from
merging gate/up. Its larger decode improvements are outside the present scope.
The reported full-model prefill change, 1.801 to 1.781 seconds, is about 1.1%
and is an all-GPU comparison, not heterogeneous FFN acceleration.

Its static ISA analysis reports substantially more unpack/dequantization and
LDS instructions than WMMA instructions. That makes dequantization and fragment
layout sensible GPU optimization targets. Hardware counters were unavailable,
so the report's strong compute-bound wording is not independently established.
Likewise, GPU+CPU bandwidth contention does not establish GPU+NPU contention.

Do not substitute its 20.222 ms GPU-event FFN number for our roughly 27 ms
wall-time baseline: its timing enqueues iterations back to back and records
clocks, while ours measures separate complete invocations with host boundaries.

There is also a fairness issue to repair before reusing its ablation:
[weight setup](https://github.com/glassescrab/HeteroMega/blob/1b0023bbe09616f720665e983634ddd50784137a/kernels/gpu/bench/bench_ffn_ablation.cpp#L80-L82)
independently generates separate gate/up, merged gate/up and dense weights.
It does not use identical numerical weights across all variants. Our canonical
shared-weight harness should remain the controlled comparison; dense BF16 is
an implementation diagnostic, not the final W4A16 baseline.

## Contract fixes before using both PRs in the experiment

- **BF16 rounding:** PR #1's [fused activation](https://github.com/glassescrab/HeteroMega/blob/1b0023bbe09616f720665e983634ddd50784137a/kernels/gpu/src/silu_mul.cu#L15-L29)
  rounds only the final product. Our NPU path rounds SiLU before multiplying.
  Preserve the original staged reference and introduce an explicit PR-fused
  reference, or align the new kernels' rounding deliberately and revalidate.
  A passing tolerance does not make these semantics identical.
- **Ownership and packing:** `GpuFfnModel` uses a GPU prefix, whereas our
  experiment uses an NPU prefix. The lower-level `pack_ffn_slice` supports
  arbitrary aligned slices, so GPU `[P,I)` can remain intact initially.
  GPU 4352-byte tiles and our NPU 2144-byte tiles are different; shared DRAM
  does not make the packed buffers interchangeable or eliminate these copies.
- **FFN boundary:** PR #1's residual helper adds residual plus both partials.
  Our current microbenchmark excludes residual. Retain the existing two-partial
  sum for the initial adapter and add the residual once in model integration.
- **Complete model path:** PR #1's partial-channel environment switch omits the
  NPU output. PR #2 correctly clears it for existing controls. Turning it on
  alone is not a complete heterogeneous implementation.
- **Strict prefill scope:** [PR #2's runner](https://github.com/glassescrab/HeteroMega/blob/71c95d83ec09bd2c1da08edeec968013b95acf47/kernels/gpu/tools/run_model_ffn.py#L174-L186)
  still warms up with eight generated tokens and pairs each `generate(1)`
  timing with a default `generate(64)` call. A prefill-only mode must use
  one-token warmups and measured calls and suppress decode metrics; setting
  `--new-tokens 1` alone still leaves the warmup decode. A first-token comparison
  is a regression check, not numerical validation.
- **Fair model baseline:** keep attention, chunking and inflight scheduling
  identical when testing FFN offload. Compare original GPU FFN, PR #1 all-GPU
  FFN, and PR #1+NPU within that same model schedule. Keep the original tuned
  HeteroMosaic heterogeneous model as an additional system baseline. Changing
  the whole model from GPU to heterogeneous does not isolate FFN offload.

## Recommended next implementation and measurements

1. Add PR #1 as a separately selected GPU backend in the existing canonical
   harness. Keep original GPU and PR all-GPU controls; run matched weights,
   input, BF16 contract and timing boundaries before attributing any gain to
   GPU–NPU cooperation. Integrate PR #2's evaluation stack in dependency order
   and adapt its runner for strict prefill.
2. Instrument one representative NPU projection. Separate dequantization and
   MAC markers, inspect generated scheduling/II, and trace DMA/FIFO stalls.
   Compare standalone versus concurrent GPU load. Existing host waits alone
   cannot rank arithmetic, DMA and runtime overhead.
3. Improve projection reuse and parallelism: use additional compute rows,
   process several M blocks per reused weight tile, and consider broadcasting
   A across N workers. Check local-memory capacity and preserve FP32 K
   accumulation. Evaluate larger M tiles/multiple accumulators before attempting
   a full FFN graph fusion; expected gains are hypotheses until measured.
4. Reduce remaining boundary costs after projection improvement: preallocate
   staging, reuse compatible NPU intermediate BOs, and then investigate an
   NPU-resident gate/up/SiLU/down graph. Measure actual zero-copy feasibility.
   Add GPU events around the branch, copies and final sum without per-stage
   synchronization in normal runs. Use separate diagnostic runs for traces.
5. Repeat complete-FFN ratios, then attention-overlap and complete prefill.
   At current speed, fitting ever-smaller offloads leaves very little useful
   headroom. No Max+395 result or whole-model heterogeneous speedup follows
   from the current HX370 FFN data.

## Reproduce the numerical analysis

The [derived JSON](results/bottleneck_analysis.json) preserves all ten rows,
raw-report hashes, host intervals, payload formulas and their limitations.
It is regenerated without an accelerator:

```bash
python experiments/ffn_partition/analyze_bottleneck.py \
  --output experiments/ffn_partition/results/bottleneck_analysis.json
```

All source measurements remain in the three raw JSONs linked from
[RESULTS.md](RESULTS.md); this analysis neither filters their samples nor
relabels them as measurements of PR #1.
