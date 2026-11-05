"""Host contracts for native8 streaming-A and preconverted-B experiments.

These tests validate routing, cache identity and evidence gates, not device
arithmetic, XRT coherence or hardware performance.
"""

import contextlib
import copy
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from . import compare_upstream_native as compare
from . import run_upstream_partition as bench
from . import upstream_npu as backend
from .test_native8_integration import optimized_report
from .test_shared_npu import FakeRunner


def weights(hidden=512, intermediate=1024):
    result = []
    for k, n in ((hidden, intermediate), (hidden, intermediate), (intermediate, hidden)):
        data = np.zeros(k // 128 * (n // 64) * 4352, np.uint8)
        data.flags.writeable = False
        result.append(backend.UpstreamWeightBuffer(data, k, n))
    return result


def options(split=False, preconvert=False, preconvert_a=False):
    return dict(arithmetic="bfp16", bfp16_native_layout=True,
        swiglu_input_layout="row_major", output_layout="down_a", down_output_layout="row_major",
        swiglu_reuse=4, down_reuse=4, swiglu_output_fifo_depth=1,
        swiglu_activation_fifo_depth=2 if split else 1,
        down_activation_fifo_depth=2 if split else 1,
        split_m32_a=split, preconvert_b=preconvert, preconvert_a=preconvert_a)


def report_with_options(split, preconvert, preconvert_a=False):
    args, job, report = optimized_report()
    args.split_m32_a, args.preconvert_b = split, preconvert
    args.preconvert_a = preconvert_a
    report["config"].update(split_m32_a=split, preconvert_b=preconvert, preconvert_a=preconvert_a)
    selected = compare.candidate_options(args)
    report["npu_options"] = selected
    part = report["partitions"][0]
    part["npu"].update(split_m32_a=split, preconvert_b=preconvert, preconvert_a=preconvert_a)
    kernel = dict(selected, down_output_fifo_depth=2,
                  split_m32_a=split, preconvert_b=preconvert, preconvert_a=preconvert_a)
    kernel.pop("segment_pipeline_depth")
    part["npu"]["kernel_options"] = kernel
    for stage, artifact in part["npu"]["artifacts"].items():
        fields = dict(split_m32_a=split, preconvert_b=preconvert,
                      preconvert_a=preconvert_a,
                      activation_m_reuse=2 if split else 4,
                      activation_fifo_depth=2 if split else 1)
        artifact["manifest"].update(fields)
        artifact["build_contract"]["expected_manifest"].update(fields)
    return args, job, report


class SplitM32IntegrationTests(unittest.TestCase):
    def test_preconverted_a_routes_only_with_split_and_preconverted_b(self):
        flags = ["--bfp16-native-layout", "--swiglu-reuse", "4", "--split-m32-a", "--preconvert-b", "--preconvert-a"]
        args = compare.parse_args(["--native-root", "/native", "--artifact-root", "/artifact",
            "--no-build-candidate", "--output-dir", "/output", *flags])
        for job in compare.build_jobs(args):
            if job["variant"] == "native":
                self.assertNotIn("--preconvert-a", job["command"])
            else:
                child, _ = bench.parse_args(job["command"][3:])
                self.assertTrue(bench.kernel_options(child)["preconvert_a"])
                self.assertEqual(bench.kernel_options(child), compare.candidate_options(args))
        for missing in ("--split-m32-a", "--preconvert-b"):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                bench.parse_args(["--no-build", *[flag for flag in flags if flag != missing]])
        args, job, report = report_with_options(True, True, True)
        compare.validate_candidate(report, job, args)
        for location in ("metadata", "kernel", "manifest", "contract"):
            broken = copy.deepcopy(report)
            npu = broken["partitions"][0]["npu"]
            target = {"metadata": npu, "kernel": npu["kernel_options"],
                "manifest": npu["artifacts"]["down"]["manifest"],
                "contract": npu["artifacts"]["down"]["build_contract"]["expected_manifest"]}[location]
            target["preconvert_a"] = False
            with self.subTest(location=location), self.assertRaises(ValueError):
                compare.validate_candidate(broken, job, args)
        with tempfile.TemporaryDirectory() as root:
            ordinary = backend._ffn_specs(512, 512, 512, *weights(), root, **options(True, True))
            enabled = backend._ffn_specs(512, 512, 512, *weights(), root, **options(True, True, True))
            for stage in enabled:
                self.assertIn("--preconvert-a", enabled[stage]["arguments"])
                self.assertTrue(enabled[stage]["expected"]["preconvert_a"])
                self.assertNotEqual(enabled[stage]["directory"], ordinary[stage]["directory"])

    def test_opt_in_cli_routes_both_stages_and_keeps_defaults(self):
        default, _ = bench.parse_args(["--no-build"])
        self.assertFalse(default.split_m32_a or default.preconvert_b)
        self.assertEqual(bench.kernel_options(default), bench.selected_options())
        for split, preconvert in ((False, True), (True, False), (True, True)):
            flags = ["--bfp16-native-layout", "--swiglu-reuse", "4"]
            if split:
                flags += ["--split-m32-a"]
            if preconvert:
                flags += ["--preconvert-b"]
            args = compare.parse_args(["--native-root", "/native", "--artifact-root", "/artifact",
                "--no-build-candidate", "--output-dir", "/output", *flags])
            for job in compare.build_jobs(args):
                if job["variant"] == "native":
                    self.assertNotIn("--split-m32-a", job["command"])
                    self.assertNotIn("--preconvert-b", job["command"])
                    continue
                run, _ = bench.parse_args(job["command"][3:])
                self.assertEqual(bench.kernel_options(run), compare.candidate_options(args))
                self.assertEqual(run.split_m32_a, split)
                self.assertEqual(run.preconvert_b, preconvert)
                if split:
                    for stage in ("swiglu", "down"):
                        self.assertEqual(bench.kernel_options(run)[stage + "_activation_fifo_depth"], 2)
        for bad in (["--split-m32-a"], ["--preconvert-b"],
                    ["--bfp16-native-layout", "--split-m32-a"]):
            with self.subTest(flags=bad), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                bench.parse_args(["--no-build", *bad])

    def test_four_combinations_have_distinct_cache_and_manifest_identity(self):
        full = weights()
        identities = {stage: set() for stage in ("swiglu", "down")}
        with tempfile.TemporaryDirectory() as root:
            for split in (False, True):
                for preconvert in (False, True):
                    specs = backend._ffn_specs(512, 512, 512, *full, root, **options(split, preconvert))
                    for stage, spec in specs.items():
                        identities[stage].add(spec["directory"])
                        manifest = spec["expected"]
                        self.assertEqual(manifest["m_reuse"], 4)
                        self.assertEqual(manifest["activation_m_reuse"], 2 if split else 4)
                        self.assertIs(manifest["split_m32_a"], split)
                        self.assertIs(manifest["preconvert_b"], preconvert)
                        self.assertEqual("--split-m32-a" in spec["arguments"], split)
                        self.assertEqual("--preconvert-b" in spec["arguments"], preconvert)
                        self.assertEqual((manifest["m"], manifest["k"], manifest["n"]), (512, 512, 512))
                        self.assertEqual(manifest["weight_tile_bytes"], 4352)
            self.assertEqual([len(values) for values in identities.values()], [4, 4])

    def test_unsupported_shapes_depths_and_arithmetic_fail_before_build(self):
        full = weights()
        with tempfile.TemporaryDirectory() as root:
            for changed in ({"bfp16_native_layout": False}, {"arithmetic": "bf16"},
                    {"swiglu_activation_fifo_depth": 1}, {"down_activation_fifo_depth": 1},
                    {"swiglu_output_fifo_depth": 2}, {"swiglu_reuse": 2},
                    {"split_m32_a": 1}, {"preconvert_b": 1}):
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    backend._ffn_specs(512, 512, 512, *full, root, **(options(True) | changed))
            # Effective R2, an odd N32 ownership tail, and down N256 are unsupported.
            for m, hidden, channels in ((128, 512, 512), (512, 512, 384), (512, 256, 512)):
                with self.subTest(shape=(m, hidden, channels)), self.assertRaises(ValueError):
                    backend._ffn_specs(m, hidden, channels, *weights(hidden), root, **options(True))

    def test_actual_adapter_preserves_host_shapes_weights_and_counts(self):
        full, loaded, events = weights(), [], []

        def load(spec):
            loaded.append(spec)
            return dict(xclbin=spec["expected"]["mode"], insts="fake", manifest=spec["expected"])

        def runner(binary, instructions, specs):
            return FakeRunner("swiglu" if binary == "swiglu" else "down", specs, events)

        with tempfile.TemporaryDirectory() as root, \
             patch.object(backend, "_load_artifact", side_effect=load), \
             patch.object(backend, "PersistentXrtRunner", side_effect=runner):
            npu = backend.UpstreamNpuFFN(512, 512, 512, *full, root, **options(True, True))
            for _ in range(2):
                output = npu.run(np.zeros((512, 512), np.uint16))
            self.assertEqual(output.shape, (512, 512))
            self.assertTrue(npu.metadata["split_m32_a"] and npu.metadata["preconvert_b"])
            self.assertFalse(npu.metadata["weight_repacking"])
            self.assertEqual(npu.swiglu.input_write_counts, [2, 1, 1])
            self.assertEqual(npu.down.input_write_counts, [2, 1])
            self.assertEqual([r.completed_dispatches for r in npu.runners.values()], [2, 2])
            self.assertEqual(npu.swiglu.specs[0], ((512 * 512,), np.uint16))
            self.assertEqual(npu.down.specs[0], ((512 * 512,), np.uint16))
            for actual, expected in zip(npu.weights, full):
                self.assertIs(actual.data, expected.data)
                self.assertFalse(actual.data.flags.writeable)
        self.assertTrue(all(s["expected"]["activation_m_reuse"] == 2 for s in loaded))

    def test_comparator_requires_executed_flags_and_activation_geometry(self):
        for split, preconvert in ((False, True), (True, False), (True, True)):
            args, job, report = report_with_options(split, preconvert)
            compare.validate_candidate(report, job, args)
            mutations = [
                lambda r: r["partitions"][0]["npu"].update(split_m32_a=not split),
                lambda r: r["partitions"][0]["npu"].update(preconvert_b=not preconvert),
                lambda r: r["partitions"][0]["npu"]["artifacts"]["swiglu"]["manifest"].update(activation_m_reuse=8),
                lambda r: r["partitions"][0]["npu"]["artifacts"]["down"]["manifest"].update(preconvert_b=not preconvert),
                lambda r: r["partitions"][0]["npu"]["artifacts"]["down"]["build_contract"]["expected_manifest"].update(split_m32_a=not split),
            ]
            for index, mutate in enumerate(mutations):
                broken = copy.deepcopy(report)
                mutate(broken)
                with self.subTest(split=split, preconvert=preconvert, mutation=index), self.assertRaises(ValueError):
                    compare.validate_candidate(broken, job, args)


if __name__ == "__main__":
    unittest.main()
