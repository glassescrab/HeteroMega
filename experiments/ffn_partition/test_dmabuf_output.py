"""Fail-closed/routing tests. These mocks do not establish DMA-BUF coherence."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from .dmabuf_output import GpuDmaBufOutput, DmaBufOutputNpuFFN
from .test_shared_npu import FakeBO, fake_parent_init
from .upstream_npu import UpstreamNpuFFN


class FakeAllocation:
    def __init__(self, size, device):
        self.size, self.device, self.closed = size, device, False
        self.output = object()

    def metadata(self):
        return dict(nbytes=self.size, backing_nbytes=self.size, export_offset=0, export_fd_closed=self.closed)

    def fd(self):
        if self.closed:
            raise RuntimeError("closed")
        return 77

    def tensor(self, shape):
        self.shape = shape
        return self.output

    def close_export(self):
        self.closed = True


class FakeBridge:
    def __init__(self):
        self.shared = True
        self.bank = 0
        self.bo_type = FakeBO
        self.imports = []
        self.size_delta = 0
        self.sub_buffers = []

    def registry(self):
        return dict(registered_types_shared=self.shared)

    def import_fd(self, device, fd, size, group, owner):
        self.imports.append((device, fd, size, group, owner))
        bo = self.bo_type(((size + self.size_delta) // 2,), np.uint16)
        bo.owner = owner
        return bo

    def describe(self, bo):
        return dict(nbytes=bo.size(), bank_id=self.bank, address=4096, flags=0)

    def sub_buffer(self, parent, size, offset, owner):
        self.sub_buffers.append((parent, size, offset, owner))
        if offset != 0 or size > parent.size():
            raise ValueError("invalid sub-buffer")
        result = FakeBO((size // 2,), np.uint16)
        result.owner = owner
        result.values = parent.values[:size // 2]
        return result


def runner():
    bo = FakeBO((4096,), np.uint16)
    return SimpleNamespace(specs=[((4096,), np.uint16)] * 3, buffers=[bo, bo, bo],
        completed_dispatches=0, device=object(), kernel=SimpleNamespace(group_id=lambda index: 0x10000),
        xrt=SimpleNamespace(bo=FakeBO, xclBOSyncDirection=SimpleNamespace(XCL_BO_SYNC_BO_FROM_DEVICE=2)))


class DmaBufOutputTests(unittest.TestCase):
    def setUp(self):
        self.runner, self.bridge = runner(), FakeBridge()
        self.extensions = self.bridge, SimpleNamespace(HipAllocation=FakeAllocation), SimpleNamespace(index=0), {}

    def create(self):
        return GpuDmaBufOutput(self.runner, (64, 64), extensions=self.extensions)

    def test_bind_exact_output_only_after_checks_and_close_fd(self):
        inputs = self.runner.buffers[:2]
        old_output = self.runner.buffers[-1]
        result = self.create()
        self.assertEqual(self.runner.buffers[:2], inputs)
        self.assertIsNot(self.runner.buffers[-1], old_output)
        self.assertIs(self.runner.buffers[-1], result.bo)
        self.assertIs(result.bo.owner, result.allocation)
        self.assertTrue(result.allocation.closed)
        self.assertEqual(self.bridge.imports[0][1:4], (77, 8192, 0x10000))
        self.assertEqual(result.metadata["output_argument"], 5)
        self.assertIs(result.sync_from_npu(), result.tensor)
        self.assertEqual(result.bo.syncs, [2])
        self.assertEqual(result.bo.reads, 0)

    def test_rejects_binding_replacement(self):
        result = self.create()
        self.runner.buffers[-1] = FakeBO((4096,), np.uint16)
        with self.assertRaisesRegex(RuntimeError, "binding changed"):
            result.sync_from_npu()

    def test_larger_backing_is_explicit_bounded_zero_offset_subbuffer(self):
        class PooledAllocation(FakeAllocation):
            def metadata(self):
                return dict(super().metadata(), backing_nbytes=self.size * 4)
        self.extensions = self.bridge, SimpleNamespace(HipAllocation=PooledAllocation), SimpleNamespace(index=0), {}
        result = self.create()
        self.assertEqual(self.bridge.imports[0][2], 32768)
        self.assertEqual(self.bridge.sub_buffers[0][1:3], (8192, 0))
        self.assertIs(result.bo.owner, result.allocation)
        self.assertIs(result.parent_bo.owner, result.allocation)
        self.assertEqual(result.parent_bo.size(), 32768)
        self.assertEqual(result.bo.size(), 8192)
        self.assertTrue(result.metadata["sub_buffer_used"])
        self.assertEqual(result.metadata["sub_buffer_offset"], 0)
        result.parent_bo.values[4096:] = 99
        result.bo.values[:] = 7
        np.testing.assert_array_equal(result.parent_bo.values[4096:], 99)
        self.assertIs(result.sync_from_npu(), result.tensor)
        self.assertEqual(result.bo.syncs, [2])
        self.assertEqual(result.parent_bo.syncs, [])

    def test_registry_mismatch_cannot_allocate_or_bind(self):
        original = self.runner.buffers[-1]
        self.bridge.shared = False
        with self.assertRaisesRegex(RuntimeError, "registered types"):
            self.create()
        self.assertEqual(self.bridge.imports, [])
        self.assertIs(self.runner.buffers[-1], original)

    def test_mismatched_bank_size_and_type_never_replace_output(self):
        for failure in ("bank", "size", "type"):
            with self.subTest(failure=failure):
                self.setUp()
                original = self.runner.buffers[-1]
                if failure == "bank":
                    self.bridge.bank = 1
                elif failure == "size":
                    self.bridge.size_delta = 4096
                else:
                    self.runner.xrt.bo = type("ForeignBO", (), {})
                with self.assertRaises(RuntimeError):
                    self.create()
                self.assertIs(self.runner.buffers[-1], original)
                self.assertFalse(self.bridge.imports[0][-1].closed)

    def test_rejects_nonzero_export_offset_before_import(self):
        original = self.runner.buffers[-1]
        class OffsetAllocation(FakeAllocation):
            def metadata(self):
                return dict(nbytes=self.size, export_offset=4096)
        self.extensions = self.bridge, SimpleNamespace(HipAllocation=OffsetAllocation), SimpleNamespace(index=0), {}
        with self.assertRaisesRegex(RuntimeError, "offset/extent"):
            self.create()
        self.assertIs(self.runner.buffers[-1], original)
        self.assertEqual(self.bridge.imports, [])

    def test_rejects_post_dispatch_and_nonpage_shapes(self):
        self.runner.completed_dispatches = 1
        with self.assertRaisesRegex(ValueError, "before first dispatch"):
            self.create()
        self.runner.completed_dispatches = 0
        self.runner.specs[-1] = ((4032,), np.uint16)
        with self.assertRaisesRegex(ValueError, "page sized"):
            GpuDmaBufOutput(self.runner, (64, 63), extensions=self.extensions)

    def test_parent_rejects_mapping_or_compact_before_initialization(self):
        for options in ({}, {"down_output_layout": "row_major", "mapped_output": True}):
            with self.subTest(options=options), patch.object(UpstreamNpuFFN, "__init__") as parent:
                with self.assertRaises(ValueError):
                    DmaBufOutputNpuFFN(**options)
                parent.assert_not_called()

    def test_parent_raw_path_has_zero_bo_reads_and_owned_gpu_output(self):
        # The fake output is an opaque marker: a NumPy conversion/reshape/copy
        # on the raw path would fail. Kernel fake writes still target its BO.
        def initialize(self, *args, **kwargs):
            fake_parent_init(self, *args, **kwargs)
            self.down.device = object()
            self.down.xrt.bo = FakeBO
        with patch.object(UpstreamNpuFFN, "__init__", initialize):
            branch = DmaBufOutputNpuFFN(128, 128, 128,
                shared_intermediate=True, output_layout="down_a", down_output_layout="row_major",
                dmabuf_extensions=self.extensions)
        y = branch.run_raw(np.ones((128, 128), np.uint16))
        self.assertIs(y, branch.gpu_output.tensor)
        self.assertEqual(branch.down.completed_dispatches, 1)
        self.assertEqual(branch.swiglu.completed_dispatches, 1)
        self.assertEqual(branch.down.buffers[-1].reads, 0)
        self.assertEqual(branch.down.buffers[-1].syncs, [2])
        self.assertEqual(branch.gpu_output_sync_count, 1)
        self.assertFalse(branch.mapped_output)
        self.assertEqual(branch.down.input_write_counts, [0, 1])
        self.assertEqual(branch.last_diagnostics["final_output_h2d_copies"], 0)


if __name__ == "__main__":
    unittest.main()
