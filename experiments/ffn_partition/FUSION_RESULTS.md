# Combined gate/up projection and partition sweep

**Measured:** combined gate/up supports a useful NPU allocation around
**P768–P896**, or **5.36%–6.25%** of the FFN channels, at
`M512/H4096/I14336` on the available Ryzen AI 9 HX370 / Radeon 890M / NPU2.
Across the main sweep and three independent repeat blocks, these candidates
take **19.784–20.228 ms**, with **1.101–1.125×** speedup over their own
GPU-only controls. The lowest-latency candidate changes between runs; a
unique or universal optimum is not established.

The main sweep's minimum was P896 at **19.948 ms**, versus its **22.272 ms
GPU-only control**: **1.1165× speedup, or 10.44% lower latency**. The main
unfused minimum was P512 at 20.537 ms; its independent repeat is 20.764 ms.
All 62 sweep/confirmation jobs pass, and a separate exact comparison confirms
unchanged native gate/up and complete NPU-branch output bits on four tested
partitions.

This is a synthetic complete-FFN experiment with prefill shapes. It does not
measure complete model prefill, TTFT, attention interference, or Max+ 395.
The requested PR remains paused.

## What is fused

**Code-confirmed:** the NPU owns intermediate channels `[0,P)` and the GPU
owns `[P,I)`. Both keep their matching gate/up channels through SiLU and
multiply, then consume the corresponding down-projection K slice. The GPU
adds the two `[M,H]` partial outputs after both branches have completed.

The new NPU graph computes one wider projection:

```text
[G_npu | U_npu] = X @ [Wgate_npu; Wup_npu].T
Z_npu = SiLU(G_npu) * U_npu
Y_npu = Z_npu @ Wdown_npu.T
Y = Y_gpu + Y_npu                         # final sum on the GPU
```

| Property | Original array8 NPU branch | Combined gate/up branch |
| --- | --- | --- |
| NPU launch sequence | Gate → up → SiLU/multiply → down | Gate/up → SiLU/multiply → down |
| Completed launches per FFN call | 4 | 3 |
| Projection weight BOs | Gate, up, down | Packed gate+up, down |
| Total packed weight payload | Three logical matrices | Same three logical matrices |
| Gate/up activation upload | One for gate and another for up | One shared input upload |
| Gate/up output layout | Two compact native buffers | Same two compact native buffers |
| Down-input layout conversion | CPU | CPU |
| FFN partial reduction | GPU | GPU |

The combined projection uses eight columns × four compute rows, with all
32 workers active. Columns 0–3 compute gate; columns 4–7 compute up. The
existing native BF16 MMUL / FP32 accumulation kernel is unchanged. Direct
DMA scatter writes separate compact gate and up output BOs, avoiding a CPU
split/compaction of a wide output. The full graph and ABI are described in
[GATE_UP.md](../../npu/ffn/GATE_UP.md).

This is projection fusion, not on-chip SwiGLU or full-FFN fusion. Gate/up
outputs are still read back and written into the separate SiLU/multiply
context. Down remains a separate NPU launch, with the existing CPU layout
conversion. Logical channel ownership is persistent; on-chip residency is
not established.

**Code-confirmed traffic estimate:** at `M512/H4096`, one redundant 4 MiB
host activation upload is removed. For `P512`, estimated explicit BO payload
per NPU branch falls from 15 MiB to 11 MiB. These are byte counts from the
host calls, excluding layout copies, instructions, device DMA replay and
cache effects; they are not physical DRAM-bandwidth measurements. Both
matrix products and their weight/output bytes remain necessary.

For `P` divisible by 256, including `P512`, logical device activation DMA
does not decrease: the wider projection still replays A for local N tiles.
For `P=128 mod 256`, including `P128/P384/P896`, the old graph uses two
four-column token-row groups. The combined graph broadcasts across all eight
columns and halves logical A DMA relative to those two projections. At
`M128`, this also changes M reuse from one to two. Those points therefore
include a mapping improvement as well as fewer launches.

## Baseline, numerical contract and timing

The GPU baseline is the unchanged HeteroMosaic packed W4A16 kernel dispatcher
in `src/hipkernels/w4a16_gemm_packed.cu`, with three projections and separate
Torch BF16 SiLU and multiply operations. The concurrent GPU suffix uses the
same kernels. Teammate PR kernels are not integrated into these measurements.
This isolates the NPU graph change while preserving a reproducible original
GPU FFN without offload.

The ordinary sweep uses the same canonical synthetic unsigned-int4 weights,
BF16 scales, zero points, group size 128, seed 12832 and alternating BF16
inputs across variants and partitions. Gate/up have matching N slices; down
has the matching K slice. Projection outputs, SiLU, multiplication and each
down partial retain their existing BF16 rounding boundaries. No correctness
tolerance is relaxed for the combined graph.

Each ordinary job measures GPU-only, serialized GPU–NPU and concurrent
GPU–NPU FFNs, with randomized mode order within an iteration. The boundary
starts with ready GPU input and ends with synchronized GPU output. It includes
input/output staging, all NPU launches and waits, explicit BO I/O, CPU layout
conversions and the GPU partial sum. Compilation, fixed-weight preparation
and correctness readback are excluded. Fused/unfused job order alternates
between partition points. Each point retains its own GPU-only control rather
than comparing every point against one old baseline measurement.

Separate instrumented jobs record GPU HIP event spans, CPU submission calls,
NPU host waits, host BO intervals and CPU layouts. **NPU wait is the CPU's
wait for a submitted NPU operation to complete:** it can include scheduling,
device DMA, computation and notification. Explicit host BO reads/writes and
CPU layout changes are outside that wait. It is not a measurement of data
movement alone or of pure NPU compute.

GPU events include scheduling and probe overhead. CPU submission calls include
Python/C++ runtime work, not just driver overhead. CPU and GPU clocks are not
calibrated to each other; the plots cannot be interpreted as an exact shared
timeline. Independent stage medians are not additive. Ordinary latency supplies
the acceleration comparison; diagnostic latency does not replace it.

## Power mode and environment

**Measured:** the NPU reports `default`. Earlier requests to set `performance`
were rejected with permission error -13, including under sudo; see
[POWER_TIMING.md](POWER_TIMING.md). No shared driver or kernel was changed.
The sweep queries the actual XRT NPU platform mode before and after every
measurement process and requires both snapshots to report `default`.

Boundary snapshots do not establish continuous clocks, temperature, electrical
power or absence of host interference. Prior array8 measurements without power
capture are kept as historical evidence and are not relabeled retrospectively.

The prepared execution environment is Torch 2.11.0+ROCm7.2, NumPy 1.26.4 and
the notebook's XRT bindings. The MLIR-AIE compiler remains pinned to
`7e00b57955e108fe9d8e9419f5828a0c7e650858`; the separate IRON interpreter
builds the artifacts. `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` are
used for the experiment. Runtime setup and compatibility details remain in
[README.md](README.md).

## Main partition sweep

The [completed sweep manifest](results/fusion_sweep_m512/sweep_manifest.json)
binds all raw reports, logs and power snapshots. Each variant uses 30 ordinary
samples per mode and 10 diagnostic samples after three excluded warmups.
All durations below are ordinary complete-FFN medians in milliseconds. Each
speedup divides that job's GPU-only median by its concurrent median.

| NPU P | NPU channels % | Unfused GPU control | Unfused concurrent | Unfused speedup | Fused GPU control | Fused concurrent | Fused speedup |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 0.893 | 22.058 | 21.800 | 1.0118× | 22.323 | 21.596 | 1.0337× |
| 256 | 1.786 | 22.264 | 21.165 | 1.0519× | 22.368 | 21.321 | 1.0491× |
| 384 | 2.679 | 22.339 | 20.600 | 1.0845× | 22.274 | 21.638 | 1.0294× |
| 512 | 3.571 | 22.380 | **20.537** | **1.0897×** | 22.414 | 21.590 | 1.0382× |
| 640 | 4.464 | 22.480 | 21.143 | 1.0633× | 22.559 | 21.187 | 1.0647× |
| 768 | 5.357 | 22.385 | 22.520 | 0.9940× | 22.269 | 20.228 | 1.1009× |
| 896 | 6.250 | 22.240 | 22.835 | 0.9740× | 22.272 | **19.948** | **1.1165×** |
| 1024 | 7.143 | 22.206 | 23.680 | 0.9377× | 22.287 | 20.316 | 1.0970× |
| 1536 | 10.714 | 22.386 | 27.485 | 0.8145× | 22.236 | 24.801 | 0.8966× |
| 2048 | 14.286 | 22.233 | 31.448 | 0.7070× | 22.307 | 27.966 | 0.7976× |
| 4096 | 28.571 | 19.881 | 46.690 | 0.4258× | 20.130 | 42.728 | 0.4711× |
| 7168 | 50.000 | 19.775 | 69.433 | 0.2848× | 19.749 | 65.968 | 0.2994× |

The saved [full-range plot](results/fusion_figures/total_ffn_m512_h4096_i14336.pdf)
and [P≤2048 view](results/fusion_figures/zoom_le2048/total_ffn_m512_h4096_i14336.pdf)
show ordinary latency and matched-control speedup with sample ranges.
[CSV data](results/fusion_figures/ordinary.csv) and
[JSON summaries](results/fusion_figures/summary.json) retain the exact values.

P896 combined beats its paired GPU control in all 30 iterations; the unfused
P512 winner does so in 29 of 30. Their concurrent sample p10–p90 ranges are
19.427–20.617 ms and 20.050–21.326 ms, respectively; these are sample ranges,
not confidence intervals. Fusion does not improve every fixed ratio:
the main P384 and P512 concurrent results are slower than their unfused
counterparts. Conversely, it makes P768–P1024 useful allocations in this run,
while large NPU shares remain slower than GPU-only. These observations
motivate independent repeats around the apparent minimum instead of claiming
that one fewer launch guarantees acceleration.

GPU-only controls range from 19.749 to 22.559 ms across the sweep despite an
identical mathematical workload. Shared-host drift remains, and snapshots of
`default` power mode do not resolve its cause. Raw data, p10–p90 sample ranges
and paired comparisons are retained. The smallest sampled latency is not a
global optimum; baseline drift can also make the best absolute latency and
largest control-relative speedup occur at different points. Independent
repeats are not pooled and slow samples are not discarded.

### What was covered before this sweep

The earlier [array8 characterization](ARRAY8_RESULTS.md) tested only
`P=128,512,1024,2048` at M512. Its M128, M2048 and M4096 model-shaped tests
used P512 and P2048. That coverage was sparse, not a dense or exhaustive
partition search. The current main sweep adds every 128-channel step through
P1024, then P1536, P2048, P4096 and P7168. The independent confirmation also
adds P1152; other prompt lengths have not received this denser search.

### Validation and evidence

**Measured:** all 48 jobs and all **2,400 timed calls** pass correctness,
with **7,644 completed NPU dispatches** including checks and warmups. The
1,536 explicit numerical checks pass; maximum recorded explicit relative-L2
error is **0.003546**, under the unchanged 0.02 bound. Every fixed projection
weight BO is uploaded once. There are 96 before/after power snapshots, all
reporting `default`. Report and snapshot SHA-256 hashes, measurement-source
hashes and artifact source/graph/planner bindings have been verified against
the saved manifest and current source.

The combined graph also passed the earlier small hardware smoke at
`M128/H128/P128` and `M128/H128/P384`. Seventy-seven local CPU tests pass
(31 NPU tests and 46 experiment tests), covering exact nonoverlapping output
addresses, all 32 workers, odd local channel-tile counts, quantization
metadata, runtime output indexing and experiment bookkeeping.

The first sweep attempt could not find Ninja on `PATH`. Prepending the
prepared runtime's `bin` directory fixed the environment without installing
another dependency, and the job was rerun successfully. The manifest retains
the historical error string on that first job; its current status, return
code and hashed report are successful. Raw evidence is preserved.

## Independent confirmation and order reversal

Each ordinary repeat below uses 50 samples per mode after three excluded
warmups. The [first fused confirmation](results/fusion_confirmation/sweep_manifest.json)
ran P1024 → P768 → P896 → P1152; a separate
[unfused confirmation](results/fusion_unfused_confirmation/sweep_manifest.json)
repeated P512. Both also have separate 20-sample diagnostic runs. The two
additional ordinary-only blocks ran
[P768 → P896](results/fusion_order_ab/sweep_manifest.json), then
[P896 → P768](results/fusion_order_ba/sweep_manifest.json).

| Repeat block | Variant / P | GPU control ms | Concurrent ms | Concurrent p10–p90 ms | Speedup | Paired wins |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| First confirmation | Combined 1024 | 22.248 | 21.193 | 19.968–21.874 | 1.0498× | 46/50 |
| First confirmation | Combined 768 | 22.260 | **19.784** | 19.193–20.579 | **1.1252×** | 49/50 |
| First confirmation | Combined 896 | 22.301 | 20.108 | 19.738–20.807 | 1.1091× | 50/50 |
| First confirmation | Combined 1152 | 22.254 | 21.837 | 20.968–23.029 | 1.0191× | 32/50 |
| Unfused confirmation | Unfused 512 | 22.378 | 20.764 | 20.327–22.023 | 1.0777× | 48/50 |
| P768 → P896 | Combined 768 | 22.271 | 19.997 | 19.426–20.544 | 1.1137× | 50/50 |
| P768 → P896 | Combined 896 | 22.343 | **19.944** | 19.539–21.157 | 1.1203× | 49/50 |
| P896 → P768 | Combined 896 | 22.375 | **20.003** | 19.531–20.973 | 1.1186× | 50/50 |
| P896 → P768 | Combined 768 | 22.433 | 20.023 | 19.545–20.762 | 1.1204× | 50/50 |

The separate refinement figure set uses only the first fused and unfused
confirmations: [ordinary latency/speedup](results/fusion_refinement_figures/total_ffn_m512_h4096_i14336.pdf)
from 50 samples per mode, plus
[operations](results/fusion_refinement_figures/stages_m512_h4096_i14336.pdf),
[host handling](results/fusion_refinement_figures/npu_host_m512_h4096_i14336.pdf)
and [submissions](results/fusion_refinement_figures/submission_m512_h4096_i14336.pdf)
from separate 20-sample diagnostics. These include P1152 and keep the unfused
P512 reference distinct; they do not replace or merge with the main sweep.

The [repeat-comparison figure](results/fusion_confirmation_figures/repeat_candidates_m512_h4096_i14336.pdf)
shows main, confirmation, forward-order and reverse-order runs separately.
Its [CSV](results/fusion_confirmation_figures/repeat_comparison.csv) and
[JSON](results/fusion_confirmation_figures/repeat_comparison.json) retain
run order and exact values. The candidate chart contains only combined P768
and P896; the unfused reference remains in the table above.

The main sweep favors P896, the first longer confirmation favors P768, and
the two order-reversal blocks favor P896 by only **0.053 ms** and **0.020 ms**.
Their sample ranges overlap substantially. In the reverse block, P896 has
slightly lower latency while P768 has slightly higher matched-control speedup
because the GPU baselines differ. No samples are pooled across runs.

**Measured conclusion:** P768–P896 is a useful allocation region on this
workload. If one value is needed for the next integration experiment, P896
is a practical candidate—it has the lower median in three of four blocks—
with P768 retained as the neighboring control. These runs do not establish
a uniquely faster or universally optimal value. The 50% NPU allocation is
substantially slower; equal channel ownership does not balance these devices.

### Exact projection and complete-branch comparison

The [standalone exact check](results/gate_up_sweep/gate_up_exact_m512.json)
passes all **160 checks**, including 72 exact-bit comparisons, at
`M512/H4096/P128,384,512,896`. Within each
partition, combined and separate variants use identical fixed weights and
random-A, random-B, zero and repeated-A inputs. Native packed gate/up outputs
and final NPU-branch BF16 outputs are **bit-identical** between variants for
every tested input. Complete-branch outputs also pass the unchanged CPU
reference tolerances; maximum recorded relative-L2 error is **0.003643**.

The check records 112 successful NPU completions for 32 correctness-only
FFN calls, verifies three versus four dispatches per call, fixed weights
uploaded once, exact repeats and changed-input outputs. It is a numerical
diagnostic, not a latency measurement or proof of model accuracy.

Across the five sweep/confirmation manifests, **62 jobs**, **3,850 timed
calls**, **2,046 explicit checks** and **11,268 NPU completions** pass.
Their 124 before/after power snapshots all report `default`. Adding the exact
diagnostic gives **2,206 passing checks and 11,380 NPU completions**; its 32
correctness-only calls are separate from the 3,850 timed calls. Report/power
hashes and measured source bindings are verified. These totals exclude earlier
historical array8 experiments and the small smoke run.
The [final verification summary](results/fusion_confirmation_analysis.json)
records per-run statistics, power and source bindings, counts and selection
caveats without pooling the repeats.

## Operation and host diagnostics

The [derived stage analysis](results/fusion_stage_analysis.json) records all
raw report hashes and preserves the ordinary/instrumented distinction. The
saved [operation plots](results/fusion_figures/stages_m512_h4096_i14336.pdf),
[host-handling plots](results/fusion_figures/npu_host_m512_h4096_i14336.pdf)
and [submission plots](results/fusion_figures/submission_m512_h4096_i14336.pdf)
keep those metrics separate. The following are medians from separate
ten-sample instrumented runs, in ms:

| Diagnostic span | Unfused P512 | Combined P512 | Combined P896 |
| --- | ---: | ---: | ---: |
| Whole FFN, instrumented host wall | 22.265 | 20.674 | 20.123 |
| GPU branch, HIP events | 19.827 | 20.422 | 19.779 |
| GPU down projection, HIP events | 6.184 | 6.516 | 5.961 |
| Full NPU call, host wall | 20.957 | 15.088 | 18.324 |
| NPU result host→GPU copy, HIP events | 0.226 | 0.207 | 0.205 |
| GPU boundary sum, HIP events | 0.155 | 0.133 | 0.142 |

At combined P896, GPU gate/up/down event medians are 6.845/6.232/5.961 ms;
SiLU and multiplication are 0.293/0.433 ms. The three projections account
for a median 96.22% of the GPU branch event span when the fraction is computed
per invocation. The final GPU reduction is small compared with those
projections; it is measured after dependencies, not including the final wait.

The NPU stages at the same combined P896 diagnostic are:

| NPU stage | CPU submission µs | CPU wait ms | Host stage including BO I/O ms |
| --- | ---: | ---: | ---: |
| Combined gate/up | 96.3 | 6.740 | 7.613 |
| SiLU/multiply | 143.7 | 1.621 | 2.088 |
| Down | 81.0 | 5.091 | 5.859 |

Per-invocation aggregates give a 12.012 ms median for projection dispatch/wait,
13.508 ms for all NPU host waits, 0.317 ms for all submission API calls,
2.390 ms for CPU layouts, and 1.679 ms for explicit BO I/O plus wrapper work
outside dispatch. These independent medians cannot be added to reconstruct
the whole branch. Submission-call cost alone is small; removing a launch also
changes context scheduling, input upload and overlap, none of which is isolated
as a single cost by these measurements.

At fixed P512, fusion lowers the **ordinary** NPU branch host median by
3.851 ms, while the ordinary whole FFN becomes 1.052 ms slower. The measured
per-invocation host bookkeeping shows a higher output-staging/final-wait mean
rather than a higher CPU-layout mean. That interval includes GPU completion
waiting and is not copy time alone.
The separate diagnostic observes a longer GPU branch and down event with
fusion, and the H2D copy event overlaps down in 10/10 combined samples versus
2/10 unfused samples. This is a scheduling association, not proof that the
copy caused the regression. Clock changes, contention, cache effects and
host interference were not isolated.

The P512 diagnostic's total-latency ordering actually reverses the ordinary
ordering: 20.674 ms combined versus 22.265 ms unfused, compared with ordinary
21.590 versus 20.537 ms. In particular, unfused diagnostic CPU layouts have a
4.033 ms median aggregate versus 2.115 ms in the ordinary run. The diagnostic
therefore must not be presented as an exact decomposition of ordinary latency.

Within the common HIP clock, the H2D copy finishes before the GPU branch end
in 10/10 combined P896 samples, 5/10 P1024 samples and 0/10 P1536 samples.
This is consistent with a balance region, then a later NPU-result arrival
at larger shares. It does not align NPU host timestamps with GPU events or
establish an exact simultaneous execution timeline. A controlled experiment
that delays the result copy could test its interaction with GPU down; it
has not been run here.

## Reproduction

Run from the repository root in the prepared notebook terminal. The sweep
driver never changes power mode. Use a new output directory for another run;
`--resume` requires identical configuration and measurement source hashes.

```bash
export PATH="/notebooks/heteromega-ffn-venv/bin:$PATH"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
/notebooks/heteromega-ffn-venv/bin/python -m experiments.ffn_partition.sweep_partition \
  --m 512 --hidden 4096 --intermediate 14336 \
  --npu-channels 128,256,384,512,640,768,896,1024,1536,2048,4096,7168 \
  --iterations 30 --diagnostic-iterations 10 --warmup 3 \
  --required-power-mode default \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python \
  --output-dir experiments/ffn_partition/results/fusion_sweep_m512
```

The separate exact-comparison diagnostic is not a performance benchmark.
It creates and releases each variant's contexts separately, using identical
weights and inputs within each comparison. The following command requires
the matching artifacts already built by the sweep:

```bash
/notebooks/heteromega-ffn-venv/bin/python -m experiments.ffn_partition.check_gate_up \
  --m 512 --hidden 4096 --channels 128 384 512 896 --no-build \
  --output experiments/ffn_partition/results/gate_up_sweep/gate_up_exact_m512.json
```

Generate shareable SVG/PDF/PNG figures and CSV/JSON summaries from saved
evidence. The plotter keeps repeats as separate series and shows the full
partition range plus a separately labeled view of `P<=2048`:

```bash
python -m experiments.ffn_partition.plot_partition_sweep \
  experiments/ffn_partition/results/fusion_sweep_m512 \
  --m 512 --output experiments/ffn_partition/results/fusion_figures
```

The repeat plot is reproduced from the saved independent manifests, without
pooling samples. The candidate plot selects only fused P768 and P896; the
unfused confirmation is included in the separate refinement figures:

```bash
python -m experiments.ffn_partition.plot_partition_sweep \
  experiments/ffn_partition/results/fusion_sweep_m512 \
  experiments/ffn_partition/results/fusion_confirmation \
  experiments/ffn_partition/results/fusion_order_ab \
  experiments/ffn_partition/results/fusion_order_ba \
  --m 512 --repeat-only --repeat-channels 768 896 \
  --output experiments/ffn_partition/results/fusion_confirmation_figures
```

The confirmation manifests contain every exact execution command. To repeat
the first confirmation with new evidence, use the sweep command above with
`--variants fused --npu-channels 1024,768,896,1152 --iterations 50
--diagnostic-iterations 20` and a new output directory. For the order test,
use `--variants fused --measurements ordinary --iterations 50` in two fresh
directories, first with `--npu-channels 768,896`, then `896,768`.

For the separate 50-sample confirmation / 20-sample diagnostic refinement
figures, run the plotter on only `results/fusion_confirmation` and
`results/fusion_unfused_confirmation` (under `experiments/ffn_partition/`),
without `--repeat-only`, and use output directory
`experiments/ffn_partition/results/fusion_refinement_figures`.

For CPU-only checks:

```bash
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s npu/ffn -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 python -m unittest discover \
  -s experiments/ffn_partition -p 'test_*.py' -v
```

## Limits and next step

The combined graph currently supports `P<=8192` aligned to 128, so the
full-NPU 14,336-channel endpoint is unsupported. GPU-only is measured inside
every ordinary job. Wide partitions, other prompt lengths, model weights,
attention contention and complete model prefill need their own validation.
The next step is to test the P768/P896 candidates inside the existing prefill
schedule, including overlapping attention, while preserving the original
model baseline. A controlled result-copy scheduling experiment can investigate
the fixed-P512 regression before further fusion. On-chip gate/up/SiLU fusion
would be a separate implementation experiment.
