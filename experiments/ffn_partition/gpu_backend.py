"""Asynchronous FFN adapter around the original HeteroMosaic GPU kernels.

Only preparation packs weights. Timed execution retains compact channel-shard
buffers through gate/up, separate BF16 SiLU/multiply, and the sliced down GEMM.
The standalone extension compiles the existing GPU source without changing its
math or linking the model/direct-XDNA runtime. Importing this module and packing
weights require NumPy only; ROCm Torch is imported when constructing a branch.
"""

from hashlib import sha256
from numbers import Integral
from pathlib import Path
import json
import os

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
GPU_SOURCE = ROOT / "src/hipkernels/w4a16_gemm_packed.cu"
GPU_HEADER = ROOT / "include/hipkernels/w4a16_gemm_packed.hpp"
BINDINGS = Path(__file__).with_name("gpu_bindings.cpp")
PACKED_TILE_BYTES = 4352
PACKED_LAYOUT = "heteromosaic_k128_n64_zigzag8_v1"


def _aligned(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0 or value % 128:
        raise ValueError(f"{name} must be a positive multiple of 128")
    return int(value)


def pack_heteromosaic_weights(weight):
    """Convert canonical W4A16 [N,K] weights to original packed GPU bytes.

    This is an exact NumPy adapter for QuantizedLinearImpl's original packer:
    128x64 tiles, ordered by N-tile % 8, N-tile, then K-tile; 8x8
    microtiles with adjacent-N int4 nibbles; BF16 scales; and duplicate
    eight-byte zero-point groups. Canonical metadata is [N,K/128].
    """
    n, k = weight.shape
    _aligned(k, "K")
    _aligned(n, "N")
    if weight.group_size != 128:
        raise ValueError("the original packed GPU kernel requires group_size=128")
    packed = np.asarray(weight.packed)
    scales = np.asarray(weight.scales, dtype=np.float32)
    zeros = np.asarray(weight.zeros)
    if packed.dtype != np.uint8 or packed.shape != (n, k // 2):
        raise ValueError("canonical weights must be uint8 [N,K/2]")
    if scales.shape != (n, k // 128) or zeros.shape != scales.shape:
        raise ValueError("canonical metadata must have shape [N,K/128]")
    if not np.all(np.isfinite(scales)) or np.any(scales <= 0):
        raise ValueError("scales must be finite and positive")
    if not np.issubdtype(zeros.dtype, np.integer) or np.any((zeros < 0) | (zeros > 15)):
        raise ValueError("zero points must be integers in [0,15]")

    # Round FP32 metadata to BF16, ties to even, before storing its raw bytes.
    bits = np.ascontiguousarray(scales).view(np.uint32)
    scale_bits = ((bits + np.uint32(0x7FFF) + ((bits >> 16) & 1)) >> 16).astype("<u2")
    nt, kt = n // 64, k // 128
    result = np.empty((nt * kt, PACKED_TILE_BYTES), dtype=np.uint8)
    index = 0
    for col_mod in range(8):
        for ni in range(col_mod, nt, 8):
            ns = slice(ni * 64, (ni + 1) * 64)
            for ki in range(kt):
                # Unpack only this tile, avoiding a full int8 weight replica.
                source = packed[ns, ki * 64:(ki + 1) * 64]
                q = np.empty((64, 128), dtype=np.uint8)
                q[:, 0::2], q[:, 1::2] = source & 15, source >> 4
                native = q.T.reshape(16, 8, 8, 8).transpose(0, 2, 1, 3)
                result[index, :4096] = (native[..., 0::2] | (native[..., 1::2] << 4)).reshape(-1)
                result[index, 4096:4224] = np.ascontiguousarray(scale_bits[ns, ki]).view(np.uint8)
                result[index, 4224:] = np.repeat(zeros[ns, ki].astype(np.uint8).reshape(8, 8), 2, axis=0).reshape(-1)
                index += 1
    return result.reshape(-1)


def load_gpu_extension(device="cuda", verbose=False):
    """Build/cache a thin extension for the installed Torch and native GPU.

    HETEROMEGA_ROCM_PATH can select the compiler installation explicitly.
    HETEROMEGA_GPU_BUILD_ROOT can select the cache root. Source contents,
    Torch/HIP versions, native architecture, and ROCm path all key the cache.
    No model extension, NPU driver library, or model weight download is needed.
    """
    import torch

    if not torch.version.hip or not torch.cuda.is_available():
        raise RuntimeError("GPUBranch requires a ROCm-enabled Torch environment and an available AMD GPU")
    device = torch.device(device)
    if device.type != "cuda":
        raise ValueError("GPUBranch device must be a ROCm Torch cuda device")
    index = torch.cuda.current_device() if device.index is None else device.index
    device = torch.device("cuda", index)
    props = torch.cuda.get_device_properties(device)
    arch = getattr(props, "gcnArchName", "").split(":", 1)[0]
    if not arch.startswith("gfx11"):
        raise RuntimeError(f"the existing wave32 GPU kernel requires gfx11, observed {arch!r}")

    explicit_rocm = os.environ.get("HETEROMEGA_ROCM_PATH")
    if explicit_rocm:
        rocm = Path(explicit_rocm)
    elif Path("/opt/rocm-7.2.0/bin/hipcc").exists():
        rocm = Path("/opt/rocm-7.2.0")
    else:
        rocm = Path(os.environ.get("ROCM_HOME", os.environ.get("ROCM_PATH", "/opt/rocm")))
    rocm = rocm.resolve()
    if not (rocm / "bin/hipcc").exists() or not (rocm / "include/hip/hip_runtime.h").exists():
        raise RuntimeError(f"no complete HIP compiler/headers under {rocm}; set HETEROMEGA_ROCM_PATH")
    os.environ["ROCM_HOME"] = str(rocm)
    os.environ["ROCM_PATH"] = str(rocm)
    # Torch 2.11's extension builder can append the wheel's complete architecture
    # list even when extra_cuda_cflags contains --offload-arch. rocWMMA rejects
    # several of those targets. This adapter intentionally builds for the device
    # selected above, so constrain both Torch's list and the explicit HIP flag.
    os.environ["PYTORCH_ROCM_ARCH"] = arch
    from torch.utils import cpp_extension

    # cpp_extension may already have been imported before the environment was
    # selected. Keep its compiler choice aligned with our explicit flags.
    cpp_extension.ROCM_HOME = str(rocm)
    cpp_extension.IS_HIP_EXTENSION = True
    sources = (GPU_SOURCE, GPU_HEADER, BINDINGS, Path(__file__))
    hashes = {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in sources}
    build_info = {"source_sha256": hashes, "torch_version": str(torch.__version__),
                  "hip_version": str(torch.version.hip), "gpu_arch": arch, "rocm_path": str(rocm),
                  "pytorch_rocm_arch": arch,
                  "packed_layout": PACKED_LAYOUT}
    fingerprint = sha256(json.dumps(build_info, sort_keys=True).encode()).hexdigest()
    build_root = Path(os.environ.get("HETEROMEGA_GPU_BUILD_ROOT", Path.home() / ".cache/heteromega/ffn_gpu"))
    build_dir = build_root / fingerprint[:20]
    build_dir.mkdir(parents=True, exist_ok=True)
    include_flag = f"-isystem{rocm / 'include'}"
    module = cpp_extension.load(
        name=f"heteromega_ffn_gpu_{fingerprint[:16]}",
        sources=[str(BINDINGS), str(GPU_SOURCE)],
        extra_include_paths=[str(ROOT / "include")],
        extra_cflags=["-O3", "-std=c++17", "-D__HIP_PLATFORM_AMD__=1", include_flag],
        extra_cuda_cflags=["-O3", "-std=c++17", "-ffast-math", "-D__HIP_PLATFORM_AMD__=1",
                          "-DRDNA3=1", f"--offload-arch={arch}", include_flag,
                          f"--hip-path={rocm}", f"--rocm-path={rocm}"],
        extra_ldflags=[f"-L{rocm / 'lib'}", f"-Wl,-rpath,{rocm / 'lib'}", "-lamdhip64"],
        build_directory=str(build_dir), verbose=verbose, with_cuda=True,
    )
    build_info["build_fingerprint"] = fingerprint
    return module, device, build_info


class GPUBranch:
    """One reusable compact FFN branch; enqueue is asynchronous and non-reentrant.

    Canonical weights may represent all channels (the baseline) or matching
    gate/up N slices and a down K slice. Inputs must already be ready on the
    selected stream; callers own any dependency on another producing stream.
    The returned output is reused by the next enqueue, so consume it before
    reusing this branch. Constructor setup/transfers are outside timed execution.
    """

    def __init__(self, gate, up, down, m, device="cuda", verbose_build=False):
        self.m = _aligned(m, "M")
        self.channels, self.hidden = gate.shape
        _aligned(self.hidden, "hidden size")
        _aligned(self.channels, "branch channels")
        if up.shape != gate.shape or down.shape != (self.hidden, self.channels):
            raise ValueError("gate/up must match [I,H] and down must have shape [H,I]")
        # Validate/pack before loading Torch or compiling the extension.
        packed = [pack_heteromosaic_weights(weight) for weight in (gate, up, down)]
        self._module, self.device, self.metadata = load_gpu_extension(device, verbose_build)
        import torch

        self._torch = torch
        with torch.cuda.device(self.device):
            self.weights = [torch.from_numpy(weight).to(self.device) for weight in packed]
            self.gate_output = torch.empty((self.m, self.channels), dtype=torch.bfloat16, device=self.device)
            self.up_output = torch.empty_like(self.gate_output)
            self.output = torch.empty((self.m, self.hidden), dtype=torch.bfloat16, device=self.device)
            self._last_stream = torch.cuda.current_stream(self.device)
            self._done = torch.cuda.Event()
            self._last_stream.synchronize()
        self.metadata = dict(self.metadata, backend="heteromosaic_original_gpu_packed",
                             m=self.m, hidden=self.hidden, channels=self.channels,
                             weight_bytes=sum(weight.nbytes for weight in packed),
                             scratch_bytes=2 * self.m * (2 * self.channels + self.hidden),
                             activation="separate_bf16_silu_then_multiply")
        self._has_run = False

    def enqueue(self, x_gpu, stream=None):
        """Queue the complete FFN on one HIP stream without a CPU wait."""
        torch = self._torch
        if x_gpu.device != self.device or x_gpu.dtype != torch.bfloat16 or tuple(x_gpu.shape) != (self.m, self.hidden):
            raise ValueError(f"input must be BF16 [{self.m},{self.hidden}] on {self.device}")
        if not x_gpu.is_contiguous():
            raise ValueError("input must be compact and contiguous; prepare it outside the timed region")
        with torch.cuda.device(self.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self.device)
            if selected.device != self.device:
                raise ValueError("stream belongs to a different GPU")
            with torch.cuda.stream(selected):
                if self._has_run and selected != self._last_stream:
                    selected.wait_event(self._done)
                handle = int(selected.cuda_stream)
                self._module.gemm(self.gate_output, x_gpu, self.weights[0], self.hidden, self.channels, handle)
                self._module.gemm(self.up_output, x_gpu, self.weights[1], self.hidden, self.channels, handle)
                torch.nn.functional.silu(self.gate_output, inplace=True)
                self.gate_output.mul_(self.up_output)
                self._module.gemm(self.output, self.gate_output, self.weights[2], self.channels, self.hidden, handle)
                self._done.record(selected)
            self._last_stream = selected
            self._has_run = True
        return self.output

    def synchronize(self):
        """Wait for the latest enqueue's stream; excluded only in kernel timers."""
        self._last_stream.synchronize()
