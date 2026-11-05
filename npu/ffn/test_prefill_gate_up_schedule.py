"""CPU checks of paired projection ownership, packed weights and output DMA."""

from collections import Counter
import json
import unittest

import numpy as np

from prefill_gate_up_schedule import (gate_up_output_tap, gate_up_output_target,
                                     gate_up_plan_metadata, plan_gate_up)
from prefill_reference import C_TILE_ELEMENTS, pack_weights, unpack_weights
from prefill_schedule import plan_prefill
from reference import W4A16, bf16, pack_int4


class GateUpScheduleTests(unittest.TestCase):
    def test_all_columns_and_workers_own_exactly_one_projection(self):
        for m in (128, 512, 4096):
            for channels in (128, 256, 384, 512, 640, 1024, 2048, 8192):
                with self.subTest(m=m, channels=channels):
                    plan = plan_gate_up(m, 4096, channels)
                    self.assertEqual(plan.worker_count, 32)
                    self.assertEqual(plan.m_column_groups, 1)
                    self.assertEqual(plan.n_columns, 8)
                    self.assertEqual(plan.m_reuse, 2)
                    self.assertEqual(plan.local_nb, channels // 128)
                    coverage = Counter()
                    for worker in plan.workers:
                        label = gate_up_output_target(plan, worker.column)
                        offset = 0 if label == 'gate' else channels // 32
                        self.assertTrue(worker.m_groups and worker.n_tiles)
                        for group in worker.m_groups:
                            for mt in group:
                                for nt in worker.n_tiles:
                                    self.assertLess(nt - offset, channels // 32)
                                    self.assertGreaterEqual(nt - offset, 0)
                                    coverage[(label, mt, nt - offset)] += 1
                    self.assertEqual(coverage, Counter({(label, mt, nt): 1
                        for label in ('gate', 'up') for mt in range(m // 16)
                        for nt in range(channels // 32)}))

    def test_separate_output_taps_preserve_compact_native_layout(self):
        # Odd local N counts (P384/P640) catch an accidental requirement that
        # P be divisible by256. Distinct values in both matrices detect swapped
        # outputs, missing row strides, cross-BO offsets and overlap.
        for m, channels in ((128, 128), (128, 256), (128, 384), (128, 640),
                            (512, 512), (512, 2048), (128, 8192)):
            with self.subTest(m=m, channels=channels):
                plan = plan_gate_up(m, 256, channels)
                shape = (m // 16, channels // 32, C_TILE_ELEMENTS)
                expected = {'gate': np.arange(m * channels, dtype=np.int32).reshape(shape),
                            'up': (np.arange(m * channels, dtype=np.int32)
                                   + m * channels).reshape(shape)}
                wide = np.concatenate((expected['gate'], expected['up']), axis=1)
                actual = {name: np.full(m * channels, -1, np.int32) for name in expected}
                written = {name: np.zeros(m * channels, np.uint8) for name in expected}
                for col in range(8):
                    label = gate_up_output_target(plan, col)
                    for group in range(plan.groups_per_column):
                        # This is the existing array8 memtile stream order,
                        # built from the independent wide projection tensor.
                        stream = np.concatenate([wide[mt, nt]
                            for nt in plan.worker(col, 0).n_tiles for row in range(4)
                            for mt in plan.worker(col, row).m_groups[group]])
                        tap = gate_up_output_tap(plan, col, group)
                        addresses = tap.indices()
                        self.assertEqual(tap.buffer_elements, m * channels)
                        self.assertEqual(addresses.size, stream.size)
                        self.assertLessEqual(max(tap.sizes), 512)
                        self.assertFalse(np.any(written[label][addresses]))
                        actual[label][addresses] = stream
                        written[label][addresses] += 1
                for label in expected:
                    np.testing.assert_array_equal(written[label], 1)
                    np.testing.assert_array_equal(actual[label], expected[label].reshape(-1))

    def test_packed_concatenation_preserves_weights_and_quantization_metadata(self):
        rng = np.random.default_rng(20261018)
        for channels in (128, 384):
            k = 256
            weights = []
            for _ in range(2):
                q = rng.integers(0, 16, (channels, k), dtype=np.uint8)
                scales = rng.uniform(.002, .06, (channels, k // 128)).astype(np.float32)
                zeros = rng.integers(0, 16, scales.shape, dtype=np.uint8)
                weights.append(W4A16(pack_int4(q), scales, zeros, 128))
            joined = W4A16(np.concatenate([w.packed for w in weights]),
                           np.concatenate([w.scales for w in weights]),
                           np.concatenate([w.zeros for w in weights]), 128)
            payload = np.concatenate([pack_weights(w) for w in weights])
            np.testing.assert_array_equal(payload, pack_weights(joined))
            restored = unpack_weights(payload, k, 2 * channels)
            np.testing.assert_array_equal(restored.packed, joined.packed)
            np.testing.assert_array_equal(restored.scales, bf16(joined.scales))
            np.testing.assert_array_equal(restored.zeros, joined.zeros)
            np.testing.assert_array_equal(restored.dequantize(True),
                                          np.concatenate([w.dequantize(True) for w in weights]))

    def test_provenance_exposes_two_buffers_and_unchanged_total_output_size(self):
        plan = plan_gate_up(512, 4096, 512)
        metadata = json.loads(json.dumps(gate_up_plan_metadata(plan)))
        self.assertEqual(metadata['n'], 1024)
        self.assertEqual(metadata['channels'], 512)
        self.assertEqual(metadata['output_count'], 2)
        self.assertEqual(metadata['host_output_elements'], 512 * 1024)
        self.assertEqual(metadata['host_output_elements_per_buffer'], 512 * 512)
        self.assertEqual(metadata['output_columns'], {'gate': [0, 1, 2, 3], 'up': [4, 5, 6, 7]})
        self.assertEqual(plan_gate_up(128, 256, 128, max_reuse=1).m_reuse, 1)

    def test_invalid_geometry_or_nonpaired_plan_is_rejected(self):
        for channels in (0, 64, 192, 8320, True, 128.0):
            with self.subTest(channels=channels), self.assertRaises(ValueError):
                plan_gate_up(128, 4096, channels)
        for kwargs in ({'columns': 4}, {'rows': 2}, {'max_reuse': 3}):
            with self.assertRaises(ValueError):
                plan_gate_up(128, 4096, 512, **kwargs)
        plan = plan_gate_up(128, 256, 128)
        for column in (-1, 8, True, 0.0):
            with self.assertRaises(ValueError):
                gate_up_output_tap(plan, column, 0)
        with self.assertRaises(ValueError):
            gate_up_output_tap(plan, 0, plan.groups_per_column)
        with self.assertRaises(ValueError):
            gate_up_output_target(plan_prefill(128, 256, 128), 0)


if __name__ == '__main__':
    unittest.main()
