"""CPU-only regressions for NPU FFN staging, BO reuse and artifact provenance.

The fake runners evaluate NumPy oracles; these tests do not establish NPU
execution, numerical fidelity of compiled kernels, or measured performance.
"""

from hashlib import sha256
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

import npu_backend as backend
from contract import error_metrics, random_weights, reference_full
from prefill_reference import (bf16_bits, bf16_from_bits, pack_output,
                               projection_reference, unpack_activations,
                               unpack_weights)
from reference import silu_multiply


def _write_mock_artifacts(root, m=128, hidden=128, channels=256,
                          columns=4, design="legacy", fuse_gate_up=False,
                          fuse_swiglu=False, arithmetic="bf16"):
    """Valid manifests with unmistakably fake binaries, never sent to XRT."""
    specs = backend._artifact_specs(m, hidden, channels, root, columns, design, fuse_gate_up,
                                    fuse_swiglu, arithmetic)
    for spec in specs.values():
        directory = spec["directory"]
        directory.mkdir(parents=True, exist_ok=True)
        xclbin = b"CPU TEST MOCK -- NOT AN NPU BINARY"
        instructions = b"MOCK"
        (directory / "final.xclbin").write_bytes(xclbin)
        (directory / "insts.bin").write_bytes(instructions)
        manifest = dict(
            spec["expected"], target_mlir_aie_commit=backend.TARGET_COMMIT,
            source_sha256=spec["source_sha256"][f"npu/ffn/{backend._kernel_source(spec['stem'], arithmetic)}.cc"],
            xclbin_sha256=sha256(xclbin).hexdigest(),
            insts_sha256=sha256(instructions).hexdigest(),
        )
        (directory / "final.xclbin.json").write_text(json.dumps(manifest))
        (directory / "build_contract.json").write_text(json.dumps(backend._build_contract(spec)))
    return specs


class _OracleRunner:
    """Observe exact uploaded bytes and independently compute fake outputs."""

    def __init__(self, xclbin, insts, specs, output_count=1):
        self.manifest = json.loads(Path(str(xclbin) + ".json").read_text())
        self.specs = specs
        self.inputs = {}
        self.input_write_counts = [0, 0]
        self.completed_dispatches = 0
        self.output_count = output_count

    def write_input(self, index, data):
        shape, dtype = self.specs[index]
        if data.shape != shape or data.dtype != np.dtype(dtype):
            raise AssertionError("backend uploaded bytes incompatible with compiled BO geometry")
        self.inputs[index] = data.copy()
        self.input_write_counts[index] += 1

    def dispatch_wait(self):
        if set(self.inputs) != {0, 1}:
            raise AssertionError("backend dispatched before initializing both inputs")
        manifest = self.manifest
        if manifest["kind"] == "silu_mul_bf16":
            result = silu_multiply(bf16_from_bits(self.inputs[0]),
                                   bf16_from_bits(self.inputs[1]), bf16_io=True)
            self.result = bf16_bits(result)
        else:
            x = unpack_activations(self.inputs[0], manifest["m"], manifest["k"])
            weight = unpack_weights(self.inputs[1], manifest["k"], manifest["n"])
            projected = projection_reference(x, weight)
            if self.output_count == 2:
                p = manifest["channels"]
                self.result = (pack_output(projected[:, :p]), pack_output(projected[:, p:]))
            else:
                self.result = pack_output(projected)
        self.completed_dispatches += 1
        return 1.0  # Synthetic placeholder, never a latency measurement.

    def output_bits(self, index=0, *, copy=True):
        result = self.result[index] if self.output_count == 2 else self.result
        return result.copy() if copy else result


class NPUBackendTests(unittest.TestCase):
    def test_arithmetic_separates_projection_cache_but_reuses_standalone_silu(self):
        with tempfile.TemporaryDirectory() as root:
            for fused, swiglu in ((False, False), (True, False), (True, True)):
                with self.subTest(fused=fused, swiglu=swiglu):
                    native = backend._artifact_specs(128, 128, 256, root,
                        fuse_gate_up=fused, fuse_swiglu=swiglu)
                    block = backend._artifact_specs(128, 128, 256, root,
                        fuse_gate_up=fused, fuse_swiglu=swiglu, arithmetic="bfp16")
                    self.assertEqual(set(native), set(block))
                    for label in native:
                        if label == "silu_mul":
                            self.assertEqual(native[label], block[label])
                            continue
                        a, b = native[label], block[label]
                        self.assertNotEqual(a["directory"], b["directory"])
                        self.assertIn("_bfp16_", b["directory"].name)
                        self.assertNotEqual(a["source_sha256"], b["source_sha256"])
                        self.assertIn("npu/ffn/w4a16_prefill_bfp16.cc", b["source_sha256"])
                        self.assertNotIn("npu/ffn/w4a16_prefill_reuse.cc", b["source_sha256"])
                        self.assertIn("npu/ffn/projection_arithmetic.py", b["source_sha256"])
                        self.assertEqual(b["expected"]["arithmetic"], "bfp16")
                        self.assertEqual(b["expected"]["worker_stack_size"], 4096)
                        self.assertEqual(a["expected"]["worker_stack_size"], 2048)
                        arg = b["arguments"].index("--arithmetic")
                        self.assertEqual(b["arguments"][arg + 1], "bfp16")
                        self.assertEqual(a["expected"]["kind"], b["expected"]["kind"])
                        a_plan, b_plan = dict(a.get("plan", {})), dict(b.get("plan", {}))
                        if swiglu and label == "swiglu":
                            a_memory = a_plan.pop("memory_estimate")
                            b_memory = b_plan.pop("memory_estimate")
                            for side in ("gate", "up"):
                                self.assertEqual(b_memory[side + "_raw_bytes"],
                                                 a_memory[side + "_raw_bytes"] + 2048)
                                self.assertEqual(b_memory[side + "_components_bytes"]["stack"], 4096)
                        self.assertEqual(a_plan, b_plan)

    def test_bfp16_load_rejects_wrong_arithmetic_source_helper_or_stack(self):
        with tempfile.TemporaryDirectory() as root:
            spec = _write_mock_artifacts(root, columns=8, design="array8",
                                         fuse_swiglu=True, arithmetic="bfp16")["swiglu"]
            backend._load_artifact(spec)
            path = spec["directory"] / "final.xclbin.json"
            original = json.loads(path.read_text())
            for key, replacement in (("arithmetic", "bf16"), ("compute_format", "bf16"),
                    ("source_sha256", "wrong-source"), ("arithmetic_source_sha256", "wrong-helper"),
                    ("upstream_kernel_commit", backend.TARGET_COMMIT), ("worker_stack_size", 2048)):
                with self.subTest(key=key):
                    path.write_text(json.dumps(dict(original, **{key: replacement})))
                    with self.assertRaisesRegex(ValueError, f"manifest {key}"):
                        backend._load_artifact(spec)

    def test_bfp16_build_propagates_compiler_mode_and_reuses_certified_artifacts(self):
        with tempfile.TemporaryDirectory() as root:
            specs = backend._artifact_specs(128, 128, 256, root, fuse_swiglu=True,
                                            arithmetic="bfp16")
            by_directory = {str(spec["directory"]): spec for spec in specs.values()}

            def fake_compile(command, **kwargs):
                directory = str(Path(command[command.index("--xclbin-path") + 1]).parent)
                spec = by_directory[directory]
                self.assertEqual(command[command.index("--arithmetic") + 1], "bfp16")
                xclbin, instructions = b"CPU TEST MOCK -- NOT AN NPU BINARY", b"MOCK"
                (spec["directory"] / "final.xclbin").write_bytes(xclbin)
                (spec["directory"] / "insts.bin").write_bytes(instructions)
                kernel = backend._kernel_source(spec["stem"], "bfp16")
                manifest = dict(spec["expected"], target_mlir_aie_commit=backend.TARGET_COMMIT,
                    source_sha256=spec["source_sha256"][f"npu/ffn/{kernel}.cc"],
                    xclbin_sha256=sha256(xclbin).hexdigest(),
                    insts_sha256=sha256(instructions).hexdigest())
                (spec["directory"] / "final.xclbin.json").write_text(json.dumps(manifest))
                return SimpleNamespace(returncode=0)

            with patch.object(backend.subprocess, "run", side_effect=fake_compile) as compile_call:
                artifacts = backend.build_artifacts(128, 128, 256, root,
                    python_executable="CPU_TEST_COMPILER_STUB", fuse_swiglu=True,
                    npu_arithmetic="bfp16")
                self.assertEqual(compile_call.call_count, 2)
                self.assertEqual(set(artifacts), {"swiglu", "down"})
                backend.build_artifacts(128, 128, 256, root, fuse_swiglu=True,
                                        npu_arithmetic="bfp16")
                self.assertEqual(compile_call.call_count, 2)

    def test_bfp16_branch_records_selection_without_claiming_hardware_numerics(self):
        weights = random_weights(128, 256, seed=124)
        with tempfile.TemporaryDirectory() as root:
            _write_mock_artifacts(root, columns=8, design="array8", arithmetic="bfp16")
            with patch.object(backend, "PersistentXrtRunner", _OracleRunner):
                branch = backend.NPUBranch(weights.gate, weights.up, weights.down,
                                           128, root, npu_arithmetic="bfp16")
            self.assertEqual(branch.metadata["npu_arithmetic"], "bfp16")
            self.assertTrue(branch.copy_output_bits)
            self.assertEqual(branch.metadata["host_output_readback"], "owned_copy")
            self.assertEqual(branch.metadata["compute_format"], "bfp16")
            self.assertEqual(branch.metadata["worker_stack_size"], 4096)
            self.assertEqual(branch.metadata["launches_per_run"], 4)
            for label in ("gate_up", "down"):
                self.assertEqual(branch.metadata["artifacts"][label]["manifest"]["arithmetic"], "bfp16")
            with self.assertRaisesRegex(ValueError, "requires the array8"):
                backend._artifact_specs(128, 128, 256, root, design="legacy", arithmetic="bfp16")
            with self.assertRaisesRegex(ValueError, "unknown projection arithmetic"):
                backend._artifact_specs(128, 128, 256, root, arithmetic="fp16")

    def test_two_output_readbacks_select_distinct_buffers(self):
        runner = backend.PersistentXrtRunner.__new__(backend.PersistentXrtRunner)
        runner.output_count = 2
        runner.xrt = SimpleNamespace(xclBOSyncDirection=SimpleNamespace(
            XCL_BO_SYNC_BO_FROM_DEVICE=1))
        first = np.array([0x3F80, 0xBF80], np.uint16)
        second = np.array([0x4000, 0xC000], np.uint16)
        runner.specs = [((2,), np.dtype(np.uint16))] * 4
        runner.buffers = [None, None] + [
            SimpleNamespace(sync=lambda direction: None,
                            read=lambda nbytes, offset, data=data: data.view(np.int8))
            for data in (first, second)]
        np.testing.assert_array_equal(runner.output_bits(0), first)
        np.testing.assert_array_equal(runner.output_bits(1), second)
        with self.assertRaisesRegex(ValueError, "output index"):
            runner.output_bits(2)

    def test_strided_byte_readback_preserves_bf16_bits_and_ownership(self):
        expected = np.array([0x0000, 0x8000, 0x3F80, 0xBF80, 0x7FC1, 0x0080], np.uint16)
        storage = np.zeros(expected.nbytes * 2, dtype=np.uint8)
        storage[::2] = expected.view(np.uint8)
        raw = storage[::2]
        self.assertFalse(raw.flags.c_contiguous)
        observed = {}

        class Buffer:
            def sync(self, direction):
                observed["sync"] = direction

            def read(self, nbytes, offset):
                observed["read"] = (nbytes, offset)
                return raw

        runner = backend.PersistentXrtRunner.__new__(backend.PersistentXrtRunner)
        direction = object()
        runner.xrt = SimpleNamespace(xclBOSyncDirection=SimpleNamespace(
            XCL_BO_SYNC_BO_FROM_DEVICE=direction))
        runner.specs = [((2, 3), np.dtype(np.uint16))]
        runner.buffers = [Buffer()]
        result = runner.output_bits()
        self.assertIs(observed["sync"], direction)
        self.assertEqual(observed["read"], (expected.nbytes, 0))
        np.testing.assert_array_equal(result, expected.reshape(2, 3))
        self.assertFalse(np.shares_memory(result, raw))
        result[:] = 0
        np.testing.assert_array_equal(raw, expected.view(np.uint8))
        borrowed = runner.output_bits(copy=False)
        np.testing.assert_array_equal(borrowed, expected.reshape(2, 3))
        self.assertFalse(borrowed.flags.writeable)
        # Positive-strided readback still needs a normalization copy.
        self.assertFalse(np.shares_memory(borrowed, raw))

    def test_invalid_readback_abi_rejected_before_copy(self):
        # NumPy 2.5.4 with the notebook's prebuilt pyxrt returned exactly
        # this zero-stride shape. Copying it repeats one byte silently.
        invalid = {
            "zero_stride": np.broadcast_to(np.array([1], np.uint8), (8,)),
            "wrong_dtype": np.arange(8, dtype=np.uint16),
            "wrong_count": np.arange(7, dtype=np.uint8),
            "wrong_rank": np.arange(8, dtype=np.uint8).reshape(2, 4),
            "negative_stride": np.arange(8, dtype=np.uint8)[::-1],
        }
        runner = backend.PersistentXrtRunner.__new__(backend.PersistentXrtRunner)
        runner.xrt = SimpleNamespace(xclBOSyncDirection=SimpleNamespace(
            XCL_BO_SYNC_BO_FROM_DEVICE=1))
        runner.specs = [((4,), np.dtype(np.uint16))]
        for name, raw in invalid.items():
            runner.buffers = [SimpleNamespace(sync=lambda direction: None,
                                              read=lambda nbytes, offset: raw)]
            for copy in (True, False):
                with self.subTest(case=name, copy=copy), self.assertRaisesRegex(RuntimeError, "NumPy 1.26.4"):
                    runner.output_bits(copy=copy)
        # Ordinary byte buffers still succeed with independent ownership.
        raw = np.arange(8, dtype=np.uint8)
        runner.buffers = [SimpleNamespace(sync=lambda direction: None,
                                          read=lambda nbytes, offset: raw)]
        result = runner.output_bits()
        np.testing.assert_array_equal(result, raw.view(np.uint16))
        self.assertFalse(np.shares_memory(result, raw))

    def test_signed_char_readback_preserves_high_bits(self):
        # Compatible pyxrt exposes std::vector<char> as int8, including
        # negative values for bytes whose high bit is set. Reinterpret bytes;
        # do not reject the signed-char representation or numerically convert.
        expected = np.array([0xBF80, 0xFFFF, 0x8000, 0x3F80], dtype=np.uint16)
        raw = expected.view(np.int8).copy()
        self.assertTrue(np.any(raw < 0))
        runner = backend.PersistentXrtRunner.__new__(backend.PersistentXrtRunner)
        runner.xrt = SimpleNamespace(xclBOSyncDirection=SimpleNamespace(
            XCL_BO_SYNC_BO_FROM_DEVICE=1))
        runner.specs = [((4,), np.dtype(np.uint16))]
        runner.buffers = [SimpleNamespace(sync=lambda direction: None,
                                          read=lambda nbytes, offset: raw)]
        np.testing.assert_array_equal(runner.output_bits(), expected)

    def test_borrowed_readback_is_readonly_and_default_copy_stays_independent(self):
        expected = np.array([0x0000, 0x8000, 0x3F80, 0xBF80, 0x7FC1, 0x0080], np.uint16)
        raw = expected.view(np.int8).copy()
        runner = backend.PersistentXrtRunner.__new__(backend.PersistentXrtRunner)
        runner.xrt = SimpleNamespace(xclBOSyncDirection=SimpleNamespace(
            XCL_BO_SYNC_BO_FROM_DEVICE=1))
        runner.specs = [((2, 3), np.dtype(np.uint16))]
        runner.buffers = [SimpleNamespace(sync=lambda direction: None,
                                          read=lambda nbytes, offset: raw)]
        borrowed = runner.output_bits(copy=False)
        owned = runner.output_bits()
        np.testing.assert_array_equal(borrowed, expected.reshape(2, 3))
        self.assertTrue(np.shares_memory(borrowed, raw))
        self.assertFalse(np.shares_memory(owned, raw))
        self.assertFalse(borrowed.flags.writeable)
        self.assertTrue(raw.flags.writeable)
        self.assertTrue(owned.flags.writeable)
        raw[:] = 0  # Model a later dispatch reusing output storage.
        np.testing.assert_array_equal(borrowed, np.zeros((2, 3), np.uint16))
        np.testing.assert_array_equal(owned, expected.reshape(2, 3))

    def test_layout_consumers_detach_borrowed_output_for_supported_shapes(self):
        from contract import packed_output_to_activation
        # Include every BF16 bit pattern; this is a permutation, not a
        # floating-point conversion. Small and model-sized shapes cover the
        # nondegenerate dimensions enforced by NPUBranch's geometry contract.
        for m, n in ((128, 128), (128, 384), (512, 1792), (512, 4096)):
            with self.subTest(m=m, n=n):
                storage = np.arange(m * n, dtype=np.uint16)
                borrowed = storage.view()
                borrowed.flags.writeable = False
                output = backend._unpack_output_bits(borrowed, m, n)
                down_input = packed_output_to_activation(borrowed, m, n)
                expected_output, expected_down = output.copy(), down_input.copy()
                self.assertFalse(np.shares_memory(output, storage))
                self.assertFalse(np.shares_memory(down_input, storage))
                storage[:] = 0
                np.testing.assert_array_equal(output, expected_output)
                np.testing.assert_array_equal(down_input, expected_down)

    def test_borrowed_readback_keeps_transient_read_array_alive(self):
        import gc
        import weakref
        observed = {}

        def read(nbytes, offset):
            raw = np.arange(nbytes, dtype=np.int8)
            observed['raw'] = weakref.ref(raw)
            return raw

        runner = backend.PersistentXrtRunner.__new__(backend.PersistentXrtRunner)
        runner.xrt = SimpleNamespace(xclBOSyncDirection=SimpleNamespace(
            XCL_BO_SYNC_BO_FROM_DEVICE=1))
        runner.specs = [((4,), np.dtype(np.uint16))]
        runner.buffers = [SimpleNamespace(sync=lambda direction: None, read=read)]
        result = runner.output_bits(copy=False)
        gc.collect()
        self.assertIsNotNone(observed['raw']())
        np.testing.assert_array_equal(result, np.arange(8, dtype=np.int8).view(np.uint16))
        del result
        gc.collect()
        self.assertIsNone(observed['raw']())

    def test_branch_borrowed_results_survive_overwrite_and_match_owned_control(self):
        from test_swiglu import _SwiGLUOracleRunner, _mock_artifacts
        weights = random_weights(128, 128, seed=145)
        x = np.random.default_rng(146).normal(0, .5, (128, 128)).astype(np.float32)
        with tempfile.TemporaryDirectory() as root:
            _mock_artifacts(root, 128, True)
            for copy in (False, True):
                with self.subTest(copy=copy), patch.object(backend, 'PersistentXrtRunner', _SwiGLUOracleRunner):
                    branch = backend.NPUBranch(weights.gate, weights.up, weights.down,
                        128, root, fuse_swiglu=True, copy_output_bits=copy)
                    self.assertEqual(branch.metadata['host_output_readback'],
                                     'owned_copy' if copy else 'borrowed_until_consumed')
                    result = branch.run(bf16_bits(x))
                    snapshot = result.copy()
                    for runner in branch.runners.values():
                        self.assertFalse(np.shares_memory(result, runner.result))
                        runner.result[:] = 0  # Later dispatch may reuse BO storage.
                    np.testing.assert_array_equal(result, snapshot)
                    np.testing.assert_array_equal(result, bf16_bits(reference_full(x, weights)))
                    repeated = branch.run(bf16_bits(-x))
                    self.assertFalse(np.array_equal(repeated, result))
                    np.testing.assert_array_equal(result, snapshot)

    def test_weights_upload_once_across_complete_ffn_and_alternating_inputs(self):
        for design, columns in (("legacy", 4), ("array8", 8)):
            with self.subTest(design=design):
                self._check_weights_upload_once(design, columns)

    def test_fused_gate_up_preserves_outputs_metadata_and_weight_reuse(self):
        # P384 exercises an odd number of N32 tiles per physical column in
        # the combined graph, as well as the compact two-output host ABI.
        weights = random_weights(128, 384, seed=121)
        x = np.random.default_rng(122).normal(0, 0.5, (128, 128)).astype(np.float32)
        with tempfile.TemporaryDirectory() as root:
            _write_mock_artifacts(root, channels=384, columns=8, design="array8", fuse_gate_up=True)
            with patch.object(backend, "PersistentXrtRunner", _OracleRunner):
                branch = backend.NPUBranch(weights.gate, weights.up, weights.down, 128, root,
                                           fuse_gate_up=True)
                self.assertEqual(branch.metadata["launches_per_run"], 3)
                self.assertEqual(branch.metadata["fixed_weight_uploads"], 2)
                self.assertEqual(branch.metadata["host_bo_io_bytes_per_run_estimate"],
                                 4 * 128 * 128 + 12 * 128 * 384)
                for index, value in enumerate((x, -x, np.zeros_like(x), x)):
                    output = branch.run(bf16_bits(value))
                    # The fake combined [gate|up] NumPy GEMM has a different
                    # output width from the separate reference GEMMs. BLAS
                    # may round FP32 reductions differently across thread
                    # configurations before BF16 rounding. Compare the same
                    # fixed numerical contract used on hardware; exact packed
                    # addresses and uploaded bytes are checked separately.
                    metrics = error_metrics(bf16_from_bits(output), reference_full(value, weights))
                    self.assertTrue(metrics['passed'], metrics)
                    self.assertEqual(branch.gate_up.input_write_counts, [index + 1, 1])
                    self.assertEqual(branch.down.input_write_counts, [index + 1, 1])
                    self.assertEqual(branch.last_diagnostics["completed_dispatches_total"], 3 * (index + 1))
                    self.assertEqual(branch.last_diagnostics["weight_upload_counts"], {"gate_up": 1, "down": 1})
                    self.assertEqual(set(branch.last_diagnostics["dispatch_wait_us"]),
                                     {"gate_up", "silu_mul", "down"})

    def test_fused_artifacts_reject_unsupported_geometry_and_stale_split_layout(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "array8"):
                backend._artifact_specs(128, 128, 256, root, 8, "legacy", True)
            with self.assertRaisesRegex(ValueError, "8192"):
                backend._artifact_specs(128, 128, 8320, root, fuse_gate_up=True)
            spec = _write_mock_artifacts(root, columns=8, design="array8", fuse_gate_up=True)["gate_up"]
            backend._load_artifact(spec)
            path = spec["directory"] / "final.xclbin.json"
            manifest = json.loads(path.read_text())
            manifest["output_order"] = ["up", "gate"]
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "output_order"):
                backend._load_artifact(spec)

    def _check_weights_upload_once(self, design, columns):
        weights = random_weights(128, 256, seed=111)
        x = np.random.default_rng(112).normal(0, 0.5, (128, 128)).astype(np.float32)
        with tempfile.TemporaryDirectory() as root:
            _write_mock_artifacts(root, columns=columns, design=design)
            with patch.object(backend, "PersistentXrtRunner", _OracleRunner):
                branch = backend.NPUBranch(weights.gate, weights.up, weights.down, 128, root,
                                           columns=columns, npu_design=design)
                self.assertEqual(branch.metadata["npu_design"], design)
                weight_snapshots = {name: getattr(branch, name).inputs[1].copy()
                                    for name in ("gate", "up", "down")}
                outputs = []
                for index, value in enumerate((x, -x, np.zeros_like(x), x)):
                    result = branch.run(bf16_bits(value))
                    outputs.append(result.copy())
                    np.testing.assert_array_equal(result, bf16_bits(reference_full(value, weights)))
                    for name in ("gate", "up", "down"):
                        runner = getattr(branch, name)
                        self.assertEqual(runner.input_write_counts, [index + 1, 1])
                        self.assertEqual(runner.completed_dispatches, index + 1)
                        np.testing.assert_array_equal(runner.inputs[1], weight_snapshots[name])
                    self.assertEqual(branch.silu.input_write_counts, [index + 1, index + 1])
                    self.assertEqual(branch.silu.completed_dispatches, index + 1)
                    self.assertEqual(branch.last_diagnostics["completed_dispatches_total"], 4 * (index + 1))
                    self.assertEqual(branch.last_diagnostics["weight_upload_counts"],
                                     {"gate": 1, "up": 1, "down": 1})
                self.assertFalse(np.array_equal(outputs[0], outputs[1]))
                np.testing.assert_array_equal(outputs[0], outputs[3])
                np.testing.assert_array_equal(outputs[2], np.zeros_like(outputs[2]))

    def test_stale_graph_provenance_rejected_despite_valid_binary_hashes(self):
        with tempfile.TemporaryDirectory() as root:
            spec = _write_mock_artifacts(root)["gate_up"]
            backend._load_artifact(spec)  # The complete fixture is initially valid.
            contract = backend._build_contract(spec)
            # Copy through JSON so mutating the fixture does not mutate spec.
            contract = json.loads(json.dumps(contract))
            contract["source_sha256"]["npu/ffn/w4a16_prefill.py"] = "0" * 64
            (spec["directory"] / "build_contract.json").write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValueError, "graph/kernel build provenance"):
                backend._load_artifact(spec)

    def test_array8_requires_and_plans_all_eight_columns(self):
        with tempfile.TemporaryDirectory() as root:
            # P=128 has only four N32 tiles. The legacy design silently uses
            # four columns; array8 must spread row groups to retain all eight.
            array = backend._artifact_specs(128, 4096, 128, root)
            legacy = backend._artifact_specs(128, 4096, 128, root, 8, "legacy")
            self.assertEqual(legacy["gate_up"]["expected"]["cols"], 4)
            for label in ("gate_up", "down"):
                spec = array[label]
                self.assertEqual(spec["stem"], "w4a16_prefill_reuse")
                self.assertEqual(spec["expected"]["design"], "array8")
                self.assertEqual(spec["expected"]["cols"], 8)
                self.assertEqual(spec["expected"]["compute_rows"], 4)
                self.assertEqual(spec["expected"]["worker_count"], 32)
                self.assertEqual(spec["plan"]["worker_count"], 32)
                self.assertIn(spec["expected"]["m_reuse"], (1, 2))
                self.assertEqual(spec["arguments"][-2:], ["--max-reuse", "2"])
                self.assertIn("npu/ffn/prefill_schedule.py", spec["source_sha256"])
                self.assertNotEqual(spec["directory"], legacy[label]["directory"])
            self.assertEqual(array["silu_mul"]["expected"]["num_columns"], 8)
            for columns in (1, 4, 7):
                with self.subTest(columns=columns), self.assertRaisesRegex(ValueError, "exactly eight"):
                    backend._artifact_specs(128, 4096, 128, root, columns)

    def test_stale_array8_schedule_hash_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            spec = _write_mock_artifacts(root, columns=8, design="array8")["gate_up"]
            loaded = backend._load_artifact(spec)
            self.assertEqual(loaded["plan"]["worker_count"], 32)
            contract = json.loads(json.dumps(backend._build_contract(spec)))
            contract["source_sha256"]["npu/ffn/prefill_schedule.py"] = "0" * 64
            (spec["directory"] / "build_contract.json").write_text(json.dumps(contract))
            with self.assertRaisesRegex(ValueError, "graph/kernel build provenance"):
                backend._load_artifact(spec)

            # The graph's emitted manifest must independently agree with
            # current planner source, even when the sidecar itself is valid.
            (spec["directory"] / "build_contract.json").write_text(json.dumps(backend._build_contract(spec)))
            manifest_path = spec["directory"] / "final.xclbin.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["schedule_sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "manifest schedule_sha256"):
                backend._load_artifact(spec)


if __name__ == "__main__":
    unittest.main()
