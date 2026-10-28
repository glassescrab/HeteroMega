"""Opt-in GPU-owned DMA-BUF input imported into XRT; no host activation staging.

The SwiGLU input BO is replaced by an imported HIP allocation before the first
dispatch. Each call copies the ready GPU input into that allocation, waits for
the GPU copy, and launches the unchanged NPU graph. The allocation is retained
by both the Torch tensor and the imported pyxrt BO. Construction proves neither
NPU visibility nor acceleration; the hardware comparison must validate both.
"""

import time
from pathlib import Path

import numpy as np

from .dmabuf_output import DmaBufOutputNpuFFN, load_dmabuf_extensions
from .run import TimedFFN


def _validate_export(exported, nbytes):
    offset = exported.get("export_offset")
    backing = exported.get("backing_nbytes")
    if (type(offset) is not int or offset < 0 or offset % 4096 or
            exported.get("nbytes") != nbytes or type(backing) is not int or
            backing < nbytes or offset + nbytes > backing or backing % 4096):
        raise RuntimeError(f"HIP export offset/extent failed independent validation: {exported}")


class GpuDmaBufInput:
    """Bind one retained HIP allocation to the SwiGLU input argument.

    Both the returned Torch tensor and the imported pyxrt BO retain the
    allocation. The caller must finish the GPU copy before NPU dispatch and
    must complete the NPU before overwriting the input on the next call.
    """

    def __init__(self, runner, shape, *, device="cuda", extensions=None, verbose_build=False):
        shape = tuple(shape)
        if len(shape) != 2 or any(type(value) is not int or value <= 0 for value in shape):
            raise ValueError("DMA-BUF input requires a positive two-dimensional shape")
        spec_shape, spec_dtype = runner.specs[0]
        nbytes = int(np.prod(shape)) * 2
        if np.dtype(spec_dtype) != np.dtype(np.uint16) or int(np.prod(spec_shape)) != int(np.prod(shape)):
            raise ValueError("DMA-BUF input geometry/dtype differs from the compiled input")
        if nbytes % 4096 or runner.completed_dispatches:
            raise ValueError("DMA-BUF input must be page sized and bound before first dispatch")
        if int(runner.buffers[0].size()) != nbytes:
            raise ValueError("original input BO extent differs from compiled geometry")
        bridge, hip, selected, build = extensions or load_dmabuf_extensions(device, verbose_build)
        registry = dict(bridge.registry())
        if not registry.get("registered_types_shared"):
            raise RuntimeError("XRT bridge does not share pyxrt's registered types")
        group = int(runner.kernel.group_id(3))
        allocation = hip.HipAllocation(nbytes, selected.index)
        exported = dict(allocation.metadata())
        _validate_export(exported, nbytes)
        backing_nbytes = exported["backing_nbytes"]
        export_offset = exported["export_offset"]
        parent_bo = bridge.import_fd(runner.device, allocation.fd(), backing_nbytes, group, allocation)
        if not isinstance(parent_bo, runner.xrt.bo):
            raise RuntimeError("bridge did not return a genuine pyxrt.bo")
        parent_description = dict(bridge.describe(parent_bo))
        if int(parent_bo.size()) != backing_nbytes or parent_description.get("nbytes") != backing_nbytes:
            raise RuntimeError("imported input backing BO extent failed independent validation")
        sub_buffer = backing_nbytes != nbytes or export_offset != 0
        bo = bridge.sub_buffer(parent_bo, nbytes, export_offset, allocation) if sub_buffer else parent_bo
        if not isinstance(bo, runner.xrt.bo):
            raise RuntimeError("bridge did not return a genuine pyxrt.bo sub-buffer")
        description = dict(bridge.describe(bo))
        if int(bo.size()) != nbytes or description.get("nbytes") != nbytes:
            raise RuntimeError("imported input BO extent failed independent validation")
        if description.get("bank_id") != (group & 0xffff):
            raise RuntimeError("imported input BO bank differs from the input kernel bank")
        if any(description.get(key) != parent_description.get(key) for key in
               ("group_id", "bank_id", "flags")):
            raise RuntimeError("logical input sub-buffer differs from imported backing group/flags")
        tensor = allocation.tensor(shape)
        allocation.close_export()
        self.allocation, self.bo, self.tensor, self.runner = allocation, bo, tensor, runner
        self.parent_bo = parent_bo
        from hashlib import sha256
        self.metadata = dict(build=build, registry=registry, allocation=dict(allocation.metadata()),
            source_sha256={str(path.relative_to(Path(__file__).resolve().parents[2])):
                           sha256(path.read_bytes()).hexdigest()
                           for path in (Path(__file__), Path(__file__).with_name("dmabuf_output.py"))},
            imported_bo=description, shape=list(shape), dtype="BF16", input_argument=3,
            imported_backing_bo=parent_description,
            import_extent_policy="page_offset_logical_subbuffer" if sub_buffer else "whole_backing",
            sub_buffer_used=sub_buffer, sub_buffer_offset=export_offset,
            python_buffer_type="pyxrt.bo", kernel_group_id=group, kernel_bank_id=group & 0xffff,
            import_api="xrt::bo(device, exported DMA-BUF FD)", fd_closed_after_import=True,
            direction="gpu_write_to_npu_read", copy_fallback=False,
            host_input_staging="none", hardware_coherency_validated=False)
        runner.buffers[0] = bo
        runner.device_owned_inputs = set(getattr(runner, "device_owned_inputs", set())) | {0}

    def fill_from(self, tensor):
        if self.runner.buffers[0] is not self.bo:
            raise RuntimeError("imported GPU input BO binding changed")
        self.tensor.copy_(tensor, non_blocking=False)
        return self.tensor


class DmaBufInputNpuFFN(DmaBufOutputNpuFFN):
    """Same down/shared path as output-only DMA-BUF, with a GPU-owned input BO."""

    def __init__(self, *args, gpu_device="cuda", dmabuf_extensions=None,
                 verbose_build=False, **kwargs):
        super().__init__(*args, gpu_device=gpu_device, dmabuf_extensions=dmabuf_extensions,
                         verbose_build=verbose_build, **kwargs)
        self.gpu_input = GpuDmaBufInput(self.swiglu, (self.m, self.hidden),
            device=gpu_device, extensions=dmabuf_extensions, verbose_build=verbose_build)
        self.gpu_input_dmabuf = True
        self.gpu_input_sync_count = 0
        self.metadata = dict(self.metadata, gpu_input_dmabuf=True,
            gpu_input_dmabuf_contract=self.gpu_input.metadata,
            host_input_staging="gpu_owned_dmabuf")

    def sync_gpu_input(self):
        self.gpu_input_sync_count += 1
        self.swiglu.buffers[0].sync(self.swiglu.xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE)
        return self.gpu_input.tensor

    def _read_final(self):
        return super()._read_final()

    def run_npu_only(self):
        """Run both NPU stages using the already-populated GPU-owned input."""
        start = time.perf_counter_ns()
        stages, waits = {}, {}
        before = time.perf_counter_ns()
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
        output = (y if not self.shared_intermediate else y)
        stages["output_layout_us"] = (time.perf_counter_ns() - before) / 1000.0
        self.last_diagnostics = dict(
            branch_host_wall_us=(time.perf_counter_ns() - start) / 1000.0,
            stages=stages, dispatch_wait_us=waits,
            completed_dispatches_total=sum(r.completed_dispatches for r in self.runners.values()),
            weight_upload_counts={"gate": self.swiglu.input_write_counts[1],
                                  "up": self.swiglu.input_write_counts[2],
                                  "down": self.down.input_write_counts[1]},
            shared_intermediate=self.shared_intermediate,
            shared_input_completed_consumptions=(self.shared_edge.completed_consumptions if self.shared_edge else 0),
            down_input_host_write_count=self.down.input_write_counts[0],
            gpu_input_dmabuf=True, gpu_input_sync_count=self.gpu_input_sync_count,
            host_input_write_count=self.swiglu.input_write_counts[0],
            final_output_h2d_copies=0, final_output_bo_reads=0,
            returned_output_layout=self.down_output_layout)
        return output

    def run_raw(self, x_bits=None):
        if x_bits is not None:
            raise ValueError("GPU DMA-BUF input adapter accepts only an already-populated input BO")
        result = self.run_npu_only()
        self.last_diagnostics.update(gpu_output_dmabuf=True,
            gpu_output_sync_count=self.gpu_output_sync_count)
        return result

    def host_snapshot(self):
        return self.gpu_output.tensor.detach().cpu()

    def run(self, x_bits=None):
        if x_bits is not None:
            import torch
            self.gpu_input.tensor.copy_(x_bits)
            torch.cuda.synchronize(self.gpu_input.tensor.device)
            self.sync_gpu_input()
        self.run_npu_only()
        import torch
        return self.host_snapshot().view(torch.uint16).numpy().copy()


class TimedDmaBufInputFFN(TimedFFN):
    """Ready GPU input to synchronized GPU reduction with no host input staging."""

    def __init__(self, gpu, npu, m, hidden, device):
        if not isinstance(npu, DmaBufInputNpuFFN) or (npu.m, npu.hidden) != (m, hidden):
            raise ValueError("DMA-BUF input timer requires the matching NPU adapter")
        super().__init__(gpu, None, m, hidden, device)
        self.npu = npu
        self.npu_gpu_output = npu.gpu_output.tensor
        self.metadata = dict(gpu_input_dmabuf=True, gpu_output_dmabuf=True,
            input=npu.gpu_input.metadata, output=npu.gpu_output.metadata,
            input_staging="GPU-to-GPU copy into imported HIP input BO; no host copy or write",
            output_staging="completed NPU/FROM_DEVICE sync then direct GPU reduction")
        self.torch.cuda.synchronize(device)

    @property
    def host_y(self):
        return self.npu.host_snapshot()

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
            self.npu.gpu_input.tensor.copy_(x, non_blocking=True)
        self.transfer.synchronize()
        self.npu.sync_gpu_input()
        diagnostics["input_gpu_to_gpu_us"] = (time.perf_counter_ns() - before) / 1000
        self.npu.run_npu_only()
        before = time.perf_counter_ns()
        with self.torch.cuda.stream(self.reduce):
            if self.gpu is not None:
                self.reduce.wait_event(self.gpu_done)
                self.torch.add(y_gpu, self.npu_gpu_output, out=self.output)
            else:
                self.output.copy_(self.npu_gpu_output)
        self.reduce.synchronize()
        diagnostics["output_stage_and_boundary_wait_us"] = (time.perf_counter_ns() - before) / 1000
        elapsed = (time.perf_counter_ns() - start) / 1000
        diagnostics.update(npu=self.npu.last_diagnostics, gpu_input_dmabuf=True,
                           gpu_output_dmabuf=True, final_output_h2d_copies=0,
                           final_output_cpu_layout_copies=0, input_gpu_to_gpu_copies=1,
                           host_input_copies=0)
        return self.output, elapsed, diagnostics
