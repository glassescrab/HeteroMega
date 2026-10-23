"""CPU-only regression checks for the new SwiGLU correctness diagnostic.

Synthetic oracle snapshots and fault injection test the validation gates.
They are not evidence of NPU execution or compiled-kernel correctness.
"""

from hashlib import sha256
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from experiments.ffn_partition import check_swiglu as checker
from experiments.ffn_partition import npu_backend as backend
from experiments.ffn_partition.contract import bf16, random_weights, reference_full
from prefill_reference import (bf16_bits, bf16_from_bits, pack_output,
                               projection_reference, unpack_activations, unpack_weights)
from reference import silu_multiply


def _mock_artifacts(root, channels, fuse_swiglu):
    """Exercise real build/load contracts with visibly fake binary bytes."""
    specs = backend._artifact_specs(128, 128, channels, root, columns=8,
                                    design='array8', fuse_gate_up=not fuse_swiglu,
                                    fuse_swiglu=fuse_swiglu)
    for spec in specs.values():
        folder = spec['directory']
        folder.mkdir(parents=True, exist_ok=True)
        xclbin, instructions = b'CPU SWIGLU TEST MOCK -- NOT NPU CODE', b'MOCK'
        (folder/'final.xclbin').write_bytes(xclbin)
        (folder/'insts.bin').write_bytes(instructions)
        manifest = dict(spec['expected'], target_mlir_aie_commit=backend.TARGET_COMMIT,
                        source_sha256=spec['source_sha256'][
                            f"npu/ffn/{backend._kernel_source(spec['stem'])}.cc"],
                        xclbin_sha256=sha256(xclbin).hexdigest(),
                        insts_sha256=sha256(instructions).hexdigest())
        (folder/'final.xclbin.json').write_text(json.dumps(manifest))
        (folder/'build_contract.json').write_text(json.dumps(backend._build_contract(spec)))
    return specs


class _SwiGLUOracleRunner:
    """CPU arithmetic instead of device execution; never used by benchmarks."""

    def __init__(self, xclbin, insts, specs, output_count=1):
        self.manifest = json.loads(Path(str(xclbin)+'.json').read_text())
        self.specs, self.output_count = specs, output_count
        self.inputs, self.completed_dispatches = {}, 0
        self.input_write_counts = [0] * (len(specs) - output_count)

    def write_input(self, index, value):
        shape, dtype = self.specs[index]
        if value.shape != shape or value.dtype != np.dtype(dtype):
            raise AssertionError('uploaded BO differs from compiled shape or dtype')
        self.inputs[index] = value.copy()
        self.input_write_counts[index] += 1

    def dispatch_wait(self):
        if set(self.inputs) != {0, 1}:
            raise AssertionError('both input BOs must be initialized')
        manifest = self.manifest
        if manifest['kind'] == 'silu_mul_bf16':
            self.result = bf16_bits(silu_multiply(bf16_from_bits(self.inputs[0]),
                                                 bf16_from_bits(self.inputs[1]), True))
        else:
            x = unpack_activations(self.inputs[0], manifest['m'], manifest['k'])
            weight = unpack_weights(self.inputs[1], manifest['k'], manifest['n'])
            projected = projection_reference(x, weight)
            if manifest['kind'] == 'w4a16_swiglu_bf16':
                p = manifest['channels']
                self.result = pack_output(silu_multiply(projected[:, :p], projected[:, p:], True))
            elif self.output_count == 2:
                p = manifest['channels']
                self.result = (pack_output(projected[:, :p]), pack_output(projected[:, p:]))
            else:
                self.result = pack_output(projected)
        self.completed_dispatches += 1
        return 1.0  # Synthetic interval, never a performance result.

    def output_bits(self, index=0, *, copy=True):
        result = self.result[index] if self.output_count == 2 else self.result
        return result.copy() if copy else result


class SwiGLUBackendOracleTests(unittest.TestCase):
    def test_swiglu_branch_preserves_packed_z_and_full_ffn_with_fixed_weights(self):
        for channels in (128, 384):
            with self.subTest(channels=channels), tempfile.TemporaryDirectory() as root:
                weights = random_weights(128, channels, seed=808)
                x = np.random.default_rng(809).normal(0, .5, (128, 128)).astype(np.float32)
                _mock_artifacts(root, channels, True)
                with patch.object(backend, 'PersistentXrtRunner', _SwiGLUOracleRunner):
                    branch = backend.NPUBranch(weights.gate, weights.up, weights.down,
                                               128, root, fuse_swiglu=True)
                    self.assertTrue(branch.fuse_gate_up)
                    self.assertEqual(set(branch.runners), {'swiglu', 'down'})
                    self.assertFalse(hasattr(branch, 'silu'))
                    self.assertEqual(branch.metadata['host_bo_io_bytes_per_run_estimate'],
                                     4 * 128 * 128 + 4 * 128 * channels)
                    fixed = {name: runner.inputs[1].copy()
                             for name, runner in branch.projection_runners.items()}
                    snapshots = []
                    for index, value in enumerate((x, -x, np.zeros_like(x), x)):
                        result = branch.run(bf16_bits(value))
                        expected_z = pack_output(checker._reference_z(value, weights))
                        np.testing.assert_array_equal(branch.swiglu.output_bits(), expected_z)
                        np.testing.assert_array_equal(result, bf16_bits(reference_full(value, weights)))
                        snapshots.append(result.copy())
                        for name, runner in branch.projection_runners.items():
                            self.assertEqual(runner.input_write_counts, [index + 1, 1])
                            np.testing.assert_array_equal(runner.inputs[1], fixed[name])
                        self.assertEqual(branch.last_diagnostics['completed_dispatches_total'], 2*(index+1))
                        self.assertEqual(set(branch.last_diagnostics['dispatch_wait_us']), {'swiglu', 'down'})
                    self.assertFalse(np.array_equal(snapshots[0], snapshots[1]))
                    np.testing.assert_array_equal(snapshots[0], snapshots[3])

    def test_checker_reads_z_and_complete_results_from_both_actual_backend_paths(self):
        weights = random_weights(128, 384, seed=811)
        rng = np.random.default_rng(812)
        a, b = [bf16(rng.normal(0, .5, (128, 128)).astype(np.float32)) for _ in range(2)]
        inputs = [('random_a', a), ('random_b', b), ('zero', np.zeros_like(a)), ('repeat_a', a.copy())]
        references = {label: {'z': checker._reference_z(x, weights), 'ffn': reference_full(x, weights)}
                      for label, x in inputs}
        with tempfile.TemporaryDirectory() as root:
            for fused in (False, True):
                _mock_artifacts(root, 384, fused)
            outputs = {}
            with patch.object(backend, 'PersistentXrtRunner', _SwiGLUOracleRunner):
                for fused in (False, True):
                    values, metadata = checker._run_variant(weights, inputs,
                        SimpleNamespace(m=128, artifact_root=root), fused)
                    checks = checker._variant_checks(values, metadata, references, 128, 128, 384, fused)
                    self.assertTrue(all(check['passed'] for check in checks.values()), checks)
                    self.assertEqual(len(metadata['output_sha256']), 4)
                    outputs[fused] = values
            for baseline, candidate in zip(outputs[False], outputs[True]):
                for stage in ('z', 'ffn'):
                    self.assertTrue(checker._exact(candidate[stage], baseline[stage])['passed'])

    def test_swiglu_build_contract_rejects_stale_output_abi_and_silu_kernel_hash(self):
        with tempfile.TemporaryDirectory() as root:
            spec = _mock_artifacts(root, 384, True)['swiglu']
            backend._load_artifact(spec)
            manifest_path = spec['directory']/'final.xclbin.json'
            original = json.loads(manifest_path.read_text())
            for field, wrong in (('output_count', 2), ('output_order', ['gate', 'up']),
                                  ('silu_source_sha256', 'wrong')):
                changed = dict(original, **{field: wrong})
                manifest_path.write_text(json.dumps(changed))
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                    backend._load_artifact(spec)
            manifest_path.write_text(json.dumps(original))
            contract_path = spec['directory']/'build_contract.json'
            contract = json.loads(contract_path.read_text())
            contract['source_sha256']['npu/ffn/silu_mul.cc'] = 'wrong'
            contract_path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValueError, 'provenance'):
                backend._load_artifact(spec)


class SwiGLUCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = cls.hidden = cls.channels = 128
        cls.weights = random_weights(cls.hidden, cls.channels, seed=263)
        rng = np.random.default_rng(264)
        a, b = [bf16(rng.normal(0, .5, (cls.m, cls.hidden)).astype(np.float32))
                for _ in range(2)]
        cls.inputs = [('random_a', a), ('random_b', b),
                      ('zero', np.zeros_like(a)), ('repeat_a', a.copy())]
        cls.references = {label: {'z': checker._reference_z(x, cls.weights),
                                  'ffn': reference_full(x, cls.weights)}
                          for label, x in cls.inputs}

    def snapshots(self, fused):
        stages = {'swiglu', 'down'} if fused else {'gate_up', 'silu_mul', 'down'}
        projections = stages - {'silu_mul'}
        values = [{'input': label, 'z': pack_output(self.references[label]['z']),
                   'ffn': bf16_bits(self.references[label]['ffn']),
                   'dispatch_deltas': {stage: 1 for stage in stages},
                   'weight_upload_counts': {stage: 1 for stage in projections}}
                  for label, _ in self.inputs]
        metadata = {'completed_dispatches': {stage: 4 for stage in stages},
                    'weight_upload_counts': {stage: 1 for stage in projections},
                    'metadata': {'fuse_swiglu': fused, 'fuse_gate_up': True,
                                 'launches_per_run': len(stages),
                                 'fixed_weight_uploads': len(projections),
                                 'cpu_activation_fallback': False}}
        return values, metadata

    def validate(self, values, metadata, fused=True):
        return checker._variant_checks(values, metadata, self.references,
                                       self.m, self.hidden, self.channels, fused)

    def test_exact_checks_uint16_layout_and_signed_zero(self):
        bits = np.array([0x0000, 0x8000, 0x3F80], np.uint16)
        self.assertTrue(checker._exact(bits.copy(), bits)['passed'])
        changed = bits.copy()
        changed[1] = 0
        self.assertFalse(checker._exact(changed, bits)['passed'])
        self.assertEqual(checker._exact(changed, bits)['mismatched_elements'], 1)
        self.assertFalse(checker._exact(bits.astype(np.uint32), bits)['passed'])
        self.assertFalse(checker._exact(bits.reshape(1, 3), bits)['passed'])
        self.assertFalse(checker._exact(np.zeros(3), np.zeros(3))['passed'])

    def test_reference_z_retains_complete_ffn_numerical_contract(self):
        # Applying the existing down projection to the intermediate oracle
        # must reproduce the established whole-FFN oracle, including rounding.
        for label, _ in self.inputs:
            z = self.references[label]['z']
            actual = bf16(z @ self.weights.down.dequantize(True).T)
            np.testing.assert_array_equal(actual, self.references[label]['ffn'])
        self.assertFalse(np.array_equal(self.references['random_a']['z'],
                                        self.references['random_b']['z']))

    def test_both_variant_contracts_accept_independent_cpu_oracle_snapshots(self):
        for fused in (False, True):
            with self.subTest(fuse_swiglu=fused):
                values, metadata = self.snapshots(fused)
                checks = self.validate(values, metadata, fused)
                self.assertTrue(all(value['passed'] for value in checks.values()), checks)
                self.assertEqual(checks['launches_per_run']['expected'], 2 if fused else 3)
                self.assertEqual(checks['random_a/z_vs_cpu']['l2_limit'], .02)
                self.assertEqual(checks['random_a/ffn_vs_cpu']['rtol'], .03)
                self.assertEqual(checks['random_a/ffn_vs_cpu']['atol'], .05)

    def test_per_runner_gate_rejects_skipped_launch_even_when_total_is_correct(self):
        values, metadata = self.snapshots(True)
        values[1]['dispatch_deltas'] = {'swiglu': 0, 'down': 2}
        self.assertEqual(sum(values[1]['dispatch_deltas'].values()), 2)
        self.assertFalse(self.validate(values, metadata)['launches_per_run']['passed'])
        metadata['completed_dispatches']['swiglu'] = 3
        self.assertFalse(self.validate(values, metadata)['completed_dispatches']['passed'])

    def test_each_run_rejects_weight_reupload_or_missing_weight_runner(self):
        values, metadata = self.snapshots(True)
        values[1]['weight_upload_counts']['swiglu'] = 2
        self.assertFalse(self.validate(values, metadata)['one_fixed_weight_upload']['passed'])
        values, metadata = self.snapshots(True)
        del metadata['weight_upload_counts']['down']
        self.assertFalse(self.validate(values, metadata)['one_fixed_weight_upload']['passed'])

    def test_stale_intermediate_and_repeat_corruption_are_rejected(self):
        values, metadata = self.snapshots(True)
        values[1]['z'] = values[0]['z'].copy()
        checks = self.validate(values, metadata)
        self.assertFalse(checks['z_changed_input']['passed'])
        self.assertFalse(checks['random_b/z_vs_cpu']['passed'])
        values[3]['ffn'][0, 0] ^= 1
        self.assertFalse(self.validate(values, metadata)['ffn_repeat']['passed'])

    def test_bad_packed_layout_and_nonfinite_outputs_are_rejected(self):
        values, metadata = self.snapshots(True)
        values[0]['z'] = values[0]['z'].reshape(self.m, self.channels)
        checks = self.validate(values, metadata)
        self.assertFalse(checks['random_a/z_buffer_contract']['passed'])
        self.assertNotIn('random_a/z_vs_cpu', checks)
        values[1]['ffn'][0, 0] = 0x7FC0
        self.assertFalse(self.validate(values, metadata)['random_b/ffn_vs_cpu']['passed'])

    def test_zero_reference_is_exact_and_wrong_stage_metadata_fails(self):
        values, metadata = self.snapshots(True)
        values[2]['z'][0] = 0x0080
        checks = self.validate(values, metadata)
        self.assertFalse(checks['zero/z_zero']['passed'])
        self.assertFalse(checks['zero/z_vs_cpu']['passed'])
        metadata['metadata']['cpu_activation_fallback'] = True
        self.assertFalse(self.validate(values, metadata)['branch_contract']['passed'])
        metadata['metadata']['cpu_activation_fallback'] = False
        metadata['metadata']['launches_per_run'] = 3
        self.assertFalse(self.validate(values, metadata)['branch_contract']['passed'])

    def test_reordered_or_missing_snapshots_cannot_pass(self):
        values, metadata = self.snapshots(True)
        with self.assertRaisesRegex(ValueError, 'ordered random'):
            self.validate(values[1:] + values[:1], metadata)
        with self.assertRaisesRegex(ValueError, 'ordered random'):
            self.validate(values[:-1], metadata)


if __name__ == '__main__':
    unittest.main()
