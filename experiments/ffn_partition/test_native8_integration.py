"""CPU integration routing only; fake BOs establish neither NPU math nor coherence."""

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
from .shared_npu import SharedNpuFFN
from .test_shared_npu import FakeRunner
from .test_compare_upstream_native import (arguments, candidate_report, refresh_accuracy)
from .contract import accuracy_metrics


def original_weights():
    result = []
    for k, n in ((256, 512), (256, 512), (512, 256)):
        data = np.zeros((k // 128) * (n // 64) * 4352, np.uint8)
        data.flags.writeable = False
        result.append(backend.UpstreamWeightBuffer(data, k, n))
    return result


def optimized_report(*, teammate=False):
    args = arguments("/output")
    args.bfp16_native_layout, args.swiglu_reuse = True, 4
    if teammate:
        args.gpu_variant = "teammate"
    job = next(job for job in compare.build_jobs(args) if job["variant"] == "upstream")
    report = candidate_report(args, job)
    part, p = report["partitions"][0], job["npu_channels"]
    options = compare.candidate_options(args)
    report["npu_options"] = options
    kernel_options = dict(options, down_output_fifo_depth=2)
    kernel_options.pop("segment_pipeline_depth")
    part["npu"].update(bfp16_native_layout=True, accumulator_format="bf16",
        segment_pipeline_depth=2, kernel_options=kernel_options)
    closure = {name: str(index) * 64 for index, name in enumerate((
        "w4a16_upstream.py", "w4a16_prefill_upstream.cc", "upstream_schedule.py",
        "upstream_output.py", "upstream_weights.py"))}
    artifacts = {}
    for name, fields in (("swiglu", dict(mode="swiglu", k=4096, n=p, weight_k=4096,
            weight_n=14336, input_layout="row_major", output_layout="down_a", output_fifo_depth=1)),
            ("down", dict(mode="projection", k=p, n=4096, weight_k=14336,
            weight_n=4096, input_layout="compact", output_layout="row_major", output_fifo_depth=2))):
        expected = dict(kind="w4a16_upstream_bfp16", arithmetic="bfp16", compute_format="bfp16",
            m=512, cols=8, compute_rows=4, worker_count=32, worker_stack_size=4096,
            weight_tile_bytes=4352, segment_pipeline_depth=2, vector_zero=True, mmul_m_reuse=1,
            bfp16_native_layout=True, accumulator_format="bf16", k_start=0, n_start=0,
            m_reuse=4, activation_fifo_depth=1, dependency_sha256=closure,
            source_sha256=closure["w4a16_prefill_upstream.cc"], graph_sha256=closure["w4a16_upstream.py"],
            **fields)
        artifacts[name] = dict(manifest=dict(expected, xclbin_sha256="a" * 64, insts_sha256="b" * 64),
            build_contract=dict(expected_manifest=expected, source_sha256=closure))
    report["artifacts"] = {str(p): artifacts}
    part["npu"]["artifacts"] = artifacts
    if teammate:
        from .teammate_gpu import SOURCE_DEPENDENCIES, ROOT
        part["gpu"] = dict(backend="teammate_three_kernel_gpu_ffn", m=512, hidden=4096,
            channels=14336-p, source_intermediate=14336, source_channel_begin=p,
            source_channel_end=14336, kernels_per_prefill=3, gemm_autotune=0,
            source_sha256={str(path.relative_to(ROOT)): "e" * 64 for path in SOURCE_DEPENDENCIES},
            source_packed_sha256=report["gpu_baseline_packed_weight_sha256"],
            prepared_packed_sha256=dict(gate_up="c" * 64, down="d" * 64),
            build_fingerprint="a" * 64, binary_sha256="b" * 64)
    return args, job, report


class Native8IntegrationTests(unittest.TestCase):
    def test_gpu_diagnostic_timings_are_excluded_from_ordinary_comparison(self):
        args, job, report = optimized_report()
        for mutate in (lambda r: r["config"].update(gpu_device_diagnostics=True),
                       lambda r: r.update(measurement_mode="gpu_device_diagnostic"),
                       lambda r: r.update(ordinary_headline_eligible=False)):
            broken = copy.deepcopy(report)
            mutate(broken)
            with self.assertRaisesRegex(ValueError, "diagnostic timing"):
                compare.validate_candidate(broken, job, args)

    def test_native8_execution_manifest_and_cache_provenance_are_enforced(self):
        args, job, report = optimized_report()
        self.assertEqual(compare.validate_candidate(report, job, args)["status"], "passed")
        mutations = [
            lambda r: r["partitions"][0]["npu"].update(bfp16_native_layout=False),
            lambda r: r["partitions"][0]["npu"].update(accumulator_format="float32"),
            lambda r: r["partitions"][0]["npu"]["kernel_options"].update(swiglu_reuse=2),
            lambda r: r["partitions"][0]["npu"]["artifacts"]["swiglu"]["manifest"].update(m_reuse=2),
            lambda r: r["partitions"][0]["npu"]["artifacts"]["swiglu"]["manifest"].update(output_fifo_depth=2),
            lambda r: r["partitions"][0]["npu"]["artifacts"]["down"]["manifest"].update(output_layout="compact"),
            lambda r: r["partitions"][0]["npu"]["artifacts"]["down"]["manifest"].update(accumulator_format="float32"),
            lambda r: r["partitions"][0]["npu"]["artifacts"]["down"]["manifest"].update(xclbin_sha256="bad"),
            lambda r: r["partitions"][0]["npu"]["artifacts"]["down"]["build_contract"].update(source_sha256={}),
            lambda r: r.update(artifacts={}),
        ]
        for index, mutate in enumerate(mutations):
            broken = copy.deepcopy(report)
            mutate(broken)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                compare.validate_candidate(broken, job, args)

    def test_native8_keeps_strict_gpu_and_structural_acceptance(self):
        args, job, report = optimized_report()
        broken = copy.deepcopy(report)
        sample = broken["partitions"][0]["validation_runs"][0]
        sample["accuracy"]["gpu"].update(accuracy_metrics(np.full(2, 2, np.float32), np.ones(2, np.float32), "strict"))
        refresh_accuracy(broken)
        with self.assertRaises(ValueError):
            compare.validate_candidate(broken, job, args)
        for mutate in (lambda r: r["partitions"][0]["validation_runs"][4].update(output_sha256="1" * 64),
                       lambda r: r["partitions"][0]["completed_npu_dispatches_by_stage"].update(down=0)):
            broken = copy.deepcopy(report)
            mutate(broken)
            with self.assertRaises(ValueError):
                compare.validate_candidate(broken, job, args)

    def test_teammate_source_and_full_weight_provenance_are_required(self):
        args, job, report = optimized_report(teammate=True)
        compare.validate_candidate(report, job, args)
        for field, wrong in (("source_channel_begin", 0), ("source_packed_sha256", {}),
                             ("source_sha256", {}), ("binary_sha256", "bad"),
                             ("prepared_packed_sha256", {})):
            broken = copy.deepcopy(report)
            broken["partitions"][0]["gpu"][field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                compare.validate_candidate(broken, job, args)

    def test_default_profile_is_unchanged_and_native8_requires_bfp(self):
        args, _ = bench.parse_args(["--no-build"])
        self.assertEqual(bench.kernel_options(args), bench.selected_options())
        self.assertFalse(args.shared_intermediate)
        self.assertFalse(args.mapped_npu_output)
        self.assertEqual(args.gpu_variant, "original")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            bench.parse_args(["--no-build", "--npu-arithmetic", "bf16", "--bfp16-native-layout"])

    def test_comparison_commands_and_execution_options_agree(self):
        args = compare.parse_args(["--native-root", "/native", "--artifact-root", "/artifact",
            "--no-build-candidate", "--output-dir", "/output", "--npu-channels", "2560",
            "--bfp16-native-layout", "--swiglu-reuse", "4", "--mapped-npu-output",
            "--shared-intermediate", "--gpu-variant", "teammate"])
        jobs = compare.build_jobs(args)
        self.assertEqual([job["variant"] for job in jobs], ["native", "upstream", "upstream", "native"])
        for job in jobs:
            if job["variant"] == "native":
                self.assertNotIn("--bfp16-native-layout", job["command"])
                self.assertNotIn("--gpu-variant", job["command"])
                continue
            run_args, channels = bench.parse_args(job["command"][3:])
            self.assertEqual(channels, [2560])
            self.assertEqual(bench.kernel_options(run_args), compare.candidate_options(args))
            self.assertTrue(run_args.shared_intermediate)
            self.assertTrue(run_args.mapped_npu_output)
            self.assertEqual(run_args.gpu_variant, "teammate")
            self.assertEqual(bench.kernel_options(run_args)["down_output_layout"], "row_major")

    def test_native8_cache_identity_and_invalid_layout_combinations(self):
        weights = original_weights()
        with tempfile.TemporaryDirectory() as root:
            options = dict(arithmetic="bfp16", swiglu_input_layout="row_major",
                           output_layout="down_a", down_output_layout="row_major")
            control = backend._ffn_specs(128, 256, 256, *weights, root, **options)
            candidate = backend._ffn_specs(128, 256, 256, *weights, root,
                                           bfp16_native_layout=True, **options)
            for label, spec in candidate.items():
                self.assertNotEqual(spec["directory"], control[label]["directory"])
                self.assertIn("--bfp16-native-layout", spec["arguments"])
                self.assertTrue(spec["expected"]["bfp16_native_layout"])
                self.assertEqual(spec["expected"]["accumulator_format"], "bf16")
                self.assertEqual(control[label]["expected"]["accumulator_format"], "float32")
                self.assertEqual(spec["expected"]["weight_tile_bytes"], 4352)
            for changed in ({"swiglu_input_layout": "compact"}, {"output_layout": "compact"},
                            {"down_output_layout": "compact"}, {"arithmetic": "bf16"}):
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    backend._ffn_specs(128, 256, 256, *weights, root,
                        bfp16_native_layout=True, **(options | changed))

    def test_actual_parent_and_shared_adapter_preserve_native8_row_major_routing(self):
        weights, loaded, events = original_weights(), [], []

        def load(spec):
            loaded.append(spec)
            return dict(xclbin=spec["expected"]["mode"], insts="fake", manifest=spec["expected"])

        def runner(xclbin, insts, specs):
            return FakeRunner("swiglu" if xclbin == "swiglu" else "down", specs, events)

        options = dict(arithmetic="bfp16", bfp16_native_layout=True,
            swiglu_input_layout="row_major", output_layout="down_a", down_output_layout="row_major",
            copy_output_bits=False)
        with patch.object(backend, "_load_artifact", side_effect=load), \
             patch.object(backend, "PersistentXrtRunner", side_effect=runner), \
             patch.object(backend, "_pack_activation_bits", side_effect=AssertionError("native4 input pack")), \
             patch.object(backend, "_unpack_output_bits", side_effect=AssertionError("native4 output unpack")), \
             patch.object(backend, "packed_output_to_activation", side_effect=AssertionError("native4 Z transpose")), \
             patch("experiments.ffn_partition.shared_npu._pack_activation_bits", side_effect=AssertionError("shared native4 pack")), \
             patch("experiments.ffn_partition.shared_npu._unpack_output_bits", side_effect=AssertionError("shared native4 unpack")):
            staged = backend.UpstreamNpuFFN(128, 256, 256, *weights, Path("unused"), **options)
            shared = SharedNpuFFN(128, 256, 256, *weights, Path("unused"),
                shared_intermediate=True, mapped_output=True, **options)
            x = (np.arange(128 * 512, dtype=np.uint16).reshape(128, 512) % 128)[:, ::2]
            self.assertFalse(x.flags.c_contiguous)
            output = staged.run(x)
            shared_output = shared.run(x)
            # FakeRunner deliberately returns A+1, then Z+2. Coordinate-varying
            # values expose unintended native4 host permutations.
            np.testing.assert_array_equal(output, x + 3)
            np.testing.assert_array_equal(shared_output, output)
            np.testing.assert_array_equal(staged.swiglu.buffers[0].values.reshape(x.shape), x)
            saved = shared_output.copy()
            shared.run(np.zeros_like(x))
            np.testing.assert_array_equal(shared_output, saved)
            self.assertFalse(np.shares_memory(shared_output, shared.mapped_output_view))
            bench.assert_runtime_counts(staged, 1)
            bench.assert_runtime_counts(shared, 2)
        self.assertEqual(len(loaded), 4)
        self.assertTrue(all(spec["expected"]["bfp16_native_layout"] for spec in loaded))
        self.assertTrue(shared.metadata["bfp16_native_layout"])
        self.assertEqual(shared.metadata["accumulator_format"], "bf16")
        self.assertIs(shared.swiglu.buffers[-1], shared.down.buffers[0])
        self.assertEqual(shared.swiglu.buffers[-1].reads, 0)
        self.assertEqual(shared.swiglu.buffers[-1].syncs, [])
        for original, uploaded in zip(weights, (shared.swiglu.buffers[1], shared.swiglu.buffers[2], shared.down.buffers[1])):
            np.testing.assert_array_equal(original.data, uploaded.values)


if __name__ == "__main__":
    unittest.main()
