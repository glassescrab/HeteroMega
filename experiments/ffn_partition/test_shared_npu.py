"""Host routing tests only; fake BOs do not establish XRT coherence or FFN math."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from .shared_npu import SharedInputEdge, SharedNpuFFN
from .upstream_npu import UpstreamNpuFFN
from .npu_backend import _unpack_output_bits


class FakeBO:
    def __init__(self, shape, dtype):
        self.values = np.zeros(shape, dtype)
        self.reads, self.syncs, self.maps = 0, [], 0

    def size(self):
        return self.values.nbytes

    def map(self):
        self.maps += 1
        return memoryview(self.values).cast("B")

    def sync(self, direction):
        self.syncs.append(direction)


class FakeRunner:
    def __init__(self, name, specs, events):
        self.name, self.specs, self.events = name, specs, events
        self.buffers = [FakeBO(shape, dtype) for shape, dtype in specs]
        self.input_write_counts = [0] * (len(specs) - 1)
        self.completed_dispatches = 0
        self.instruction_bo, self.instruction_bytes = object(), 4
        self.group, self.failure = 0, False
        self.xrt = SimpleNamespace(ert_cmd_state=SimpleNamespace(ERT_CMD_STATE_COMPLETED=4),
            xclBOSyncDirection=SimpleNamespace(XCL_BO_SYNC_BO_FROM_DEVICE=2))
        self.kernel = self.Kernel(self)

    class Kernel:
        def __init__(self, runner):
            self.runner = runner

        def group_id(self, index):
            return self.runner.group

        def __call__(self, opcode, instruction, length, *buffers):
            runner = self.runner
            assert list(buffers) == runner.buffers
            runner.events.append(runner.name + "_dispatch")
            # A deterministic stand-in that depends on the linked BO, not FFN
            # arithmetic. Direct device writes do not invoke host read/sync.
            buffers[-1].values[:] = buffers[0].values[:len(buffers[-1].values)] + (1 if runner.name == "swiglu" else 2)

            def wait(timeout):
                runner.events.append(runner.name + "_wait")
                return 1 if runner.failure else 4

            return SimpleNamespace(wait=wait)

    def write_input(self, index, values):
        self.events.append(self.name + "_write" + str(index))
        self.buffers[index].values[:] = values
        self.input_write_counts[index] += 1

    def dispatch_wait(self):
        if any(count == 0 for count in self.input_write_counts):
            raise RuntimeError("uninitialized fake input")
        handle = self.kernel(3, self.instruction_bo, self.instruction_bytes, *self.buffers)
        if handle.wait(10000) != 4:
            raise RuntimeError("fake dispatch failed")
        self.completed_dispatches += 1
        return 0.0  # Synthetic placeholder, never a hardware measurement.

    def output_bits(self, *, copy=True):
        bo = self.buffers[-1]
        bo.reads += 1
        bo.sync(2)
        return bo.values.copy() if copy else bo.values


def fake_parent_init(self, m, hidden, channels, **options):
    self.m, self.hidden, self.channels = m, hidden, channels
    self.output_layout = options.get("output_layout", "compact")
    self.swiglu_input_layout = options.get("swiglu_input_layout", "row_major")
    self.down_output_layout = options.get("down_output_layout", "compact")
    self.copy_output_bits = options.get("copy_output_bits", False)
    self.events = []
    self.swiglu = FakeRunner("swiglu", [((m * hidden,), np.uint16), ((8,), np.uint8),
        ((8,), np.uint8), ((m * channels,), np.uint16)], self.events)
    self.down = FakeRunner("down", [((m * channels,), np.uint16), ((8,), np.uint8),
        ((m * hidden,), np.uint16)], self.events)
    self.swiglu.write_input(1, np.arange(8, dtype=np.uint8))
    self.swiglu.write_input(2, np.arange(8, dtype=np.uint8) + 1)
    self.down.write_input(1, np.arange(8, dtype=np.uint8) + 2)
    self.runners = dict(swiglu=self.swiglu, down=self.down)
    self.metadata = dict(weight_repacking=False, arithmetic="bfp16", worker_count=32)


class SharedNpuTests(unittest.TestCase):
    def make(self, **options):
        with patch.object(UpstreamNpuFFN, "__init__", fake_parent_init):
            return SharedNpuFFN(128, 128, 128, **options)

    def test_default_delegates_to_unchanged_control(self):
        branch = self.make()
        marker = object()
        with patch.object(UpstreamNpuFFN, "run", return_value=marker) as run:
            self.assertIs(branch.run("input"), marker)
        run.assert_called_once_with("input")
        self.assertIsNot(branch.swiglu.buffers[-1], branch.down.buffers[0])

    def test_link_requires_explicit_down_a_and_boolean_options(self):
        for options in ({"shared_intermediate": True}, {"shared_intermediate": 1},
                        {"mapped_output": 1}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.make(**options)

    def test_shared_execution_has_no_intermediate_host_io_and_keeps_real_counts(self):
        branch = self.make(shared_intermediate=True, output_layout="down_a")
        self.assertIs(branch.swiglu.buffers[-1], branch.down.buffers[0])
        for value in (1, 9, 0, 1):
            x = np.full((128, 128), value, np.uint16)
            y = branch.run(x)
            np.testing.assert_array_equal(y, value + 3)
        shared = branch.shared_edge.buffer
        self.assertEqual((shared.reads, shared.syncs, shared.maps), (0, [], 0))
        self.assertEqual(branch.down.input_write_counts, [0, 1])
        self.assertEqual(branch.swiglu.input_write_counts, [4, 1, 1])
        self.assertEqual(branch.shared_edge.completed_consumptions, 4)
        self.assertEqual(branch.swiglu.completed_dispatches, 4)
        self.assertEqual(branch.down.completed_dispatches, 4)
        calls = [event for event in branch.events if event.endswith(("dispatch", "wait"))]
        self.assertEqual(calls, ["swiglu_dispatch", "swiglu_wait", "down_dispatch", "down_wait"] * 4)
        self.assertEqual(branch.metadata["intermediate_host_payload_bytes_avoided"], 4 * 128 * 128)
        self.assertEqual(branch.last_diagnostics["down_input_host_write_count"], 0)

    def test_staged_and_shared_outputs_match_under_fake_routing(self):
        staged = self.make(output_layout="down_a")
        shared = self.make(shared_intermediate=True, output_layout="down_a")
        for value in (1, 9, 0, 1):
            x = np.full((128, 128), value, np.uint16)
            np.testing.assert_array_equal(staged.run_packed(x), shared.run_packed(x))
        self.assertEqual(staged.swiglu.buffers[-1].reads, 4)
        self.assertEqual(staged.down.input_write_counts, [4, 1])

    def test_readonly_mapped_output_borrows_while_row_major_output_owns(self):
        branch = self.make(shared_intermediate=True, mapped_output=True, output_layout="down_a")
        x = np.arange(128 * 128, dtype=np.uint16).reshape(128, 128) % 128
        packed = branch.run_packed(x)
        self.assertFalse(packed.flags.writeable)
        self.assertTrue(np.shares_memory(packed, branch.down.buffers[-1].values))
        owned = branch.run(x)
        np.testing.assert_array_equal(owned, _unpack_output_bits(packed, 128, 128))
        saved = owned.copy()
        branch.run_packed(np.zeros_like(x))
        np.testing.assert_array_equal(owned, saved)
        np.testing.assert_array_equal(packed, 3)
        self.assertEqual(branch.down.buffers[-1].reads, 0)
        self.assertEqual(branch.down.buffers[-1].maps, 1)
        self.assertEqual(branch.down.buffers[-1].syncs, [2, 2, 2])

    def test_row_major_projection_forwards_and_skips_permutation(self):
        branch = self.make(shared_intermediate=True, mapped_output=True, output_layout="down_a",
                           down_output_layout="row_major")
        x = np.arange(128 * 128, dtype=np.uint16).reshape(128, 128) % 128
        with patch("experiments.ffn_partition.shared_npu._unpack_output_bits",
                   side_effect=AssertionError("unexpected compact output permutation")):
            raw = branch.run_raw(x)
            owned = branch.run(x)
        self.assertIs(branch.output_bo, branch.down.buffers[-1])
        self.assertIs(raw, branch.mapped_output_view)
        self.assertFalse(raw.flags.writeable)
        np.testing.assert_array_equal(raw.reshape(x.shape), x + 3)
        np.testing.assert_array_equal(owned, x + 3)
        self.assertFalse(np.shares_memory(owned, raw))
        self.assertEqual(branch.last_diagnostics["returned_output_layout"], "row_major")

    def test_readiness_and_mutated_binding_are_rejected(self):
        branch = self.make(shared_intermediate=True, output_layout="down_a")
        with self.assertRaisesRegex(RuntimeError, "completed producer"):
            branch.shared_edge.dispatch_wait()
        branch.swiglu.completed_dispatches = 1
        branch.down.buffers[0] = FakeBO((128 * 128,), np.uint16)
        with self.assertRaisesRegex(RuntimeError, "binding changed"):
            branch.shared_edge.dispatch_wait()

    def test_wrong_group_size_and_preexisting_upload_are_rejected(self):
        for mutation in ("group", "size", "upload", "dtype"):
            branch = self.make(output_layout="down_a")
            if mutation == "group":
                branch.down.group = 9
            elif mutation == "size":
                branch.down.buffers[0] = FakeBO((1,), np.uint16)
            elif mutation == "upload":
                branch.down.input_write_counts[0] = 1
            else:
                branch.down.specs[0] = ((128 * 128,), np.float32)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                SharedInputEdge(branch.swiglu, branch.down)

    def test_different_xclbin_slots_with_same_bank_can_share(self):
        branch = self.make(output_layout="down_a")
        branch.swiglu.group = 0xC0000
        branch.down.group = 0xD0000
        edge = SharedInputEdge(branch.swiglu, branch.down)
        self.assertIs(branch.swiglu.buffers[-1], branch.down.buffers[0])
        self.assertEqual(edge.metadata["source_group_id"], 786432)
        self.assertEqual(edge.metadata["target_group_id"], 851968)
        self.assertEqual(edge.metadata["source_bank_id"], 0)
        self.assertEqual(edge.metadata["target_bank_id"], 0)
        self.assertEqual(edge.metadata["source_xclbin_slot"], 12)
        self.assertEqual(edge.metadata["target_xclbin_slot"], 13)

    def test_failed_producer_or_consumer_never_claims_completion(self):
        for failed in ("swiglu", "down"):
            branch = self.make(shared_intermediate=True, output_layout="down_a")
            getattr(branch, failed).failure = True
            with self.assertRaises(RuntimeError):
                branch.run(np.zeros((128, 128), np.uint16))
            self.assertEqual(branch.down.completed_dispatches, 0)
            self.assertEqual(branch.shared_edge.completed_consumptions, 0)
            self.assertEqual(branch.swiglu.completed_dispatches, 0 if failed == "swiglu" else 1)

    def test_input_validation_precedes_submission(self):
        branch = self.make(shared_intermediate=True, output_layout="down_a")
        for x in (np.zeros((1, 128), np.uint16), np.zeros((128, 128), np.float32),
                  np.full((128, 128), 0x7F80, np.uint16)):
            with self.assertRaises(ValueError):
                branch.run(x)
        self.assertEqual(branch.swiglu.completed_dispatches, 0)


if __name__ == "__main__":
    unittest.main()
