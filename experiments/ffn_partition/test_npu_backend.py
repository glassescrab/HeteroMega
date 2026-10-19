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
from contract import random_weights, reference_full
from prefill_reference import (bf16_bits, bf16_from_bits, pack_output,
                               projection_reference, unpack_activations,
                               unpack_weights)
from reference import silu_multiply


def _write_mock_artifacts(root, m=128, hidden=128, channels=256,
                          columns=4, design="legacy", fuse_gate_up=False):
    """Valid manifests with unmistakably fake binaries, never sent to XRT."""
    specs = backend._artifact_specs(m, hidden, channels, root, columns, design, fuse_gate_up)
    for spec in specs.values():
        directory = spec["directory"]
        directory.mkdir(parents=True, exist_ok=True)
        xclbin = b"CPU TEST MOCK -- NOT AN NPU BINARY"
        instructions = b"MOCK"
        (directory / "final.xclbin").write_bytes(xclbin)
        (directory / "insts.bin").write_bytes(instructions)
        manifest = dict(
            spec["expected"], target_mlir_aie_commit=backend.TARGET_COMMIT,
            source_sha256=spec["source_sha256"][f"npu/ffn/{backend._kernel_source(spec['stem'])}.cc"],
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

    def output_bits(self, index=0):
        return (self.result[index] if self.output_count == 2 else self.result).copy()


class NPUBackendTests(unittest.TestCase):
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
            with self.subTest(case=name), self.assertRaisesRegex(RuntimeError, "NumPy 1.26.4"):
                runner.output_bits()
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
                    np.testing.assert_array_equal(output, bf16_bits(reference_full(value, weights)))
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
