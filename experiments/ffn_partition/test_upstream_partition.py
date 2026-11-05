"""Host-only routing/report tests; fake branches do not execute GPU/NPU math."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from experiments.ffn_partition import run_upstream_partition as bench
from experiments.ffn_partition.contract import OutputIntegrity, random_weights


class FakeGPU:
    instances = []
    factor = 1.0

    def __init__(self, gate, up, down, m, device="fake", **kwargs):
        self.device, self.metadata = device, {"fake": True}
        self.gate, self.up, self.down = gate, up, down
        self.__class__.instances.append(self)


class FakeNPU:
    instances = []
    factor = 1.0
    bad_zero = False
    stale = False

    def __init__(self, m, hidden, p, gate, up, down, root, **kwargs):
        self.weights = (gate, up, down)
        self.options = kwargs
        self.metadata = {"fake": True}
        self.swiglu = SimpleNamespace(completed_dispatches=0, input_write_counts=[0, 1, 1])
        self.down = SimpleNamespace(completed_dispatches=0, input_write_counts=[0, 1])
        self.runners = {"swiglu": self.swiglu, "down": self.down}
        self.__class__.instances.append(self)


class FakeTimed:
    def __init__(self, gpu, npu, m, hidden, device):
        self.gpu, self.npu = gpu, npu

    def run(self, x, serial=False):
        if self.npu is None:
            return 2 * x, 30.0, {}
        self.gpu.output = self.gpu.factor * x
        self.host_y = self.npu.factor * x
        if self.npu.bad_zero and not np.any(x):
            self.host_y = np.ones_like(x)
        if self.npu.stale:
            self.host_y = np.ones_like(x)
        for runner in self.npu.runners.values():
            runner.completed_dispatches += 1
            runner.input_write_counts[0] += 1
        return self.gpu.output + self.host_y, 25.0 if serial else 20.0, {"fake": True}


class UpstreamPartitionTests(unittest.TestCase):
    def setUp(self):
        FakeGPU.instances, FakeNPU.instances = [], []
        FakeGPU.factor = FakeNPU.factor = 1.0
        FakeNPU.bad_zero = FakeNPU.stale = False

    def test_original_buffers_are_full_readonly_and_not_partition_repacked(self):
        weights = random_weights(128, 512, seed=3)
        with patch.object(bench, "pack_heteromosaic_weights", wraps=bench.pack_heteromosaic_weights) as pack:
            original = bench.prepare_original_weights(weights)
        self.assertEqual(pack.call_count, 3)
        for call, source, descriptor in zip(pack.call_args_list,
                (weights.gate, weights.up, weights.down), original):
            self.assertIs(call.args[0], source)
            self.assertEqual((descriptor.n, descriptor.k), source.shape)
            self.assertFalse(descriptor.data.flags.writeable)
            self.assertEqual(descriptor.nbytes, descriptor.n // 64 * (descriptor.k // 128) * 4352)

    def test_selected_profile_and_explicit_iron_interpreter(self):
        opts = bench.selected_options()
        self.assertEqual(opts, dict(arithmetic="bfp16", segment_pipeline_depth=2,
            swiglu_reuse=2, down_reuse=4, swiglu_activation_fifo_depth=2,
            down_activation_fifo_depth=1, vector_zero=True, mmul_m_reuse=1,
            output_layout="down_a", swiglu_input_layout="row_major"))
        with patch.dict(bench.os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                bench.parse_args([])
        args, channels = bench.parse_args(["--no-build"])
        self.assertEqual(channels, [1024, 1792, 2560, 3072])
        self.assertEqual(args.accuracy_policy, "report")
        args, _ = bench.parse_args(["--no-build", "--npu-arithmetic", "bf16"])
        self.assertEqual(args.accuracy_policy, "strict")

    def test_invalid_empty_or_whole_partition_rejected(self):
        for value in ("0", "14336", "127", "", "-128"):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    bench.parse_args(["--no-build", "--npu-channels", value])

    def test_build_only_never_constructs_runtime_and_keeps_exact_buffers(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            seen = []

            def build(m, hidden, p, *args, **kwargs):
                seen.append((p, args[:3], kwargs))
                return {"swiglu": {"fake": True}, "down": {"fake": True}}

            with patch.object(bench, "provenance", return_value={}), \
                 patch.object(bench, "build_upstream_artifacts", side_effect=build), \
                 patch.object(bench, "gpu_preflight") as preflight, \
                 patch.object(bench, "GPUBranch") as gpu, \
                 patch.object(bench, "UpstreamNpuFFN") as npu, \
                 contextlib.redirect_stdout(io.StringIO()):
                bench.main(["--m", "128", "--hidden", "128", "--intermediate", "512",
                    "--npu-channels", "128,256", "--build-only", "--iron-python", "/explicit/iron/python",
                    "--output", str(output)])
            preflight.assert_not_called()
            gpu.assert_not_called()
            npu.assert_not_called()
            for first, second in zip(seen[0][1], seen[1][1]):
                self.assertIs(first, second)
                self.assertIs(first.data, second.data)
            for _, _, kwargs in seen:
                self.assertEqual(kwargs["python_executable"], "/explicit/iron/python")
                self.assertEqual(kwargs["arithmetic"], "bfp16")
                self.assertEqual(kwargs["channel_start"], 0)
            report = json.loads(output.read_text())
            self.assertEqual(report["status"], "build_complete")
            self.assertTrue(report["original_weight_buffers_unchanged"])

    def test_gpu_access_failure_precedes_weight_preparation_and_compilation(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with patch.object(bench, "provenance", return_value={}), \
                 patch.object(bench, "gpu_preflight", side_effect=RuntimeError("GPU unavailable")), \
                 patch.object(bench, "random_weights") as prepare, \
                 patch.object(bench, "build_upstream_artifacts") as build:
                with self.assertRaisesRegex(RuntimeError, "GPU unavailable"):
                    bench.main(["--iron-python", "/explicit/iron/python", "--output", str(output)])
            prepare.assert_not_called()
            build.assert_not_called()
            report = json.loads(output.read_text())
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["error"], "GPU unavailable")

    def _run_fake(self, entry, policy="report"):
        weights = random_weights(128, 256, seed=3)
        original = bench.prepare_original_weights(weights)
        args = SimpleNamespace(m=128, hidden=128, artifact_root=Path("unused"),
            verbose_build=False, npu_arithmetic="bfp16", accuracy_policy=policy,
            seed=4, warmup=1, iterations=2)
        inputs = [np.full((2, 2), 1, np.float32), np.full((2, 2), 2, np.float32),
                  np.zeros((2, 2), np.float32)]
        baseline_gpu = SimpleNamespace(device="fake")
        baseline = FakeTimed(baseline_gpu, None, 128, 128, "fake")
        references = [2 * x for x in inputs]
        with patch.object(bench, "GPUBranch", FakeGPU), \
             patch.object(bench, "UpstreamNpuFFN", FakeNPU), \
             patch.object(bench, "TimedFFN", FakeTimed), \
             patch.object(bench, "cpu_values", side_effect=lambda x: x.copy()), \
             patch.object(bench, "reference_partitioned", side_effect=lambda x, *_: (2 * x, {"gpu": x, "npu": x})), \
             contextlib.redirect_stdout(io.StringIO()):
            bench.run_partition(args, 128, weights, original, baseline_gpu, baseline,
                inputs, inputs, references, references, OutputIntegrity(), entry)
        return original

    def test_partition_routing_alternation_exact_counters_and_strict_controls(self):
        entry = {}
        original = self._run_fake(entry)
        self.assertEqual(entry["status"], "passed")
        self.assertEqual(entry["completed_npu_dispatches_by_stage"], {"swiglu": 14, "down": 14})
        self.assertEqual(entry["fixed_weight_upload_counts"], {"gate": 1, "up": 1, "down": 1})
        self.assertEqual(entry["input_write_counts_by_stage"], {"swiglu": [14, 1, 1], "down": [14, 1]})
        self.assertEqual(len(entry["samples"]), 6)
        self.assertEqual(len(entry["warmup_samples"]), 3)
        self.assertEqual(len(entry["validation_runs"]), 8)
        for iteration in range(2):
            self.assertEqual({r["mode"] for r in entry["samples"] if r["iteration"] == iteration},
                             {"baseline", "serial", "concurrent"})
        self.assertAlmostEqual(entry["latency_ratio_vs_gpu_baseline"], 1.5)
        self.assertTrue(entry["original_weight_buffers_unchanged"])
        for actual, expected in zip(FakeNPU.instances[0].weights, original):
            self.assertIs(actual.data, expected.data)
        self.assertFalse(FakeNPU.instances[0].options["copy_output_bits"])
        self.assertEqual(FakeNPU.instances[0].options["output_layout"], "down_a")
        self.assertEqual(FakeGPU.instances[0].gate.shape, (128, 128))

    def test_report_accepts_numerical_deviation_preserving_original_failure(self):
        FakeNPU.factor = 1.5
        entry = {}
        self._run_fake(entry)
        self.assertEqual(entry["status"], "completed_with_accuracy_deviations")
        self.assertFalse(entry["accuracy"]["passed"])
        self.assertTrue(entry["accuracy"]["accepted"])
        self.assertIsNone(entry["speedup_vs_gpu_baseline"])
        self.assertEqual(entry["latency_ratio_vs_gpu_baseline"], 1.5)

    def test_report_never_relaxes_gpu_partial_failure_and_retains_counts(self):
        FakeGPU.factor = 1.5
        entry = {}
        with self.assertRaisesRegex(RuntimeError, "gpu_partial"):
            self._run_fake(entry)
        self.assertEqual(entry["status"], "failed")
        self.assertEqual(entry["completed_npu_dispatches_by_stage"], {"swiglu": 1, "down": 1})
        self.assertEqual(entry["fixed_weight_upload_counts"], {"gate": 1, "up": 1, "down": 1})

    def test_report_rejects_nonzero_zero_case_and_retains_counts(self):
        FakeNPU.bad_zero = True
        entry = {}
        with self.assertRaises(RuntimeError):
            self._run_fake(entry)
        self.assertEqual(entry["status"], "failed")
        self.assertEqual(entry["completed_npu_dispatches_by_stage"], {"swiglu": 5, "down": 5})
        self.assertTrue(entry["original_weight_buffers_unchanged"])

    def test_report_rejects_stale_partial_even_when_sum_changes(self):
        FakeNPU.stale = True
        entry = {}
        with self.assertRaisesRegex(RuntimeError, "npu_partial"):
            self._run_fake(entry)
        self.assertEqual(entry["completed_npu_dispatches_by_stage"], {"swiglu": 3, "down": 3})

    def test_counter_invariants_reject_extra_weight_upload_or_missing_wait(self):
        npu = FakeNPU(1, 1, 1, None, None, None, None)
        bench.assert_runtime_counts(npu, 0)
        npu.swiglu.input_write_counts[1] += 1
        with self.assertRaisesRegex(RuntimeError, "upload"):
            bench.assert_runtime_counts(npu, 0)
        npu.swiglu.input_write_counts[1] = 1
        npu.swiglu.completed_dispatches = 1
        with self.assertRaisesRegex(RuntimeError, "completion"):
            bench.assert_runtime_counts(npu, 0)


if __name__ == "__main__":
    unittest.main()
