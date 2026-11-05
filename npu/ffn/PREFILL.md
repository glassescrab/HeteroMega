# W4A16 prefill projection development

The current milestone is a source-built, multi-token NPU projection for
HeteroMega. `w4a16_prefill.cc` uses AIE2P matrix-multiply instructions;
`w4a16_prefill.py` streams quantized weight and activation tiles through
one compute core per selected NPU column. The default logical shape is
`M=128, K=4096, N=2048`: a batch of 128 token activations and a 2048-channel
slice of a Llama FFN gate or up projection.

This milestone covers prefill only. Shapes with `M=1` are rejected. It does
not yet connect gate/up, local SiLU-and-multiply, and down projection into
one persistent FFN graph, or schedule a corresponding GPU partition. The
historical scalar decode and activation bring-up remain documented in
[README.md](README.md) and [VALIDATION.md](VALIDATION.md).

## Build and run

Use the supplied `ironenv` with MLIR-AIE revision
`7e00b57955e108fe9d8e9419f5828a0c7e650858`. Compilation requires its IRON
Python package, AIE compiler, NumPy, and `ml_dtypes`; hardware execution
also requires `pyxrt` and an accessible NPU2 device. The managed notebook
environment and target-machine distinction are described in
[README.md](README.md#environment).

From `npu/ffn`, start with a small build that exercises multiple token,
output-channel, and K tiles:

```bash
make -f Makefile.prefill M=32 K=256 N=64 cols=1 build_dir=build_prefill_small
python run_w4a16_prefill.py \
  --xclbin build_prefill_small/final.xclbin \
  --insts build_prefill_small/insts.bin \
  -M32 -K256 -N64 -co 1 --cases full \
  --json results/prefill_small.json
```

The default model-shaped shard can then be built and checked separately:

```bash
make -f Makefile.prefill M=128 K=4096 N=2048 cols=4
python run_w4a16_prefill.py \
  --xclbin build_prefill/final.xclbin --insts build_prefill/insts.bin \
  -M128 -K4096 -N2048 -co 4 --cases smoke \
  --json results/prefill_128x4096x2048.json
```

`make -f Makefile.prefill run` compiles and runs the default `basic` checks.
It forwards `M`, `K`, `N`, and `cols` to both compiler and runner, including
when they are overridden. `make -f Makefile.prefill mlir` emits the graph
without running it.

Every build writes `final.xclbin`, `insts.bin`, `final.pdi`, and
`final.xclbin.json` under `build_dir`. The manifest records dimensions,
columns, tile sizes, C++ source hash, intended MLIR-AIE revision, and binary
hashes. The runner checks binary hashes and requested dimensions before
allocating device buffers. It checks columns when `-co` is supplied. Rebuild
when dimensions, source, or toolchain change. Source hashes are also part
of JIT specialization and object names to prevent stale C++ object reuse.

From the repository root, CPU packing and algebra checks run with:

```bash
python -m unittest discover -s npu/ffn -v
```

Hardware measurements are recorded in [PREFILL_VALIDATION.md](PREFILL_VALIDATION.md)
and its linked raw JSON files, identifying the actual machine and artifacts. The
historical measurements in `VALIDATION.md` describe the earlier bring-up;
they do not validate this prefill implementation.

## Logical and device buffer layouts

The logical operation is `C[M,N] = A[M,K] @ W[N,K].T`. Canonical host
weights use the existing `reference.W4A16` format: unsigned int4 packed
output-major as `[N,K/2]`, low nibble for even K, high nibble for odd K,
with scales and zero points `[N,K/128]`. Quantization groups span 128
consecutive K elements. Device packing below is a separate adapter.

The fixed core tile is `16 × 128 × 32`; the matrix instruction operates
on `4 × 8 × 8` microtiles. Define `Mb=M/16`, `Kb=K/128`, and `Nb=N/32`.

| Buffer | Dtype | Compact host layout | Byte size |
| --- | --- | --- | --- |
| A input | BF16 | `[Mb,Kb,2048]` | `2*M*K` |
| W input | uint8 | `[Nb,Kb,2144]` | `(Nb*Kb)*2144` |
| C output | BF16 | `[Mb,Nb,512]` | `2*M*N` |

Each A tile stores `[m_micro=4,k_micro=16,mi=4,ki=8]`. Each output C tile
stores `[m_micro=4,n_micro=4,mi=4,ni=8]`. The host helpers represent BF16
values as uint16 bits for CPU-only testing; the hardware runner views
those bits as `ml_dtypes.bfloat16` without a numerical conversion.

Each W tile contains three consecutive regions:

| Byte offset | Length | Contents |
| --- | --- | --- |
| 0 | 2048 | Int4 microtiles `[k_micro=16,n_micro=4,ki=8,ni=8]`, with adjacent ni values packed low-even/high-odd |
| 2048 | 64 | Little-endian BF16 scales for 32 output channels |
| 2112 | 32 | Unsigned uint8 zero points for those channels, each in `[0,15]` |

The tile's K coordinate selects its quantization group. Both metadata
arrays follow the tile's local N channel order. The layout is not binary
compatible with HeteroMosaic's 4352-byte, 128×64 packed tiles.

Columns own contiguous, equally sized ranges of N tiles. Each worker
consumes tiles in M-block, local-N-block, K-block order. The graph repeats
reads of the compact A buffer across N blocks and columns, and reads of
the compact W buffer across M blocks. It emits one DMA task group per M
block. Each weight tile occurs once in the compiled input BO, but repeated
device reads still consume memory bandwidth. Packing creates a device
layout from the canonical host layout; this is not a claim that the whole
application stores only one representation of every weight.

## Numerical behavior and correctness checks

The core dequantizes `(unsigned_q - zero) * scale` to BF16, then performs
native BF16 matrix multiplication with FP32 accumulation. A local FP32 C
buffer survives all K=128 contributions to an output tile. Only the final
tile is converted to BF16, using round-to-nearest-even. The C++ source
rejects compilation with BF16-to-BFP16 matrix multiplication emulation
enabled.

`prefill_reference.py` models BF16 activation storage, BF16 scales and
dequantized weights, FP32 full-K accumulation, and BF16 output. Different
FP32 accumulation orders can move a result across a BF16 rounding boundary;
the reference therefore does not promise bitwise device agreement.

The runner reuses one set of XRT buffers across independently checked cases:

- `smoke`: random data from a nonzero output-channel slice of a larger weight.
- `basic`: adds changed activations and exact-zero activations.
- `full`: also tests quantized weights equal to their zero points, and a
  nonzero input/K slice from a larger down-projection weight. Two one-hot
  activation cases probe quantized lane order and varying zero-point/scale
  lanes with an exact, zero-tolerance comparison.

After these cases, the runner restores the original random input and
checks every warmup and timing output. Exact-zero reference outputs must
remain exactly zero. Other cases must be finite, satisfy relative L2 error
at most `0.02`, and have maximum absolute error at most
`0.05 + 0.03 * max(abs(reference))` by default. The latter is a tensor-level
bound, not an elementwise relative-error guarantee. JSON records the
configured limits, per-case errors, elementwise-close fraction, artifact
identity, compact buffer sizes, and each measured dispatch time. These
are kernel bring-up tolerances; they do not establish model accuracy.

A sliced down projection produces a BF16 partial result on this kernel.
The FFN CPU partition oracle currently reduces FP32 partials before its
final rounding. Real GPU–NPU reduction must separately validate device
partial rounding, reduction order, and greedy-token agreement.

## Current limits and integration work

M must be a positive multiple of 16, K of 128, and N of 32. The graph accepts
1–8 columns that divide the N tile count, with at most 64 N tiles per column.
Current shape guards limit M to 4096 and K/N to 16384. These are accepted
source dimensions, not a claim that every shape has been compiled or run.
The design uses one compute core per selected column and a fixed tile
shape; it does not yet tune row parallelism or tile sizes.

The core has an 8-KiB BF16 dequantization scratch buffer and a 2-KiB FP32
accumulator. It dequantizes a weight tile again for each M tile. Weights
are not retained across M blocks in on-chip memory, and A is reread for
different N blocks. Profiling must distinguish matrix arithmetic from
dequantization, DMA, and task-group overhead before choosing an FFN ratio.

The standalone runner uploads inputs and synchronizes XRT BOs on each
call. Its timer spans dispatch to device completion, including NPU DMA
and compute, but excludes host BO writes/synchronization, output download,
packing, allocation, compilation, and the CPU reference. Reported GOP/s
uses that timing scope. It is not an FFN, TTFT, or end-to-end latency result.

Next integration steps are persistent gate/up-to-activation-to-down
connections, packed checkpoint loading, shared GPU/NPU buffers and
synchronization, CPU/GPU reduction profiling, and end-to-end correctness
and latency evaluation. This XRT harness does not yet use the inherited
HeteroMosaic DRM/DMA-BUF submission path. Shared physical DRAM alone does
not establish coherent concurrent access or eliminate layout conversions.
