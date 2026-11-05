# Partition experiment support

These source/test utilities support the historical isolated FFN experiments
and the integrated deployment smoke test. Model inference directly calls the
C++ executor; it does not run this Python benchmark framework.

For current setup and model testing, read
[docs/ffn-teammate-testing.md](../../docs/ffn-teammate-testing.md).
The original experiment documentation, historical measurements and rejected
variants remain on [the pinned source revision](https://github.com/glassescrab/HeteroMega/tree/e6ca183c0a78a74496f797b37905f7830e422caa/experiments/ffn_partition).
Earlier result archives are not prerequisites for model deployment.
