"""CPU execution of direct graph arithmetic/cache and CLI manifest selection.

Only the hardware compiler is replaced. These checks do not establish AIE
compilation, memory placement, numerical accuracy or device performance.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from projection_arithmetic import ProjectionArithmetic, UPSTREAM_KERNEL_COMMIT
from upstream_schedule import (plan_upstream, validate_segment_pipeline_depth,
                               validate_kernel_tuning, validate_upstream_buffering,
                               validate_input_layout, upstream_worker_stack_size)
from upstream_weights import UPSTREAM_LAYOUT_VERSION


ROOT = Path(__file__).parent
GRAPH = ROOT / 'w4a16_upstream.py'


def _graph_environment():
    tree = ast.parse(GRAPH.read_text())
    dependencies = next(node.value for node in tree.body
                        if isinstance(node, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'DEPENDENCIES'
                                for t in node.targets))
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
              for name in ast.literal_eval(dependencies)}
    environment = dict(ROOT=ROOT, HASHES=hashes,
        SOURCE=(ROOT / 'w4a16_prefill_upstream.cc').read_text(),
        FINGERPRINT=hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
        ProjectionArithmetic=ProjectionArithmetic, plan_upstream=plan_upstream,
        validate_segment_pipeline_depth=validate_segment_pipeline_depth,
        validate_kernel_tuning=validate_kernel_tuning,
        validate_upstream_buffering=validate_upstream_buffering,
        validate_input_layout=validate_input_layout,
        upstream_worker_stack_size=upstream_worker_stack_size,
        iron=SimpleNamespace(get_current_device=lambda: SimpleNamespace(cols=8)),
        np=np, bfloat16=np.uint16)
    return tree, environment


class UpstreamArithmeticTests(unittest.TestCase):
    def test_real_graph_selection_keeps_source_and_isolates_compiled_objects(self):
        tree, environment = _graph_environment()
        design = copy.deepcopy(next(node for node in tree.body
                                    if isinstance(node, ast.FunctionDef)
                                    and node.name == '_design'))
        # Execute the actual validation, buffer-type and object-selection
        # prefix, stopping before any MLIR/AIE object is constructed.
        end = next(index for index, node in enumerate(design.body)
                   if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'obj' for t in node.targets))
        design.body = design.body[:end + 1] + [ast.Return(value=ast.Tuple(
            elts=[ast.Name(id=name, ctx=ast.Load())
                  for name in ('projection', 'worker_stack_size', 'obj')], ctx=ast.Load()))]
        exec(compile(ast.fix_missing_locations(ast.Module(body=[design], type_ignores=[])),
                     str(GRAPH), 'exec'), environment)
        objects = []
        for arithmetic, stack in (('bf16', 2048), ('bfp16', 4096)):
            for mode in ('projection', 'swiglu'):
                with self.subTest(arithmetic=arithmetic, mode=mode):
                    projection, actual_stack, obj = environment['_design'](
                        512, 4096, 2560, mode, 4096, 14336, 0, 0, 8,
                        2, 2, 2, True, 1, 'row_major',
                        'down_a' if mode == 'swiglu' else 'compact',
                        environment['FINGERPRINT'], arithmetic)
                    self.assertEqual(projection.source_path, ROOT / 'w4a16_prefill_upstream.cc')
                    self.assertEqual(projection.source_sha256,
                                     environment['HASHES']['w4a16_prefill_upstream.cc'])
                    self.assertEqual(actual_stack, stack)
                    self.assertIn(f'-DAIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16='
                                  f'{int(arithmetic == "bfp16")}', projection.compile_flags(2))
                    self.assertIn(f'_{arithmetic}_', obj)
                    objects.append(obj)
        self.assertEqual(objects[0], objects[1])
        self.assertEqual(objects[2], objects[3])
        self.assertNotEqual(objects[0], objects[2])

    def test_real_jit_entry_points_forward_default_and_explicit_arithmetic(self):
        tree, environment = _graph_environment()
        calls = []
        environment.update(CompileTime=type, In=object, Out=object,
                           _design=lambda *args: calls.append(args))
        for name, inputs in (('upstream_projection', 3), ('upstream_swiglu', 4)):
            entry = copy.deepcopy(next(node for node in tree.body
                                       if isinstance(node, ast.FunctionDef) and node.name == name))
            entry.decorator_list = []
            exec(compile(ast.Module(body=[entry], type_ignores=[]), str(GRAPH), 'exec'), environment)
            for options, expected in (({}, 'bf16'), ({'arithmetic': 'bfp16'}, 'bfp16')):
                environment[name](*([None] * inputs), m=128, k=256, n=128,
                                  weight_k=256, weight_n=512, **options)
                self.assertEqual(calls[-1][-1], expected)

    def test_real_cli_manifest_and_compile_options_match_arithmetic(self):
        tree, base = _graph_environment()
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'main')
        for mode in ('projection', 'swiglu'):
            for selection in (None, 'bf16', 'bfp16'):
                arithmetic = selection or 'bf16'
                with self.subTest(mode=mode, selection=selection), tempfile.TemporaryDirectory() as tmp:
                    binary, insts = Path(tmp) / 'kernel.xclbin', Path(tmp) / 'insts.bin'
                    binary.write_bytes(b'CPU MOCK; NOT AN NPU ARTIFACT')
                    insts.write_bytes(b'CPU MOCK')
                    calls = []

                    def compile_args(parser, **unused):
                        parser.add_argument('--xclbin-path')
                        parser.add_argument('--insts-path')
                        parser.add_argument('--emit-mlir', action='store_true')

                    environment = dict(base, argparse=argparse, hashlib=hashlib,
                        json=json, Path=Path, __doc__='CPU graph manifest check',
                        add_compile_args=compile_args, device_from_args=lambda *a, **k: None,
                        run_design_cli=lambda *a, **k: calls.append(k),
                        upstream_swiglu=object(), upstream_projection=object(),
                        UPSTREAM_LAYOUT_VERSION=UPSTREAM_LAYOUT_VERSION,
                        UPSTREAM_KERNEL_COMMIT=UPSTREAM_KERNEL_COMMIT,
                        TARGET_COMMIT='cpu-test-target')
                    exec(compile(ast.Module(body=[main], type_ignores=[]), str(GRAPH), 'exec'), environment)
                    argv = [str(GRAPH), '--mode', mode, '-M', '512', '-K', '2560', '-N', '4096',
                            '--weight-k', '14336', '--weight-n', '4096', '--vector-zero',
                            '--input-layout', 'row_major', '--xclbin-path', str(binary),
                            '--insts-path', str(insts)]
                    if mode == 'projection':
                        argv += ['--max-reuse', '4', '--activation-fifo-depth', '1']
                    else:
                        argv += ['--output-layout', 'down_a']
                    if selection:
                        argv += ['--arithmetic', selection]
                    with patch.object(sys, 'argv', argv):
                        environment['main']()
                    manifest = json.loads(Path(str(binary) + '.json').read_text())
                    self.assertEqual(manifest['kind'], f'w4a16_upstream_{arithmetic}')
                    for name in ('arithmetic', 'compute_format'):
                        self.assertEqual(manifest[name], arithmetic)
                    self.assertEqual(calls[0]['compile_kwargs']['arithmetic'], arithmetic)
                    self.assertEqual(manifest['worker_stack_size'], 4096 if arithmetic == 'bfp16' else 2048)
                    self.assertEqual(manifest['weight_tile_bytes'], 4352)
                    self.assertEqual(manifest['dependency_sha256'], base['HASHES'])
                    self.assertEqual(manifest['input_layout'], 'row_major')
                    self.assertEqual(manifest['m_reuse'], 4 if mode == 'projection' else 2)
                    self.assertEqual(manifest['activation_fifo_depth'], 1 if mode == 'projection' else 2)
                    self.assertTrue(manifest['vector_zero'])
                    self.assertEqual(manifest['mmul_m_reuse'], 1)
                    self.assertEqual(manifest['segment_pipeline_depth'], 2)
                    if arithmetic == 'bfp16':
                        with patch.object(sys, 'argv', argv + ['--mmul-m-reuse', '2']):
                            with self.assertRaisesRegex(ValueError, 'bfp16 requires mmul_m_reuse=1'):
                                environment['main']()
                        self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
