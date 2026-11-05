# On-chip gate/up and SiLU/multiply

**Code-confirmed:** `w4a16_swiglu.py` adds an opt-in eight-column graph that
keeps matching gate/up projection tiles on the NPU through SiLU and
multiplication. It returns only the gated intermediate `Z`. The NPU FFN
branch then launches the existing down projection separately, for **two
completed launches per call**. This is not a single-launch full FFN.

**Measured:** the downloaded [M128/H128/P128 report](../../experiments/ffn_partition/results/swiglu_fusion/exact_smoke.json)
passes 60 checks, and the [M512/H4096/P384,P896 report](../../experiments/ffn_partition/results/swiglu_fusion/exact_m512.json)
passes 120 checks. Packed BF16 `Z` and complete NPU FFN outputs match the
three-launch comparator exactly for random A/B, zero and repeat A. The
reports confirm 60 completed NPU launches across 24 correctness-only branch
calls; CPU-reference checks also pass unchanged tolerances. The
[offline evidence audit](../../experiments/ffn_partition/results/swiglu_fusion/exact_verification.json)
verifies seeded input/weight hashes, source bindings and recorded counters;
it does not independently re-execute the hardware. The main ordinary
partition sweep finds P1152 at 19.657 ms versus its 22.474 ms GPU control
(1.1433×), and 1.86% lower latency than that sweep's best retuned three-launch
point. Independent confirmation finds P1152 at 19.643 ms, 1.1349× its GPU
control and 2.99% lower latency than that repeat's retuned three-launch
minimum. P1024 is within 0.17% in the repeat, so the practical candidate
region is P1024–P1152, not a proven unique optimum. See
[SWIGLU_RESULTS.md](../../experiments/ffn_partition/SWIGLU_RESULTS.md) for
sample ranges, stage timings and the distinction between these comparisons.

## Computation and placement

For `M` token rows, hidden size `H`, and `P` NPU intermediate channels:

```text
G = BF16(X @ Wgate.T)        U = BF16(X @ Wup.T)
Z = BF16(BF16(SiLU(G)) * U)
Y_npu = BF16(Z @ Wdown.T)
```

The native projection kernel remains `w4a16_prefill_reuse.cc`: unsigned
W4A16, group size 128, BF16 products and FP32 accumulation, followed by BF16
storage after the complete K reduction. Pointwise work calls the unchanged
`silu_mul.cc`, including its sigmoid LUT and BF16 rounding boundaries. There
is no CPU activation fallback. The exact-device checker compares the new
packed `Z` against the existing combined gate/up graph followed by the
standalone NPU SiLU/multiply graph, as well as checking CPU-reference error.

All **32 projection workers** remain active: eight columns by four compute
rows. The **16 up workers also perform SiLU/multiply** after their projection.
Physical columns alternate gate and up so each pair shares adjacent tile
memory:

| Physical column | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Projection | Gate | Up | Gate | Up | Gate | Up | Gate | Up |
| Logical column in packed gate-then-up weights | 0 | 4 | 1 | 5 | 2 | 6 | 3 | 7 |
| Partner column | 1 | 0 | 3 | 2 | 5 | 4 | 7 | 6 |
| Runs pointwise and drains `Z` | No | Yes | No | Yes | No | Yes | No | Yes |

Each pair owns the same `P/4` channels and the same token rows. Each compute
row processes `R` native `16×32` output tiles per iteration, where M-tile
reuse `R` is one or two. The default planner uses two where supported. A
worker reduces over all `H/128` K tiles before producing its BF16 result.
At `M512`, reuse two gives four token groups per column; `P896` gives seven
local N tiles per worker. Gate and up are computed on separate workers;
pointwise work on an up worker follows its own projection and the matching
gate tile's readiness.

The host packed weights remain gate first, then up. Only the weight DMA taps
map logical columns to physical columns; the host does not interleave or
repack those weights for this placement. Four output streams, from columns
1/3/5/7, scatter directly into compact `Z[M/16,P/32,512]`.

## FIFO ordering and resource contract

A row's activation stream is multicast to the eight projection columns;
each column's weight stream is multicast across its four compute rows. A
gate worker finishes its full-K accumulation, acquires a gate FIFO object,
stores BF16 gate values, then releases it. Its adjacent up worker finishes
the same K reduction, stores a private BF16 up tile, acquires the gate tile
and output space, executes pointwise work, and releases both FIFO objects.
Every A/W object is released before either worker waits for the gate
handoff. This ordering avoids holding a multicast input while waiting for
another consumer to finish that input stream. The runtime arms final `Z`
drains before supplying A/W and waits for the group to finish.

**Code-confirmed in the pinned compiler:** AIE2 compute tiles expose two
inbound DMA channels. A distant gate-to-up stream would compete with the
existing A and W streams for a third channel. The up core can access its
west neighbor's tile memory, so the one-producer/one-consumer even-to-odd
gate FIFO can use one shared memory pool on the gate tile. Keep this FIFO
free of DMA layout transforms, links, repeat attributes and forced DMA;
those can change its lowering. See the pinned
[memory-affinity implementation](https://github.com/Xilinx/mlir-aie/blob/7e00b57955e108fe9d8e9419f5828a0c7e650858/lib/Dialect/AIE/IR/AIETargetModel.cpp)
and [ObjectFifo lowering](https://github.com/Xilinx/mlir-aie/blob/7e00b57955e108fe9d8e9419f5828a0c7e650858/lib/Dialect/AIE/Transforms/AIEObjectFifoStatefulTransform.cpp).

The planner reports conservative raw per-tile bounds of **39,104 bytes** for
gate and **49,344 bytes** for up at reuse two. These include a 2 KiB stack,
projection FIFOs/scratch, the up BF16 scratch, output FIFO and unchanged
4 KiB sigmoid LUT. The up bound deliberately counts the shared gate pool on
up as well; the adjacent lowering normally allocates it on gate. These are
not two copies of gate data and are not compiler allocation measurements.
Alignment, linker data, spills and bank placement require compiled-artifact
evidence. The graph restricts reuse to one or two, rather than assuming
reuse four fits.

**Compiled-artifact confirmed at M128/H128/P128, reuse two:** the
[retained topology and linker audit](../../experiments/ffn_partition/results/swiglu_fusion/compiler_audit/README.md)
passes 661 static checks across all 32 cores. Each pair has one two-deep
4 KiB gate pool on the even producer tile, accessed directly by the odd
consumer through west-neighbor symbols. There are no gate DMA descriptors
or compute-to-compute stream routes. Each core receives A on S2MM0 and W on
S2MM1; only odd cores drain Z on MM2S0. Its linked data SRAM is:

| Per-core static allocation | Gate | Up + pointwise |
| --- | ---: | ---: |
| Graph buffers | 37,056 B | 39,104 B |
| Reserved stack | 2,048 B | 2,048 B |
| Sigmoid LUT | 0 B | 4,096 B |
| Total | **39,104 B** | **45,248 B** |
| Remaining in 64 KiB | 26,432 B | 20,288 B |

These figures are static allocation plus reserved stack, not runtime stack
high-water or bank-contention measurements. The exact audit covers this
small compiled shape only. It records the six source hashes, binary hashes,
lowered MLIR, linker and ELF hashes; it does not infer other shapes' success.

## ABI and host staging

After the standard opcode/instruction arguments, the graph takes:

| BO index | Argument | Host type and elements | Native layout |
| ---: | --- | --- | --- |
| 0 | Activation | `uint16`, `M*H` BF16 bits | `A[M/16,H/128,2048]` |
| 1 | Combined weight | `uint8`, `(2P/32)*(H/128)*2144` | `W[2P/32,H/128,2144]`, gate then up |
| 2 | Gated output | `uint16`, `M*P` BF16 bits | `Z[M/16,P/32,512]` |

There is one output BO (`output_count=1`, `output_order=[silu_mul]`). Gate and
up have no host output BOs in this graph. The experiment's reusable runner
uploads combined gate/up weights once and down weights once. The three
logical weight matrices and their total packed bytes remain unchanged.

`NPUBranch(..., fuse_swiglu=True)` implies `fuse_gate_up=True`. Its launch
sequence is `swiglu → down`. It reads `Z` back, performs the existing
**CPU down-input layout conversion**, writes that converted activation to
the down BO, then reads the down partial. Consequently the graph retains
gate/up on-chip only through pointwise work; `Z` is still host-staged before
down. GPU/XRT zero-copy and full-FFN on-chip residency are not implemented.

Estimated explicit per-call BO read/write payload, excluding fixed weights:

| Branch | Payload bytes |
| --- | ---: |
| Separate gate/up, separate pointwise | `6*M*H + 12*M*P` |
| Combined gate/up, separate pointwise | `4*M*H + 12*M*P` |
| On-chip gate/up + pointwise | **`4*M*H + 4*M*P`** |

The last row comprises the input write and down-output read (`4MH`) plus
the `Z` read and down-input write (`4MP`). At `M512/H4096/P896` this is
**9.75 MiB**, versus 13.25 MiB for combined gate/up with separate pointwise.
This estimates host BO payload, not physical DRAM traffic or measured
bandwidth. It excludes CPU layout copies, GPU staging, instruction reads,
DMA replay, caches and fixed-weight upload.

## Build, limits and provenance

The graph/planner require eight columns, four compute rows, M/H multiples
of 128, `128<=M<=4096`, `128<=H<=16384`, and `128<=P<=8192` divisible by 128.
These are accepted geometry bounds, not a statement that every shape has
passed hardware validation. Use the pinned MLIR-AIE/IRON environment from
[the experiment runbook](../../experiments/ffn_partition/README.md), revision
`7e00b57955e108fe9d8e9419f5828a0c7e650858`.

Example build from `npu/ffn`, with `IRON_PYTHON` set to that interpreter:

```bash
mkdir -p build_swiglu
"$IRON_PYTHON" w4a16_swiglu.py -M 512 -K 4096 -P 896 -co 8 \
  --max-reuse 2 \
  --xclbin-path build_swiglu/final.xclbin \
  --insts-path build_swiglu/insts.bin \
  --pdi-path build_swiglu/final.pdi
```

The artifact manifest identifies `kind=w4a16_swiglu_bf16`,
`design=array8_swiglu`, `n=2P`, `channels=P`, 32 projection workers and
16 pointwise workers. It records physical-to-logical column mapping, output
columns, arithmetic/planner source hashes, the compiler revision, and
xclbin/instruction SHA-256 hashes. The experiment build contract also hashes
the graph source itself and uses a source-derived artifact directory.

Earlier gate/up measurements predate the new runtime flags and remain bound
to their original sources. The verified [26-file source archive](../../experiments/ffn_partition/results/swiglu_fusion/baseline_sources.tar.gz)
and [hash manifest](../../experiments/ffn_partition/results/swiglu_fusion/baseline_source_manifest.json)
preserve those sources; their hashes match the original main sweep manifest.
Do not relabel earlier gate/up results as SwiGLU measurements.

The profiler reports one composite `swiglu` host interval and one `down`
interval. It cannot infer separate internal gate, up, SiLU or multiply
compute times. Host submission, completion wait and explicit BO I/O remain
distinct quantities; CPU and HIP clocks are not calibrated to each other.
Use separate ordinary complete-FFN runs to establish acceleration.

## Proposed next step: the boundary before down

**Proposed, not implemented:** first investigate emitting `Z` in the down
kernel's required activation layout while preserving the two dispatches.
A single-launch full FFN needs a broader dataflow change; replacing the
current host boundary with one FIFO is insufficient.

**Code-confirmed constraints:**

- Native `Z` is `C[Mb,P/32,4,4,4,8]`, whereas down consumes
  `A[Mb,P/128,4,16,4,8]`. The current
  [`packed_output_to_activation`](../../experiments/ffn_partition/contract.py)
  groups four neighboring N32 tiles into each K128 tile and moves the
  four-N-tile axis inside the row-microtile axis. At P896, each up column
  owns seven N32 tiles, so some K128 groups cross producer pairs. A local
  FIFO join alone does not perform the necessary assembly and permutation.
- All 32 compute cores are already assigned to projections. A single-launch
  graph must reuse them in phases or change the core allocation between
  projection, pointwise and down work.
- At H4096, the current down schedule has 16 local N32 output tiles per
  core and replays its complete input for each output tile. A one-pass `Z`
  stream therefore needs retention/replay or a different accumulation
  schedule. Keeping all 32 native FP32 accumulator tiles for reuse two and
  those 16 outputs would consume 64 KiB per core before any other storage.
  Full `Z` for one 32-row group at P896 is 57,344 bytes; it cannot simply be
  appended to the current up-core allocation.
- Preserving the ordered complete K128 reduction requires gathering,
  broadcasting and replaying the needed `Z`, but does not require an
  additional NPU sum. Assigning down partials to intermediate-channel
  owners instead would introduce an internal partial-output reduction and
  change summation order. The final GPU-plus-NPU FFN boundary sum remains
  necessary in either case.

A bounded first experiment would use segmented output DMA scatter to place
each produced `Z` element directly in down-A order. Start at P512, where
each pair owns an aligned group of four N32 tiles; then handle segment
boundaries explicitly at P768/P896. Check every destination address and
compare output BF16 bits exactly against `packed_output_to_activation`
before running down. This would isolate removal of the CPU permutation
without simultaneously changing the projection or reduction schedule.

After that layout is validated, separately test whether the two XRT graphs
can hand off a shared BO with correct lifetime and coherency, eliminating
the host `Z` read/write pair. That capability is not implied by shared
system DRAM or by direct output scatter. Neither the segmented-DMA variant
nor shared-BO handoff has been built or measured here, and no speedup is
predicted from this assessment.
