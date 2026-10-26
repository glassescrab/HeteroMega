"""Independent logical DMA address checks for direct down-A SwiGLU output."""

import unittest

import numpy as np

from upstream_output import upstream_down_activation_tap
from upstream_schedule import plan_upstream


def _layouts(m, channels):
    # Unique logical element IDs reveal every transpose, including M/channel
    # ownership boundaries, without introducing any floating-point arithmetic.
    logical = np.arange(m * channels, dtype=np.int64).reshape(m, channels)
    native_c = logical.reshape(m // 16, 4, 4, channels // 32, 4, 8)
    native_c = native_c.transpose(0, 3, 1, 4, 2, 5).copy().reshape(-1)
    down_a = logical.reshape(m // 16, 4, 4, channels // 128, 16, 8)
    down_a = down_a.transpose(0, 3, 1, 4, 2, 5).copy().reshape(-1)
    return native_c, down_a


class UpstreamOutputTests(unittest.TestCase):
    def test_all_outputs_land_once_in_down_activation_order(self):
        for m, channels in ((128, 128), (256, 256), (128, 384),
                            (512, 512), (128, 1152), (512, 2560)):
            for start in (0, 32, 64, 96, 128, 288):
                for reuse in (1, 2):
                    with self.subTest(m=m, channels=channels, start=start, reuse=reuse):
                        direct = plan_upstream(m, 256, channels, mode='swiglu',
                            weight_k=512, weight_n=((channels + start + 63) // 64 + 8) * 64,
                            k_start=128, n_start=start, max_reuse=reuse)
                        original, expected = _layouts(m, channels)
                        actual = np.full(expected.size, -1, np.int64)
                        visits = np.zeros(expected.size, np.uint8)
                        tasks = 0
                        for col in (1, 3, 5, 7):
                            for group in range(direct.base.groups_per_column):
                                for segment in range(direct.segment_count):
                                    source = direct.output_tap(col, group, segment)
                                    target = upstream_down_activation_tap(direct, col, group, segment)
                                    stream = original[source.indices()]
                                    addresses = target.indices()
                                    self.assertEqual(stream.size, addresses.size)
                                    self.assertEqual(target.buffer_elements, m * channels)
                                    self.assertFalse(np.any(visits[addresses]))
                                    actual[addresses] = stream
                                    visits[addresses] += 1
                                    tasks += 1
                        np.testing.assert_array_equal(actual, expected)
                        np.testing.assert_array_equal(visits, np.ones_like(visits))
                        self.assertEqual(tasks, 4 * direct.base.groups_per_column * direct.segment_count)

    def test_cross_k128_segment_uses_one_dma_with_longer_n_stride(self):
        direct = plan_upstream(128, 256, 1152, mode='swiglu', weight_n=1280, n_start=32)
        taps = [upstream_down_activation_tap(direct, col, 0, segment)
                for col in (1, 3, 5, 7) for segment in range(direct.segment_count)]
        self.assertTrue(any(tap.sizes[0] == 2 and tap.strides[0] == 1664 for tap in taps))
        self.assertTrue(any(tap.sizes[0] == 1 for tap in taps))
        self.assertTrue(all(len(tap.sizes) == len(tap.strides) == 4 for tap in taps))
        self.assertTrue(all(max(tap.sizes) <= 512 for tap in taps))

    def test_permutation_preserves_arbitrary_bf16_bits(self):
        m, channels = 128, 512
        direct = plan_upstream(m, 128, channels, mode='swiglu')
        native_ids, expected_ids = _layouts(m, channels)
        bits = np.arange(65536, dtype=np.uint16)
        original = bits[native_ids]
        actual = np.empty_like(original)
        for col in (1, 3, 5, 7):
            for group in range(direct.base.groups_per_column):
                for segment in range(direct.segment_count):
                    actual[upstream_down_activation_tap(direct, col, group, segment).indices()] = (
                        original[direct.output_tap(col, group, segment).indices()])
        np.testing.assert_array_equal(actual, bits[expected_ids])

    def test_invalid_ownership_and_indices_rejected(self):
        direct = plan_upstream(128, 128, 128, mode='swiglu')
        for col in (-1, 0, 2, 4, 6, 8, True, 1.0):
            with self.subTest(col=col), self.assertRaises(ValueError):
                upstream_down_activation_tap(direct, col, 0, 0)
        for segment in (-1, direct.segment_count, True, 0.0):
            with self.subTest(segment=segment), self.assertRaises(ValueError):
                upstream_down_activation_tap(direct, 1, 0, segment)
        for group in (-1, direct.base.groups_per_column, True):
            with self.subTest(group=group), self.assertRaises(ValueError):
                upstream_down_activation_tap(direct, 1, group, 0)
        with self.assertRaisesRegex(ValueError, 'only supported for SwiGLU'):
            upstream_down_activation_tap(plan_upstream(128, 128, 128), 1, 0, 0)


if __name__ == '__main__':
    unittest.main()
