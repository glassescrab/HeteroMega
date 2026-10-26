"""CPU stream/address checks for eight-column direct upstream-weight graphs.

These tests independently enumerate original upstream tile order and worker
ownership. They validate host DMA streams and the existing memory-tile
permutation, not device allocation, compilation, or execution.
"""

import ast
from collections import Counter
from pathlib import Path
import unittest

import numpy as np

from upstream_schedule import plan_upstream, segment_pipeline_actions


def _upstream_offsets(k, n):
    offsets = {}
    index = 0
    for stripe in range(8):
        for nt in range(stripe, n // 64, 8):
            for kg in range(k // 128):
                offsets[kg, nt] = index * 4352
                index += 1
    return offsets


def _cases():
    for mode in ('projection', 'swiglu'):
        for m, n, start in ((128, 128, 0), (512, 128, 32),
                            (128, 512, 0), (128, 512, 32),
                            (512, 1152, 0), (128, 1152, 32),
                            (128, 2560, 128)):
            yield dict(m=m, k=256, n=n, mode=mode, weight_k=512,
                       weight_n=((n + start + 63) // 64 + 9) * 64,
                       k_start=128, n_start=start)


class UpstreamScheduleTests(unittest.TestCase):
    def test_segment_pipeline_preserves_fifo_order_and_bounds_live_transfers(self):
        cases = list(_cases()) + [
            dict(m=512, k=4096, n=2560, mode='swiglu', weight_n=14336),
            dict(m=512, k=2560, n=4096, weight_k=14336),
        ]
        for kwargs in cases:
            direct = plan_upstream(**kwargs)
            expected = [(g, s) for g in range(direct.base.groups_per_column)
                        for s in range(direct.segment_count)]
            output_cols = range(8) if direct.mode == 'projection' else (1, 3, 5, 7)
            # Graph uses a dedicated channel per A, W and Y stream, with
            # at most these three streams sharing one shim's BD pool.
            channels = ([(lane, 'MM2S', 0) for lane in
                         range(direct.base.m_column_groups * 4)]
                        + [(col, 'MM2S', 1) for col in range(8)]
                        + [(col, 'S2MM', 0) for col in output_cols])
            for depth in (1, 2):
                with self.subTest(**kwargs, depth=depth):
                    pending, submitted, finished = [], [], []
                    queues, shim_bds = Counter(), Counter()
                    for action in segment_pipeline_actions(direct, depth):
                        key = (action.group, action.segment)
                        if action.kind == 'submit':
                            self.assertNotIn(key, pending)
                            submitted.append(key)
                            pending.append(key)
                            sign = 1
                        else:
                            self.assertEqual(action.kind, 'finish')
                            self.assertEqual(key, pending.pop(0))
                            finished.append(key)
                            sign = -1
                        for channel in channels:
                            queues[channel] += sign
                            shim_bds[channel[0]] += sign
                        self.assertLessEqual(len(pending), depth)
                        self.assertTrue(all(0 <= count <= depth for count in queues.values()))
                        self.assertTrue(all(0 <= count <= 3 * depth
                                            for count in shim_bds.values()))
                    self.assertEqual(submitted, expected)
                    self.assertEqual(finished, expected)
                    self.assertFalse(pending)
                    self.assertFalse(+queues)
                    self.assertFalse(+shim_bds)

    def test_segment_pipeline_prefetches_across_waves_and_flushes_tail(self):
        narrow = plan_upstream(512, 256, 128, mode='swiglu',
                               weight_k=512, weight_n=512, k_start=128, n_start=32)
        self.assertEqual(narrow.segment_count, 1)
        events = [(e.kind, e.group, e.segment) for e in segment_pipeline_actions(narrow, 2)]
        self.assertEqual(events[:5], [('submit', 0, 0), ('submit', 1, 0),
                                     ('finish', 0, 0), ('submit', 2, 0),
                                     ('finish', 1, 0)])
        self.assertEqual(events[-2:], [('finish', 2, 0), ('finish', 3, 0)])
        odd = plan_upstream(128, 256, 1152, mode='swiglu')
        self.assertEqual(odd.segment_count, 5)
        events = [(e.kind, e.group, e.segment) for e in segment_pipeline_actions(odd, 2)]
        self.assertEqual(events[-3:], [('submit', 0, 4), ('finish', 0, 3), ('finish', 0, 4)])
        serial = [(e.kind, e.group, e.segment) for e in segment_pipeline_actions(odd, 1)]
        self.assertEqual(serial, [(kind, 0, s) for s in range(5)
                                  for kind in ('submit', 'finish')])

    def test_segment_pipeline_rejects_unbounded_or_ambiguous_depth(self):
        direct = plan_upstream(128, 256, 128)
        for depth in (0, 3, 4, -1, True, False, 1.0, '2', None):
            with self.subTest(depth=depth), self.assertRaises(ValueError):
                segment_pipeline_actions(direct, depth)

    def test_graph_submission_drains_before_fills_and_finishes_every_group(self):
        # Execute the actual graph's nested submission function with recording
        # handles, without importing MLIR-AIE. Address/worker tests below
        # independently validate the taps this function hands to those handles.
        source = Path(__file__).with_name('w4a16_upstream.py').read_text()
        design = next(n for n in ast.parse(source).body
                      if isinstance(n, ast.FunctionDef) and n.name == '_design')
        submit = next(n for n in design.body
                      if isinstance(n, ast.FunctionDef) and n.name == 'submit')
        code = compile(ast.Module(body=[submit], type_ignores=[]), '<graph submit>', 'exec')
        for mode in ('projection', 'swiglu'):
            for depth in (1, 2):
                with self.subTest(mode=mode, depth=depth):
                    direct = plan_upstream(512, 256, 1152, mode=mode,
                                           weight_k=512, weight_n=1280,
                                           k_start=128, n_start=32)
                    output_cols = list(range(8)) if mode == 'projection' else [1, 3, 5, 7]
                    log, groups = [], []

                    class RecordingGroup:
                        def __init__(self):
                            self.id = len(groups)
                            groups.append(self)
                        def finish(self):
                            log.append(('finish', self.id, None, None))

                    class RecordingHandle:
                        def __init__(self, label):
                            self.label = label
                        def fill(self, buffer, tap, *, group):
                            log.append(('fill', group.id, self.label, buffer))
                        def drain(self, buffer, tap, *, wait, group):
                            self.assert_wait = wait
                            log.append(('drain', group.id, self.label, wait))

                    context = dict(plan=direct.base, direct=direct, mode=mode,
                                   output_cols=output_cols, segment_pipeline_depth=depth,
                                   segment_pipeline_actions=segment_pipeline_actions,
                                   TaskGroup=RecordingGroup, _tap=lambda tap: tap)
                    exec(code, context)
                    context['submit']('A', ('gate', 'up') if mode == 'swiglu' else ('W',),
                                      'Y', [RecordingHandle(f'A{i}') for i in range(4)],
                                      [RecordingHandle(f'W{i}') for i in range(8)],
                                      [RecordingHandle(f'Y{i}') for i in output_cols])
                    live, starts, finishes = set(), [], []
                    for kind, gid, label, value in log:
                        if kind == 'drain' and gid not in live:
                            live.add(gid)
                            starts.append(gid)
                        if kind == 'finish':
                            live.remove(gid)
                            finishes.append(gid)
                        self.assertLessEqual(len(live), depth)
                    self.assertFalse(live)
                    self.assertEqual(starts, finishes)
                    self.assertEqual(len(groups), direct.base.groups_per_column * direct.segment_count)
                    for gid in starts:
                        entries = [entry for entry in log if entry[1] == gid]
                        self.assertEqual([e[0] for e in entries],
                                         ['drain'] * len(output_cols) + ['fill'] * 12 + ['finish'])
                        self.assertTrue(all(e[3] is True for e in entries[:len(output_cols)]))
                        weights = [e[3] for e in entries if e[2] and e[2].startswith('W')]
                        self.assertEqual(weights, ['gate', 'up'] * 4 if mode == 'swiglu'
                                         else ['W'] * 8)

    def test_n64_segments_cover_worker_ownership_without_duplicate_acquisitions(self):
        for kwargs in _cases():
            with self.subTest(**kwargs):
                direct = plan_upstream(**kwargs)
                base = direct.base
                self.assertEqual(base.worker_count, 32)
                self.assertTrue(all(base.worker(c, r).m_groups for c in range(8)
                                    for r in range(4)))
                self.assertEqual(len(direct.segments), 8)
                self.assertTrue(all(len(items) == direct.segment_count
                                    for items in direct.segments))
                for col in range(8):
                    logical = direct.logical_column(col)
                    local_start = base.n_start(logical) % (direct.n // 32)
                    expected = list(range(direct.n_start // 32 + local_start,
                                          direct.n_start // 32 + local_start + base.local_nb))
                    observed, tile_ids = [], []
                    for item in direct.segments[col]:
                        self.assertIn(item.halves, ((0,), (1,), (0, 1)))
                        self.assertEqual(item.first_local_tile, len(observed))
                        observed.extend(item.n64_tile * 2 + h for h in item.halves)
                        tile_ids.append(item.n64_tile)
                    self.assertEqual(observed, expected)
                    # Both halves within one worker consume one original FIFO
                    # object. Cross-column ownership boundaries may reread it.
                    self.assertEqual(len(tile_ids), len(set(tile_ids)))
                if direct.mode == 'swiglu':
                    for gate in (0, 2, 4, 6):
                        self.assertEqual(direct.segments[gate], direct.segments[gate + 1])

    def test_weight_streams_select_full_geometry_stripes_and_k_slice(self):
        for kwargs in _cases():
            with self.subTest(**kwargs):
                direct = plan_upstream(**kwargs)
                offsets = _upstream_offsets(direct.weight_k, direct.weight_n)
                for col in range(8):
                    transferred = 0
                    for si, item in enumerate(direct.segments[col]):
                        tap = direct.weight_tap(col, si)
                        expected = np.concatenate([
                            np.arange(offsets[kg, item.n64_tile],
                                      offsets[kg, item.n64_tile] + 4352)
                            for kg in range(direct.k_start // 128,
                                            (direct.k_start + direct.base.k) // 128)])
                        np.testing.assert_array_equal(tap.indices(), expected)
                        self.assertEqual(tap.buffer_elements, direct.weight_bytes)
                        transferred += tap.element_count
                    self.assertEqual(transferred, direct.segment_count * direct.base.kb * 4352)

    def test_activation_stream_is_once_per_n64_segment_with_correct_m_reuse(self):
        for kwargs in _cases():
            with self.subTest(**kwargs):
                direct = plan_upstream(**kwargs)
                base = direct.base
                original = np.arange(base.m * base.k).reshape(base.mb, base.kb, 2048)
                dims = base.activation_dims_to_stream
                permutation = np.array([
                    i * dims[0][1] + j * dims[1][1] + z * dims[2][1]
                    for i in range(dims[0][0]) for j in range(dims[1][0])
                    for z in range(dims[2][0])])
                seen_workers = set()
                for col in range(8):
                    logical = direct.logical_column(col)
                    m_group = logical // base.n_columns
                    for row in range(4):
                        seen_workers.add((col, row + 2))
                        worker = base.worker(logical, row)
                        lane = m_group * 4 + row
                        for group, m_tiles in enumerate(worker.m_groups):
                            expected_shim = np.concatenate([
                                original[mt, kg, quarter * 512:(quarter + 1) * 512]
                                for kg in range(base.kb) for quarter in range(4)
                                for mt in m_tiles])
                            expected_core = np.concatenate([
                                original[mt, kg] for kg in range(base.kb)
                                for mt in m_tiles])
                            tap = direct.activation_tap(lane, group)
                            shim = original.reshape(-1)[tap.indices()]
                            np.testing.assert_array_equal(shim, expected_shim)
                            core = shim.reshape(-1, base.m_reuse * 2048)[:, permutation].reshape(-1)
                            np.testing.assert_array_equal(core, expected_core)
                            self.assertEqual(tap.element_count, base.kb * base.m_reuse * 2048)
                            self.assertEqual(direct.segment_count * tap.element_count,
                                len(direct.segments[col]) * base.kb * base.m_reuse * 2048)
                self.assertEqual(seen_workers, {(c, r) for c in range(8) for r in range(2, 6)})

    def test_joined_outputs_cover_every_element_exactly_once_in_stream_order(self):
        for kwargs in _cases():
            with self.subTest(**kwargs):
                direct = plan_upstream(**kwargs)
                base, nb = direct.base, direct.n // 32
                expected = np.arange(base.m * direct.n).reshape(base.mb, nb, 512)
                actual = np.full(base.m * direct.n, -1, dtype=np.int64)
                written = np.zeros(actual.size, np.uint8)
                output_cols = range(8) if direct.mode == 'projection' else (1, 3, 5, 7)
                ownership = Counter()
                for col in output_cols:
                    logical = direct.logical_column(col)
                    for group in range(base.groups_per_column):
                        for si, item in enumerate(direct.segments[col]):
                            nts = [item.n64_tile * 2 + half - direct.n_start // 32
                                   for half in item.halves]
                            stream = []
                            for nt in nts:
                                for row in range(4):
                                    for mt in base.worker(logical, row).m_groups[group]:
                                        stream.append(expected[mt, nt])
                                        ownership[mt, nt] += 1
                            stream = np.concatenate(stream)
                            addresses = direct.output_tap(col, group, si).indices()
                            self.assertEqual(stream.size, addresses.size)
                            self.assertFalse(np.any(written[addresses]))
                            actual[addresses] = stream
                            written[addresses] += 1
                np.testing.assert_array_equal(written, np.ones_like(written))
                np.testing.assert_array_equal(actual, expected.reshape(-1))
                self.assertEqual(ownership, Counter({(mt, nt): 1 for mt in range(base.mb)
                                                    for nt in range(nb)}))
                if direct.mode == 'swiglu':
                    for col in (0, 2, 4, 6):
                        with self.assertRaises(ValueError):
                            direct.output_tap(col, 0, 0)

    def test_odd_column_boundary_is_explicit_and_only_boundary_tiles_repeat(self):
        for mode in ('projection', 'swiglu'):
            direct = plan_upstream(128, 256, 1152, mode=mode)
            self.assertEqual(direct.base.local_nb, 9)
            self.assertEqual(direct.segment_count, 5)
            # Distinct N owners overlap exactly one original tile at an odd
            # N32 boundary; matching gate/up columns use separate weight BOs.
            cols = (0, 1, 2, 3) if mode == 'projection' else (0, 2, 4, 6)
            groups = [set(s.n64_tile for s in direct.segments[c]) for c in cols]
            for i in range(3):
                shared = groups[i] & groups[i + 1]
                self.assertEqual(shared, {(i + 1) * 9 // 2} if i % 2 == 0 else set())
            self.assertEqual(direct.segments[cols[0]][-1].halves, (0,))
            self.assertEqual(direct.segments[cols[1]][0].halves, (1,))


if __name__ == '__main__':
    unittest.main()
