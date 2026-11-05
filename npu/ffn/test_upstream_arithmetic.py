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
                               validate_split_m32_a, validate_preconvert_a,
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
        validate_split_m32_a=validate_split_m32_a,
        validate_preconvert_a=validate_preconvert_a,
        validate_input_layout=validate_input_layout,
        upstream_worker_stack_size=upstream_worker_stack_size,
        Path=Path, config=SimpleNamespace(cxx_header_path=lambda: '/cpu-test-headers'),
        ExternalFunction=lambda *a, **kw: kw,
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
        # prefix. ExternalFunction is recorded, without any MLIR/compiler.
        end = next(index for index, node in enumerate(design.body)
                   if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'compile_kernel' for t in node.targets))
        design.body = design.body[:end + 1] + [ast.Return(value=ast.Tuple(
            elts=[ast.Name(id=name, ctx=ast.Load())
                  for name in ('projection', 'worker_stack_size', 'obj', 'c_tile', 'compile_kernel')], ctx=ast.Load()))]
        exec(compile(ast.fix_missing_locations(ast.Module(body=[design], type_ignores=[])),
                     str(GRAPH), 'exec'), environment)
        objects = []
        variants = [('bf16', 2048, False, False, False), ('bfp16', 4096, False, False, False)]
        variants += [('bfp16', 4096, True, split, preconvert)
                     for split in (False, True) for preconvert in (False, True)]
        variants = [(*variant, False) for variant in variants]
        variants.append(('bfp16', 4096, True, True, True, True))
        for arithmetic, stack, native8, split, preconvert, preconvert_a in variants:
            for mode in ('projection', 'swiglu'):
                with self.subTest(arithmetic=arithmetic, mode=mode):
                    projection, actual_stack, obj, c_tile, kernel = environment['_design'](
                        512, 4096, 2560, mode, 4096, 14336, 0, 0, 8,
                        4 if split else 2, 2, 2, 1 if split and mode == 'swiglu' else 2,
                        True, 1, 'row_major',
                        'down_a' if mode == 'swiglu' else 'compact',
                        environment['FINGERPRINT'], arithmetic, native8, split, preconvert, preconvert_a)
                    self.assertEqual(projection.source_path, ROOT / 'w4a16_prefill_upstream.cc')
                    self.assertEqual(projection.source_sha256,
                                     environment['HASHES']['w4a16_prefill_upstream.cc'])
                    self.assertEqual(actual_stack, stack)
                    self.assertIn(f'-DAIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16='
                                  f'{int(arithmetic == "bfp16")}', projection.compile_flags(2))
                    self.assertIn(f'_{arithmetic}_', obj)
                    self.assertEqual(c_tile.__args__[1].__args__[0], np.uint16 if native8 else np.float32)
                    self.assertIn(f'-DHETEROMEGA_BFP16_NATIVE_LAYOUT={int(native8)}', kernel['compile_flags'])
                    self.assertEqual('_native8_bf16partial' in obj, native8)
                    self.assertIn(f'-DHETEROMEGA_SPLIT_M32_A={int(split)}', kernel['compile_flags'])
                    self.assertIn(f'-DHETEROMEGA_PRECONVERT_B={int(preconvert)}', kernel['compile_flags'])
                    self.assertEqual('_splitm32a' in obj, split)
                    self.assertEqual('_preconvertb' in obj, preconvert)
                    self.assertIn(f'-DHETEROMEGA_PRECONVERT_A={int(preconvert_a)}', kernel['compile_flags'])
                    self.assertEqual('_preconverta' in obj, preconvert_a)
                    objects.append(obj)
        for offset in range(0, len(objects), 2):
            self.assertEqual(objects[offset], objects[offset + 1])
        self.assertEqual(len(set(objects)), len(variants))

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
            for options, expected in (({}, 'bf16'),
                                      ({'arithmetic': 'bfp16', 'output_fifo_depth': 1,
                                        'bfp16_native_layout': True, 'split_m32_a': True,
                                        'preconvert_b': True, 'preconvert_a': True}, 'bfp16')):
                environment[name](*([None] * inputs), m=128, k=256, n=128,
                                  weight_k=256, weight_n=512, **options)
                self.assertEqual(calls[-1][-5], expected)
                self.assertEqual(calls[-1][-4], options.get('bfp16_native_layout', False))
                self.assertEqual(calls[-1][-3], options.get('split_m32_a', False))
                self.assertEqual(calls[-1][-2], options.get('preconvert_b', False))
                self.assertEqual(calls[-1][-1], options.get('preconvert_a', False))
                self.assertEqual(calls[-1][12], options.get('output_fifo_depth', 2))

    def test_real_cli_manifest_and_compile_options_match_arithmetic(self):
        tree, base = _graph_environment()
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'main')
        for mode in ('projection', 'swiglu'):
            for selection in (None, 'bf16', 'bfp16', 'bfp16_native8',
                               'bfp16_split', 'bfp16_preconvert', 'bfp16_split_preconvert',
                               'bfp16_split_preconvert_a'):
                native8 = selection not in (None, 'bf16', 'bfp16')
                preconvert_a = selection == 'bfp16_split_preconvert_a'
                split = selection in ('bfp16_split', 'bfp16_split_preconvert') or preconvert_a
                preconvert = selection in ('bfp16_preconvert', 'bfp16_split_preconvert') or preconvert_a
                arithmetic = 'bfp16' if native8 else selection or 'bf16'
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
                        if selection:
                            argv += ['--output-layout', 'row_major']
                    else:
                        argv += ['--output-layout', 'down_a']
                        if selection:
                            argv += ['--max-reuse', '4', '--activation-fifo-depth', '1',
                                     '--output-fifo-depth', '1']
                    if selection:
                        argv += ['--arithmetic', arithmetic]
                    if native8:
                        argv += ['--bfp16-native-layout']
                    if split:
                        argv += ['--split-m32-a', '--activation-fifo-depth', '2']
                    if preconvert:
                        argv += ['--preconvert-b']
                    if preconvert_a:
                        argv += ['--preconvert-a']
                    with patch.object(sys, 'argv', argv):
                        environment['main']()
                    manifest = json.loads(Path(str(binary) + '.json').read_text())
                    self.assertEqual(manifest['kind'], f'w4a16_upstream_{arithmetic}')
                    for name in ('arithmetic', 'compute_format'):
                        self.assertEqual(manifest[name], arithmetic)
                    self.assertEqual(calls[0]['compile_kwargs']['arithmetic'], arithmetic)
                    self.assertEqual(manifest['bfp16_native_layout'], native8)
                    self.assertEqual(manifest['accumulator_format'], 'bf16' if native8 else 'float32')
                    self.assertEqual(calls[0]['compile_kwargs']['bfp16_native_layout'], native8)
                    self.assertEqual(manifest['split_m32_a'], split)
                    self.assertEqual(manifest['preconvert_b'], preconvert)
                    self.assertEqual(manifest['preconvert_a'], preconvert_a)
                    self.assertEqual(manifest['activation_m_reuse'], 2 if split else manifest['m_reuse'])
                    self.assertEqual(manifest['worker_stack_size'], 4096 if arithmetic == 'bfp16' else 2048)
                    self.assertEqual(manifest['weight_tile_bytes'], 4352)
                    self.assertEqual(manifest['dependency_sha256'], base['HASHES'])
                    self.assertEqual(manifest['input_layout'], 'row_major')
                    output_layout = ('down_a' if mode == 'swiglu' else
                                     'row_major' if selection else 'compact')
                    self.assertEqual(manifest['output_layout'], output_layout)
                    self.assertEqual(calls[0]['compile_kwargs']['output_layout'], output_layout)
                    self.assertEqual(manifest['m_reuse'], 4 if mode == 'projection' or selection else 2)
                    self.assertEqual(manifest['activation_fifo_depth'],
                                     2 if split else 1 if mode == 'projection' or selection else 2)
                    output_depth = 1 if mode == 'swiglu' and selection else 2
                    self.assertEqual(manifest['output_fifo_depth'], output_depth)
                    self.assertEqual(calls[0]['compile_kwargs']['output_fifo_depth'], output_depth)
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
