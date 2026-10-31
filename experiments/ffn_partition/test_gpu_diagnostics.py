"""CPU event/routing tests; these do not establish GPU timings."""

from contextlib import nullcontext, redirect_stdout
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from . import run_upstream_partition as bench
from .contract import OutputIntegrity, random_weights
from .gpu_diagnostics import DiagnosticGPUBranch
from .test_upstream_partition import FakeGPU, FakeNPU, FakeTimed


class EventTests(unittest.TestCase):
    def test_order_completion_units_and_delegation_without_sync(self):
        calls = []

        class Event:
            def __init__(self, enable_timing):
                self.enabled, self.done = enable_timing, False
            def record(self, stream):
                self.done = False
                calls.append(("record", self, stream))
            def query(self):
                calls.append(("query", self))
                return self.done
            def elapsed_time(self, stop):
                calls.append(("elapsed", self, stop))
                return 1.25

        stream = SimpleNamespace(device="cuda:0", cuda_stream=42)
        torch = SimpleNamespace(cuda=SimpleNamespace(device=lambda _: nullcontext(),
            stream=lambda _: nullcontext(), current_stream=lambda _: stream, Event=Event))
        output, weights = object(), [object()]
        branch = SimpleNamespace(_torch=torch, device="cuda:0", metadata={"original": True},
            output=output, weights=weights,
            enqueue=lambda x, s: (calls.append(("enqueue", x, s)), output)[1])
        wrapped = DiagnosticGPUBranch(branch)
        self.assertTrue(wrapped._start.enabled and wrapped._stop.enabled)
        self.assertIs(wrapped.weights, weights)
        self.assertIs(wrapped.output, output)
        self.assertNotIn("gpu_device_diagnostics", branch.metadata)
        with self.assertRaisesRegex(RuntimeError, "no successful"):
            wrapped.collect()
        x = object()
        self.assertIs(wrapped.enqueue(x), output)
        self.assertEqual([c[0] for c in calls], ["record", "enqueue", "record"])
        self.assertIs(calls[0][1], wrapped._start)
        self.assertIs(calls[2][1], wrapped._stop)
        with self.assertRaisesRegex(RuntimeError, "complete the FFN boundary"):
            wrapped.collect()
        wrapped._start.done = wrapped._stop.done = True
        result = wrapped.collect()
        self.assertEqual(result["device_elapsed_us"], 1250.0)
        self.assertEqual(result["enqueue_count"], 1)
        self.assertFalse(result["ordinary_headline_eligible"])
        # The mock deliberately has no synchronization methods.


class HarnessTests(unittest.TestCase):
    def test_ordinary_default_does_not_construct_events_or_collect(self):
        args, _ = bench.parse_args(["--no-build"])
        self.assertFalse(args.gpu_device_diagnostics)
        branch, record = object(), {"wall_us": 4.0}
        with patch("experiments.ffn_partition.gpu_diagnostics.DiagnosticGPUBranch") as wrapper:
            self.assertIs(bench._instrument_gpu(branch, args), branch)
            bench._attach_gpu_diagnostics(record, branch, args)
        wrapper.assert_not_called()
        self.assertEqual(record, {"wall_us": 4.0})

    def test_each_diagnostic_sample_collects_its_own_completed_branch(self):
        FakeGPU.instances, FakeNPU.instances = [], []
        FakeGPU.factor = FakeNPU.factor = 1.0
        FakeNPU.bad_zero = FakeNPU.stale = False
        history, wrappers = [], []

        class Wrapper:
            def __init__(self, branch):
                self.branch, self.ready, self.completed = branch, False, 0
                self.tag = len(wrappers)
                self.metadata = dict(branch.metadata, diagnostic=True)
                wrappers.append(self)
            def __getattr__(self, name):
                return getattr(self.branch, name)
            def collect(self):
                if not self.ready:
                    raise AssertionError("collection occurred before completed run")
                history.append(("collect", self.tag, self.completed))
                self.ready = False
                return dict(device_elapsed_us=10.0 + self.tag, enqueue_count=self.completed,
                            ordinary_headline_eligible=False)

        class Timed(FakeTimed):
            def run(self, x, serial=False):
                result = super().run(x, serial)
                self.gpu.completed += 1
                self.gpu.ready = True
                history.append(("boundary_complete", self.gpu.tag, self.gpu.completed))
                return result

        weights = random_weights(128, 256, seed=3)
        original = bench.prepare_original_weights(weights)
        args = SimpleNamespace(m=128, hidden=128, artifact_root=Path("unused"),
            verbose_build=False, npu_arithmetic="bfp16", accuracy_policy="report",
            seed=4, warmup=1, iterations=2, gpu_device_diagnostics=True)
        inputs = [np.full((2, 2), 1, np.float32), np.full((2, 2), 2, np.float32),
                  np.zeros((2, 2), np.float32)]
        refs = [2 * x for x in inputs]
        entry = {}
        with patch("experiments.ffn_partition.gpu_diagnostics.DiagnosticGPUBranch", Wrapper), \
             patch.object(bench, "GPUBranch", FakeGPU), \
             patch.object(bench, "UpstreamNpuFFN", FakeNPU), \
             patch.object(bench, "TimedFFN", Timed), \
             patch.object(bench, "cpu_values", side_effect=lambda x: x.copy()), \
             patch.object(bench, "reference_partitioned", side_effect=lambda x, *_: (2 * x, {"gpu": x, "npu": x})), \
             redirect_stdout(io.StringIO()):
            gpu = bench._instrument_gpu(SimpleNamespace(device="fake", metadata={"baseline": True}), args)
            baseline = Timed(gpu, None, 128, 128, "fake")
            bench.run_partition(args, 128, weights, original, gpu, baseline,
                inputs, inputs, refs, refs, OutputIntegrity(), entry)
        self.assertEqual(entry["status"], "passed")
        self.assertEqual(entry["measurement_mode"], "gpu_device_diagnostic")
        self.assertFalse(entry["ordinary_headline_eligible"])
        self.assertIsNone(entry["speedup_vs_gpu_baseline"])
        self.assertIsNone(entry["speedup_vs_serial_partition"])
        self.assertEqual(entry["completed_candidate_calls"], 14)
        self.assertEqual(len(history), 34)
        for before, after in zip(history[::2], history[1::2]):
            self.assertEqual(before[0], "boundary_complete")
            self.assertEqual(after, ("collect", *before[1:]))
        for record in [*entry["validation_runs"], *entry["warmup_samples"], *entry["samples"]]:
            self.assertEqual(record["gpu_device_diagnostics"]["device_elapsed_us"],
                             10.0 if record["mode"] == "baseline" else 11.0)
        self.assertEqual(entry["gpu_device_stats"]["baseline"]["count"], 2)
        self.assertEqual(entry["gpu_device_stats"]["serial"]["median_us"], 11.0)


if __name__ == "__main__":
    unittest.main()
