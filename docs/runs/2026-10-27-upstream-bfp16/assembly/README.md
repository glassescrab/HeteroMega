# Direct-upstream BFP16 assembly audit

**Measured:** the first SwiGLU launch's median host launch-plus-wait interval
fell **11.729 → 6.512 ms** in ABBA and **11.795 → 6.593 ms** in BAAB
(100 samples per arithmetic mode in each order; 44.5% and 44.1% reductions).
This launch includes gate/up projections, DMA/locks, gate transfer and
SiLU/multiply. These are not device-only matrix timings. See the
[experiment evidence](../README.md) for numerical results and complete runs.

**Compiled-artifact-confirmed:** the candidate uses
`vconv.bfp16ebs8.fp32` to construct BFP16 operands in `ex` registers, then
`vmac.f` with those operands. Each 8×8×8 API MAC lowers to one such matrix
instruction. The native 4×8×8 API MAC lowers to eight `vmac.f` instructions.

| Projection work | Native BF16 | BFP16 |
|---|---:|---:|
| Matrix instructions per steady K8 iteration | 32 | 4 |
| Decoded bundles per steady K8 iteration | 36 | 20 |
| Register-block groups per K128/N32 call, reuse 2 | 8 | 4 |
| Matrix instructions per complete call | 4,096 | 256 |
| Steady MMUL bundles per call | 4,320 | 1,200 |
| BF16 scratch written/read per call | 8/32 KiB | 8/16 KiB |

The native count is `(19 + 15×32 + 13) × 8 = 4,096`; the BFP16 count is
`(0 + 15×4 + 4) × 4 = 256`. The terms account for software-pipeline
prologue, repeated body and epilogue. Steady bundle counts are only
`36×15×8` versus `20×15×4`; they exclude prologues, epilogues,
outer-loop control and all dequantization/graph work. **Bundles are not
measured cycles.** The BFP16 body also has four operand conversions, two
helper multiplies and gather/shuffle work per iteration.

The full first launch has 81,920 half-calls: 335,544,320 native versus
20,971,520 BFP16 matrix instructions across 32 parallel workers. Fewer
matrix instructions and fewer local scratch reads support the observed
improvement. They do not attribute measured time to individual phases or
predict a 16× latency reduction. Dequantization still precedes MMUL, and
its shared inner loop remains 13 bundles repeated 14 times per N8 block,
plus preparation and tail work.

**The weight ABI is unchanged:** both profiles consume the same original
4,352-byte packed W4 payloads and use the same BF16 dequantization routine.
BFP16 conversion occurs on core operands. Local A/C gather/scatter preserves
the external 4×8 layout and FP32 K-group partials; it is not host weight
repacking. BFP16 arithmetic is not numerically identical to native BF16.

The audit checks all **128 ELFs** for nonoverlapping stack, assigned buffers
and static data within 64 KiB, and program size within 128 KiB. Eight
representative disassemblies byte-match their ELFs. Neither arithmetic mode
spills accumulators in the MMUL loop. Observed nested stack use is 256 B for
projection calls and 704 B through the separate SiLU call, within the
2 KiB native and 4 KiB BFP16 reservations. Maximum local allocation is
59,904 B native / 61,952 B BFP16, both in down workers.

[audit.json](audit.json) records hashes, exact instruction addresses/lines,
loop bodies, frame evidence and every ELF memory region. Reproduce after
extracting the raw evidence archive, with Python and `llvm-readelf` installed:

```bash
python docs/runs/2026-10-27-upstream-bfp16/assembly/audit.py \
  --evidence-root /tmp/upstream-bfp16-evidence-20261027 \
  --output docs/runs/2026-10-27-upstream-bfp16/assembly/audit.json
```

The script only reads saved artifacts. It neither compiles nor runs a device.
