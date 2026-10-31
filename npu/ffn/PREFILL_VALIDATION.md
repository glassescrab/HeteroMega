# Prefill NPU validation — 2026-10-14 UTC

The source-built W4A16 prefill projection passes hardware checks for all
four planned prompt lengths. This is a standalone projection milestone;
the persistent gate/up → SiLU-and-multiply → down FFN graph remains to be
connected. Inputs are synthetic, with seed `12832`, not a loaded Llama checkpoint.

## Machine and artifacts

- AMD Ryzen AI 9 HX370 with Radeon 890M; XRT reports NPU Strix, `aie2p`,
  topology 6×8. These measurements do not characterize Ryzen AI Max+ 395.
- Ubuntu 24.04.4, kernel `6.17.0-42-generic`, XRT `2.26.0`.
- MLIR-AIE/IRON revision `7e00b57955e108fe9d8e9419f5828a0c7e650858`.
- Validated C++ SHA256:
  `090e87845395f730b580be537c7da5f11c0f53eaee110b28786e362cdfd32ba2`.
- Raw JSON files below were downloaded from the notebook unchanged. Each
  contains geometry, source/binary hashes, every case error, and measured
  launch times. The recorded runs used the default seed; the runner now
  also writes `seed` and `cases_mode` explicitly for future runs.

## Results

Median of three launches after one warmup; every timed output and warmup
output was checked. The timer includes dispatch, NPU DMA, and execution,
but excludes host BO copies/synchronization, packing, allocation, and CPU
reference evaluation. Times are exploratory measurements without clock
locking or controlled system-load isolation.

| M tokens | K | N | Columns | Cases passed | Median launch (ms) | Effective GOP/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [32](results/prefill_m32_k256_n64_hx370.json) | 256 | 64 | 1 | 7/7 | 0.124 | 8.47 |
| [128](results/prefill_m128_k4096_n2048_hx370.json) | 4096 | 2048 | 4 | 7/7 | 11.795 | 182.06 |
| [512](results/prefill_m512_k4096_n2048_hx370.json) | 4096 | 2048 | 4 | 3/3 | 46.501 | 184.72 |
| [2048](results/prefill_m2048_k4096_n2048_hx370.json) | 4096 | 2048 | 4 | 3/3 | 186.101 | 184.63 |
| [4096](results/prefill_m4096_k4096_n2048_hx370.json) | 4096 | 2048 | 4 | 3/3 | 371.522 | 184.97 |
| [128](results/prefill_m128_k2048_n4096_hx370.json) | 2048 | 4096 | 4 | 7/7 | 11.828 | 181.57 |

K4096/N2048 represents a gate or up channel shard. K2048/N4096 represents
the corresponding down-projection input shard. Both use the same tiled
kernel; this does not yet test their composition or heterogeneous reduction.
There are 30 correctness cases and 24 additional checked warmup/timing
launches across the six builds. The 18 CPU unit tests also pass.

The full seven-case suite includes nonzero output slices, changed inputs,
exact-zero inputs, quantized values equal to zero points, a nonzero K slice,
and exact one-hot tests for zero-point/scale lanes and packed int4 lanes.
The three-case suite includes random output slices, changed inputs, and
exact-zero inputs. Every exact case passed with zero error. Across all
random cases, maximum absolute error was `0.0625` and maximum relative L2
error was `5.982e-5`, relative to BF16 inputs/dequantized weights, FP32
accumulation, and BF16 output. All elements also passed the recorded
elementwise `rtol=0.03, atol=0.05` diagnostic. Full model accuracy remains
unmeasured.

## Implementation finding

The initial vector metadata path produced wrong varying zero-point lanes
despite correct constant-weight tests. The current core converts only
the 32 zero-point values scalarly and loads eight metadata lanes directly.
The 4096 weight elements per tile are still unpacked/dequantized with
vectors, and all matrix MACs use `aie::mmul`. Two exact one-hot regressions
guard this path. The diagnostics do not isolate an underlying compiler or
intrinsic defect, since the fix changed both conversion and metadata loads.

The design uses one compute core per column, rereads weights per M tile,
and dequantizes each incoming K128/N32 weight tile. The roughly 182–185
GOP/s observed for model-shaped projections is a starting point for
profiling, not a speedup claim. No GPU-only, HeteroMosaic, FFN, TTFT, or
end-to-end model comparison has been measured in this milestone.

## Reproduction and next step

Use [PREFILL.md](PREFILL.md) for ABI, build commands, and detailed numerical
semantics. For the length sweep, build each M separately with K4096/N2048,
four columns, and run `--cases basic`. Use `--cases full` for the small
case and the two 128-token projection shapes above. All runs used three
timed iterations and one warmup.

Next, connect matching gate/up shards to the fused activation and the
corresponding down shard in one prefill graph, preserving the intermediate
channel partition. Validate that complete NPU FFN shard before introducing
GPU reduction or measuring model latency. Optimize the scalar metadata
conversion and wider core utilization only against these correctness checks.
