"""Experimental HIP access to existing mapped XRT buffers, without BO imports.

This module does not establish that a driver permits HIP registration of its
XRT mappings, or that cross-device coherency works. Probe on the target first.
No automatic copy fallback is hidden behind the shared-memory interface.
"""

from hashlib import sha256
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BINDINGS = Path(__file__).with_name("shared_gpu_bindings.cpp")


def load_shared_gpu_extension(device="cuda", verbose=False):
    """Compile only a host-side HIP/Torch binding; no GPU/NPU kernels change."""
    import torch

    if not torch.version.hip or not torch.cuda.is_available():
        raise RuntimeError("mapped XRT GPU access requires ROCm Torch and an AMD GPU")
    device = torch.device(device)
    if device.type != "cuda":
        raise ValueError("device must identify a ROCm Torch GPU")
    index = torch.cuda.current_device() if device.index is None else device.index
    device = torch.device("cuda", index)
    rocm = Path(os.environ.get("HETEROMEGA_ROCM_PATH", os.environ.get("ROCM_PATH", "/opt/rocm"))).resolve()
    if not (rocm / "include/hip/hip_runtime_api.h").is_file():
        raise RuntimeError("set HETEROMEGA_ROCM_PATH to the runtime's ROCm headers/library installation")
    os.environ["ROCM_HOME"] = str(rocm)
    from torch.utils.cpp_extension import load

    metadata = dict(torch=str(torch.__version__), hip=str(torch.version.hip), rocm=str(rocm),
        gpu_name=torch.cuda.get_device_name(device), device_index=index,
        source_sha256={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in (BINDINGS, Path(__file__))})
    fingerprint = sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    build = Path(os.environ.get("HETEROMEGA_SHARED_GPU_BUILD_ROOT", Path.home() / ".cache/heteromega/shared_gpu")) / fingerprint[:20]
    build.mkdir(parents=True, exist_ok=True)
    module = load(name="heteromega_shared_gpu_" + fingerprint[:16], sources=[str(BINDINGS)],
        extra_include_paths=[str(rocm / "include")],
        extra_cflags=["-O3", "-std=c++17", "-D__HIP_PLATFORM_AMD__=1"],
        extra_ldflags=[f"-L{rocm / 'lib'}", f"-Wl,-rpath,{rocm / 'lib'}", "-lamdhip64"],
        with_cuda=False, build_directory=str(build), verbose=verbose)
    metadata.update(build_fingerprint=fingerprint, binding_library_sha256=sha256(Path(module.__file__).read_bytes()).hexdigest())
    return module, device, metadata


class SharedXrtBuffer:
    """A GPU tensor view of the *same* mapped XRT BO storage.

    Synchronization is explicit: finish GPU writes, call the BO's TO_DEVICE
    sync before NPU use, complete the NPU run and FROM_DEVICE sync before GPU
    reads. Never overlap writes across devices. This object introduces no sync
    inside an existing timer and never assumes that host/device pointers match.

    For zero-copy input, create the input in this storage before measurement
    and use this same tensor for the own-GPU control. Starting from a separate
    GPU allocation requires a GPU copy into this BO. Output is zero-copy only
    when its ABI already matches the tensor's row-major shape; compact NPU
    output needs an explicit GPU layout kernel or a row-major output artifact.
    """

    def __init__(self, bo, shape, *, dtype="bf16", device="cuda", mapped=None,
                 extension=None, verbose_build=False):
        import numpy as np

        if extension is None:
            module, selected, build = load_shared_gpu_extension(device, verbose_build)
        else:
            module, selected, build = extension
        self.bo = bo
        self.mapping = bo.map() if mapped is None else mapped
        # This is a view, not a copy. It also prevents registering a logical
        # subview instead of the whole mapped allocation.
        self.host_bytes = np.frombuffer(self.mapping, dtype=np.uint8)
        if not self.host_bytes.flags.writeable or self.host_bytes.size == 0:
            raise ValueError("XRT mapping must be writable and nonempty")
        if self.host_bytes.ctypes.data % 64:
            raise ValueError("XRT mapping is not cache-line aligned")
        self._registration = module.RegisteredHost(self.host_bytes, (self.bo, self.mapping), selected.index)
        self.tensor = self._registration.tensor(tuple(shape), dtype, 0)
        self.metadata = dict(build=build, mapping=self._registration.metadata(), dtype=dtype,
            shape=list(shape), storage="HIP-registered existing XRT BO mapping", copy_fallback=False,
            measured_coherency="not established by construction")

    def view(self, shape, *, dtype="bf16", byte_offset=0):
        """Create another storage-owning view; cannot resize the shared BO."""
        return self._registration.tensor(tuple(shape), dtype, byte_offset)


def probe_shared_gpu_access(bo, *, device="cuda", verbose_build=False):
    """Check CPU/GPU visibility and lifetime for a scratch BO; overwrites it.

    This probe alone does not establish NPU coherency. Follow it with an actual
    NPU changed/zero/repeated-input run and required XRT syncs before timing.
    """
    import numpy as np
    import torch

    mapping = bo.map()
    shared = SharedXrtBuffer(bo, (memoryview(mapping).nbytes,), dtype="uint8", device=device,
                             mapped=mapping, verbose_build=verbose_build)
    expected = (np.arange(shared.host_bytes.size, dtype=np.uint64) * 17 + 3).astype(np.uint8)
    shared.host_bytes[:] = expected
    torch.cuda.synchronize(shared.tensor.device)
    if not np.array_equal(shared.tensor.cpu().numpy(), expected):
        raise RuntimeError("GPU did not observe mapped BO host writes")
    shared.tensor.fill_(0x5A)
    torch.cuda.synchronize(shared.tensor.device)
    if not np.all(shared.host_bytes == 0x5A):
        raise RuntimeError("host did not observe GPU writes to mapped BO")
    return dict(status="passed_cpu_gpu_mapping_probe", bytes=int(shared.host_bytes.size),
                metadata=shared.metadata, npu_coherency_tested=False)
