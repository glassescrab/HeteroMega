"""Opt-in HIP-owned output imported into XRT; no implicit copy fallback.

API basis: xrt::bo(device, export_handle) and ROCr's
hsa_amd_portable_export_dmabuf, also used by native HeteroMosaic. A matching
pybind registry is required to return a genuine pyxrt.bo to the existing runner.
Successful construction proves neither NPU/GPU coherence nor acceleration.
Validate changed/zero/repeated inputs against the staged candidate first.
"""

from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sysconfig
import time

import numpy as np

from .shared_npu import SharedNpuFFN
from .run import TimedFFN


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def _hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _load_xrt_bridge(verbose=False):
    """Use standalone GCC/pybind2, never Torch's incompatible pybind flags."""
    import pyxrt

    xrt_root = Path(os.environ.get("XILINX_XRT", "/opt/xilinx/xrt")).resolve()
    sdk = xrt_root / "include"
    library = xrt_root / "lib/libxrt_coreutil.so"
    for path in (sdk / "xrt/xrt_bo.h", sdk / "xrt/xrt_device.h", library):
        if not path.is_file():
            raise RuntimeError(f"missing installed XRT dependency: {path}")
    selected = os.environ.get("HETEROMEGA_XRT_PYBIND_INCLUDE")
    if selected:
        pybind_include = Path(selected).resolve()
    else:
        import pybind11
        pybind_include = Path(pybind11.get_include()).resolve()
    common = pybind_include / "pybind11/detail/common.h"
    header = common.read_text()
    version = tuple(int(re.search(r"#define PYBIND11_VERSION_" + key + r"\s+(\d+)", header)[1])
                    for key in ("MAJOR", "MINOR", "PATCH"))
    if version[0] != 2 or version[1] < 12:
        raise RuntimeError("XRT bridge requires pybind11 2.12+ in the 2.x series; use an isolated 2.13.6 include tree")
    binary_ids = set(re.findall(rb"__pybind11_internals_v\d+_gcc_libstdcpp_cxxabi\d+__",
                                Path(pyxrt.__file__).read_bytes()))
    if len(binary_ids) != 1:
        raise RuntimeError("could not identify exactly one installed pyxrt GCC/libstdc++ registry")
    expected_id = next(iter(binary_ids)).decode()
    compiler = shlex.split(os.environ.get("HETEROMEGA_XRT_CXX", "g++"))
    macros = subprocess.run(compiler + ["-dM", "-E", "-x", "c++", "-"], input="", text=True,
                            check=True, capture_output=True).stdout
    abi = int(re.search(r"#define __GXX_ABI_VERSION (\d+)", macros)[1])
    expected_from_compiler = f"__pybind11_internals_v5_gcc_libstdcpp_cxxabi{abi}__"
    if expected_id != expected_from_compiler:
        raise RuntimeError(f"compiler/pyxrt ABI mismatch: {expected_from_compiler} != {expected_id}; select matching GCC")
    source = HERE / "xrt_dmabuf_bindings.cpp"
    metadata = dict(pyxrt_file=str(Path(pyxrt.__file__).resolve()), pyxrt_sha256=_hash(pyxrt.__file__),
        xrt_library=str(library.resolve()), xrt_library_sha256=_hash(library),
        xrt_header_sha256={str(path.relative_to(sdk)): _hash(path) for path in
                          (sdk / "xrt/xrt_bo.h", sdk / "xrt/xrt_device.h")},
        pybind_version=list(version), pybind_include=str(pybind_include),
        pybind_header_sha256={str(p.relative_to(pybind_include)): _hash(p)
                              for p in sorted((pybind_include / "pybind11").rglob("*.h"))},
        compiler=compiler, compiler_version=subprocess.run(compiler + ["--version"], check=True,
            capture_output=True, text=True).stdout,
        expected_pybind_internals_id=expected_id, python_soabi=sysconfig.get_config_var("SOABI"),
        source_sha256={str(p.relative_to(ROOT)): _hash(p) for p in (source, Path(__file__))})
    fingerprint = sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    name = "heteromega_xrt_dmabuf_" + fingerprint[:16]
    directory = Path(os.environ.get("HETEROMEGA_DMABUF_BUILD_ROOT",
        Path.home() / ".cache/heteromega/dmabuf")) / fingerprint[:20]
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / (name + sysconfig.get_config_var("EXT_SUFFIX"))
    command = compiler + ["-O2", "-shared", "-fPIC", "-std=c++17", "-fvisibility=hidden",
        "-DPYBIND11_INTERNALS_VERSION=5", "-D_GLIBCXX_USE_CXX11_ABI=1",
        f"-DHETEROMEGA_XRT_MODULE={name}", f"-I{pybind_include}",
        f"-I{sysconfig.get_path('include')}", f"-I{sdk}", str(source),
        f"-L{xrt_root / 'lib'}", f"-Wl,-rpath,{xrt_root / 'lib'}", "-lxrt_coreutil", "-o", str(output)]
    if not output.is_file():
        subprocess.run(command, check=True, capture_output=not verbose, text=True)
    spec = importlib.util.spec_from_file_location(name, output)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    registry = dict(module.registry())
    if not registry.get("registered_types_shared") or registry.get("pybind_internals_id") != expected_id:
        raise RuntimeError(f"XRT bridge shared type registry check failed: {registry}")
    if registry.get("glibcxx_cxx11_abi") != 1:
        raise RuntimeError("XRT bridge C++ string ABI differs from the installed pyxrt build")
    metadata.update(build_fingerprint=fingerprint, build_command=command, registry=registry,
                    binding_library=str(output), binding_library_sha256=_hash(output))
    return module, metadata


def load_dmabuf_extensions(device="cuda", verbose=False):
    import torch

    if not torch.version.hip or not torch.cuda.is_available():
        raise RuntimeError("HIP DMA-BUF output requires ROCm Torch and an AMD GPU")
    device = torch.device(device)
    if device.type != "cuda":
        raise ValueError("device must be a ROCm Torch GPU")
    index = torch.cuda.current_device() if device.index is None else device.index
    device = torch.device("cuda", index)
    bridge, bridge_metadata = _load_xrt_bridge(verbose)
    rocm = Path(os.environ.get("HETEROMEGA_ROCM_PATH",
        os.environ.get("ROCM_PATH", "/opt/rocm"))).resolve()
    for header in ("hip/hip_runtime_api.h", "hsa/hsa_ext_amd.h"):
        if not (rocm / "include" / header).is_file():
            raise RuntimeError(f"missing ROCm header {header} under {rocm}")
    from torch.utils.cpp_extension import load

    source = HERE / "hip_dmabuf_bindings.cpp"
    metadata = dict(torch_version=str(torch.__version__), hip_version=str(torch.version.hip),
        rocm=str(rocm), device_index=index, gpu_name=torch.cuda.get_device_name(device),
        runtime_dependency_sha256={str(p.resolve()): _hash(p) for p in (
            rocm / "include/hip/hip_runtime_api.h", rocm / "include/hsa/hsa_ext_amd.h",
            rocm / "lib/libamdhip64.so", rocm / "lib/libhsa-runtime64.so")},
        source_sha256={str(p.relative_to(ROOT)): _hash(p) for p in (source, Path(__file__))})
    fingerprint = sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    directory = Path(os.environ.get("HETEROMEGA_DMABUF_BUILD_ROOT",
        Path.home() / ".cache/heteromega/dmabuf")) / ("hip-" + fingerprint[:20])
    directory.mkdir(parents=True, exist_ok=True)
    hip = load(name="heteromega_hip_dmabuf_" + fingerprint[:16], sources=[str(source)],
        extra_include_paths=[str(rocm / "include")],
        extra_cflags=["-O2", "-std=c++17", "-D__HIP_PLATFORM_AMD__=1"],
        extra_ldflags=[f"-L{rocm / 'lib'}", f"-Wl,-rpath,{rocm / 'lib'}", "-lamdhip64", "-lhsa-runtime64"],
        with_cuda=False, build_directory=str(directory), verbose=verbose)
    metadata.update(build_fingerprint=fingerprint, binding_library=str(hip.__file__),
                    binding_library_sha256=_hash(hip.__file__))
    return bridge, hip, device, dict(xrt_bridge=bridge_metadata, hip_allocation=metadata)


class GpuDmaBufOutput:
    """Bind a retained HIP allocation to one untouched XRT output argument.

    Both the returned Torch storage and imported pyxrt BO retain HipAllocation.
    Releasing the Python facade alone therefore cannot free live storage. The
    caller must complete both accelerators before destroying their last views.
    """

    def __init__(self, runner, shape, *, device="cuda", extensions=None, verbose_build=False):
        shape = tuple(shape)
        if len(shape) != 2 or any(type(value) is not int or value <= 0 for value in shape):
            raise ValueError("DMA-BUF output requires a positive two-dimensional shape")
        spec_shape, spec_dtype = runner.specs[-1]
        nbytes = int(np.prod(shape)) * 2
        if np.dtype(spec_dtype) != np.dtype(np.uint16) or int(np.prod(spec_shape)) != int(np.prod(shape)):
            raise ValueError("DMA-BUF output geometry/dtype differs from the compiled output")
        if nbytes % 4096 or runner.completed_dispatches:
            raise ValueError("DMA-BUF output must be page sized and bound before first dispatch")
        if int(runner.buffers[-1].size()) != nbytes:
            raise ValueError("original output BO extent differs from compiled geometry")
        bridge, hip, selected, build = extensions or load_dmabuf_extensions(device, verbose_build)
        registry = dict(bridge.registry())
        if not registry.get("registered_types_shared"):
            raise RuntimeError("XRT bridge does not share pyxrt's registered types")
        group = int(runner.kernel.group_id(len(runner.buffers) + 2))
        allocation = hip.HipAllocation(nbytes, selected.index)
        exported = dict(allocation.metadata())
        backing_nbytes = exported.get("backing_nbytes")
        export_offset = exported.get("export_offset")
        if (type(export_offset) is not int or export_offset < 0 or export_offset % 4096 or
                exported.get("nbytes") != nbytes or
                type(backing_nbytes) is not int or backing_nbytes < nbytes or
                export_offset + nbytes > backing_nbytes or backing_nbytes % 4096):
            raise RuntimeError(f"HIP export offset/extent failed independent validation: {exported}")
        parent_bo = bridge.import_fd(runner.device, allocation.fd(), backing_nbytes, group, allocation)
        if not isinstance(parent_bo, runner.xrt.bo):
            raise RuntimeError("bridge did not return a genuine pyxrt.bo")
        parent_description = dict(bridge.describe(parent_bo))
        if int(parent_bo.size()) != backing_nbytes or parent_description.get("nbytes") != backing_nbytes:
            raise RuntimeError("imported backing BO extent failed independent validation")
        sub_buffer = backing_nbytes != nbytes or export_offset != 0
        bo = bridge.sub_buffer(parent_bo, nbytes, export_offset, allocation) if sub_buffer else parent_bo
        if not isinstance(bo, runner.xrt.bo):
            raise RuntimeError("bridge did not return a genuine pyxrt.bo sub-buffer")
        description = dict(bridge.describe(bo))
        if int(bo.size()) != nbytes or description.get("nbytes") != nbytes:
            raise RuntimeError("imported BO extent failed independent validation")
        if description.get("bank_id") != (group & 0xffff):
            raise RuntimeError("imported BO bank differs from output kernel bank")
        if any(description.get(key) != parent_description.get(key) for key in ("group_id", "bank_id", "flags")):
            raise RuntimeError("logical output sub-buffer differs from imported backing group/flags")
        tensor = allocation.tensor(shape)
        allocation.close_export()
        self.allocation, self.bo, self.tensor, self.runner = allocation, bo, tensor, runner
        self.parent_bo = parent_bo
        self.metadata = dict(build=build, registry=registry, allocation=dict(allocation.metadata()),
            imported_bo=description, shape=list(shape), dtype="BF16", output_argument=len(runner.buffers) + 2,
            imported_backing_bo=parent_description,
            import_extent_policy="page_offset_logical_subbuffer" if sub_buffer else "whole_backing",
            sub_buffer_used=sub_buffer, sub_buffer_offset=export_offset,
            python_buffer_type="pyxrt.bo",
            kernel_group_id=group, kernel_bank_id=group & 0xffff,
            import_api="xrt::bo(device, exported DMA-BUF FD)", fd_closed_after_import=True,
            copy_fallback=False, hardware_coherency_validated=False)
        # Commit binding only after every check and Tensor construction succeeds.
        runner.buffers[-1] = bo

    def sync_from_npu(self):
        if self.runner.buffers[-1] is not self.bo:
            raise RuntimeError("imported GPU output BO binding changed")
        self.bo.sync(self.runner.xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_FROM_DEVICE)
        return self.tensor


class DmaBufOutputNpuFFN(SharedNpuFFN):
    """Same kernels and input staging; final output stays in HIP-owned storage."""

    def __init__(self, *args, gpu_device="cuda", dmabuf_extensions=None,
                 verbose_build=False, **kwargs):
        if kwargs.get("down_output_layout", "compact") != "row_major":
            raise ValueError("HIP DMA-BUF output requires down_output_layout='row_major'")
        if kwargs.get("mapped_output", False):
            raise ValueError("HIP DMA-BUF output cannot retain the original XRT output mapping")
        kwargs["mapped_output"] = False
        super().__init__(*args, **kwargs)
        self.gpu_output = GpuDmaBufOutput(self.down, (self.m, self.hidden), device=gpu_device,
            extensions=dmabuf_extensions, verbose_build=verbose_build)
        self.gpu_output_sync_count = 0
        self.metadata = dict(self.metadata, gpu_output_dmabuf=True,
            gpu_output_dmabuf_contract=self.gpu_output.metadata,
            host_output_readback="gpu_owned_dmabuf")

    def _read_final(self):
        result = self.gpu_output.sync_from_npu()
        self.gpu_output_sync_count += 1
        return result

    def run_raw(self, x_bits):
        result = super().run_raw(x_bits)
        self.last_diagnostics.update(gpu_output_dmabuf=True,
            gpu_output_sync_count=self.gpu_output_sync_count,
            final_output_bo_reads=0, final_output_h2d_copies=0)
        return result

    def host_snapshot(self):
        """Owned validation snapshot after completed NPU/GPU work, outside timer."""
        return self.gpu_output.tensor.detach().cpu()

    def run(self, x_bits):
        self.run_raw(x_bits)
        import torch
        return self.host_snapshot().view(torch.uint16).numpy().copy()


class TimedDmaBufOutputFFN(TimedFFN):
    """Ready GPU input → synchronized GPU reduction; input staging included."""

    def __init__(self, gpu, npu, m, hidden, device):
        if not isinstance(npu, DmaBufOutputNpuFFN) or (npu.m, npu.hidden) != (m, hidden):
            raise ValueError("DMA-BUF timer requires the matching output-only NPU adapter")
        super().__init__(gpu, None, m, hidden, device)
        self.npu = npu
        self.host_x = self.torch.empty((m, hidden), dtype=self.torch.bfloat16, pin_memory=True)
        self.host_x_bits = self.host_x.view(self.torch.uint16).numpy()
        self.npu_gpu_output = npu.gpu_output.tensor
        self.metadata = dict(gpu_output_dmabuf=True, output=npu.gpu_output.metadata,
            input_staging="unchanged GPU-to-pinned-host copy and NPU BO upload",
            output_staging="completed NPU and FROM_DEVICE sync then direct GPU reduction")
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
        elapsed = (time.perf_counter_ns() - start) / 1000
        diagnostics.update(npu=self.npu.last_diagnostics, gpu_output_dmabuf=True,
                           final_output_h2d_copies=0, final_output_cpu_layout_copies=0)
        return self.output, elapsed, diagnostics
