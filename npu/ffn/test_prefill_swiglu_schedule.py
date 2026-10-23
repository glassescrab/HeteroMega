"""CPU checks of adjacent SwiGLU ownership, native layouts and buffer bounds."""

import json
import unittest

import numpy as np

from prefill_reference import (C_TILE_ELEMENTS, bf16_bits, bf16_from_bits,
                               pack_output)
from prefill_swiglu_schedule import (plan_swiglu, swiglu_logical_column,
                                    swiglu_memory_estimate, swiglu_output_tap,
                                    swiglu_plan_metadata)
from reference import bf16, silu_multiply


class SwigluScheduleTests(unittest.TestCase):
    def test_adjacent_workers_have_matching_channel_and_token_order(self):
        self.assertEqual([swiglu_logical_column(c) for c in range(8)],
                         [0, 4, 1, 5, 2, 6, 3, 7])
        for m in (128, 512, 4096):
            for p in (128, 384, 512, 768, 896, 1152, 8192):
                with self.subTest(m=m, p=p):
                    plan = plan_swiglu(m, 4096, p)
                    self.assertEqual(plan.worker_count, 32)
                    self.assertEqual(plan.m_column_groups, 1)
                    self.assertEqual(plan.n_columns, 8)
                    for pair in range(4):
                        for row in range(4):
                            gate = plan.worker(swiglu_logical_column(2 * pair), row)
                            up = plan.worker(swiglu_logical_column(2 * pair + 1), row)
                            self.assertEqual(gate.m_groups, up.m_groups)
                            self.assertEqual(gate.n_tiles,
                                             tuple(nt - p // 32 for nt in up.n_tiles))
                            self.assertEqual(len(gate.n_tiles) * len(gate.m_groups),
                                             len(up.n_tiles) * len(up.m_groups))

    def test_weight_dma_uses_interleaved_columns_without_repacking_host_buffer(self):
        for p in (128, 384, 896):
            plan = plan_swiglu(128, 256, p)
            weights = np.arange(plan.nb * plan.kb * 2144, dtype=np.int32)
            native = weights.reshape(plan.nb, plan.kb, 2144)
            seen = []
            for physical in range(8):
                logical = swiglu_logical_column(physical)
                tap = plan.weight_tap(logical)
                worker = plan.worker(logical, 0)
                expected = np.concatenate([native[nt, kt]
                    for nt in worker.n_tiles for kt in range(plan.kb)])
                np.testing.assert_array_equal(weights[tap.indices()], expected)
                seen.extend(worker.n_tiles)
            self.assertEqual(sorted(seen), list(range(plan.nb)))

    def test_onchip_pointwise_and_four_drains_match_compact_z(self):
        # CPU emulation of FIFO order and the numerical storage boundaries,
        # not an emulation of the AIE sigmoid LUT or a hardware performance test.
        rng = np.random.default_rng(20261019)
        for m, p, reuse in ((128, 128, 1), (128, 128, 2), (128, 384, 2),
                            (512, 512, 2), (128, 896, 2)):
            with self.subTest(m=m, p=p, reuse=reuse):
                plan = plan_swiglu(m, 256, p, max_reuse=reuse)
                gate = bf16(rng.normal(size=(m, p)).astype(np.float32))
                up = bf16(rng.normal(size=(m, p)).astype(np.float32))
                g = pack_output(gate).reshape(m // 16, p // 32, C_TILE_ELEMENTS)
                u = pack_output(up).reshape(m // 16, p // 32, C_TILE_ELEMENTS)
                expected = pack_output(silu_multiply(gate, up, bf16_io=True))
                actual = np.zeros(m * p, np.uint16)
                written = np.zeros(m * p, np.uint8)
                for pair in range(4):
                    physical = 2 * pair + 1
                    for group in range(plan.groups_per_column):
                        stream = []
                        for nt in plan.worker(pair, 0).n_tiles:
                            for row in range(4):
                                # The gate FIFO and local up buffer each hold
                                # R native C tiles with identical element order.
                                mts = plan.worker(pair, row).m_groups[group]
                                g_object = np.concatenate([g[mt, nt] for mt in mts])
                                u_object = np.concatenate([u[mt, nt] for mt in mts])
                                self.assertEqual(g_object.size, plan.m_reuse * 512)
                                z_object = silu_multiply(bf16_from_bits(g_object),
                                                         bf16_from_bits(u_object), bf16_io=True)
                                stream.append(bf16_bits(z_object))
                        addresses = swiglu_output_tap(plan, physical, group).indices()
                        payload = np.concatenate(stream)
                        self.assertEqual(payload.size, addresses.size)
                        self.assertFalse(np.any(written[addresses]))
                        actual[addresses] = payload
                        written[addresses] += 1
                np.testing.assert_array_equal(written, 1)
                np.testing.assert_array_equal(actual, expected)

    def test_metadata_tracks_physical_ownership_one_output_and_conservative_memory(self):
        plan = plan_swiglu(512, 4096, 896)
        metadata = json.loads(json.dumps(swiglu_plan_metadata(plan)))
        self.assertEqual(metadata['output_columns'], [1, 3, 5, 7])
        self.assertEqual(metadata['output_order'], ['silu_mul'])
        self.assertEqual(metadata['host_projection_elements'], 512 * 896 * 2)
        self.assertEqual(metadata['host_output_elements'], 512 * 896)
        self.assertEqual(metadata['pointwise_worker_count'], 16)
        self.assertEqual(len(metadata['workers']), 32)
        for worker in metadata['workers']:
            physical = worker['column']
            self.assertEqual(worker['logical_n_column'], swiglu_logical_column(physical))
            self.assertEqual(worker['runs_silu_multiply'], bool(physical % 2))
        estimate = swiglu_memory_estimate(plan)
        self.assertEqual(estimate['gate_raw_bytes'], 39104)
        self.assertEqual(estimate['up_raw_bytes'], 49344)
        for kind in ('gate', 'up'):
            self.assertEqual(sum(estimate[kind + '_components_bytes'].values()),
                             estimate[kind + '_raw_bytes'])
            self.assertLess(estimate[kind + '_raw_bytes'], estimate['compute_tile_capacity_bytes'])

    def test_reject_nonadjacent_column_indices_wrong_output_side_and_reuse_four(self):
        for column in (-1, 8, True, 0.0):
            with self.subTest(column=column), self.assertRaises(ValueError):
                swiglu_logical_column(column)
        plan = plan_swiglu(128, 256, 128)
        for column in (0, 2, 4, 6):
            with self.assertRaises(ValueError):
                swiglu_output_tap(plan, column, 0)
        with self.assertRaises(ValueError):
            swiglu_output_tap(plan, 1, plan.groups_per_column)
        for reuse in (0, 3, 4, True):
            with self.assertRaises(ValueError):
                plan_swiglu(128, 256, 128, max_reuse=reuse)
        for p in (64, 192, 8320):
            with self.assertRaises(ValueError):
                plan_swiglu(128, 256, p)

    def test_bfp_stack_estimate_tracks_allocated_bytes_without_changing_ownership(self):
        plan = plan_swiglu(512, 4096, 896)
        native = swiglu_plan_metadata(plan)
        block = swiglu_plan_metadata(plan, stack_size=4096)
        self.assertEqual(native['workers'], block['workers'])
        for side in ('gate', 'up'):
            self.assertEqual(block['memory_estimate'][side + '_components_bytes']['stack'], 4096)
            self.assertEqual(block['memory_estimate'][side + '_raw_bytes'],
                             native['memory_estimate'][side + '_raw_bytes'] + 2048)
        for stack in (0, -1024, 2049, True, 4096.0):
            with self.subTest(stack=stack), self.assertRaisesRegex(ValueError, 'stack_size'):
                swiglu_memory_estimate(plan, stack_size=stack)


if __name__ == '__main__':
    unittest.main()
