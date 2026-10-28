"""Independent address checks for row-major input DMA and native core A tiles."""

import itertools
import unittest

import numpy as np

from upstream_schedule import plan_upstream, validate_input_layout


def _stream_permutation(dims):
    return np.array([sum(index * stride for index, (_, stride) in zip(indices, dims))
                     for indices in itertools.product(*(range(size) for size, _ in dims))])


def _compact_host(x, native8=False):
    m, k = x.shape
    mr = 8 if native8 else 4
    return x.reshape(m // 16, 16 // mr, mr, k // 128, 16, 8).transpose(0, 3, 1, 4, 2, 5).reshape(-1)


class UpstreamInputTests(unittest.TestCase):
    def _check_streams(self, direct, x, native8=False):
        plan = direct.base
        mr = 8 if native8 else 4
        expected_indices, observed_indices = [], []
        perms = {layout: _stream_permutation(direct.activation_dims_to_stream(layout, native8))
                 for layout in ('compact', 'row_major')}
        for permutation in perms.values():
            np.testing.assert_array_equal(np.sort(permutation), np.arange(plan.m_reuse * 2048))
        compact = _compact_host(x, native8)
        addresses = np.arange(x.size).reshape(x.shape)
        for lane in range(plan.m_column_groups * 4):
            worker = plan.worker((lane // 4) * plan.n_columns, lane % 4)
            for group, m_tiles in enumerate(worker.m_groups):
                # Independently build native [R,mb4,kb16,mr4,kr8] objects
                # from logical matrix rows, once for every K128 group.
                rows = [row for mt in m_tiles for row in range(mt * 16, (mt + 1) * 16)]
                expected = np.concatenate([
                    x[rows, kg * 128:(kg + 1) * 128]
                    .reshape(plan.m_reuse, 16 // mr, mr, 16, 8).transpose(0, 1, 3, 2, 4).reshape(-1)
                    for kg in range(plan.kb)])
                for layout, host in (('compact', compact), ('row_major', x.reshape(-1))):
                    tap = direct.activation_tap(lane, group, layout)
                    stream = host[tap.indices()].reshape(plan.kb, plan.m_reuse * 2048)
                    native = stream[:, perms[layout]].reshape(-1)
                    np.testing.assert_array_equal(native, expected)
                observed_indices.extend(direct.activation_tap(lane, group, 'row_major').indices())
                expected_indices.extend(addresses[rows].reshape(-1))
        # Count a single N64 replay, across all M ownership groups/rows.
        # No logical input element is omitted, duplicated or assigned twice.
        np.testing.assert_array_equal(np.sort(observed_indices), np.arange(x.size))
        np.testing.assert_array_equal(np.sort(expected_indices), np.arange(x.size))

    def test_row_major_shim_and_memtile_match_native_a_for_all_worker_groups(self):
        cases = [
            ('swiglu', 512, 4096, 2560, 2),
            ('swiglu', 512, 4096, 2560, 4),
            ('swiglu', 128, 256, 1152, 1),
            ('swiglu', 512, 128, 128, 2),
            ('projection', 512, 2560, 4096, 4),
            ('projection', 512, 128, 128, 4),
            ('projection', 128, 256, 128, 2),
            ('projection', 128, 512, 1152, 4),
        ]
        for mode, m, k, n, reuse in cases:
            with self.subTest(mode=mode, m=m, k=k, n=n, reuse=reuse):
                # Weight slices are deliberately offset: input row strides
                # use logical K, independently of the original full weight K.
                direct = plan_upstream(m, k, n, mode=mode, max_reuse=reuse,
                                       weight_k=k + 256, weight_n=n + 128,
                                       k_start=128, n_start=32)
                for native8 in (False, True):
                    with self.subTest(native8=native8):
                        self._check_streams(direct, np.arange(m * k, dtype=np.uint32).reshape(m, k), native8)

    def test_permutation_preserves_all_65536_bf16_bit_patterns(self):
        direct = plan_upstream(512, 128, 128, max_reuse=4)
        for native8 in (False, True):
            with self.subTest(native8=native8):
                self._check_streams(direct, np.arange(65536, dtype=np.uint16).reshape(512, 128), native8)

    def test_compact_default_and_invalid_layouts(self):
        direct = plan_upstream(512, 4096, 2560, mode='swiglu')
        self.assertEqual(direct.activation_dims_to_stream(), direct.base.activation_dims_to_stream)
        self.assertEqual(direct.activation_tap(0, 0), direct.activation_tap(0, 0, 'compact'))
        for layout in ('compact', 'row_major'):
            self.assertEqual(validate_input_layout(layout), layout)
        for bad in ('rowmajor', 'down_a', '', None, 0, True):
            with self.subTest(layout=bad), self.assertRaises(ValueError):
                direct.activation_tap(0, 0, bad)
            with self.subTest(layout=bad), self.assertRaises(ValueError):
                direct.activation_dims_to_stream(bad)

    def test_largest_supported_geometry_has_bounded_dma_dimensions(self):
        direct = plan_upstream(4096, 16384, 16384, max_reuse=4)
        dims = direct.activation_dims_to_stream('row_major')
        self.assertEqual(len(dims), 4)
        self.assertTrue(all(1 <= size <= 512 for size, _ in dims))
        for lane in range(4):
            tap = direct.activation_tap(lane, direct.base.groups_per_column - 1, 'row_major')
            self.assertEqual(tap.sizes, (1, 128, 64, 128))
            self.assertEqual(tap.strides, (0, 128, 16384, 1))
            self.assertLess(int(tap.indices().max()), 4096 * 16384)


if __name__ == '__main__':
    unittest.main()
