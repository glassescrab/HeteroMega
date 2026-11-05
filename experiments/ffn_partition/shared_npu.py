"""Opt-in shared-BO execution for the unchanged upstream eight-column FFN.

The default delegates to UpstreamNpuFFN's archived host-staged control. The
shared path binds the same device-allocated XRT BO to the SwiGLU output and
down input, with a completed producer launch before the consumer submission.
It requires the exact down_a ABI and matching kernel memory banks. Host tests
establish routing only: cross-context coherence needs a real hardware check.

XRT documents device-scoped BOs as kernel arguments, and pyxrt.bo.map() as a
memoryview. This is the API basis, not a guarantee for every XDNA driver:
https://xilinx.github.io/XRT/2024.2/html/xrt_native_apis.html
https://xilinx.github.io/XRT/2022.1/html/pyxrt.html

Mapped output is a separate opt-in. It retains FROM_DEVICE synchronization but
skips BO.read's host copy. run_raw() also skips CPU output permutation; a GPU
consumer must understand the projection's selected layout and finish before the
next invocation. No GPU import/registration is performed by this module.
"""

import time

import numpy as np

from .upstream_npu import UpstreamNpuFFN
from .npu_backend import _pack_activation_bits, _unpack_output_bits


class SharedInputEdge:
    """One sequential device-produced input; never masquerades as a host write."""

    def __init__(self, producer, consumer):
        source_index = len(producer.buffers) - 1
        source_shape, source_dtype = producer.specs[source_index]
        target_shape, target_dtype = consumer.specs[0]
        if tuple(source_shape) != tuple(target_shape) or np.dtype(source_dtype) != np.dtype(target_dtype):
            raise ValueError("shared intermediate BO geometry or dtype differs")
        if producer.completed_dispatches or consumer.completed_dispatches:
            raise ValueError("shared BOs must be linked before first execution")
        if consumer.input_write_counts[0]:
            raise ValueError("shared input must not have a host upload")
        source_group = int(producer.kernel.group_id(source_index + 3))
        target_group = int(consumer.kernel.group_id(3))
        # group_id includes the context's xclbin slot above the low16 bank.
        # XRT kernel::group_id packs grp.bank and grp.slot; run validation
        # checks grp.bank only. Comparing full IDs incorrectly rejects BOs
        # shared across slots, while ignoring bank mismatches would let XRT
        # silently clone a BO and destroy this device-to-device edge.
        # Source: archived vendor-xrt-kernel.cpp:2144-2170,2542-2567 under
        # docs/runs/2026-10-13-compat/evidence/ (xcl_bo_flags encoding).
        source_bank, target_bank = source_group & 0xFFFF, target_group & 0xFFFF
        if source_bank != target_bank:
            raise ValueError("shared intermediate BO kernel memory banks differ")
        nbytes = int(np.prod(source_shape)) * np.dtype(source_dtype).itemsize
        source = producer.buffers[source_index]
        if int(source.size()) != nbytes or int(consumer.buffers[0].size()) != nbytes:
            raise ValueError("shared intermediate BO allocation size differs")
        # Both unchanged XrtRunner constructors allocate with xrt.device(0),
        # not with hw_context. Keep the identical BO Python object alive in
        # both runners; the consumer's unused original input BO is released.
        consumer.buffers[0] = source
        self.producer, self.consumer, self.buffer = producer, consumer, source
        self.completed_consumptions = 0
        self.metadata = dict(source_index=source_index, target_index=0,
            source_group_id=source_group, target_group_id=target_group,
            source_bank_id=source_bank, target_bank_id=target_bank,
            source_xclbin_slot=(source_group >> 16) & 0xFF,
            target_xclbin_slot=(target_group >> 16) & 0xFF,
            nbytes=nbytes, device_ordinal=0, same_python_bo=True,
            producer_wait_before_consumer=True, host_intermediate_write_count=0,
            host_intermediate_read_count=0, host_intermediate_sync_count=0)

    def dispatch_wait(self):
        producer, consumer = self.producer, self.consumer
        if producer.buffers[-1] is not self.buffer or consumer.buffers[0] is not self.buffer:
            raise RuntimeError("shared intermediate BO binding changed")
        if producer.completed_dispatches != self.completed_consumptions + 1:
            raise RuntimeError("shared input requires exactly one new completed producer")
        if consumer.input_write_counts[0] != 0:
            raise RuntimeError("shared input was unexpectedly overwritten by host")
        if any(count == 0 for count in consumer.input_write_counts[1:]):
            raise RuntimeError("consumer weight inputs must be initialized")
        start = time.perf_counter_ns()
        handle = consumer.kernel(3, consumer.instruction_bo, consumer.instruction_bytes,
                                 *consumer.buffers)
        state = handle.wait(10000)
        elapsed_us = (time.perf_counter_ns() - start) / 1000.0
        if state != consumer.xrt.ert_cmd_state.ERT_CMD_STATE_COMPLETED:
            raise RuntimeError(f"shared-input NPU execution failed or timed out: {state}")
        consumer.completed_dispatches += 1
        self.completed_consumptions += 1
        return elapsed_us


class SharedNpuFFN(UpstreamNpuFFN):
    """Same artifacts/weights/math; optional shared Z and mapped packed output.

    Non-reentrant. Any borrowed packed view is invalidated by the next run and
    requires this object to stay alive until its CPU/GPU consumer completes.
    run() still returns an owned row-major output, preserving the parent ABI.
    """

    def __init__(self, *args, shared_intermediate=False, mapped_output=False, **kwargs):
        if type(shared_intermediate) is not bool or type(mapped_output) is not bool:
            raise ValueError("shared_intermediate and mapped_output must be bool")
        if shared_intermediate and kwargs.get("output_layout", "compact") != "down_a":
            raise ValueError("shared intermediate requires output_layout='down_a'")
        super().__init__(*args, **kwargs)
        self.shared_intermediate = shared_intermediate
        self.mapped_output = mapped_output
        self.shared_edge = SharedInputEdge(self.swiglu, self.down) if shared_intermediate else None
        self._output_mapping = self._mapped_output_bits = None
        self.mapped_output_sync_count = 0
        if mapped_output:
            self._output_mapping = self.down.buffers[-1].map()
            view = memoryview(self._output_mapping)
            shape, dtype = self.down.specs[-1]
            dtype = np.dtype(dtype)
            nbytes = int(np.prod(shape)) * dtype.itemsize
            if not view.c_contiguous or view.nbytes != nbytes:
                raise RuntimeError("XRT output map must expose the exact contiguous byte extent")
            self._mapped_output_bits = np.frombuffer(view, dtype=dtype).reshape(shape)
            self._mapped_output_bits.flags.writeable = False
        self.metadata = dict(self.metadata, shared_intermediate=shared_intermediate,
            shared_intermediate_contract=self.shared_edge.metadata if self.shared_edge else None,
            mapped_output=mapped_output,
            mapped_output_lifetime="borrowed until next run; keep adapter alive through GPU consumption",
            gpu_zero_copy=False,
            intermediate_host_payload_bytes_avoided=(4 * self.m * self.channels if shared_intermediate else 0),
            hardware_validation="requires changed/zero/repeat and exact comparison to staged control on the target XRT driver")

    def _read_final(self):
        if not self.mapped_output:
            return self.down.output_bits(copy=self.copy_output_bits)
        self.down.buffers[-1].sync(self.down.xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_FROM_DEVICE)
        self.mapped_output_sync_count += 1
        return self._mapped_output_bits

    @property
    def output_bo(self):
        """Retained BO for explicit GPU mapping; no synchronization is implied."""
        return self.down.buffers[-1]

    @property
    def mapped_output_view(self):
        """Read-only raw view for registration; consume only after run_raw()."""
        if not self.mapped_output:
            raise RuntimeError("mapped_output=True is required")
        return self._mapped_output_bits

    def run(self, x_bits):
        if not self.shared_intermediate and not self.mapped_output:
            return super().run(x_bits)
        return self._run(x_bits, packed_output=False)

    def run_raw(self, x_bits):
        """Return raw BF16 bits in down_output_layout, without CPU permutation."""
        return self._run(x_bits, packed_output=True)

    def run_packed(self, x_bits):
        """Compatibility alias for run_raw; inspect down_output_layout first."""
        return self.run_raw(x_bits)

    def _run(self, x_bits, *, packed_output):
        x_bits = np.asarray(x_bits)
        if x_bits.dtype != np.uint16 or x_bits.shape != (self.m, self.hidden):
            raise ValueError(f"input must be uint16 BF16 bits with shape {(self.m, self.hidden)}")
        if np.any((x_bits & 0x7F80) == 0x7F80):
            raise ValueError("NPU branch input must contain finite BF16 values")
        start = time.perf_counter_ns()
        stages, waits = {}, {}
        before = time.perf_counter_ns()
        activation = (np.ascontiguousarray(x_bits).reshape(-1)
                      if self.swiglu_input_layout == "row_major" else _pack_activation_bits(x_bits))
        stages["input_layout_us"] = (time.perf_counter_ns() - before) / 1000.0
        before = time.perf_counter_ns()
        self.swiglu.write_input(0, activation)
        waits["swiglu"] = self.swiglu.dispatch_wait()
        z = None if self.shared_intermediate else self.swiglu.output_bits(copy=self.copy_output_bits)
        stages["swiglu_with_host_io_us"] = (time.perf_counter_ns() - before) / 1000.0
        before = time.perf_counter_ns()
        if not self.shared_intermediate:
            from .contract import packed_output_to_activation
            down_a = z if self.output_layout == "down_a" else packed_output_to_activation(z, self.m, self.channels)
        stages["down_input_layout_us"] = (time.perf_counter_ns() - before) / 1000.0
        before = time.perf_counter_ns()
        if self.shared_intermediate:
            waits["down"] = self.shared_edge.dispatch_wait()
        else:
            self.down.write_input(0, down_a)
            waits["down"] = self.down.dispatch_wait()
        y = self._read_final()
        stages["down_with_host_io_us"] = (time.perf_counter_ns() - before) / 1000.0
        before = time.perf_counter_ns()
        down_layout = getattr(self, "down_output_layout", "compact")
        output = (y if packed_output else y.reshape(self.m, self.hidden).copy()
                  if down_layout == "row_major" else _unpack_output_bits(y, self.m, self.hidden))
        stages["output_layout_us"] = (time.perf_counter_ns() - before) / 1000.0
        self.last_diagnostics = dict(branch_host_wall_us=(time.perf_counter_ns() - start) / 1000.0,
            stages=stages, dispatch_wait_us=waits,
            completed_dispatches_total=sum(r.completed_dispatches for r in self.runners.values()),
            weight_upload_counts={"gate": self.swiglu.input_write_counts[1],
                                  "up": self.swiglu.input_write_counts[2], "down": self.down.input_write_counts[1]},
            shared_intermediate=self.shared_intermediate,
            shared_input_completed_consumptions=(self.shared_edge.completed_consumptions if self.shared_edge else 0),
            down_input_host_write_count=self.down.input_write_counts[0],
            mapped_output=self.mapped_output, mapped_output_sync_count=self.mapped_output_sync_count,
            returned_output_layout=down_layout if packed_output else "row_major")
        return output
