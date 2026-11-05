"""CPU checks that GPU shards and direct NPU buffers share quantized weights.

These checks exercise original packed-byte interoperability and complementary
channel ownership. They do not model BFP16 MMUL or establish device accuracy.
"""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from contract import W4A16, bf16, random_weights, split_weights
from gpu_backend import pack_heteromosaic_weights
import upstream_npu
from experiments.ffn_partition.check_upstream import prepare_weights
from reference import pack_int4
from upstream_weights import UpstreamWeightBuffer


def _decode_slice(weight, k_start, n_start, k, n):
    """Decode original bytes using scalar-coordinate addresses, not reshapes.

    Enumerate full-source stripe ordinals independently of weight_tile_offset.
    Returned logical weights have the canonical [N,K] orientation.
    """
    tile_ids = np.empty((weight.k // 128, weight.n // 64), np.int64)
    ordinal = 0
    for stripe in range(8):
        for nt in range(stripe, weight.n // 64, 8):
            for kg in range(weight.k // 128):
                tile_ids[kg, nt] = ordinal
                ordinal += 1
    ns = np.arange(n_start, n_start + n)[:, None]
    ks = np.arange(k_start, k_start + k)[None, :]
    nl, kl = ns % 64, ks % 128
    base = tile_ids[ks // 128, ns // 64] * 4352
    # One byte packs adjacent N lanes, unlike canonical adjacent-K nibbles.
    q_address = base + ((kl // 8) * 8 + nl // 8) * 32 + (kl % 8) * 4 + (nl % 8) // 2
    q = (weight.data[q_address] >> (4 * (nl % 2))) & 15
    scale_address = base + 4096 + nl * 2
    scale_bits = (weight.data[scale_address].astype(np.uint32)
                  | (weight.data[scale_address + 1].astype(np.uint32) << 8))
    scale = (scale_bits << 16).view(np.float32)
    zero_address = base + 4224 + (nl // 8) * 16 + nl % 8
    zeros = weight.data[zero_address]
    np.testing.assert_array_equal(weight.data[zero_address + 8], zeros)
    return bf16((q.astype(np.float32) - zeros) * scale)


class UpstreamGpuContractTests(unittest.TestCase):
    def test_original_gpu_bytes_equal_independent_upstream_fixtures(self):
        # Unequal modulo-eight stripe lengths and multiple K groups expose
        # full-geometry/stripe mistakes, q nibble swaps and zero duplication.
        for k, n in ((128, 128), (384, 640), (256, 1152)):
            with self.subTest(k=k, n=n):
                fixture = prepare_weights(k, n, seed=k + n)
                canonical = W4A16(pack_int4(fixture.q.T), fixture.scales.T,
                                  fixture.zeros.T, 128)
                original = pack_heteromosaic_weights(canonical)
                np.testing.assert_array_equal(original, fixture.weight.data)
                wrapped = UpstreamWeightBuffer(original, k, n)
                self.assertIs(wrapped.data, original)
                np.testing.assert_array_equal(_decode_slice(wrapped, 0, 0, k, n),
                                              canonical.dequantize(True))

    def test_npu_full_buffer_prefix_and_gpu_suffix_are_exact_complements(self):
        weights = random_weights(384, 1152, seed=271027)
        full = {name: UpstreamWeightBuffer(pack_heteromosaic_weights(getattr(weights, name)),
                         getattr(weights, name).shape[1], getattr(weights, name).shape[0])
                for name in ('gate', 'up', 'down')}
        originals = {name: value.data.copy() for name, value in full.items()}
        for channels in (128, 512, 1024):
            with self.subTest(channels=channels):
                branches = split_weights(weights, channels)
                for name in ('gate', 'up', 'down'):
                    source = getattr(weights, name)
                    npu = getattr(branches['npu'], name)
                    gpu = getattr(branches['gpu'], name)
                    # Both canonical slices retain source q/metadata views;
                    # no requantization or renormalized scales is permitted.
                    for field in ('packed', 'scales', 'zeros'):
                        self.assertTrue(np.shares_memory(getattr(npu, field), getattr(source, field)))
                        self.assertTrue(np.shares_memory(getattr(gpu, field), getattr(source, field)))
                    npu_slice = ((0, 0, weights.hidden, channels) if name != 'down'
                                 else (0, 0, channels, weights.hidden))
                    actual_npu = _decode_slice(full[name], *npu_slice)
                    gpu_bytes = pack_heteromosaic_weights(gpu)
                    actual_gpu = _decode_slice(UpstreamWeightBuffer(gpu_bytes, gpu.shape[1], gpu.shape[0]),
                                                0, 0, gpu.shape[1], gpu.shape[0])
                    np.testing.assert_array_equal(actual_npu, npu.dequantize(True))
                    np.testing.assert_array_equal(actual_gpu, gpu.dequantize(True))
                    combined = np.concatenate((actual_npu, actual_gpu), axis=0 if name != 'down' else 1)
                    np.testing.assert_array_equal(combined, source.dequantize(True))
                    np.testing.assert_array_equal(full[name].data, originals[name])
                    # Reinterpreting a full source BO as a partition shape
                    # must fail instead of silently changing stripe strides.
                    with self.assertRaisesRegex(ValueError, 'full source K/N'):
                        UpstreamWeightBuffer(full[name].data, npu.shape[1], npu.shape[0])
        self.assertIsNone(split_weights(weights, 0)['npu'])
        self.assertIsNone(split_weights(weights, weights.intermediate)['gpu'])

    def test_direct_adapter_uploads_full_original_arrays_without_repacking(self):
        weights = random_weights(384, 1152, seed=271028)
        originals = tuple(UpstreamWeightBuffer(pack_heteromosaic_weights(w), w.shape[1], w.shape[0])
                          for w in (weights.gate, weights.up, weights.down))
        for weight in originals:
            weight.data.flags.writeable = False

        class RecordingRunner:
            def __init__(self, *args):
                self.writes = {}

            def write_input(self, index, value):
                self.writes[index] = value

        with tempfile.TemporaryDirectory() as root:
            # Only artifact I/O and hardware construction are replaced. The
            # real descriptor/geometry validation and weight upload path run.
            with patch.object(upstream_npu, '_load_artifact',
                              return_value={'xclbin': 'cpu-mock', 'insts': 'cpu-mock'}), \
                    patch.object(upstream_npu, 'PersistentXrtRunner', RecordingRunner), \
                    patch('gpu_backend.pack_heteromosaic_weights', side_effect=AssertionError('NPU repack')), \
                    patch('npu_backend.pack_weights', side_effect=AssertionError('compact NPU repack')):
                for channels in (128, 512, 1024):
                    branch = upstream_npu.UpstreamNpuFFN(512, 384, channels, *originals, Path(root),
                        channel_start=0, arithmetic='bfp16', swiglu_input_layout='row_major',
                        output_layout='down_a', down_reuse=4, down_activation_fifo_depth=1,
                        vector_zero=True, copy_output_bits=False)
                    self.assertIs(branch.swiglu.writes[1], originals[0].data)
                    self.assertIs(branch.swiglu.writes[2], originals[1].data)
                    self.assertIs(branch.down.writes[1], originals[2].data)
                    self.assertEqual(branch.metadata['full_intermediate'], 1152)
                    self.assertFalse(branch.metadata['weight_repacking'])
                    specs = upstream_npu._ffn_specs(512, 384, channels, *originals, root,
                        arithmetic='bfp16', channel_start=0)
                    gate, down = specs['swiglu']['expected'], specs['down']['expected']
                    self.assertEqual((gate['weight_k'], gate['weight_n'], gate['k'], gate['n']),
                                     (384, 1152, 384, channels))
                    self.assertEqual((down['weight_k'], down['weight_n'], down['k'], down['n']),
                                     (1152, 384, channels, 384))
                    self.assertEqual((gate['n_start'], down['k_start']), (0, 0))


if __name__ == '__main__':
    unittest.main()
