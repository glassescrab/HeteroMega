# Native8 split-A and preconverted-B assembly audit

**Code-confirmed from actual compiled objects:** preconverting B removes its
conversion work from the matrix loop, but the split-M32 implementation adds
vector stack transfers around each K128 traversal. These are static findings,
not device-cycle measurements or an explanation assigning a fraction of
measured latency to a particular instruction.

Reproduce the bounded audit with:

```sh
python docs/runs/2026-10-27-native-adaptation/assembly/audit.py
```

The archived `.o` and `.dis` files are sufficient; the script needs only
Python's standard library. [audit.json](audit.json) contains hashes, exact
function sizes, stack operations, loop ranges and opcode counts. Addresses
below are offsets within the named function, because these are relocatable
objects. The candidate SwiGLU and down objects have the same SHA256
`0439fa66588508c3b4e2cd11d42f24e2749f52cc07aad2f041d4365bdbe86872`.

## Matrix loop

| Per K8 steady iteration | Native8 R4 | Split-M32 + preconverted B |
|---|---:|---:|
| Encoded instruction bundles | 23 | 12 |
| Matrix `vmac.f` operations | 4 | 4 |
| BFP operand conversions | 4: two A, two B | 2: A only |
| BFP block pops | 0 | 2 |
| Stack accesses | 0 | 0 |

The control loop is `w4a16_prefill_reuse_accumulate_low` at
`[0x320,0x3c0)`; high is identical. The candidate loops are
`w4a16_prefill_accumulate_pair_m0` at `[0x180,0x1f0)` and
`[0x350,0x3c0)`, with corresponding M1 loops shifted by `0x10`.
The candidate retains A widening/conversion and four live matrix accumulators;
packed B arrives through `vldb.fill.512` and `vldb.pop.576`.

For one **M64/K128/N64** projection tile there are 16 register groups
(`4 M16 × 2 N32 × 2 N16`). Each processes 15 steady K8 iterations and peeled
work for the 16th. Both variants therefore execute 1,024 matrix MAC
instructions. Operand conversions fall from 1,024 to 640: A stays 512; B falls
512→128. The latter 128 occur once during dequantization, through
`vst.push.576.conv.bfp16ebs8.fp32`; low's steady store is at `0x182` and
its peeled final store at `0x1e6`. Each N8 stream uses 15+1 conversions,
over four streams and two N32 halves. BF16 weight dequantization still occurs
before this conversion and original packed W buffers remain unchanged.

The corresponding **steady matrix-loop only** bundle totals are 5,520→2,880.
This excludes dequantization, preparation, loop boundaries, partial-output
I/O, FIFO waits and transfers. Variable bundle lengths and hardware stalls
prevent interpreting either count as cycles or a predicted speedup.

## Preparation cost and storage

The candidate has eight 64-byte vector stores and eight reloads before each
register-group K loop. M0's first preparation ranges from `0x110` to `0x170`;
the second from `0x2e0` to `0x340`. They are compiler-generated stack
round trips, outside the steady loop. Their derived traffic is 16 KiB per
M64/K128/N64 tile. The control has no vector stack transfers. Leaf stack
frames increase 64→576 bytes; dequantize-pair has no frame. The graph reserves
4 KiB, but this object-only audit does not prove complete linked call-chain
stack safety.

Logical B scratch writes fall 16→9 KiB and reads 64→36 KiB per tile. These are
payload sizes, not measured memory transactions: packed-stream refill and
flush behavior can add transactions. The additional stack traffic partially
offsets this reduction.

The relevant projection exports occupy 2,560→3,504 encoded bytes
(640→876 32-bit storage-word equivalents). The entire objects contain 2,912
and 6,096 executable bytes, respectively; the candidate includes unused legacy
exports. Neither count is a full linked-core program size, and a storage word
is not an instruction or a cycle.

This audit covers v9 split-M32 plus preconverted B. The subsequent optional
A-preconversion experiment requires its own compiled evidence.
