"""CPU checks for arithmetic selection, artifact provenance and cache isolation."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from prefill_schedule import plan_prefill
from prefill_gate_up_schedule import plan_gate_up
from prefill_swiglu_schedule import plan_swiglu, swiglu_logical_column
from projection_arithmetic import (ARITHMETIC_CHOICES, ARITHMETIC_SOURCE_SHA,
    UPSTREAM_KERNEL_COMMIT, projection_arithmetic, validate_projection_identity)


ROOT = Path(__file__).parent
ORIGINAL_BF16_SHA = '4aceceb605b57b4ca224dee4b1c4b4ec8d5013225262cf8232ffbb3dc0c33ee7'
COMPILER_COMMIT = '7e00b57955e108fe9d8e9419f5828a0c7e650858'


class ProjectionArithmeticTests(unittest.TestCase):
    def test_default_retains_checkpointed_native_bf16_source(self):
        projection = projection_arithmetic()
        self.assertEqual(projection.arithmetic, 'bf16')
        self.assertEqual(projection.source_path.name, 'w4a16_prefill_reuse.cc')
        self.assertEqual(projection.source_sha256, ORIGINAL_BF16_SHA)
        self.assertEqual(projection.compile_flags(2), ['-DHETEROMEGA_M_REUSE=2'])
        self.assertEqual(projection.stack_size, 2048)
        self.assertIsNone(projection.manifest_fields()['upstream_kernel_commit'])

    def test_bfp16_is_an_explicit_distinct_source_and_compile_mode(self):
        native = projection_arithmetic('bf16')
        block = projection_arithmetic('bfp16')
        self.assertEqual(block.source_path.name, 'w4a16_prefill_bfp16.cc')
        self.assertEqual(block.stack_size, 4096)
        self.assertNotEqual(native.source_sha256, block.source_sha256)
        self.assertIn('-DAIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16=1', block.compile_flags(2))
        self.assertEqual(block.manifest_fields()['upstream_kernel_commit'], UPSTREAM_KERNEL_COMMIT)
        for reuse in (1, 2, 4):
            with self.subTest(reuse=reuse):
                self.assertNotEqual(native.object_name(reuse), block.object_name(reuse))
                self.assertIn(block.source_sha256, block.object_name(reuse))
                self.assertIn(ARITHMETIC_SOURCE_SHA, block.object_name(reuse))
        self.assertEqual(len({block.object_name(reuse) for reuse in (1, 2, 4)}), 3)

    def test_unknown_arithmetic_and_unsupported_reuse_are_rejected(self):
        for mode in ('bfloat16', 'BFP16', '', None):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'unknown projection arithmetic'):
                projection_arithmetic(mode)
        with self.assertRaisesRegex(ValueError, 'M reuse'):
            projection_arithmetic().compile_flags(3)

    def test_source_or_helper_change_invalidates_cached_identity(self):
        projection = projection_arithmetic('bfp16')
        validate_projection_identity(projection, projection.source_sha256, ARITHMETIC_SOURCE_SHA)
        for source_sha, helper_sha in ((ORIGINAL_BF16_SHA, ARITHMETIC_SOURCE_SHA),
                                       (projection.source_sha256, 'stale-helper')):
            with self.subTest(source_sha=source_sha, helper_sha=helper_sha):
                with self.assertRaisesRegex(ValueError, 'rebuild the graph'):
                    validate_projection_identity(projection, source_sha, helper_sha)

    def test_all_real_cli_entry_points_propagate_selected_hash_and_provenance(self):
        # Execute the actual CLI function body with only its hardware launch
        # replaced. This tests artifact/CLI integration without importing AIE,
        # torch, creating devices or pretending to compile a graph.
        variants = (('w4a16_prefill_reuse', 'w4a16_prefill_bf16', '-N'),
                    ('w4a16_gate_up', 'w4a16_gate_up_bf16', '-P'),
                    ('w4a16_swiglu', 'w4a16_swiglu_bf16', '-P'))
        for graph, kind, width_arg in variants:
            for mode in ARITHMETIC_CHOICES:
                with self.subTest(graph=graph, mode=mode), tempfile.TemporaryDirectory() as tmp:
                    calls = []
                    artifact = Path(tmp) / 'kernel.xclbin'
                    insts = Path(tmp) / 'insts.bin'
                    artifact.write_bytes(b'not a real xclbin')
                    insts.write_bytes(b'not real instructions')

                    def compile_args(parser, **unused):
                        parser.add_argument('--xclbin-path')
                        parser.add_argument('--insts-path')
                        parser.add_argument('--emit-mlir', action='store_true')

                    environment = dict(argparse=argparse, hashlib=hashlib, json=json,
                        Path=Path, __doc__='CPU artifact provenance check',
                        ARITHMETIC_CHOICES=ARITHMETIC_CHOICES,
                        ARITHMETIC_SOURCE_SHA=ARITHMETIC_SOURCE_SHA,
                        projection_arithmetic=projection_arithmetic,
                        add_compile_args=compile_args, device_from_args=lambda *a, **kw: None,
                        run_design_cli=lambda *a, **kw: calls.append(kw),
                        plan_prefill=plan_prefill, plan_gate_up=plan_gate_up,
                        plan_swiglu=plan_swiglu, swiglu_logical_column=swiglu_logical_column,
                        TARGET_COMMIT=COMPILER_COMMIT, **{graph: object()})
                    for key, filename in (('SCHEDULE_SHA', 'prefill_schedule.py'),
                            ('GATE_UP_SCHEDULE_SHA', 'prefill_gate_up_schedule.py'),
                            ('SWIGLU_SCHEDULE_SHA', 'prefill_swiglu_schedule.py'),
                            ('SILU_SOURCE_SHA', 'silu_mul.cc')):
                        environment[key] = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()
                    tree = ast.parse((ROOT / (graph + '.py')).read_text())
                    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                                and node.name == 'main')
                    exec(compile(ast.Module(body=[main], type_ignores=[]), graph, 'exec'), environment)
                    argv = [graph, '-M', '128', '-K', '128', width_arg, '128',
                            '--xclbin-path', str(artifact), '--insts-path', str(insts)]
                    if mode != 'bf16':  # Exercise the actual default as well.
                        argv += ['--arithmetic', mode]
                    with patch.object(sys, 'argv', argv):
                        environment['main']()
                    projection = projection_arithmetic(mode)
                    self.assertEqual(len(calls), 1)
                    kwargs = calls[0]['compile_kwargs']
                    self.assertEqual(kwargs['arithmetic'], mode)
                    self.assertEqual(kwargs['source_sha256'], projection.source_sha256)
                    self.assertEqual(kwargs['arithmetic_source_sha256'], ARITHMETIC_SOURCE_SHA)
                    manifest = json.loads(Path(str(artifact) + '.json').read_text())
                    self.assertEqual(manifest['kind'], kind)
                    self.assertEqual(manifest['compute_format'], mode)
                    self.assertEqual(manifest['source_sha256'], projection.source_sha256)
                    self.assertEqual(manifest['target_mlir_aie_commit'], COMPILER_COMMIT)
                    self.assertEqual(manifest['weight_tile_bytes'], 2144)
                    for key, value in projection.manifest_fields().items():
                        self.assertEqual(manifest[key], value)


if __name__ == '__main__':
    unittest.main()
