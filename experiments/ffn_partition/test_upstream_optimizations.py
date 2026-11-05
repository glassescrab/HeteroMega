"""CPU checks for optimization-profile routing and benchmark accounting.

Fake device outputs and timings in these tests establish harness behavior,
never NPU execution, correctness of the kernels or speedup.
"""

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from experiments.ffn_partition import benchmark_upstream_optimizations as benchmark
from upstream_weights import UpstreamWeightBuffer, upstream_weight_bytes


def _weights():
    result = []
    for k, n in ((256, 512), (256, 512), (512, 256)):
        data = np.zeros(upstream_weight_bytes(k, n), np.uint8)
        data.flags.writeable = False
        result.append(UpstreamWeightBuffer(data, k, n))
    return tuple(result)


class _BorrowingFakeBranch:
    observed_keywords = []

    def __init__(self, m, hidden, channels, *weights_and_root, **kwargs):
        self.observed_keywords.append(kwargs)
        self.metadata = dict(synthetic_cpu_test=True, profile=kwargs)
        self.swiglu = SimpleNamespace(completed_dispatches=0, input_write_counts=[0, 1, 1])
        self.down = SimpleNamespace(completed_dispatches=0, input_write_counts=[0, 1])
        self.runners = dict(swiglu=self.swiglu, down=self.down)
        self.output = np.empty((m, hidden), np.uint16)
        for weight in weights_and_root[:3]:
            if weight.data.flags.writeable:
                raise AssertionError('fixture weights must be read-only')

    def run(self, x):
        self.output[:] = x
        for runner in self.runners.values():
            runner.completed_dispatches += 1
        self.last_diagnostics = dict(dispatch_wait_us=dict(swiglu=0.0, down=0.0),
            completed_dispatches_total=2 * self.down.completed_dispatches)
        return self.output  # Deliberately aliases the next call's result.


class OptimizationBenchmarkTests(unittest.TestCase):
    def test_profiles_keep_native_contract_and_separate_host_option(self):
        baseline = benchmark.resolve_profile('baseline')
        combo = benchmark.resolve_profile('combo_row_major')
        self.assertEqual(baseline, benchmark.PROFILE_DEFAULTS)
        self.assertEqual(combo['down_reuse'], 4)
        self.assertEqual(combo['down_activation_fifo_depth'], 1)
        self.assertEqual(combo['swiglu_input_layout'], 'row_major')
        self.assertEqual(combo['output_layout'], 'down_a')
        self.assertFalse(combo['copy_output_bits'])
        self.assertNotIn('copy_output_bits', benchmark.artifact_profile(combo))
        self.assertEqual(benchmark.artifact_profile(baseline),
                         benchmark.artifact_profile(benchmark.resolve_profile('borrowed')))
        self.assertNotIn('arithmetic', combo)
        self.assertNotIn('segment_pipeline_depth', combo)
        combo['down_reuse'] = 1
        self.assertEqual(benchmark.resolve_profile('combo')['down_reuse'], 4)

    def test_json_profiles_reject_ambiguous_or_unsupported_options(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'profile.json'
            path.write_text(json.dumps(dict(vector_zero=True, down_reuse=4)))
            self.assertTrue(benchmark.resolve_profile(str(path))['vector_zero'])
            for invalid in ([], {'arithmetic': 'bfp16'}, {'weight_repacking': True},
                            {'down_reuse': 4.0}, {'swiglu_reuse': True},
                            {'vector_zero': 1}, {'copy_output_bits': 'false'},
                            {'output_layout': 'other'}, {'swiglu_input_layout': 'other'}):
                with self.subTest(profile=invalid):
                    path.write_text(json.dumps(invalid))
                    with self.assertRaises(ValueError):
                        benchmark.resolve_profile(str(path))

    def test_output_snapshots_survive_next_borrowed_run_and_route_profile(self):
        args = SimpleNamespace(m=128, hidden=256, channels=128, artifact_root='CPU_MOCK',
                               channel_start=128, warmup=2, iterations=4)
        inputs = [(label, np.full((128, 256), bits, np.uint16))
                  for label, bits in (('signed_a', 0x3F80), ('signed_b', 0x4000))]
        entry = dict(profile_index=2, profile=benchmark.resolve_profile('combo_row_major'))
        _BorrowingFakeBranch.observed_keywords = []
        with patch.object(benchmark, 'UpstreamNpuFFN', _BorrowingFakeBranch):
            outputs = benchmark._run_block(args, _weights(), inputs, entry)
        benchmark._compare_outputs(entry, outputs, dict(inputs))
        self.assertEqual(entry['status'], 'passed')
        self.assertEqual(entry['completed_dispatches'], dict(swiglu=6, down=6))
        expected = dict(entry['profile'], channel_start=128, segment_pipeline_depth=2)
        self.assertEqual(_BorrowingFakeBranch.observed_keywords, [expected])
        for index, output in enumerate(outputs):
            np.testing.assert_array_equal(output, inputs[index % 2][1])
        self.assertFalse(np.shares_memory(outputs[0], outputs[1]))

    def test_worker_transport_is_readonly_and_uses_new_module(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            args = SimpleNamespace(m=128, hidden=256, channels=128, artifact_root=root,
                                   channel_start=128, warmup=2, iterations=2, block_timeout=10)
            inputs = [(label, np.full((128, 256), bits, np.uint16))
                      for label, bits in (('signed_a', 0x3F80), ('signed_b', 0x4000))]
            fixture_paths = benchmark._fixture_files(root, _weights(), inputs)
            entry = dict(profile_index=2, profile=benchmark.resolve_profile('borrowed'))

            def fake_process(command, **unused):
                self.assertEqual(command[1:3],
                    ['-m', 'experiments.ffn_partition.benchmark_upstream_optimizations'])
                code = benchmark._worker_main(Path(command[-1]))
                return SimpleNamespace(returncode=code, stdout='CPU mocked child process')

            with patch.object(benchmark, 'UpstreamNpuFFN', _BorrowingFakeBranch), \
                    patch.object(benchmark.subprocess, 'run', side_effect=fake_process):
                outputs = benchmark._subprocess_block(args, fixture_paths, entry, root / 'child')
            benchmark._compare_outputs(entry, outputs, dict(inputs))
            self.assertEqual(entry['status'], 'passed')
            self.assertEqual(entry['completed_dispatches'], dict(swiglu=4, down=4))

    def test_close_numeric_result_still_fails_exact_schedule_equivalence(self):
        output = np.full((2, 2), 0x3F80, np.uint16)
        entry = dict(profile_index=2, runs=[dict(input='signed_a')],
            warmup=[dict(input='signed_a', output_sha256=benchmark._hash(output), finite=True)],
            completed_dispatches=dict(swiglu=2, down=2),
            fixed_weight_upload_counts=dict(gate=1, up=1, down=1))
        changed = output.copy()
        changed[0, 0] += 1
        benchmark._compare_outputs(entry, [changed], {'signed_a': output})
        self.assertEqual(entry['status'], 'failed')
        self.assertTrue(entry['checks']['original_tolerances_vs_profile_a_control'])
        self.assertFalse(entry['checks']['all_identical_to_profile_a_control'])

    def test_nonfinite_warmups_fail_before_reference_or_candidate_timing(self):
        class NonfiniteBranch(_BorrowingFakeBranch):
            def run(self, x):
                output = super().run(x)
                output.fill(0x7F80)
                return output

        args = SimpleNamespace(m=128, hidden=256, channels=128, artifact_root='CPU_MOCK',
                               channel_start=128, warmup=2, iterations=4)
        inputs = [('signed_a', np.full((128, 256), 0x3F80, np.uint16))]
        for index in (1, 2):
            entry = dict(profile_index=index, profile=benchmark.resolve_profile('combo'))
            with self.subTest(profile=index), patch.object(benchmark, 'UpstreamNpuFFN', NonfiniteBranch):
                with self.assertRaisesRegex(RuntimeError, 'nonfinite.*timing was not started'):
                    benchmark._run_block(args, _weights(), inputs, entry)
            self.assertEqual(entry['runs'], [])
            self.assertEqual(entry['completed_dispatches'], dict(swiglu=1, down=1))
            self.assertFalse(entry['warmup'][0]['finite'])

    def test_finite_wrong_warmup_fails_before_candidate_timing(self):
        args = SimpleNamespace(m=128, hidden=256, channels=128, artifact_root='CPU_MOCK',
                               channel_start=128, warmup=2, iterations=4)
        inputs = [('signed_a', np.full((128, 256), 0x3F80, np.uint16))]
        expected = np.full((128, 256), 0x3F81, np.uint16)
        entry = dict(profile_index=2, profile=benchmark.resolve_profile('combo'),
                     expected_output_sha256={'signed_a': benchmark._hash(expected)})
        with patch.object(benchmark, 'UpstreamNpuFFN', _BorrowingFakeBranch):
            with self.assertRaisesRegex(RuntimeError, 'differs.*timing was not started'):
                benchmark._run_block(args, _weights(), inputs, entry)
        self.assertEqual(entry['runs'], [])
        self.assertEqual(entry['completed_dispatches'], dict(swiglu=1, down=1))

    def test_baab_summary_excludes_reference_and_counts_both_runners(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            args = SimpleNamespace(output=root / 'result.json', artifact_root=root / 'artifacts',
                iron_python='CPU_MOCK', seed=251025, m=128, hidden=256, intermediate=512,
                channels=128, channel_start=128, rounds=1, order='BAAB', warmup=2, iterations=3,
                profile_a='baseline', profile_b='combo', build_only=False, no_build=False)
            profiles_seen = []

            def fake_specs(*unused, **kwargs):
                profiles_seen.append(kwargs)
                return dict(swiglu='CPU_MOCK', down='CPU_MOCK')

            def fake_block(block_args, fixture_paths, entry, directory):
                directory.mkdir()
                inputs = [(x['label'], np.load(x['path'])) for x in fixture_paths['inputs']]
                delay = 999.0 if entry.get('excluded_from_summary') else (20.0 if entry['profile_index'] == 1 else 10.0)
                entry.update(status='completed', child_process_returncode=0,
                    completed_dispatches=dict(swiglu=block_args.warmup + block_args.iterations,
                                              down=block_args.warmup + block_args.iterations),
                    fixed_weight_upload_counts=dict(gate=1, up=1, down=1), warmup=[], runs=[])
                for index in range(block_args.warmup):
                    label, value = inputs[index % 2]
                    entry['warmup'].append(dict(input=label, finite=True, output_sha256=benchmark._hash(value)))
                outputs = []
                for index in range(block_args.iterations):
                    label, value = inputs[index % 2]
                    entry['runs'].append(dict(index=index, input=label, wall_us=delay,
                        diagnostics=dict(dispatch_wait_us=dict(swiglu=delay / 2, down=delay / 4))))
                    outputs.append(value.copy())
                return outputs

            with patch.object(benchmark, '_ffn_specs', side_effect=fake_specs), \
                    patch.object(benchmark, '_build', return_value={'synthetic_cpu_test': True}), \
                    patch.object(benchmark, '_subprocess_block', side_effect=fake_block):
                report = benchmark.run_benchmark(args)
            self.assertEqual(report['status'], 'passed', report.get('error'))
            self.assertEqual([b['profile_index'] for b in report['blocks']], [2, 1, 1, 2])
            self.assertEqual(report['completed_npu_dispatches'], 8 + 8 * (2 + 3))
            self.assertEqual(report['summary']['1']['wall']['median_us'], 20.0)
            self.assertEqual(report['summary']['2']['wall']['median_us'], 10.0)
            self.assertEqual(report['summary']['candidate_over_baseline_speedup'], 2.0)
            self.assertEqual(report['summary']['candidate_latency_reduction_percent'], 50.0)
            self.assertTrue(report['reference_block']['excluded_from_summary'])
            self.assertEqual(len(profiles_seen), 2)
            self.assertTrue(all(p['segment_pipeline_depth'] == 2 for p in profiles_seen))
            self.assertTrue(all('copy_output_bits' not in p for p in profiles_seen))
            self.assertEqual(profiles_seen[1]['down_reuse'], 4)


if __name__ == '__main__':
    unittest.main()
