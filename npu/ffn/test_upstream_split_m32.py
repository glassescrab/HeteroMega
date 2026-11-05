"""CPU contracts for the opt-in M64-weight/M32-A streaming graph.

These checks establish logical streams, ownership and call sequencing only;
the AIE compiler and hardware must validate linked FIFO lowering and timing.
"""
import ast
from collections import Counter
from pathlib import Path
import unittest

import numpy as np

from prefill_schedule import TapSpec
from upstream_schedule import (plan_upstream, validate_split_m32_a,
                               validate_kernel_tuning, validate_preconvert_a)


GRAPH = Path(__file__).with_name('w4a16_upstream.py')


def graph_design():
    return next(node for node in ast.parse(GRAPH.read_text()).body
                if isinstance(node, ast.FunctionDef) and node.name == '_design')


class SplitM32Tests(unittest.TestCase):
    def test_bounded_configuration_and_raw_memory(self):
        validate_preconvert_a(True, True, True)
        for split, preb in ((False, False), (False, True), (True, False), (1, True)):
            with self.subTest(split=split, preb=preb), self.assertRaises(ValueError):
                validate_preconvert_a(True, split, preb)
        for enabled in (1, None, 'true'):
            with self.subTest(preconvert_a=enabled), self.assertRaises(ValueError):
                validate_preconvert_a(enabled, True, True)
        for mode in ('projection', 'swiglu'):
            direct = plan_upstream(512, 4096, 4096 if mode == 'projection' else 2816,
                                   mode=mode, max_reuse=4)
            validate_split_m32_a(direct, True, True, 2, 1)
            if mode == 'projection':
                validate_split_m32_a(direct, True, True, 2, 2)
            for enabled, native8, adepth, ydepth in ((1, True, 2, 1),
                    (True, False, 2, 1), (True, True, 1, 1), (True, True, 2, 3)):
                with self.subTest(mode=mode, enabled=enabled, native8=native8,
                                  adepth=adepth, ydepth=ydepth), self.assertRaises(ValueError):
                    validate_split_m32_a(direct, enabled, native8, adepth, ydepth)
        with self.assertRaisesRegex(ValueError, 'SwiGLU requires output_fifo_depth=1'):
            validate_split_m32_a(direct, True, True, 2, 2)
        for kwargs in (dict(m=128, k=256, n=512, mode='swiglu'),
                       dict(m=512, k=256, n=1152, mode='swiglu'),
                       dict(m=512, k=256, n=2816, mode='swiglu', weight_n=14336, n_start=32)):
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                validate_split_m32_a(plan_upstream(**kwargs, max_reuse=4), True, True, 2, 1)
        # A2*M32, W2, two BF16 M64/N32 C arrays, full N64 scratch, stack4K.
        common = 2 * 32 * 128 * 2 + 2 * 4352 + 2 * 64 * 32 * 2 + 128 * 64 * 2 + 4096
        gate = common + 2 * 64 * 32 * 2
        up = common + 64 * 32 * 2 + 4096  # Z1 and sigmoid tables; no up copy.
        self.assertEqual((gate, up), (61952, 61952))
        for value in (0, 1, None, 'true'):
            with self.subTest(preconvert=value), self.assertRaisesRegex(ValueError, 'must be a bool'):
                validate_kernel_tuning(True, 1, 'bfp16', True, value)
        with self.assertRaisesRegex(ValueError, 'requires bfp16_native_layout=True'):
            validate_kernel_tuning(True, 1, 'bfp16', False, True)

    def test_real_a_fifo_link_preserves_large_permutation_and_small_core_type(self):
        design = graph_design()
        loop = next(node for node in design.body if isinstance(node, ast.For)
                    and isinstance(node.target, ast.Name) and node.target.id == 'lane')
        code = compile(ast.Module(body=[loop], type_ignores=[]), str(GRAPH), 'exec')
        direct = plan_upstream(512, 256, 2816, mode='swiglu', max_reuse=4)
        for layout in ('compact', 'row_major'):
            created = []
            class Fifo:
                def __init__(self, obj_type, **kwargs):
                    self.obj_type = obj_type
                    created.append(self)
                def prod(self, **kwargs):
                    return self
                def cons(self):
                    return self
                def forward(self, **kwargs):
                    self.forward_options = kwargs
                    return self
            environment = dict(plan=direct.base, direct=direct, a_tile='M64',
                a_core_tile='M32', a_prods=[], a_broadcasts=[], ObjectFifo=Fifo,
                Tile=lambda *coords: coords, input_layout=layout, bfp16_native_layout=True)
            exec(code, environment)
            self.assertEqual(len(created), 4)
            for fifo in created:
                self.assertEqual(fifo.obj_type, 'M64')
                self.assertEqual(fifo.forward_options['obj_type'], 'M32')
                dims = fifo.forward_options['dims_to_stream']
                self.assertEqual(tuple(dims), direct.activation_dims_to_stream(layout, True))
                self.assertEqual(np.prod([size for size, stride in dims]), 4 * 2048)

    def test_each_large_dma_object_delivers_two_correct_m32_native8_objects(self):
        for mode in ('projection', 'swiglu'):
            for k in (128, 384, 4096):
                direct = plan_upstream(512, k, 512, mode=mode, max_reuse=4)
                logical = np.arange(512 * k).reshape(512, k)
                packed = logical.reshape(32, 2, 8, k // 128, 16, 8).transpose(0, 3, 1, 4, 2, 5).reshape(-1)
                for layout, host in (('compact', packed), ('row_major', logical.reshape(-1))):
                    dims = direct.activation_dims_to_stream(layout, True)
                    permutation = TapSpec(8192, 0, tuple(size for size, stride in dims),
                                           tuple(stride for size, stride in dims)).indices()
                    for lane in range(4):
                        worker = direct.base.worker(0, lane)
                        for group, m_tiles in enumerate(worker.m_groups):
                            tap = direct.activation_tap(lane, group, layout)
                            # A large linked producer BD emits one ordered
                            # stream. Core BDs receive its first/second M32
                            # objects; they do not reapply the permutation.
                            stream = host[tap.indices()].reshape(-1, 8192)[:, permutation]
                            chunks = stream.reshape(direct.base.kb, 2, 4096)
                            for kg in range(direct.base.kb):
                                for chunk in range(2):
                                    first_row = m_tiles[chunk * 2] * 16
                                    expected = logical[first_row:first_row + 32, kg * 128:(kg + 1) * 128]
                                    expected = expected.reshape(2, 2, 8, 16, 8).transpose(0, 1, 3, 2, 4).reshape(-1)
                                    np.testing.assert_array_equal(chunks[kg, chunk], expected)

    def test_actual_split_cores_dequant_once_hold_w_and_consume_each_a_once(self):
        factories = [node for node in graph_design().body if isinstance(node, ast.FunctionDef)
                     and node.name in ('split_producer_fn', 'split_consumer_fn')]
        code = compile(ast.Module(body=factories, type_ignores=[]), str(GRAPH), 'exec')
        direct = plan_upstream(512, 256, 2816, mode='swiglu', max_reuse=4)
        for consumer in (False, True):
            events, active = [], {}
            class Fifo:
                def __init__(self, label):
                    self.label, self.index = label, -1
                    active[label] = False
                def acquire(self, count):
                    assert count == 1 and not active[self.label]
                    active[self.label] = True
                    self.index += 1
                    events.append(('acquire', self.label, self.index))
                    return (self.label, self.index)
                def release(self, count):
                    assert count == 1 and active[self.label]
                    active[self.label] = False
                    events.append(('release', self.label, self.index))
            a, w, y, gate = [Fifo(label) for label in ('A', 'W', 'Y', 'gate')]
            zero = lambda c: events.append(('zero', c))
            def dequant(weight, b):
                self.assertTrue(active['W'])
                self.assertFalse(active['A'])
                events.append(('dequant', weight))
            def mac(chunk, value, c0, c1, b):
                self.assertTrue(active['W'] and active['A'])
                self.assertEqual(value[1], 2 * w.index + chunk)
                events.append(('mac', chunk, value))
            store = lambda c, output: events.append(('store', c, output))
            activate = lambda g, c, z: events.append(('activate', g, c, z))
            environment = dict(plan=direct.base, range_=range)
            exec(code, environment)
            common = [a, w]
            operations = [zero, dequant, lambda *args: mac(0, *args), lambda *args: mac(1, *args)]
            if consumer:
                environment['split_consumer_fn'](direct.segments[1])(
                    *common, gate, y, 'c0', 'c1', 'B', *operations, activate)
            else:
                environment['split_producer_fn'](direct.segments[0])(
                    *common, y, 'c0', 'c1', 'B', *operations, store)
            count = direct.base.groups_per_column * direct.segment_count * direct.base.kb
            counts = Counter(event[0] for event in events)
            self.assertEqual(counts['dequant'], count)
            self.assertEqual(counts['mac'], 2 * count)
            self.assertEqual(a.index + 1, 2 * count)
            self.assertEqual(w.index + 1, count)
            self.assertEqual(y.index + 1, 2 * direct.base.groups_per_column * direct.segment_count)
            self.assertFalse(any(active.values()))
            if consumer:
                self.assertEqual(counts['store'], 0)
                self.assertEqual([event[2] for event in events if event[0] == 'activate'],
                                 ['c0', 'c1'] * (y.index // 2 + 1))
            # Each W object stays held across exactly two ordered A uses.
            for index in range(count):
                begin = events.index(('acquire', 'W', index))
                end = events.index(('release', 'W', index))
                self.assertEqual(events[begin + 1:end], [
                    ('dequant', ('W', index)), ('acquire', 'A', 2 * index),
                    ('mac', 0, ('A', 2 * index)), ('release', 'A', 2 * index),
                    ('acquire', 'A', 2 * index + 1), ('mac', 1, ('A', 2 * index + 1)),
                    ('release', 'A', 2 * index + 1)])


if __name__ == '__main__':
    unittest.main()
