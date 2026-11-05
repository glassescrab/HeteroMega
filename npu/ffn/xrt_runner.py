"""Small persistent-buffer XRT harness for MLIR-AIE 7e00b579 designs.

Instruction length is in bytes, following that revision's XRTHostRuntime.
This is an isolated bring-up harness, not HeteroMosaic's DRM host runtime.
"""

from pathlib import Path
import hashlib
import json
import time

import numpy as np


def load_manifest(xclbin, insts, kind):
    """Reject mismatched binaries before allocating buffers or dispatching DMA."""
    manifest = json.loads(Path(str(xclbin) + ".json").read_text())
    if manifest.get("kind") != kind:
        raise ValueError(f"expected {kind} artifact manifest")
    for path, key in ((xclbin, "xclbin_sha256"), (insts, "insts_sha256")):
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != manifest[key]:
            raise ValueError(f"artifact hash mismatch: {path}; rebuild the design")
    return manifest


class XrtRunner:
    """Last buffer is output; earlier buffers are inputs in runtime-sequence order."""

    def __init__(self, xclbin, insts, shapes_and_dtypes, kernel_name="MLIR_AIE"):
        import pyxrt as xrt

        self.xrt = xrt
        self.device = xrt.device(0)
        self.xclbin = xrt.xclbin(str(xclbin))
        names = [k.get_name() for k in self.xclbin.get_kernels()]
        if kernel_name not in names:
            raise ValueError(f"kernel {kernel_name!r} not found; available: {names}")
        self.device.register_xclbin(self.xclbin)
        self.context = xrt.hw_context(self.device, self.xclbin.get_uuid())
        self.kernel = xrt.kernel(self.context, kernel_name)
        instructions = np.frombuffer(Path(insts).read_bytes(), dtype=np.uint8)
        if not instructions.size or instructions.size % 4:
            raise ValueError("instruction binary must contain whole 32-bit words")
        self.instruction_bytes = instructions.size
        self.instruction_bo = xrt.bo(
            self.device, instructions.size, xrt.bo.cacheable, self.kernel.group_id(1)
        )
        self.instruction_bo.write(instructions, 0)
        self.instruction_bo.sync(xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE)
        self.specs = [(tuple(shape), np.dtype(dtype)) for shape, dtype in shapes_and_dtypes]
        self.buffers = []
        for i, (shape, dtype) in enumerate(self.specs):
            nbytes = int(np.prod(shape)) * dtype.itemsize
            if nbytes <= 0:
                raise ValueError("empty device buffers are unsupported")
            self.buffers.append(xrt.bo(
                self.device, nbytes, xrt.bo.host_only, self.kernel.group_id(i + 3)
            ))

    def run(self, inputs):
        if len(inputs) != len(self.buffers) - 1:
            raise ValueError("input count does not match compiled design")
        for data, bo, (shape, dtype) in zip(inputs, self.buffers, self.specs):
            array = np.asarray(data)
            if array.shape != shape or array.dtype != dtype:
                raise ValueError(f"expected {shape} {dtype}; got {array.shape} {array.dtype}")
            bo.write(np.ascontiguousarray(array).view(np.uint8).reshape(-1), 0)
            bo.sync(self.xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE)
        start = time.perf_counter_ns()
        handle = self.kernel(3, self.instruction_bo, self.instruction_bytes, *self.buffers)
        state = handle.wait(10000)
        launch_us = (time.perf_counter_ns() - start) / 1000.0
        if state != self.xrt.ert_cmd_state.ERT_CMD_STATE_COMPLETED:
            raise RuntimeError(f"NPU execution failed or timed out: {state}")
        self.buffers[-1].sync(self.xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_FROM_DEVICE)
        shape, dtype = self.specs[-1]
        nbytes = int(np.prod(shape)) * dtype.itemsize
        result = np.asarray(self.buffers[-1].read(nbytes, 0)).view(dtype).reshape(shape).copy()
        return result, launch_us
