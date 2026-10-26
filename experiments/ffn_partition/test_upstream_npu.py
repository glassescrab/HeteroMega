"""CPU checks for unchanged upstream weights and native-BF16 artifact identity.

Fake runners return deterministic buffers, not FFN arithmetic. Passing these
checks establishes host routing/provenance only, never NPU execution or speed.
"""

from hashlib import sha256
import argparse
import ast
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

import upstream_npu as backend
from upstream_weights import UpstreamWeightBuffer, upstream_weight_bytes
from contract import packed_output_to_activation
from prefill_reference import unpack_activations, bf16_bits


def _weights(hidden=256, intermediate=512):
    def make(k, n, offset):
        data = (np.arange(upstream_weight_bytes(k, n), dtype=np.uint32) + offset).astype(np.uint8)
        data.flags.writeable = False
        return UpstreamWeightBuffer(data, k, n)
    return make(hidden, intermediate, 3), make(hidden, intermediate, 47), make(intermediate, hidden, 83)


def _write_artifact(spec, contract=True):
    directory = spec["directory"]
    directory.mkdir(parents=True, exist_ok=True)
    binary, instructions = b"CPU TEST MOCK -- NOT AN NPU BINARY", b"MOCK"
    (directory / "final.xclbin").write_bytes(binary)
    (directory / "insts.bin").write_bytes(instructions)
    manifest = dict(spec["expected"], xclbin_sha256=sha256(binary).hexdigest(),
                    insts_sha256=sha256(instructions).hexdigest())
    (directory / "final.xclbin.json").write_text(json.dumps(manifest))
    if contract:
        (directory / "build_contract.json").write_text(json.dumps(backend._build_contract(spec)))


def _write_artifacts(root, weights, start=128):
    specs = backend._ffn_specs(128, 256, 128, *weights, root, start)
    for spec in specs.values():
        _write_artifact(spec)
    return specs


class _ObservedRunner:
    def __init__(self, xclbin, insts, specs):
        self.manifest = json.loads(Path(str(xclbin) + ".json").read_text())
        self.specs = specs
        self.inputs = {}
        self.input_write_counts = [0] * (len(specs) - 1)
        self.completed_dispatches = 0
        self.copies = []
        self.result = np.arange(np.prod(specs[-1][0]), dtype=np.uint16)

    def write_input(self, index, value):
        shape, dtype = self.specs[index]
        if value.shape != shape or value.dtype != np.dtype(dtype):
            raise AssertionError("uploaded buffer does not match graph BO geometry")
        self.inputs[index] = value  # Capture exact identity, deliberately no copy.
        self.input_write_counts[index] += 1

    def dispatch_wait(self):
        if set(self.inputs) != set(range(len(self.specs) - 1)):
            raise AssertionError("dispatch has uninitialized input BOs")
        self.completed_dispatches += 1
        return 0.0  # Synthetic placeholder; this is never measured hardware time.

    def output_bits(self, *, copy=True):
        self.copies.append(copy)
        return self.result.copy() if copy else self.result


class UpstreamNpuTests(unittest.TestCase):
    def test_kernel_ablations_have_distinct_cache_identity_and_strict_options(self):
        with tempfile.TemporaryDirectory() as root:
            weights = _weights()
            base = backend._ffn_specs(512, 256, 128, *weights, root)
            variants = ({'vector_zero': True}, {'mmul_m_reuse': 2},
                {'output_layout': 'down_a'},
                {'swiglu_input_layout': 'row_major'},
                {'down_reuse': 4, 'down_activation_fifo_depth': 1})
            for options in variants:
                specs = backend._ffn_specs(512, 256, 128, *weights, root, **options)
                self.assertTrue(any(specs[key]['directory'] != base[key]['directory'] for key in base))
                for spec in specs.values():
                    _write_artifact(spec)
                    backend._load_artifact(spec)
            for options in ({'vector_zero': 1}, {'mmul_m_reuse': True},
                    {'down_reuse': 4}, {'down_activation_fifo_depth': 3},
                    {'output_layout': 'unknown'}, {'swiglu_reuse': 4}):
                with self.subTest(options=options), self.assertRaises(ValueError):
                    backend._ffn_specs(512, 256, 128, *weights, root, **options)

    def test_direct_down_layout_borrows_only_until_staging_and_returns_owned_output(self):
        weights = _weights()
        with tempfile.TemporaryDirectory() as root:
            specs = backend._ffn_specs(128, 256, 128, *weights, root, output_layout='down_a')
            for spec in specs.values():
                _write_artifact(spec)
            with patch.object(backend, 'PersistentXrtRunner', _ObservedRunner), \
                    patch.object(backend, 'packed_output_to_activation', side_effect=AssertionError('unexpected permutation')):
                branch = backend.UpstreamNpuFFN(128, 256, 128, *weights, root,
                    output_layout='down_a', copy_output_bits=False)
                output = branch.run(np.zeros((128, 256), np.uint16))
                self.assertIs(branch.down.inputs[0], branch.swiglu.result)
                saved = output.copy()
                branch.down.result.fill(7)
                branch.swiglu.result.fill(9)
                branch.run(np.zeros((128, 256), np.uint16))
            np.testing.assert_array_equal(output, saved)
            self.assertEqual(branch.metadata['kernel_options']['output_layout'], 'down_a')

    def test_row_major_input_skips_pack_and_preserves_noncontiguous_values(self):
        weights = _weights()
        with tempfile.TemporaryDirectory() as root:
            specs = backend._ffn_specs(128, 256, 128, *weights, root,
                                      swiglu_input_layout='row_major')
            for spec in specs.values():
                _write_artifact(spec)
            with patch.object(backend, 'PersistentXrtRunner', _ObservedRunner), \
                    patch.object(backend, '_pack_activation_bits', side_effect=AssertionError('unexpected pack')):
                branch = backend.UpstreamNpuFFN(128, 256, 128, *weights, root,
                                               swiglu_input_layout='row_major')
                x = (np.arange(128 * 512, dtype=np.uint16) % 512).reshape(128, 512)[:, ::2]
                self.assertFalse(x.flags.c_contiguous)
                branch.run(x)
                np.testing.assert_array_equal(branch.swiglu.inputs[0].reshape(x.shape), x)
                self.assertTrue(branch.swiglu.inputs[0].flags.c_contiguous)

    def test_pipeline_depth_is_strict_and_changes_both_artifact_identities(self):
        with tempfile.TemporaryDirectory() as root:
            weights = _weights()
            serial = backend._ffn_specs(128, 256, 128, *weights, root, 128,
                                        segment_pipeline_depth=1)
            pipeline = backend._ffn_specs(128, 256, 128, *weights, root, 128,
                                          segment_pipeline_depth=2)
            for label in serial:
                self.assertNotEqual(serial[label]['directory'], pipeline[label]['directory'])
                self.assertEqual(serial[label]['expected']['segment_pipeline_depth'], 1)
                self.assertEqual(pipeline[label]['expected']['segment_pipeline_depth'], 2)
                self.assertEqual(serial[label]['arguments'][-2:], ['--segment-pipeline-depth', '1'])
                _write_artifact(serial[label])
                backend._load_artifact(serial[label])
                manifest_path = serial[label]['directory'] / 'final.xclbin.json'
                manifest = json.loads(manifest_path.read_text())
                manifest['segment_pipeline_depth'] = 2
                manifest_path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, 'segment_pipeline_depth'):
                    backend._load_artifact(serial[label])
            for invalid in (True, False, 0, 3, 1.0, 2.0, '2', None):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    backend._ffn_specs(128, 256, 128, *weights, root,
                                       segment_pipeline_depth=invalid)

    def test_real_graph_cli_manifest_matches_adapter_contract(self):
        # Execute the graph's actual CLI manifest writer, replacing only the
        # device compiler. This catches mismatches hidden by mock manifests.
        with tempfile.TemporaryDirectory() as root:
            specs = backend._ffn_specs(128, 256, 128, *_weights(), root, 128)
            for spec in specs.values():
                with self.subTest(mode=spec["expected"]["mode"]):
                    directory = spec["directory"]
                    directory.mkdir(parents=True)
                    binary, instructions = directory / "final.xclbin", directory / "insts.bin"
                    binary.write_bytes(b"CPU TEST MOCK -- NOT AN NPU BINARY")
                    instructions.write_bytes(b"MOCK")

                    def compile_args(parser, **unused):
                        parser.add_argument('--xclbin-path')
                        parser.add_argument('--insts-path')
                        parser.add_argument('--emit-mlir', action='store_true')

                    source = (backend.KERNEL_ROOT / backend.GRAPH).read_text()
                    main = next(node for node in ast.parse(source).body
                                if isinstance(node, ast.FunctionDef) and node.name == 'main')
                    hashes = backend._source_contract()
                    environment = dict(argparse=argparse, hashlib=SimpleNamespace(sha256=sha256),
                        json=json, Path=Path, __doc__='CPU graph manifest check',
                        add_compile_args=compile_args, device_from_args=lambda *a, **k: None,
                        run_design_cli=lambda *a, **k: None, plan_upstream=backend.plan_upstream,
                        upstream_worker_stack_size=backend.upstream_worker_stack_size,
                        upstream_swiglu=object(), upstream_projection=object(),
                        FINGERPRINT=sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
                        HASHES=hashes, UPSTREAM_LAYOUT_VERSION=backend.UPSTREAM_LAYOUT_VERSION,
                        UPSTREAM_KERNEL_COMMIT=backend.UPSTREAM_KERNEL_COMMIT,
                        TARGET_COMMIT=backend.TARGET_COMMIT)
                    exec(compile(ast.Module(body=[main], type_ignores=[]), backend.GRAPH, 'exec'), environment)
                    argv = [backend.GRAPH, *spec['arguments'], '--xclbin-path', str(binary),
                            '--insts-path', str(instructions)]
                    with patch.object(sys, 'argv', argv):
                        environment['main']()
                    backend._validate_manifest(spec)

    def test_full_buffers_upload_by_identity_once_with_no_packing(self):
        weights = _weights()
        snapshots = [w.data.copy() for w in weights]
        with tempfile.TemporaryDirectory() as root:
            _write_artifacts(root, weights)
            # The old compact packer must never serve as an implicit fallback.
            with patch("npu_backend.pack_weights", side_effect=AssertionError("repacked weights")):
                with patch.object(backend, "PersistentXrtRunner", _ObservedRunner):
                    branch = backend.UpstreamNpuFFN(128, 256, 128, *weights, root, channel_start=128)
                    self.assertIs(branch.swiglu.inputs[1], weights[0].data)
                    self.assertIs(branch.swiglu.inputs[2], weights[1].data)
                    self.assertIs(branch.down.inputs[1], weights[2].data)
                    x = (np.arange(128 * 256, dtype=np.uint16) % 512).reshape(128, 256)
                    first = branch.run(x)
                    branch.run(x + np.uint16(1))
            for weight, original in zip(weights, snapshots):
                np.testing.assert_array_equal(weight.data, original)
            self.assertEqual(branch.last_diagnostics["weight_upload_counts"],
                             {"gate": 1, "up": 1, "down": 1})
            self.assertEqual(branch.last_diagnostics["completed_dispatches_total"], 4)
            self.assertEqual(branch.metadata["fixed_weight_bytes"], sum(w.nbytes for w in weights))
            self.assertFalse(branch.metadata["weight_repacking"])
            self.assertTrue(branch.metadata["full_weight_buffers"])
            self.assertEqual(branch.metadata["compute_format"], "bf16")
            self.assertEqual(branch.metadata["segment_pipeline_depth"], 2)
            self.assertEqual(branch.metadata["channel_start"], 128)
            self.assertEqual(first.shape, (128, 256))
            self.assertEqual(first.dtype, np.uint16)
            np.testing.assert_array_equal(
                bf16_bits(unpack_activations(branch.swiglu.inputs[0], 128, 256)), x + np.uint16(1))
            np.testing.assert_array_equal(branch.down.inputs[0],
                packed_output_to_activation(branch.swiglu.result, 128, 128))
            first_copy = first.copy()
            branch.down.result.fill(0)
            np.testing.assert_array_equal(first, first_copy)

    def test_gate_up_and_down_dma_slices_use_full_original_geometry(self):
        weights = _weights()
        with tempfile.TemporaryDirectory() as root:
            specs = backend._ffn_specs(128, 256, 128, *weights, root, 128)
            gate, down = specs["swiglu"]["expected"], specs["down"]["expected"]
            self.assertEqual((gate["k"], gate["n"], gate["weight_k"], gate["weight_n"],
                              gate["k_start"], gate["n_start"]), (256, 128, 256, 512, 0, 128))
            self.assertEqual((down["k"], down["n"], down["weight_k"], down["weight_n"],
                              down["k_start"], down["n_start"]), (128, 256, 512, 256, 128, 0))
            first = backend._ffn_specs(128, 256, 128, *weights, root, 0)
            self.assertNotEqual(first["swiglu"]["directory"], specs["swiglu"]["directory"])
            self.assertNotEqual(first["down"]["directory"], specs["down"]["directory"])

    def test_manifest_rejects_arithmetic_layout_and_source_substitution(self):
        with tempfile.TemporaryDirectory() as root:
            spec = _write_artifacts(root, _weights())["swiglu"]
            backend._load_artifact(spec)
            path = spec["directory"] / "final.xclbin.json"
            original = json.loads(path.read_text())
            for key, replacement in (("arithmetic", "bfp16"), ("compute_format", "bfp16"),
                    ("weight_layout", "compact"), ("weight_tile_bytes", 2144),
                    ("weight_n", 128), ("n_start", 0), ("source_sha256", "stale"),
                    ("graph_sha256", "stale"), ("schedule_sha256", "stale"),
                    ("weight_layout_sha256", "stale"), ("dependency_sha256", {}),
                    ("worker_count", 16), ("cols", 4), ("worker_stack_size", 4096)):
                with self.subTest(field=key):
                    path.write_text(json.dumps(dict(original, **{key: replacement})))
                    with self.assertRaisesRegex(ValueError, f"manifest {key}"):
                        backend._load_artifact(spec)
            path.write_text(json.dumps(original))
            (spec["directory"] / "final.xclbin").write_bytes(b"wrong binary")
            with self.assertRaisesRegex(ValueError, "artifact hash mismatch"):
                backend._load_artifact(spec)

    def test_build_passes_source_geometry_and_reuses_certified_artifacts(self):
        weights = _weights()
        with tempfile.TemporaryDirectory() as root:
            specs = backend._ffn_specs(128, 256, 128, *weights, root, 128)
            by_directory = {str(s["directory"]): s for s in specs.values()}

            def fake_compile(command, **unused):
                directory = str(Path(command[command.index("--xclbin-path") + 1]).parent)
                spec = by_directory[directory]
                self.assertEqual(command[0], "CPU_TEST_COMPILER_STUB")
                self.assertEqual(command[2:2 + len(spec["arguments"])], spec["arguments"])
                self.assertNotIn("bfp16", command)
                _write_artifact(spec, contract=False)
                return SimpleNamespace(returncode=0)

            with patch.object(backend.subprocess, "run", side_effect=fake_compile) as compile_call:
                artifacts = backend.build_upstream_artifacts(128, 256, 128, *weights, root,
                    channel_start=128, python_executable="CPU_TEST_COMPILER_STUB")
                self.assertEqual(set(artifacts), {"swiglu", "down"})
                self.assertEqual(compile_call.call_count, 2)
                backend.build_upstream_artifacts(128, 256, 128, *weights, root, channel_start=128)
                self.assertEqual(compile_call.call_count, 2)

    def test_invalid_weight_geometry_and_input_rejected_before_dispatch(self):
        weights = _weights()
        with tempfile.TemporaryDirectory() as root:
            for start in (32, 64, 448, -128):
                with self.subTest(start=start), self.assertRaises(ValueError):
                    backend._ffn_specs(128, 256, 128, *weights, root, start)
            with self.assertRaises(TypeError):
                backend._ffn_specs(128, 256, 128, weights[0].data, weights[1], weights[2], root)
            with self.assertRaisesRegex(ValueError, "full gate/up"):
                backend._ffn_specs(128, 256, 128, weights[0], weights[1], weights[0], root)
            _write_artifacts(root, weights)
            with patch.object(backend, "PersistentXrtRunner", _ObservedRunner):
                branch = backend.UpstreamNpuFFN(128, 256, 128, *weights, root,
                                              channel_start=128, copy_output_bits=False)
            for invalid in (np.zeros((128, 256), np.float32),
                            np.zeros((128, 128), np.uint16),
                            np.full((128, 256), 0x7F80, np.uint16)):
                with self.assertRaises(ValueError):
                    branch.run(invalid)
            self.assertEqual(branch.swiglu.completed_dispatches, 0)
            branch.run(np.zeros((128, 256), np.uint16))
            self.assertEqual(branch.swiglu.copies, [False])
            self.assertEqual(branch.down.copies, [False])


class UpstreamPipelineBenchmarkTests(unittest.TestCase):
    @staticmethod
    def _module():
        from experiments.ffn_partition import benchmark_upstream_pipeline
        return benchmark_upstream_pipeline

    def test_abba_and_baab_order_and_bitwise_regression_rejection(self):
        benchmark = self._module()
        self.assertEqual([d for _, _, d in benchmark.block_order(2)], [1, 2, 2, 1] * 2)
        self.assertEqual([d for _, _, d in benchmark.block_order(1, 'BAAB')], [2, 1, 1, 2])
        output = np.full((2, 2), 0x3F80, np.uint16)
        entry = dict(segment_pipeline_depth=2, runs=[dict(input='signed_a')],
            warmup=[dict(input='signed_a', output_sha256=benchmark._hash(output), finite=True)],
            completed_dispatches=dict(swiglu=2, down=2),
            fixed_weight_upload_counts=dict(gate=1, up=1, down=1))
        candidate = output.copy()
        candidate[0, 0] += 1  # Numerically close, but schedule changes must be exact.
        benchmark._compare_outputs(entry, [candidate], {'signed_a': output})
        self.assertEqual(entry['status'], 'failed')
        self.assertTrue(entry['checks']['original_tolerances_vs_serial_control'])
        self.assertFalse(entry['checks']['all_identical_to_serial_control'])

    def test_isolated_worker_fixture_transport_counts_and_outputs(self):
        benchmark = self._module()

        class FakeBranch:
            def __init__(self, m, hidden, channels, *weights_and_root, **kwargs):
                self.metadata = {'synthetic_cpu_test': True}
                self.swiglu = SimpleNamespace(completed_dispatches=0, input_write_counts=[0, 1, 1])
                self.down = SimpleNamespace(completed_dispatches=0, input_write_counts=[0, 1])
                self.runners = dict(swiglu=self.swiglu, down=self.down)
                for weight in weights_and_root[:3]:
                    if weight.data.flags.writeable:
                        raise AssertionError('worker weight file must be read-only')

            def run(self, x):
                for runner in self.runners.values():
                    runner.completed_dispatches += 1
                self.last_diagnostics = dict(dispatch_wait_us=dict(swiglu=0.0, down=0.0))
                return x.copy()

        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            args = SimpleNamespace(m=128, hidden=256, channels=128, artifact_root=root,
                channel_start=128, warmup=2, iterations=2, block_timeout=30)
            inputs = [(label, np.full((128, 256), bits, np.uint16))
                      for label, bits in (('signed_a', 0x3F80), ('signed_b', 0x4000))]
            fixture_paths = benchmark._fixture_files(root, _weights(), inputs)
            entry = dict(segment_pipeline_depth=2)

            def fake_process(command, **unused):
                self.assertEqual(command[1:3], ['-m', 'experiments.ffn_partition.benchmark_upstream_pipeline'])
                code = benchmark._worker_main(Path(command[-1]))
                return SimpleNamespace(returncode=code, stdout='CPU mocked child process')

            with patch.object(benchmark, 'UpstreamNpuFFN', FakeBranch), \
                 patch.object(benchmark.subprocess, 'run', side_effect=fake_process):
                outputs = benchmark._subprocess_block(args, fixture_paths, entry, root / 'child')
            benchmark._compare_outputs(entry, outputs, dict(inputs))
            self.assertEqual(entry['status'], 'passed')
            self.assertEqual(entry['completed_dispatches'], dict(swiglu=4, down=4))
            self.assertEqual(len(entry['warmup']), 2)
            self.assertEqual(len(entry['runs']), 2)
            for output, (_, original) in zip(outputs, inputs):
                np.testing.assert_array_equal(output, original)


if __name__ == "__main__":
    unittest.main()
