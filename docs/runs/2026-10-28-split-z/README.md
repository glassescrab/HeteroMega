# Role-specialized split-Z FFN: rejected

**Tried, October 28, 2026:** the role-specialized design was implemented and
measured. The NPU computes gate/up + SiLU for channels `[0, 8192)`; the GPU
computes gate/up for `[8192, 14336)`, assembles the full Z with the NPU prefix,
and runs the **full** down projection. Both the PyTorch BF16 and packed-W4A16
GPU suffix variants are slower than the selected merged P6400 channel split.

This is an isolated synthetic FFN experiment, M512/H4096/I14336, 5 samples per
mode after 2 warmups. The selected merged P6400 reference is 13.867 ms
concurrent. Split-Z output and NPU-Z checks pass the original tolerance, but the
latency loses.

## Measured

| GPU split variant | GPU-only control | Concurrent split FFN | Serial GPU+NPU | NPU gate/up branch | Output stage |
| --- | ---: | ---: | ---: | ---: | ---: |
| PyTorch BF16 | 22.090 | **19.191** | 23.944 | 11.591 | 6.262 |
| Packed W4A16 | 22.392 | **21.588** | 27.291 | 12.531 | 8.049 |
| Selected merged P6400 (reference) | 22.458 | **13.867** | 26.391 | 12.47–12.72 (full gate/up+down) | 0.74 |

Both split variants are 38–56% slower than the selected P6400 channel split.
The split output is `within_tolerance` (0 outside-tolerance checks) for both
variants; this is a correctness improvement over the report-policy merged path,
but it does not compensate for the latency loss.

## Why it loses

- The NPU gate/up-only branch at P8192 is **11.6–12.5 ms**; it is not shorter
  than the merged P6400 branch that also executes down (12.47–12.72 ms).
- Moving the down to the GPU replaces a suffix down (K=6400) with a **full down
  (K=14336)**. The extra GPU work is larger than the NPU down work it removes.
- Under concurrent NPU execution, the full-down output stage is 6.3–8.0 ms; the
  GPU does not recover the expected isolated-kernel gain.

The split-Z design is therefore rejected for this platform. The P6400 channel
split remains selected. This result also bounds the expected value of further
role specialization without a substantially faster GPU full-down kernel or a
larger allowed NPU gate/up share.

## Evidence

- [PyTorch BF16 split report](torch_bf16_p8192.json)
- [Packed W4A16 split report](packed_p8192.json)
- [Selected merged P6400 reference](merged_p6400_reference.json)
- Implementation: `npu/ffn/w4a16_merged_gate_up.py`,
  `experiments/ffn_partition/merged_npu.py` (`MergedGateUpNpuFFN`),
  `experiments/ffn_partition/torch_gpu.py`
  (`TorchBF16SplitDownBranch`, `PackedSplitDownBranch`),
  `experiments/ffn_partition/run_split_z.py`, and the new packed
  `linear`/`silu_mul` bindings.
- The merged/full and GPU-suffix experiments remain in their separate run
  directories. No production default changed; split-Z is an explicit CLI path.
