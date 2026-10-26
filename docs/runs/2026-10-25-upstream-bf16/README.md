# Native BF16 / direct upstream-weight hardware validation

Measured 2026-10-25 on the AUP HX370 NPU using MLIR-AIE
`7e00b57955e108fe9d8e9419f5828a0c7e650858` in the isolated overlay
`/notebooks/HeteroMega-upstream-bf16-20261025`. No host driver/kernel changes.
These are synthetic NPU correctness checks; power/latency benchmarking and
model accuracy are not established by these runs.

The user selected native BF16 and direct acceptance of glassescrab's original
striped K128/N64/4352-byte weights. All test fixtures were generated directly
in that format, without conversion through the compact N32 packer. Fixed
weights remain byte-identical after execution. The complete FFN adapter uploads
them once; the activation conversion between SwiGLU and down remains.

| Report | Cases | Completed NPU dispatches | Largest relative L2 |
|---|---:|---:|---:|
| [smoke.json](smoke.json) | 5 | 24 | 0.00400048 |
| [model_p2560.json](model_p2560.json) | 1 | 8 | 0.00375981 |
| [odd_partition.json](odd_partition.json) | 1 | 8 | 0.00380069 |

Every case runs signed A, changed signed B, exact zero, then repeated A.
All original numerical bounds (`rtol=0.03`, `atol=0.05`, relative L2≤0.02),
finite output, exact-zero, bit-identical repeat and changed-input checks pass.
The largest absolute error across reports is 0.0009765625. Successful XRT
completion is checked before output validation; no CPU compute fallback exists.

Smoke covers nonzero K128/N32 offsets into full K512/N1024 buffers, paired
N64 halves, narrow N128, fused SwiGLU and a complete M128/H512/I1024/P256 FFN.
The model-shaped FFN is M512/H4096/I14336/P2560. The uneven case is
M128/H512/I2048/P1152 with channel start128, exercising partial tiles at column
boundaries. These tests do not use pretrained Llama weights.

## Reproduce

From the isolated overlay with the configured IRON Python and pyxrt:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.check_upstream \
  --output results/smoke.json --artifact-root artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.check_upstream \
  --suite model --output results/model_p2560.json --artifact-root artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m experiments.ffn_partition.check_upstream \
  --suite model --m 128 --hidden 512 --intermediate 2048 --channels 1152 \
  --channel-start 128 --output results/odd_partition.json --artifact-root artifacts \
  --iron-python /home/mliraie/mlir-aie/ironenv/bin/python
```

## Evidence identity

[evidence.tar.gz](evidence.tar.gz) contains the reports, source snapshot,
build contracts/logs, selected SwiGLU/down XCLBINs and instructions, and generated
MLIR. Archive SHA256:

```text
723c7439254b8ee67f4b7821421f93fa9d330430c3051cd6de3c39ee8d2d4d61
```

All source/dependency and selected binary hashes match the manifests and
model report. Both graphs contain 32 cores on eight columns with 2 KiB stacks;
projection calls link the native BF16 low/high kernel. The final package keeps
these binaries unchanged and only strips trailing whitespace from MLIR exports.
Old BFP16/compact artifacts remain in Git history and earlier evidence archives.

The graph introduces per-segment runtime barriers. Retune and measure the
complete GPU+NPU FFN before comparing its latency to earlier graphs; previous
performance figures cannot be assigned to this implementation.
