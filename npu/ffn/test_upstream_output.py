"""Independent logical DMA checks for down-A and row-major BF16 outputs."""

import ast
from pathlib import Path
import unittest

import numpy as np

from prefill_schedule import TapSpec
from upstream_output import (upstream_down_activation_tap,
                             upstream_row_major_dims_to_stream,
                             upstream_row_major_output_tap)
from upstream_schedule import plan_upstream


def _layouts(m, channels, native8=False):
    # Unique logical element IDs reveal every transpose, including M/channel
    # ownership boundaries, without introducing any floating-point arithmetic.
    logical = np.arange(m * channels, dtype=np.int64).reshape(m, channels)
    mr = 8 if native8 else 4
    native_c = logical.reshape(m // 16, 16 // mr, mr, channels // 32, 4, 8)
    native_c = native_c.transpose(0, 3, 1, 4, 2, 5).copy().reshape(-1)
    down_a = logical.reshape(m // 16, 16 // mr, mr, channels // 128, 16, 8)
    down_a = down_a.transpose(0, 3, 1, 4, 2, 5).copy().reshape(-1)
    return native_c, down_a


class UpstreamOutputTests(unittest.TestCase):
    def test_actual_graph_transforms_only_row_major_join_outputs(self):
        # Execute the graph's actual output-FIFO construction without MLIR.
        # Logical address tests below independently validate its permutation.
        graph = Path(__file__).with_name('w4a16_upstream.py')
        design = next(node for node in ast.parse(graph.read_text()).body
                      if isinstance(node, ast.FunctionDef) and node.name == '_design')
        loop = next(node for node in design.body if isinstance(node, ast.For)
                    and isinstance(node.iter, ast.Name) and node.iter.id == 'output_cols')
        code = compile(ast.Module(body=[loop], type_ignores=[]), str(graph), 'exec')
        for mode, layout, native8 in ((mode, layout, native8)
                for mode, layout in (('projection', 'compact'), ('projection', 'row_major'),
                                     ('swiglu', 'compact'), ('swiglu', 'down_a'))
                for native8 in (False, True)):
            with self.subTest(mode=mode, layout=layout, native8=native8):
                direct = plan_upstream(256, 256, 256, mode=mode,
                                       max_reuse=4 if mode == 'projection' else 2)
                created = []

                class Fifo:
                    def __init__(self, obj_type, **kwargs):
                        self.options = kwargs
                        created.append(self)
                    def prod(self):
                        return self
                    def cons(self, **kwargs):
                        return self
                    def join(self, offsets, **kwargs):
                        self.offsets, self.join_options = offsets, kwargs
                        return [object() for _ in offsets]

                context = dict(direct=direct, output_layout=layout,
                    bfp16_native_layout=native8,
                    output_cols=list(range(8)) if mode == 'projection' else [1, 3, 5, 7],
                    y_workers={}, y_conses=[], y_join=object(), y_tile=object(),
                    reuse=direct.base.m_reuse, ObjectFifo=Fifo, Tile=lambda c, r: (c, r),
                    upstream_row_major_dims_to_stream=upstream_row_major_dims_to_stream)
                exec(code, context)
                self.assertEqual(len(created), len(context['output_cols']))
                for fifo in created:
                    expected = (list(upstream_row_major_dims_to_stream(direct, native8))
                                if layout == 'row_major' else None)
                    self.assertEqual(fifo.options.get('dims_to_stream'), expected)
                    self.assertEqual(fifo.options['depth'], 2)
                    self.assertEqual(fifo.offsets, [r * direct.base.m_reuse * 512 for r in range(4)])
                    self.assertNotIn('dims_to_stream', fifo.join_options)

    def _row_major_transfer(self, direct, original, native8=False):
        dims = upstream_row_major_dims_to_stream(direct, native8)
        worker_elements = direct.base.m_reuse * 512
        permutation = TapSpec(worker_elements, 0, tuple(size for size, _ in dims),
                              tuple(stride for _, stride in dims)).indices()
        self.assertEqual(len(dims), 4)
        self.assertEqual(permutation.size, worker_elements)
        np.testing.assert_array_equal(np.sort(permutation), np.arange(worker_elements))
        # A join applies its transform separately to each producer slice.
        # This models the pinned compiler's four per-worker memory-tile BDs.
        actual = np.empty_like(original)
        visits = np.zeros(actual.size, np.uint8)
        for col in range(8):
            for group in range(direct.base.groups_per_column):
                for segment in range(direct.segment_count):
                    source = direct.output_tap(col, group, segment)
                    stream = original[source.indices()].reshape(-1, 4, worker_elements)
                    stream = stream[:, :, permutation].reshape(-1)
                    target = upstream_row_major_output_tap(direct, col, group, segment)
                    self.assertEqual(len(target.sizes), 4)
                    self.assertTrue(all(0 < size <= 512 for size in target.sizes))
                    addresses = target.indices()
                    self.assertEqual(stream.size, addresses.size)
                    self.assertFalse(np.any(visits[addresses]))
                    actual[addresses] = stream
                    visits[addresses] += 1
        np.testing.assert_array_equal(visits, np.ones_like(visits))
        return actual

    def test_projection_join_and_shim_produce_exact_row_major_matrix(self):
        # Includes two M-column groups, effective reuse 1/2/4, M waves,
        # odd N ownership, single-half segment tails, and original N offsets.
        for m, channels in ((128, 128), (256, 256), (512, 384),
                            (128, 1152), (512, 2560), (512, 4096)):
            for start in (0, 32, 96, 288):
                for reuse in (1, 2, 4):
                    with self.subTest(m=m, channels=channels, start=start, reuse=reuse):
                        direct = plan_upstream(m, 256, channels, mode='projection',
                            weight_k=512, weight_n=((channels + start + 63) // 64 + 8) * 64,
                            k_start=128, n_start=start, max_reuse=reuse)
                        native, _ = _layouts(m, channels)
                        actual = self._row_major_transfer(direct, native)
                        np.testing.assert_array_equal(actual, np.arange(m * channels))

    def test_projection_row_major_preserves_all_bf16_bit_patterns(self):
        for reuse in (1, 2, 4):
            with self.subTest(reuse=reuse):
                direct = plan_upstream(256, 128, 256, max_reuse=reuse)
                native, _ = _layouts(256, 256)
                bits = np.arange(65536, dtype=np.uint16)
                actual = self._row_major_transfer(direct, bits[native])
                np.testing.assert_array_equal(actual.reshape(256, 256), bits.reshape(256, 256))

    def test_native8_projection_row_major_geometry_and_bf16_bits(self):
        for m, channels in ((128, 128), (256, 256), (512, 1152), (512, 4096)):
            for start in (0, 32, 288):
                for reuse in (1, 2, 4):
                    with self.subTest(m=m, channels=channels, start=start, reuse=reuse):
                        direct = plan_upstream(m, 256, channels, mode='projection',
                            weight_n=((channels + start + 63) // 64 + 8) * 64,
                            n_start=start, max_reuse=reuse)
                        native, _ = _layouts(m, channels, native8=True)
                        # Cast IDs to uint16 to cover every BF16 bit pattern
                        # without numerical conversion, including NaN payloads.
                        actual = self._row_major_transfer(direct, native.astype(np.uint16), True)
                        np.testing.assert_array_equal(actual, np.arange(m * channels).astype(np.uint16))

    def test_native8_swiglu_scatter_matches_down_native8_input(self):
        for m, channels in ((128, 128), (256, 256), (512, 1152), (512, 2560)):
            for start in (0, 32, 288):
                for reuse in (1, 2, 4):
                    with self.subTest(m=m, channels=channels, start=start, reuse=reuse):
                        direct = plan_upstream(m, 256, channels, mode='swiglu',
                            weight_n=((channels + start + 63) // 64 + 8) * 64,
                            n_start=start, max_reuse=reuse)
                        original, expected = _layouts(m, channels, native8=True)
                        original, expected = original.astype(np.uint16), expected.astype(np.uint16)
                        actual = np.empty_like(original)
                        visits = np.zeros(actual.size, np.uint8)
                        for col in (1, 3, 5, 7):
                            for group in range(direct.base.groups_per_column):
                                for segment in range(direct.segment_count):
                                    source = direct.output_tap(col, group, segment)
                                    tap = upstream_down_activation_tap(direct, col, group, segment, True)
                                    self.assertEqual(tap.sizes[-2:], (2, 256))
                                    self.assertEqual(tap.strides[-2:], (1024, 1))
                                    addresses = tap.indices()
                                    self.assertFalse(np.any(visits[addresses]))
                                    actual[addresses] = original[source.indices()]
                                    visits[addresses] += 1
                        np.testing.assert_array_equal(actual, expected)
                        np.testing.assert_array_equal(visits, np.ones_like(visits))

    def test_projection_row_major_rejects_bad_ownership_and_indices(self):
        direct = plan_upstream(256, 256, 256, max_reuse=4)
        self.assertEqual(upstream_row_major_dims_to_stream(direct),
                         ((16, 128), (4, 8), (4, 32), (8, 1)))
        for col in (-1, 8, True, 1.0):
            with self.subTest(col=col), self.assertRaises(ValueError):
                upstream_row_major_output_tap(direct, col, 0, 0)
        for group in (-1, direct.base.groups_per_column, True):
            with self.subTest(group=group), self.assertRaises(ValueError):
                upstream_row_major_output_tap(direct, 0, group, 0)
        for segment in (-1, direct.segment_count, True, 0.0):
            with self.subTest(segment=segment), self.assertRaises(ValueError):
                upstream_row_major_output_tap(direct, 0, 0, segment)
        swiglu = plan_upstream(128, 128, 128, mode='swiglu')
        with self.assertRaisesRegex(ValueError, 'only supported for projection'):
            upstream_row_major_dims_to_stream(swiglu)
        with self.assertRaisesRegex(ValueError, 'only supported for projection'):
            upstream_row_major_output_tap(swiglu, 1, 0, 0)

    def test_all_outputs_land_once_in_down_activation_order(self):
        for m, channels in ((128, 128), (256, 256), (128, 384),
                            (512, 512), (128, 1152), (512, 2560)):
            for start in (0, 32, 64, 96, 128, 288):
                for reuse in (1, 2, 4):
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
