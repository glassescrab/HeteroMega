"""Independent CPU checks of the array8 native-stream schedule, not hardware tests."""

from collections import Counter
import json
import unittest

import numpy as np

from prefill_schedule import (A_ELEMENTS, C_ELEMENTS, WEIGHT_BYTES, plan_prefill)


class PrefillScheduleTests(unittest.TestCase):
    def test_all_model_shards_have_exact_output_coverage(self):
        for m in (128, 512):
            for p in (128, 256, 512, 1024, 2048):
                for k, n in ((4096, p), (p, 4096)):
                    with self.subTest(m=m, k=k, n=n):
                        plan = plan_prefill(m, k, n)
                        ownership = Counter((mt, nt) for worker in plan.workers
                                            for group in worker.m_groups for mt in group
                                            for nt in worker.n_tiles)
                        self.assertEqual(ownership, Counter({(mt, nt): 1
                            for mt in range(m // 16) for nt in range(n // 32)}))
                        self.assertEqual(plan.worker_count, 32)
                        self.assertEqual({(w.column, w.row) for w in plan.workers},
                                         {(c, r) for c in range(8) for r in range(2, 6)})
                        self.assertTrue(all(w.m_groups and w.n_tiles for w in plan.workers))

    def test_reuse_adapts_without_disabling_workers(self):
        for m, n, requested, expected in ((128, 128, 2, 1), (128, 256, 2, 2),
                                          (512, 128, 2, 2), (512, 512, 2, 2),
                                          (128, 128, 4, 1), (128, 256, 4, 2),
                                          (512, 128, 4, 4), (512, 512, 4, 4),
                                          (512, 512, 1, 1)):
            with self.subTest(m=m, n=n, requested=requested):
                plan = plan_prefill(m, 4096, n, max_reuse=requested)
                self.assertEqual(plan.m_reuse, expected)
                self.assertEqual(plan.worker_count, 32)
                self.assertEqual(plan.groups_per_column * plan.m_reuse
                                 * plan.compute_rows * plan.m_column_groups, plan.mb)

    def test_m_interleaving_and_horizontal_broadcast(self):
        plan = plan_prefill(512, 4096, 512)
        self.assertEqual(plan.worker(0, 0).m_groups, ((0, 1), (8, 9), (16, 17), (24, 25)))
        self.assertEqual(plan.worker(0, 3).m_groups, ((6, 7), (14, 15), (22, 23), (30, 31)))
        for c in range(1, 8):
            self.assertEqual(plan.activation_tap(c, 2, 1), plan.activation_tap(0, 2, 1))
        narrow = plan_prefill(128, 4096, 128)
        self.assertEqual(narrow.m_column_groups, 2)
        self.assertEqual(narrow.n_columns, 4)
        self.assertEqual(narrow.worker(0, 0).m_groups, ((0,),))
        self.assertEqual(narrow.worker(4, 0).m_groups, ((4,),))
        self.assertEqual(narrow.weight_tap(0), narrow.weight_tap(4))
        self.assertNotEqual(narrow.activation_tap(0, 0, 0), narrow.activation_tap(4, 0, 0))

    def test_activation_gather_and_memory_tile_restore_n_k_reuse_order(self):
        # Include local-N replay, multiple K groups, and two M-column groups.
        for m, k, n, requested in ((128, 16384, 256, 2), (128, 4096, 128, 2),
                                   (128, 256, 512, 2), (512, 256, 128, 2),
                                   (512, 128, 512, 4)):
            plan = plan_prefill(m, k, n, max_reuse=requested)
            packed = np.arange(m * k, dtype=np.uint16).reshape(plan.mb, plan.kb, A_ELEMENTS)
            for c in range(8):
                for row in range(4):
                    for group in range(plan.groups_per_column):
                        worker = plan.worker(c, row)
                        # Independent logical expectations before and after
                        # the memory-tile transpose. The shim sends quarter0
                        # of every reused M tile before quarter1,2,and3.
                        expected_shim = np.concatenate([
                            packed[mt, kt, quarter * 512:(quarter + 1) * 512]
                            for _ in worker.n_tiles for kt in range(plan.kb)
                            for quarter in range(4) for mt in worker.m_groups[group]])
                        expected_core = np.concatenate([packed[mt, kt]
                            for _ in worker.n_tiles for kt in range(plan.kb)
                            for mt in worker.m_groups[group]])
                        tap = plan.activation_tap(c, row, group)
                        shim = packed.reshape(-1)[tap.indices()]
                        np.testing.assert_array_equal(shim, expected_shim)
                        # Apply the planner's actual memtile traversal to
                        # each object, then compare with the separate native
                        # A-tile oracle above. No float conversions occur.
                        dims = plan.activation_dims_to_stream
                        stream_offsets = np.array([
                            i * dims[0][1] + j * dims[1][1] + z * dims[2][1]
                            for i in range(dims[0][0]) for j in range(dims[1][0])
                            for z in range(dims[2][0])])
                        objects = shim.reshape(-1, plan.m_reuse * A_ELEMENTS)
                        core = objects[:, stream_offsets].reshape(-1)
                        np.testing.assert_array_equal(core, expected_core)
                        self.assertEqual(len(np.unique(stream_offsets)), plan.m_reuse * A_ELEMENTS)
                        self.assertEqual(tap.sizes[-1], 512)
                        self.assertLessEqual(max(tap.sizes), 512)
                        self.assertLessEqual(max(size for size, _ in dims), 512)
                        self.assertEqual(tap.element_count, plan.local_nb * plan.kb * plan.m_reuse * A_ELEMENTS)

    def test_weight_stream_keeps_one_compact_host_representation(self):
        for n in (128, 256, 384, 512, 2048):
            plan = plan_prefill(512, 256, n)
            packed = np.arange(plan.nb * plan.kb * WEIGHT_BYTES, dtype=np.int32)
            tiles = packed.reshape(plan.nb, plan.kb, WEIGHT_BYTES)
            seen = Counter()
            for c in range(8):
                worker = plan.worker(c, 0)
                expected = np.concatenate([tiles[nt, kt] for nt in worker.n_tiles
                                           for kt in range(plan.kb)])
                tap = plan.weight_tap(c)
                self.assertEqual(tap.buffer_elements, packed.size)
                np.testing.assert_array_equal(packed[tap.indices()], expected)
                seen.update(worker.n_tiles)
            self.assertEqual(seen, Counter({nt: plan.m_column_groups for nt in range(plan.nb)}))

    def test_joined_output_scatter_is_exact_and_nonoverlapping(self):
        for m, n, requested in ((128, 128, 2), (128, 512, 2), (512, 128, 2),
                                (512, 512, 2), (512, 512, 4)):
            plan = plan_prefill(m, 256, n, max_reuse=requested)
            expected = np.arange(m * n, dtype=np.uint16).reshape(plan.mb, plan.nb, C_ELEMENTS)
            actual, written = np.zeros(m * n, np.uint16), np.zeros(m * n, np.uint8)
            for c in range(8):
                for group in range(plan.groups_per_column):
                    # Simulate memory-tile join: each local N result gathers
                    # four workers, each producing R consecutive C512 tiles.
                    stream = np.concatenate([expected[mt, nt]
                        for nt in plan.worker(c, 0).n_tiles for row in range(4)
                        for mt in plan.worker(c, row).m_groups[group]])
                    tap = plan.output_tap(c, group)
                    addresses = tap.indices()
                    self.assertEqual(stream.size, addresses.size)
                    self.assertFalse(np.any(written[addresses]))
                    actual[addresses] = stream
                    written[addresses] += 1
            np.testing.assert_array_equal(written, np.ones_like(written))
            np.testing.assert_array_equal(actual, expected.reshape(-1))

    def test_small_smoke_and_provenance_are_cpu_only(self):
        for k, n in ((256, 128), (128, 256)):
            plan = plan_prefill(128, k, n)
            metadata = json.loads(json.dumps(plan.to_dict()))
            self.assertEqual(metadata["worker_count"], 32)
            self.assertEqual(metadata["compute_rows"], 4)
            self.assertEqual(metadata["host_weight_elements"], (n // 32) * (k // 128) * 2144)
            self.assertEqual(metadata["host_activation_elements"], 128 * k)
            self.assertEqual(metadata["host_output_elements"], 128 * n)
            self.assertEqual(metadata["activation_dims_to_stream"],
                             [[plan.m_reuse, 512], [4, plan.m_reuse * 512], [512, 1]])

    def test_invalid_geometry_and_indices_fail(self):
        for args in ((64, 128, 128), (128, 64, 128), (128, 128, 64),
                     (True, 128, 128), (128, 128, 128.0), (8192, 128, 128),
                     (128, 128, 14208)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                plan_prefill(*args)
        for kwargs in ({"columns": 4}, {"rows": 2}, {"max_reuse": 3}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                plan_prefill(128, 128, 128, **kwargs)
        plan = plan_prefill(128, 128, 128)
        self.assertEqual(plan_prefill(128, 128, 16384).local_nb, 64)
        for c, row, group in ((8, 0, 0), (0, 4, 0), (0, 0, 1)):
            with self.assertRaises(ValueError):
                plan.activation_tap(c, row, group)


if __name__ == "__main__":
    unittest.main()
