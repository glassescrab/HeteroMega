"""CPU fakes test benchmark policy/accounting, never NPU speed or accuracy."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from experiments.ffn_partition import benchmark_upstream_arithmetic as bench
from upstream_weights import UpstreamWeightBuffer, upstream_weight_bytes


def weights():
    result = []
    for k, n in ((256, 512), (256, 512), (512, 256)):
        data = np.zeros(upstream_weight_bytes(k, n), np.uint8)
        data.flags.writeable = False
        result.append(UpstreamWeightBuffer(data, k, n))
    return tuple(result)


def inputs():
    a = np.full((128, 256), 0x3F80, np.uint16)
    b = np.full_like(a, 0x4000)
    result = list(zip(bench.LABELS, (a, b, np.zeros_like(a), a.copy())))
    for _, x in result:
        x.flags.writeable = False
    return result


def args(root='CPU_MOCK', **overrides):
    value = dict(m=128, hidden=256, channels=128, intermediate=512, channel_start=128,
        artifact_root=Path(root), output=Path(root) / 'result.json', seed=251025,
        warmup=2, iterations=3, rounds=1, order='BAAB', bfp16_numerics='report',
        no_build=False, build_only=False, block_timeout=10, compile_timeout=10, iron_python='CPU_MOCK')
    return SimpleNamespace(**dict(value, **overrides))


def entry(index=1, reference=False, expected=None):
    value = dict(profile_index=index, arithmetic=bench.ARITHMETICS[index],
        profile=bench.resolve_profile(bench.PROFILE_NAME), excluded_from_summary=reference)
    if expected is not None:
        value['expected_output_sha256'] = expected
    return value


class BorrowedBranch:
    observed = []
    arithmetic = None

    def __init__(self, m, hidden, channels, *weights_and_root, **kwargs):
        type(self).observed.append(deepcopy(kwargs))
        type(self).arithmetic = kwargs['arithmetic']
        self.kind = kwargs['arithmetic']
        self.metadata = dict(arithmetic=self.kind, synthetic_cpu_test=True)
        self.swiglu = SimpleNamespace(completed_dispatches=0, input_write_counts=[0, 1, 1])
        self.down = SimpleNamespace(completed_dispatches=0, input_write_counts=[0, 1])
        self.runners = dict(swiglu=self.swiglu, down=self.down)
        self.output = np.empty((m, hidden), np.uint16)
        for weight in weights_and_root[:3]:
            assert not weight.data.flags.writeable

    def run(self, x):
        assert not x.flags.writeable
        self.output[:] = x if self.kind == 'bf16' else bench.bf16_bits(bench.bf16_from_bits(x) * 2)
        for runner in self.runners.values():
            runner.completed_dispatches += 1
        self.last_diagnostics = dict(dispatch_wait_us=dict(swiglu=1., down=2.),
            stages=dict(input_layout_us=1., swiglu_with_host_io_us=2., down_input_layout_us=3.,
                        down_with_host_io_us=4., output_layout_us=5.),
            completed_dispatches_total=2 * self.down.completed_dispatches)
        return self.output


class ArithmeticBenchmarkTests(unittest.TestCase):
    def test_borrowed_snapshots_and_same_arithmetic_reference_routing(self):
        data = inputs()
        expected = {label: bench._hash(x) for label, x in data}
        item = entry(expected=expected)
        BorrowedBranch.observed = []
        with patch.object(bench, 'UpstreamNpuFFN', BorrowedBranch):
            payload = bench._run_block(args(), weights(), data, item)
        bench._compare_outputs(item, payload, dict(data), dict(data), 'report')
        self.assertEqual(item['status'], 'passed')
        self.assertEqual(item['completed_dispatches'], dict(swiglu=9, down=9))
        self.assertEqual(len(payload['preflight']), 4)
        for i, output in enumerate(payload['timed']):
            np.testing.assert_array_equal(output, data[i % 2][1])
        self.assertFalse(np.shares_memory(payload['preflight'][0], payload['preflight'][3]))
        self.assertFalse(np.shares_memory(payload['timed'][0], payload['timed'][1]))
        self.assertEqual(BorrowedBranch.observed[0], dict(item['profile'], arithmetic='bf16',
            segment_pipeline_depth=2, channel_start=128))

    def test_report_keeps_cross_arithmetic_error_but_strict_rejects_it(self):
        data = inputs()
        with patch.object(bench, 'UpstreamNpuFFN', BorrowedBranch):
            item = entry(2, reference=True)
            payload = bench._run_block(args(), weights(), data, item)
        for mode, expected_status in (('report', 'passed'), ('strict', 'failed')):
            candidate = deepcopy(item)
            bench._compare_outputs(candidate, payload, {}, dict(data), mode)
            self.assertEqual(candidate['status'], expected_status)
            self.assertFalse(candidate['numerical_checks']['original_tolerances_vs_native_control'])
            self.assertEqual(candidate['preflight'][0]['errors_vs_native_control']['relative_l2_error'], 1.)
            self.assertTrue(candidate['checks']['finite_same_arithmetic_outputs'])
        # Native retains a hard numerical gate even in BFP16 report mode.
        candidate = deepcopy(item)
        candidate['arithmetic'] = 'bf16'
        bench._compare_outputs(candidate, payload, {}, dict(data), 'report')
        self.assertEqual(candidate['status'], 'failed')

    def test_nonfinite_reference_never_reaches_timing(self):
        class Nonfinite(BorrowedBranch):
            def run(self, x):
                result = super().run(x)
                result.fill(0x7F80)
                return result
        for index in (1, 2):
            item = entry(index, reference=True)
            with patch.object(bench, 'UpstreamNpuFFN', Nonfinite):
                with self.assertRaisesRegex(RuntimeError, 'nonfinite.*timing was not started'):
                    bench._run_block(args(), weights(), inputs(), item)
            self.assertEqual(item['runs'], [])
            self.assertEqual(item['completed_dispatches'], dict(swiglu=1, down=1))

    def test_constant_bad_zero_and_nonrepeat_outputs_fail_preflight(self):
        class Broken(BorrowedBranch):
            mode = None
            def run(self, x):
                result = super().run(x)
                count = self.down.completed_dispatches
                if self.mode == 'constant':
                    result.fill(0x3F80)
                elif self.mode == 'zero' and count == 3:
                    result.fill(0x3F80)
                elif self.mode == 'repeat' and count == 4:
                    result.flat[0] += 1
                return result
        for mode in ('constant', 'zero', 'repeat'):
            Broken.mode = mode
            item = entry(2, reference=True)
            with self.subTest(mode=mode), patch.object(bench, 'UpstreamNpuFFN', Broken):
                with self.assertRaisesRegex(RuntimeError, 'preflight failed'):
                    bench._run_block(args(), weights(), inputs(), item)
            self.assertEqual(item['warmup'], [])
            self.assertEqual(item['runs'], [])
            self.assertEqual(item['completed_dispatches'], dict(swiglu=4, down=4))

    def test_exact_reference_and_warmup_checks_reject_finite_drift(self):
        data = inputs()
        expected = {label: bench._hash(x) for label, x in data}
        bad = dict(expected, signed_a='WRONG')
        item = entry(expected=bad)
        with patch.object(bench, 'UpstreamNpuFFN', BorrowedBranch):
            with self.assertRaisesRegex(RuntimeError, 'preflight failed'):
                bench._run_block(args(), weights(), data, item)
        self.assertEqual(item['runs'], [])

        class WarmupDrift(BorrowedBranch):
            def run(self, x):
                result = super().run(x)
                if self.down.completed_dispatches == 5:
                    result.flat[0] += 1
                return result
        item = entry(expected=expected)
        with patch.object(bench, 'UpstreamNpuFFN', WarmupDrift):
            with self.assertRaisesRegex(RuntimeError, 'warmup differs'):
                bench._run_block(args(), weights(), data, item)
        self.assertEqual(item['runs'], [])
        self.assertEqual(item['completed_dispatches'], dict(swiglu=5, down=5))

    def test_finite_timed_drift_is_not_relaxed_by_report_mode(self):
        class TimedDrift(BorrowedBranch):
            def run(self, x):
                result = super().run(x)
                if self.down.completed_dispatches == 7:
                    result.flat[0] += 1
                return result
        data = inputs()
        expected = {label: bench._hash(bench.bf16_bits(bench.bf16_from_bits(x) * 2)) for label, x in data}
        item = entry(2, expected=expected)
        with patch.object(bench, 'UpstreamNpuFFN', TimedDrift):
            with self.assertRaisesRegex(RuntimeError, 'timed output differs'):
                bench._run_block(args(), weights(), data, item)
        self.assertEqual(len(item['runs']), 1)
        self.assertEqual(item['completed_dispatches'], dict(swiglu=7, down=7))

    def test_wrong_completion_and_upload_counts_are_failures(self):
        data = inputs()
        item = entry(reference=True)
        with patch.object(bench, 'UpstreamNpuFFN', BorrowedBranch):
            payload = bench._run_block(args(), weights(), data, item)
        item['completed_dispatches']['down'] -= 1
        item['fixed_weight_upload_counts']['gate'] += 1
        bench._compare_outputs(item, payload, {}, dict(data), 'report')
        self.assertEqual(item['status'], 'failed')
        self.assertFalse(item['checks']['both_runners_completed'])
        self.assertFalse(item['checks']['fixed_weights_uploaded_once'])

    def test_baab_isolated_references_counters_numeric_report_and_stage_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = args(root)
            specs_seen, processes = [], []
            clock = [0]
            def specs(*unused, **kwargs):
                specs_seen.append(kwargs)
                return dict(swiglu='CPU_MOCK', down='CPU_MOCK')
            def process(command, **unused):
                self.assertEqual(command[1:3], ['-m', 'experiments.ffn_partition.benchmark_upstream_arithmetic'])
                processes.append(json.loads(Path(command[-1]).read_text())['entry']['arithmetic'])
                return SimpleNamespace(returncode=bench._worker_main(Path(command[-1])), stdout='CPU test')
            def perf_counter():
                clock[0] += 20000 if BorrowedBranch.arithmetic == 'bf16' else 10000
                return clock[0]
            with patch.object(bench.platform, 'platform', return_value='CPU_MOCK'), \
                    patch.object(bench, 'UpstreamNpuFFN', BorrowedBranch), \
                    patch.object(bench, '_ffn_specs', side_effect=specs), \
                    patch.object(bench, '_build', return_value={'synthetic_cpu_test': True}), \
                    patch.object(bench.subprocess, 'run', side_effect=process), \
                    patch.object(bench.time, 'perf_counter_ns', side_effect=perf_counter):
                report = bench.run_benchmark(settings)
            self.assertEqual(report['status'], 'passed', report.get('traceback'))
            self.assertEqual(processes, ['bf16', 'bfp16', 'bfp16', 'bf16', 'bf16', 'bfp16'])
            self.assertEqual(report['completed_npu_dispatches'], 16 + 8 * (4 + 2 + 3))
            self.assertEqual(len(report['reference_blocks']), 2)
            self.assertTrue(all(x['excluded_from_summary'] for x in report['reference_blocks']))
            self.assertTrue(all(not x['runs'] for x in report['reference_blocks']))
            self.assertEqual(report['summary']['1']['wall']['count'], 6)
            self.assertEqual(report['summary']['1']['wall']['median_us'], 20.)
            self.assertEqual(report['summary']['2']['wall']['median_us'], 10.)
            self.assertEqual(report['summary']['candidate_over_baseline_speedup'], 2.)
            self.assertEqual(report['summary']['2']['host_stages']['output_layout_us']['median_us'], 5.)
            self.assertFalse(report['summary']['2']['original_tolerances_vs_native_control'])
            self.assertEqual(report['summary']['2']['max_relative_l2_vs_native'], 1.)
            self.assertEqual(report['tolerances'], dict(rtol=.03, atol=.05, relative_l2_limit=.02))
            self.assertEqual([x.pop('arithmetic') for x in specs_seen], ['bf16', 'bfp16'])
            self.assertEqual(specs_seen[0], specs_seen[1])
            self.assertNotIn('copy_output_bits', specs_seen[0])
            self.assertEqual(specs_seen[0]['down_reuse'], 4)

    def test_strict_mode_rejects_bfp_reference_before_any_timed_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            settings = args(temporary, bfp16_numerics='strict')
            def process(command, **unused):
                return SimpleNamespace(returncode=bench._worker_main(Path(command[-1])), stdout='CPU test')
            with patch.object(bench.platform, 'platform', return_value='CPU_MOCK'), \
                    patch.object(bench, 'UpstreamNpuFFN', BorrowedBranch), \
                    patch.object(bench, '_ffn_specs', return_value=dict(swiglu='CPU_MOCK', down='CPU_MOCK')), \
                    patch.object(bench, '_build', return_value={'synthetic_cpu_test': True}), \
                    patch.object(bench.subprocess, 'run', side_effect=process):
                report = bench.run_benchmark(settings)
            self.assertEqual(report['status'], 'failed')
            self.assertIn('bfp16 reference failed', report['error'])
            self.assertEqual(report['blocks'], [])
            self.assertEqual(report['completed_npu_dispatches'], 16)


if __name__ == '__main__':
    unittest.main()
