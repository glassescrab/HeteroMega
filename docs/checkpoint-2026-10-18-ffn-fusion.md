# FFN fusion checkpoint — 2026-10-18

Checkpoint branch: `codex/ffn-partition-microbench`, following `f6961ec`.
The user requested a local checkpoint and cleanup. Push and PR creation remain
paused. No further kernel optimization or hardware measurement is part of
this checkpoint.

## Resume here

- [Latest measured results](../experiments/ffn_partition/SWIGLU_RESULTS.md).
- [Two-launch NPU architecture and proposed next optimizations](../npu/ffn/SWIGLU.md).
- [Three-launch gate/up comparison](../experiments/ffn_partition/FUSION_RESULTS.md).
- [Runtime and reproduction instructions](../experiments/ffn_partition/README.md).

**Implemented and hardware-validated:** `--fuse-swiglu` runs gate/up plus
SiLU/multiply in one eight-column, four-row NPU graph, then launches down.
Gate/up intermediates remain in adjacent on-chip memory. Z is still read
back, permuted on CPU, and uploaded to down. The GPU performs the final
partial-output sum. The four-launch and three-launch controls remain
available; original GPU kernels are unchanged.

**Measured:** M512/H4096/I14336, HX370/Radeon 890M, NPU mode `default`.
The main and reversed-order confirmation sweeps favor P1152 by median;
P1024 is nearly tied in confirmation and has a lower p90 there. Retain
P1024–P1152 as a configurable region. The confirmation at P1152 takes
19.643 ms versus 22.293 ms GPU-only (1.1349x), and is 2.99% lower in latency
than the retuned three-launch control at P896. These are synthetic complete
FFN measurements, not whole-model prefill or TTFT.

Validation already completed before checkpointing:

- 102 CPU tests and 661 small-build compiler checks pass.
- 180 exact-checker checks pass, including 24 bit-exact cross-variant
  comparisons of Z and complete NPU outputs.
- 36 performance jobs pass: 2,600 timed calls, 1,176 explicit checks and
  5,465 NPU completions; exact-only runs add 60 completions.
- All 72 performance power snapshots and four exact-checker snapshots
  report `default`. Earlier requests for `performance` were rejected by
  the host; no driver/kernel changes were made.

## Retained evidence and environment

Raw reports, power snapshots, logs, source manifests, source-only baseline
archive, compiler audit and derived plots are retained under
`experiments/ffn_partition/results/`. The interrupted zero-check run remains
labeled separately. Nested evidence logs are explicitly included in Git.
The upload-only `delivery_checksums.json` is removed after successful
notebook delivery; scientific provenance manifests remain intact.

The notebook checkout is `/notebooks/HeteroMega`. Its prepared runtime is
`/notebooks/heteromega-ffn-venv/bin/python`; compilation uses
`/home/mliraie/mlir-aie/ironenv/bin/python`, pinned MLIR-AIE commit
`7e00b57955e108fe9d8e9419f5828a0c7e650858`. Compiled artifacts and these
environments are retained. Current notebook measurements followed a server
restart; the reason for the interruption is unknown.

## Next work, not yet implemented

Integrate the candidate region into the actual prefill schedule and measure
attention interference and complete prefill against the unchanged baseline.
Teammate GPU PR kernels are not in these controlled measurements.

A separate low-risk kernel experiment is direct Z emission in down's input
layout, followed by a separately validated shared-BO handoff. A one-launch
full FFN needs new core scheduling, layout routing and replay. Do not infer
its feasibility or speedup from the current two-launch result.
