# Combined gate/up projection

**Implemented and hardware-validated** at `M128/H128/P128` and
`M128/H128/P384`, and in the `M512/H4096/I14336` partition sweep covering
12 NPU shares from P128 through P7168. Measurements and completed independent
confirmation runs are in
[FUSION_RESULTS.md](../../experiments/ffn_partition/FUSION_RESULTS.md).
Validation at these shapes does not establish acceleration at other shapes.
`w4a16_gate_up.py` is an opt-in array8 graph for one wider projection:

```text
[G | U] = X @ [Wgate; Wup].T
```

For an NPU intermediate-channel partition of width `P`, the graph computes
`M × K` by `K × 2P`. Packed gate weights precede packed up weights in one
read-only weight buffer. Columns 0–3 compute gate, columns 4–7 compute up;
each column uses all four compute rows, for 32 active workers. Every supported
`P` is divisible by 128, so the boundary between the projections always lies
between columns 3 and 4, including `P=128`, `384`, and `640`.

This is horizontal projection fusion. It uses the existing
`w4a16_prefill_reuse.cc` native BF16 multiply / FP32 accumulation kernel without
arithmetic changes. SiLU/multiply and down projection remain separate
dispatches. The original array8 graph and planner remain unchanged.

## Buffer and build contract

Runtime arguments, after the standard opcode/instruction arguments:

| Argument | Elements and host representation | Layout |
| --- | --- | --- |
| Activation | `M*K`, BF16 represented as `uint16` | `A[M/16,K/128,2048]` |
| Combined weight | `(2P/32)*(K/128)*2144`, `uint8` | `W[2P/32,K/128,2144]`, packed gate then packed up |
| Gate output | `M*P`, BF16 represented as `uint16` | `C[M/16,P/32,512]` |
| Up output | `M*P`, BF16 represented as `uint16` | `C[M/16,P/32,512]` |

The outputs are separate compact BOs. Output DMA performs the appropriate
scatter into each BO; no wide-output readback and CPU split/compaction is
required. Gate/up have identical physical order and can feed the current
elementwise SiLU/multiply kernel directly. They still use host staging in
the experiment adapter; separate BOs do not imply on-chip residency or
GPU/XRT zero-copy.

Build from `npu/ffn`, using the pinned IRON Python:

```bash
python w4a16_gate_up.py -M 512 -K 4096 -P 512 -co 8 \
  --max-reuse 2 \
  --xclbin-path build_gate_up/final.xclbin \
  --insts-path build_gate_up/insts.bin \
  --pdi-path build_gate_up/final.pdi
```

Create the output directory before invoking this command. The CLI also
supports `--emit-mlir`. The graph requires `M` and `K` divisible by 128,
`128 <= M <= 4096`, `128 <= K <= 16384`, and `128 <= P <= 8192` divisible
by 128. The `P` limit follows the original total-`N<=16384` and at-most-64
local-N-tile bounds. Default M-tile reuse is two; reuse four remains an
explicit, hardware-unvalidated option.

The manifest has `kind=w4a16_gate_up_bf16`, `design=array8_gate_up`, `n=2P`,
`channels=P`, `output_count=2`, and `output_order=[gate,up]`. It binds the
unchanged arithmetic source, original schedule, new gate/up schedule and
compiled binaries by SHA-256. The experiment's build contract must also
bind the graph source itself.

## Expected changes, not measured speedup

- The NPU FFN branch needs three dispatches rather than four: combined
  gate/up, SiLU/multiply, down. One projection context and one duplicate host
  activation upload are removed. At `M512/K4096`, that upload is 4 MiB.
- Both sets of matrix products remain necessary. Weight bytes, output bytes
  and total arithmetic do not halve merely because there is one launch.
- For `P` divisible by 256, including `P512`, the graph's local-N replay
  leaves total logical activation DMA unchanged from two separate array8
  projections. No new paired-accumulator reuse is introduced.
- For `P=128 mod 256`, the original projection divides token rows between
  two four-column groups. The wider graph can multicast A across all eight
  columns, halving its total logical A DMA versus the two original
  projections. At `M128`, this also enables reuse two instead of reuse one.
  Results at these shapes are therefore not a launch-only ablation.

The CPU tests in `test_prefill_gate_up_schedule.py` check ownership and exact
nonoverlapping separate-output addresses, including odd local channel-tile
counts, plus packed quantization metadata across the gate/up boundary. Those
checks are separate from the recorded hardware validation.

The [exact device comparison](../../experiments/ffn_partition/results/gate_up_sweep/gate_up_exact_m512.json)
passes 160 checks at `M512/H4096/P128,384,512,896`: gate, up and complete NPU
branch BF16 outputs match the unfused variant bit-for-bit for two different
random inputs, zero and a repeated input. CPU-reference error also passes the
unchanged tolerance. Performance depends on allocation and overlap; the
independent sweeps identify a useful P768–P896 region on this workload, not a
universal optimal ratio or evidence that every fixed partition improves.
