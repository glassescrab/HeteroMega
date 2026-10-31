"""Opt-in complete FFN timer with a HIP-mapped row-major NPU output.

Input staging is unchanged and remains inside the wall boundary. This class
removes only the final NPU-output CPU copy/H2D copy and CPU output permutation.
It requires hardware-validated HIP registration and XRT/GPU coherency; merely
constructing it is not proof of correct accelerator execution or speedup.
"""

import time

import numpy as np

from .run import TimedFFN
from .shared_gpu import SharedXrtBuffer


class TimedSharedOutputFFN(TimedFFN):
    """Same ready-GPU-input to synchronized-GPU-output boundary as TimedFFN.

    SharedNpuFFN.run_raw completes the NPU and FROM_DEVICE sync before returning.
    Reduction then reads the HIP-mapped BO directly. No subsequent NPU call may
    overwrite that BO until the GPU reduction completes; run() enforces this
    by synchronizing its reduction stream before return. Instances are not
    reentrant. Both the mapping and its BO stay alive through Tensor storage.
    """

    def __init__(self, gpu, npu, m, hidden, device, *, verbose_build=False,
                 shared_gpu_extension=None):
        if npu is None or not getattr(npu, "mapped_output", False):
            raise ValueError("shared GPU output requires SharedNpuFFN(mapped_output=True)")
        if getattr(npu, "down_output_layout", "compact") != "row_major":
            raise ValueError("shared GPU output requires down_output_layout='row_major'")
        if (npu.m, npu.hidden) != (m, hidden) or not callable(getattr(npu, "run_raw", None)):
            raise ValueError("shared NPU output shape/API mismatch")
        # Reuse only the base streams, events and final output allocation. The
        # base NPU staging output is intentionally not allocated.
        super().__init__(gpu, None, m, hidden, device)
        self.npu = npu
        self.m, self.hidden = m, hidden
        self.host_x = self.torch.empty((m, hidden), dtype=self.torch.bfloat16, pin_memory=True)
        self.host_x_bits = self.host_x.view(self.torch.uint16).numpy()
        self.shared_output = SharedXrtBuffer(npu.output_bo, (m, hidden), device=device,
            extension=shared_gpu_extension, verbose_build=verbose_build)
        self.npu_gpu_output = self.shared_output.tensor
        bits = npu.mapped_output_view
        if bits.dtype != np.uint16 or bits.size != m * hidden or not bits.flags.c_contiguous:
            raise ValueError("mapped NPU output must expose contiguous uint16 BF16 bits")
        self.metadata = dict(output=self.shared_output.metadata, shared_gpu_output=True,
            input_staging="unchanged GPU-to-pinned-host copy plus NPU BO upload",
            output_staging="NPU completion/FROM_DEVICE sync then GPU reads mapped row-major BO",
            validation="host_y copies the mapped output only when accessed outside run timing")
        self.torch.cuda.synchronize(device)

    @property
    def host_y(self):
        """Owned CPU BF16 snapshot for the existing out-of-timer validator.

        Taking this snapshot cannot expose the read-only mapped NumPy view as
        a writable Torch alias. Call only after run() has completed.
        """
        bits = np.array(self.npu.mapped_output_view, dtype=np.uint16, copy=True).reshape(self.m, self.hidden)
        return self.torch.from_numpy(bits).view(self.torch.bfloat16)

    def run(self, x, serial=False):
        self.torch.cuda.synchronize(x.device)
        diagnostics = {}
        start = time.perf_counter_ns()
        if self.gpu is not None:
            y_gpu = self.gpu.enqueue(x, self.compute)
            self.gpu_done.record(self.compute)
            if serial:
                self.compute.synchronize()
        before = time.perf_counter_ns()
        with self.torch.cuda.stream(self.transfer):
            self.host_x.copy_(x, non_blocking=True)
        self.transfer.synchronize()
        diagnostics["input_gpu_to_host_us"] = (time.perf_counter_ns() - before) / 1000
        self.npu.run_raw(self.host_x_bits)
        before = time.perf_counter_ns()
        with self.torch.cuda.stream(self.reduce):
            if self.gpu is not None:
                self.reduce.wait_event(self.gpu_done)
                self.torch.add(y_gpu, self.npu_gpu_output, out=self.output)
            else:
                self.output.copy_(self.npu_gpu_output)
        self.reduce.synchronize()
        diagnostics["output_stage_and_boundary_wait_us"] = (time.perf_counter_ns() - before) / 1000
        elapsed_us = (time.perf_counter_ns() - start) / 1000
        diagnostics.update(npu=self.npu.last_diagnostics, shared_gpu_output=True,
                           final_output_h2d_copies=0, final_output_cpu_layout_copies=0)
        return self.output, elapsed_us, diagnostics
