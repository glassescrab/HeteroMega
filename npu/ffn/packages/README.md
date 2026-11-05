# Reproducible NPU kernel packages

## Two-launch BFP16, M512/H4096/P2560

[bfp16_p2560](bfp16_p2560/README.md) preserves all 22 files from
[PR #3](https://github.com/glassescrab/HeteroMega/pull/3) at commit
`fd67fbf40e9e2e1d06b58d365e4657e61aed050f`, byte for byte. This includes the
matching source closure, two XCLBIN/instruction pairs, generated MLIR, manifests,
licenses and the original 21-entry `SHA256SUMS`.

**Code-confirmed:** this package uses the original 4,352-byte W4A16 tiles,
eight columns/32 workers, BFP16 MMUL with BF16 I/O and FP32 K-group partials.
It runs SwiGLU and down in two separate launches. Its P2560 activation ABI and
arithmetic differ from the current single-dispatch model path.

The package README records the October 27 hardware measurements and their
limits. It is an immutable historical document; statements about integration
status describe that package at that date. No new device run was performed
while resolving the PR's conflicts with newer `main` sources.

Verify and rebuild from the package directory so its flat Python imports use
the matching helper files:

```bash
cd npu/ffn/packages/bfp16_p2560
sha256sum -c SHA256SUMS
# In the pinned MLIR-AIE environment, use this directory's README commands.
```

Do not substitute live `npu/ffn` helper modules into this snapshot or use these
two-launch binaries with the merged deployment manifest. For the active model
integration, follow [GPU + NPU FFN testing](../../../docs/ffn-teammate-testing.md).
