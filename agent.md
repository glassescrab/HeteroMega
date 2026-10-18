# HeteroMega agent reference plan

Saved 2026-10-12 at the user's request. The user-provided plan below is preserved
verbatim. It is the current planning reference for the narrowed FFN-prefill
study; attention-head partitioning and decode optimization are deferred.
A later explicit user instruction or final proposal can revise this scope.

Read `AGENTS.md` for repository working rules, `docs/project-plan.md` for the
baseline code/build map, and `docs/progress.md` for actual progress. The plan's
future work instructions do not mean those steps have been executed or that
saving this file authorizes implementation in the current documentation task.

## Review recommendations (assistant suggestions, not user requirements)

These refinements were proposed during review; retain them for consideration
without treating them as independently approved scope changes:

1. Time-box an early NPU SiLU/gating and buffer-layout feasibility check.
   Distinguish a full NPU-local branch from one using GPU elementwise fallback.
2. Where meaningful, isolate persistence with identical channel splits, kernels,
   weights, and chunk schedules; separately compare against optimized original
   HeteroMosaic. Document unavoidable differences between the controlled paths.
3. Treat persistent token-row partitioning as an important challenger: it avoids
   the partial-output sum required by channel partitioning. Do not turn it into
   a second large implementation project without evidence that this is needed.
4. Validate correctness at every step: reference algebra, packed slices, device
   execution, concurrency, then model integration. Preserve quantization metadata
   and test repeated buffer reuse with alternating inputs.
5. Define FFN timing boundaries independently of the existing G2 stage. Separate
   host readiness/queue/submit/wait intervals from actual device execution;
   reproduce scheduler release times in representative overlap experiments.
6. Keep allocation selection as a stretch goal unless measured winners change
   across workloads by more than measurement variability.

Suggested first milestone: one representative FFN shape, one valid unequal
split, a correctness reference, an NPU capability/layout assessment, and
measurements of the unchanged baseline when target hardware is available.
No runtime feasibility, correctness, or speedup is established yet.

## User-provided plan

You are helping develop **HeteroMega**, a semester research project built on HeteroMosaic.

Repository: https://github.com/glassescrab/HeteroMega  
Upstream: https://github.com/UIUC-ChenLab/heteroMosaic

Work in the existing checkout. Read repository instructions and inspect its current state before making changes. Preserve existing work and use the repository’s established build and development practices.

## 1. Research objective

Investigate whether **preserving tensor partitions across an entire feed-forward network (FFN) sublayer** improves heterogeneous GPU–NPU LLM prefill.

HeteroMosaic already supports heterogeneous operation allocation, GEMM partitioning, and causal micro-batching that overlaps work from different prompt chunks. Our extension must account for that existing scheduling behavior.

The central research question is:

> When do persistent FFN partitions reduce execution costs enough to improve end-to-end prefill, and when does GPU participation in the FFN interfere with concurrently executing attention?

Do not assume the proposed implementation will be faster. Establish the baseline behavior and bottleneck through code inspection and measurements.

Initial scope:
- Dense, gated FFNs supported by the existing runtime.
- Prefill as the primary target.
- One supported model and one available AMD platform initially.
- Attention remains on its existing execution path.

Defer attention-head partitioning, speculative decoding, and broader model support until the FFN study is working.

## 2. Proposed FFN computation

For a gated FFN:

U = X W_up  
V = X W_gate  
Z = SiLU(V) ⊙ U  
Y = Z W_down

Partition the intermediate feature dimension into GPU and NPU portions.

For each device i:

Z_i = SiLU(X W_gate,i) ⊙ (X W_up,i)  
Y_i = Z_i W_down,i

Combine at the FFN boundary:

Y = Y_GPU + Y_NPU

The up and gate projections use matching output-feature partitions, corresponding to N-splits. The down projection consumes those partitions along its reduction dimension, corresponding to a K-split.

The intended property is that intermediate channels retain their ownership and compatible layout between these operations. This does not require intermediates to remain in on-chip memory.

Handle model-specific biases, residual connections, activation functions, and quantization metadata correctly. Apply any down-projection bias once after combining partial outputs.

## 3. Phase one: audit the existing implementation

Trace one model’s prefill path from dispatch through attention and FFN execution. Identify the actual files and functions responsible for:

- Up, gate, and down projections.
- Activation and elementwise gating.
- GEMM split dimensions and ratios.
- Packed weight layouts and quantization metadata.
- Intermediate buffers, strides, and ownership.
- GPU–NPU synchronization and output combination.
- Micro-batch dependencies and dispatch.
- NPU queue management and configuration reuse.
- Existing profiling, tuning, and benchmark infrastructure.

Answer these questions with concrete code references:

1. Does the runtime already preserve any partitions across FFN operators?
2. Where are full intermediates assembled, converted, or synchronized?
3. Do split outputs already write directly into shared output buffers?
4. Can existing kernels consume feature partitions without repacking?
5. How does an FFN allocation interact with attention from another micro-batch?
6. What operations can execute efficiently on the NPU, including SiLU and gating?
7. Which existing configuration is the strongest relevant baseline?

Distinguish findings from assumptions. If persistent channel partitioning already exists, characterize it and revise the proposed extension around a demonstrated missing capability.

Record a concise architecture map and project plan in repository documentation, following existing conventions.

## 4. Phase two: establish instrumentation and baselines

Reuse existing tracing where possible. Add only missing instrumentation needed to measure:

- Complete FFN latency.
- Projection and activation/gating latency.
- Intermediate assembly, conversion, and reduction.
- Dependency waits and synchronization.
- GPU and NPU execution intervals.
- Attention–FFN overlap.
- End-to-end prefill latency.

Separate host enqueue time from device execution time. Identify asynchronous completion correctly. Label estimates of memory traffic as estimates rather than hardware measurements.

Establish these comparison configurations where supported:

A. Original HeteroMosaic with its existing optimized configuration.  
B. Single-device FFN allocation within the existing runtime.  
C. Existing operation-level tensor partitioning.  
D. Persistent token-row partitioning across the FFN, if not already covered by the baseline.  
E. Proposed persistent intermediate-channel partitioning.

Avoid duplicate configurations when two labels describe the same implementation.

First measure the existing configurations before introducing the new execution path.

## 5. Phase three: implement a minimal persistent FFN path

Add an opt-in execution mode that preserves the original path as the default and fallback.

Start with one model, one supported shape family, and one valid split ratio. Then extend to a small ratio sweep aligned with backend tiling and quantization constraints.

Requirements:
- Matching intermediate-channel ownership for up and gate projections.
- Correct local activation and gating.
- A down projection that consumes each partition directly.
- Correct combination of partial outputs.
- Explicit dependency handling across both devices.
- Compatible packed weight and metadata access.
- No runtime repacking that silently dominates the measured result.
- No full intermediate assembly between projections unless required; document any such requirement.

If the NPU cannot execute local activation/gating efficiently, inspect available kernel capabilities before designing a new kernel. Quantify any fallback transition and its cost. Do not describe an execution path as fully device-local if it moves NPU intermediates to the GPU.

Separate one-time setup costs from inference costs. Measure additional memory capacity, including any duplicated or repacked weights.

## 6. Phase four: verify correctness

Compare against the original runtime using identical weights, quantization, inputs, and model semantics.

Check:
- FFN outputs with tolerances appropriate to the numerical format.
- Several valid ratios, aligned shapes, and supported boundary cases.
- Single-device endpoints where the interface supports them.
- Complete prefill outputs or logits.
- Multiple micro-batches with the existing dependency schedule.
- Absence of races, stale reads, and duplicate bias/residual application.

Expect floating-point differences from changed reduction order. Report the tolerance and observed error; do not require bitwise equality without justification.

Use focused tests that catch partition, layout, and synchronization errors.

## 7. Phase five: evaluate overlap and end-to-end behavior

Run three levels of experiments:

1. **Isolated FFN:** determine whether persistent partitions improve complete sublayer latency and identify the reason.
2. **Concurrent attention and FFN:** use representative attention work from the same model and micro-batch schedule. Measure both stage latencies and the time until both finish.
3. **Complete prefill:** compare the extension with the strongest original HeteroMosaic configuration.

For each comparison:
- Hold model, precision, prompt, and relevant runtime settings constant.
- Include warm-up and repeated measurements.
- Report central tendency and variability.
- Record device, software versions, power settings, and relevant thermal conditions.
- Separate fixed-schedule comparisons from results after tuning.
- Give both the baseline and extension comparable tuning opportunities.

Measure a small representative range of prompt lengths and micro-batch sizes before expanding the sweep.

Primary metric: **end-to-end prefill latency**, or TTFT if the benchmark includes producing the first token.

Supporting metrics:
- Complete FFN latency.
- Overlapping interval completion time.
- Attention slowdown caused by FFN GPU participation.
- Synchronization and intermediate handling costs.
- Memory footprint.
- Energy per prefill if suitable measurement hardware is available.

Do not claim success based only on individual GEMM speedups.

## 8. Phase six: add allocation selection only if justified

If measurements show predictable differences between configurations, implement a small policy selecting among single-device, persistent token-row, and persistent channel execution.

Use measured costs for the complete FFN and its competing attention work. Integrate with the existing scheduler rather than replacing causal micro-batching.

Begin with an offline lookup or simple selection rule. Avoid a large new scheduler until the evidence warrants it.

Compare the policy against:
- The strongest fixed allocation.
- The existing HeteroMosaic allocation/tuning approach.
- A measured best configuration over the evaluated candidates.

Use separate calibration and evaluation workloads where practical.

## 9. Research claims and decision points

Treat these as hypotheses:

- Persistent partitions reduce meaningful FFN boundary costs.
- Those savings survive backend layout and reduction overhead.
- The best FFN allocation changes with overlapping attention.
- Selecting the allocation improves complete prefill over a strong tuned baseline.

If isolated FFN performance improves but prefill worsens, investigate interference rather than presenting a kernel gain as an end-to-end gain.

If internal boundary costs are negligible, revise the motivation.

If existing code already provides the mechanism, focus on a demonstrably missing capability or document that the original hypothesis does not hold.

Keep the related-work distinction precise:
- GPU–NPU tensor partitioning is established.
- Megatron’s paired projection partitioning is established.
- HeteroMosaic’s contention-aware micro-batch scheduling is established.
- Our potential contribution is the measured benefit and selection of coordinated sublayer partitions within that schedule.

## 10. Working style and first-session deliverables

Proceed autonomously with inspection, documentation, instrumentation, implementation, and supported validation. Ask only when a missing hardware resource or consequential unresolved design choice blocks progress.

Never fabricate benchmark results. If suitable hardware is unavailable, complete the code audit, build checks, applicable correctness tests, and reproducible benchmark commands. Clearly identify measurements still requiring hardware.

For the first session:
1. Audit the repository and trace the FFN execution.
2. Document whether the proposed mechanism already exists.
3. Identify the concrete implementation changes and kernel dependencies.
4. Establish baseline commands and add focused instrumentation if feasible.
5. Recommend the smallest initial experiment based on the actual code.

At each milestone, report:
- What changed or was learned.
- Evidence supporting the conclusion.
- Checks completed.
- Remaining limitations.
- The next concrete step.

Keep implementation changes reviewable and avoid unrelated refactoring.