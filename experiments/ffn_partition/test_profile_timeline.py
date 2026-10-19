"""CPU checks for fusion-aware probes; these do not claim hardware timing."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from experiments.ffn_partition.profile_timeline import (
    KernelSubmissionProbe, completion_counts, fixed_weight_upload_counts,
    npu_runners, summarize)


HERE = Path(__file__).resolve().parent


class TimelineTests(unittest.TestCase):
    def test_launch_mapping_and_concatenated_weight_upload(self):
        runner = lambda: SimpleNamespace(input_write_counts=[12, 1], completed_dispatches=12)
        fused = SimpleNamespace(fuse_gate_up=True, gate_up=runner(), silu=runner(), down=runner())
        self.assertEqual(tuple(npu_runners(fused)), ("gate_up", "silu_mul", "down"))
        self.assertEqual(fixed_weight_upload_counts(fused), {"gate_up": 1, "down": 1})
        unfused = SimpleNamespace(fuse_gate_up=False, gate=runner(), up=runner(), silu=runner(), down=runner())
        self.assertEqual(tuple(npu_runners(unfused)), ("gate", "up", "silu_mul", "down"))
        self.assertEqual(fixed_weight_upload_counts(unfused), {"gate": 1, "up": 1, "down": 1})

    def test_swiglu_maps_only_the_two_real_launches(self):
        # There is no separate gate/up or SiLU runner in this path. Having
        # fuse_gate_up=True must not make the profiler probe nonexistent BOs.
        runner = lambda: SimpleNamespace(input_write_counts=[12, 1], completed_dispatches=12)
        npu = SimpleNamespace(fuse_gate_up=True, fuse_swiglu=True,
                              swiglu=runner(), down=runner())
        self.assertEqual(tuple(npu_runners(npu)), ("swiglu", "down"))
        self.assertEqual(fixed_weight_upload_counts(npu), {"swiglu": 1, "down": 1})
        self.assertEqual(completion_counts(npu, 12), {"swiglu": 12, "down": 12})

    def test_completion_check_rejects_compensating_stage_counts(self):
        npu = SimpleNamespace(fuse_gate_up=True, fuse_swiglu=True,
                              swiglu=SimpleNamespace(completed_dispatches=11),
                              down=SimpleNamespace(completed_dispatches=13))
        # The total is still 24, so a sum-only assertion would miss this.
        with self.assertRaisesRegex(RuntimeError, "per-stage completion"):
            completion_counts(npu, 12)

    def test_probe_preserves_failed_wait_result(self):
        handle = SimpleNamespace(wait=lambda timeout: ("failed", timeout))
        probe = KernelSubmissionProbe(lambda: handle)
        self.assertEqual(probe().wait(123), ("failed", 123))
        snapshot = probe.snapshot(0)
        self.assertGreaterEqual(snapshot["submit_host_us"], 0)
        self.assertGreaterEqual(snapshot["wait_host_us"], 0)

    def test_existing_unfused_summary_unchanged(self):
        report = json.loads((HERE / "results/timeline_m512_p512_array8.json").read_text())
        self.assertEqual(summarize(report["samples"]), report["stats"])

    def test_fused_summary_uses_combined_stage_and_rejects_mixed_schema(self):
        original = json.loads((HERE / "results/timeline_m512_p512_array8.json").read_text())["samples"][0]
        sample = copy.deepcopy(original)
        for path in (sample["npu_submit_wait_host"], sample["npu"]["dispatch_wait_us"]):
            gate, _ = path.pop("gate"), path.pop("up")
            converted = {"gate_up": gate, **path}
            path.clear()
            path.update(converted)
        stages = sample["npu"]["stages"]
        stages["gate_up_with_host_io_us"] = stages.pop("gate_with_host_io_us")
        stages.pop("up_with_host_io_us")
        summary = summarize([sample])
        self.assertEqual(tuple(summary["npu_wait_host_us"]), ("gate_up", "silu_mul", "down"))
        with self.assertRaisesRegex(ValueError, "mix"):
            summarize([sample, original])

    def test_swiglu_summary_keeps_composite_interval_unsplit(self):
        original = json.loads((HERE / "results/timeline_m512_p512_array8.json").read_text())["samples"][0]
        sample = copy.deepcopy(original)
        # Synthetic schema-only inputs: these intervals are placeholders and
        # are not presented as observed SwiGLU execution time.
        sample["npu_submit_wait_host"] = {
            "swiglu": dict(submit_host_us=10.0, wait_host_us=900.0),
            "down": dict(submit_host_us=20.0, wait_host_us=800.0),
        }
        sample["npu"]["dispatch_wait_us"] = {"swiglu": 910.0, "down": 820.0}
        sample["npu"]["stages"] = {
            "input_layout_us": 30.0, "swiglu_with_host_io_us": 1000.0,
            "down_input_layout_us": 20.0, "down_with_host_io_us": 900.0,
            "output_layout_us": 40.0,
        }
        summary = summarize([sample])
        self.assertEqual(tuple(summary["npu_wait_host_us"]), ("swiglu", "down"))
        self.assertEqual(summary["npu_stage_host_us"]["swiglu_with_host_io_us"]["median_us"], 1000.0)
        self.assertNotIn("silu_mul", summary["npu_wait_host_us"])
        self.assertNotIn("gate_up", summary["npu_wait_host_us"])
        with self.assertRaisesRegex(ValueError, "mix"):
            summarize([sample, original])


if __name__ == "__main__":
    unittest.main()
