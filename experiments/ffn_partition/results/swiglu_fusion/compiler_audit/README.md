# Compiled SwiGLU topology audit

**Compiled-artifact confirmed:** the retained `M128/K128/P128`, reuse-2
build implements the intended adjacent shared-memory handoff. This audit is
separate from runtime correctness and timing evidence.

- All 32 compute cores contain the existing projection entry points; only the
  16 odd-column cores call and link `silu_mul_bf16`.
- Each of the 16 gate/up pairs has one two-deep gate pool: two 2,048-byte
  buffers allocated on the even producer tile. Its paired odd core directly
  references those buffers in west-neighbor memory. There are no duplicated
  consumer pools, gate DMA descriptors, or compute-to-compute stream routes.
- Every compute core receives A on S2MM0 and packed W on S2MM1. Odd cores
  drain Z on MM2S0; even cores have no output DMA. Four output shim streams
  drain compact Z from columns 1, 3, 5, and 7.

| Local data SRAM | Gate core | Up + pointwise core |
|---|---:|---:|
| Graph buffers | 37,056 B | 39,104 B |
| Reserved stack | 2,048 B | 2,048 B |
| Linked static data (sigmoid LUT) | 0 B | 4,096 B |
| Total static high water | 39,104 B | 45,248 B |
| Space remaining in 64 KiB | 26,432 B | 20,288 B |

All 32 linker scripts and ELF section tables agree with the lowered buffer
allocation and fit the local SRAM and program-memory regions. The up-core
figure is lower than the planner's conservative 49,344-byte bound because the
shared gate pool is allocated only on its producer. Static allocation plus a
reserved stack is **not** a runtime stack high-water measurement or a profile
of bank contention. The retained `.stack_sizes` section does not cover the
complete linked call graph.

[audit.json](audit.json) records the per-core checks, memory intervals, all six
source hashes, and hashes of the exact input MLIR, lowered MLIR, 32 linker
scripts, 32 ELFs, manifest, and binaries. [evidence_excerpts.txt](evidence_excerpts.txt)
retains representative text with original line numbers and file hashes; no
ELF, xclbin, PDI, or instruction binary is copied here. The original `compile.log`
is empty, so the audit relies on compiler outputs rather than log messages.

To reproduce from the downloaded compiler bundle, run from the repository root:

```bash
python experiments/ffn_partition/results/swiglu_fusion/compiler_audit/audit_compiler.py \
  /path/to/build_swiglu_array8_m128_k128_p128_6975d0ccfe57
```

These exact allocation findings cover this small compiled shape only. Other
shapes use the same tile sizes at reuse 2, but their completed compilation,
correctness, and performance require their own evidence.
