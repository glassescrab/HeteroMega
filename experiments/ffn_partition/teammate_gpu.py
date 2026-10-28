"""Candidate-only asynchronous adapter for kernels/gpu's three-kernel FFN.

Setup gathers unchanged W4A16 tiles into one interleaved gate/up buffer and
one down slice. Timed calls use the teammate implementation verbatim: original
prefill GEMM, FP32 SiLU*up with one BF16 rounding, original prefill GEMM.
The original GPUBranch remains the strict baseline and is never replaced here.
"""

from hashlib import sha256
from pathlib import Path
import json
import os

import numpy as np

from .gpu_backend import ROOT, PACKED_LAYOUT, PACKED_TILE_BYTES, _aligned, pack_heteromosaic_weights

BINDINGS = Path(__file__).with_name("teammate_gpu_bindings.cpp")
COMPILED_SOURCES = (
    BINDINGS,
    ROOT / "kernels/gpu/src/gpu_ffn.cpp",
    ROOT / "kernels/gpu/src/pack_w4a16.cpp",
    ROOT / "kernels/gpu/src/silu_mul.cu",
    ROOT / "kernels/gpu/src/gemv_w4a16.cu",
    ROOT / "src/hipkernels/w4a16_gemm_packed.cu",
    ROOT / "src/hipkernels/w4a16_gemv_packed.cu",
)
SOURCE_DEPENDENCIES = (*COMPILED_SOURCES,
    ROOT / "kernels/gpu/include/heteromega/gpu_ffn.hpp",
    ROOT / "kernels/gpu/src/bf16_device.hpp",
    ROOT / "include/hipkernels/w4a16_gemm_packed.hpp",
    Path(__file__), Path(__file__).with_name("gpu_backend.py"))


def source_hashes():
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
            for path in SOURCE_DEPENDENCIES}


def _validate_packed(weights, hidden, intermediate, begin, end):
    hidden, intermediate = _aligned(hidden, "hidden"), _aligned(intermediate, "intermediate")
    if isinstance(begin, bool) or not isinstance(begin, (int, np.integer)) or begin < 0 or begin % 128:
        raise ValueError("begin must be a nonnegative multiple of 128")
    end = _aligned(end, "end")
    if not begin < end <= intermediate:
        raise ValueError("packed FFN requires 0 <= begin < end <= intermediate")
    if len(weights) != 3:
        raise ValueError("three original packed gate/up/down buffers are required")
    size = (hidden // 128) * (intermediate // 64) * PACKED_TILE_BYTES
    arrays = tuple(np.asarray(weight) for weight in weights)
    if any(w.dtype != np.uint8 or w.ndim != 1 or w.size != size or not w.flags.c_contiguous
           for w in arrays):
        raise ValueError(f"each original weight must be contiguous uint8 [{size}]")
    return arrays, hidden, intermediate, int(begin), end


def load_teammate_gpu_extension(device="cuda", verbose=False):
    """Build a separate extension/cache; do not alter the baseline loader."""
    import torch

    if not torch.version.hip or not torch.cuda.is_available():
        raise RuntimeError("TeammateGPUBranch requires ROCm Torch and an available AMD GPU")
    device = torch.device(device)
    if device.type != "cuda":
        raise ValueError("device must be a ROCm Torch cuda device")
    device = torch.device("cuda", torch.cuda.current_device() if device.index is None else device.index)
    arch = getattr(torch.cuda.get_device_properties(device), "gcnArchName", "").split(":", 1)[0]
    if not arch.startswith("gfx11"):
        raise RuntimeError(f"the teammate packed GEMM requires gfx11, observed {arch!r}")
    explicit = os.environ.get("HETEROMEGA_ROCM_PATH")
    rocm = Path(explicit or ("/opt/rocm-7.2.0" if Path("/opt/rocm-7.2.0/bin/hipcc").exists()
                            else os.environ.get("ROCM_HOME", os.environ.get("ROCM_PATH", "/opt/rocm")))).resolve()
    if not (rocm / "bin/hipcc").exists() or not (rocm / "include/hip/hip_runtime.h").exists():
        raise RuntimeError(f"no HIP compiler/headers under {rocm}; set HETEROMEGA_ROCM_PATH")
    os.environ.update(ROCM_HOME=str(rocm), ROCM_PATH=str(rocm), PYTORCH_ROCM_ARCH=arch)
    from torch.utils import cpp_extension
    cpp_extension.ROCM_HOME, cpp_extension.IS_HIP_EXTENSION = str(rocm), True
    metadata = dict(source_sha256=source_hashes(), torch_version=str(torch.__version__),
                    hip_version=str(torch.version.hip), gpu_arch=arch, rocm_path=str(rocm),
                    pytorch_rocm_arch=arch, packed_layout=PACKED_LAYOUT, gemm_autotune=0)
    fingerprint = sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    cache = Path(os.environ.get("HETEROMEGA_TEAMMATE_GPU_BUILD_ROOT",
                                Path.home() / ".cache/heteromega/ffn_teammate_gpu")) / fingerprint[:20]
    cache.mkdir(parents=True, exist_ok=True)
    include_flag = f"-isystem{rocm / 'include'}"
    module = cpp_extension.load(
        name=f"heteromega_teammate_ffn_{fingerprint[:16]}",
        sources=[str(path) for path in COMPILED_SOURCES],
        extra_include_paths=[str(ROOT / "include"), str(ROOT / "kernels/gpu/include")],
        extra_cflags=["-O3", "-std=c++17", "-D__HIP_PLATFORM_AMD__=1", include_flag],
        extra_cuda_cflags=["-O3", "-std=c++17", "-ffast-math", "-D__HIP_PLATFORM_AMD__=1",
                          "-DRDNA3=1", "-DAUTOTUNE=0", f"--offload-arch={arch}", include_flag,
                          f"--hip-path={rocm}", f"--rocm-path={rocm}"],
        extra_ldflags=[f"-L{rocm / 'lib'}", f"-Wl,-rpath,{rocm / 'lib'}", "-lamdhip64"],
        build_directory=str(cache), verbose=verbose, with_cuda=True)
    metadata.update(build_fingerprint=fingerprint, binary_path=str(module.__file__),
                    binary_sha256=sha256(Path(module.__file__).read_bytes()).hexdigest())
    return module, device, metadata


class TeammateGPUBranch:
    """Drop-in enqueue/output contract for a GPU suffix; setup copies tiles.

    Non-reentrant; the output and scratch are reused. Inputs must be ready on
    the selected stream. Cross-stream reuse waits for the previous enqueue.
    The fused activation differs from the baseline's two BF16 roundings and
    must pass the runner's unchanged strict GPU partial checks.
    """

    def __init__(self, gate, up, down, m, device="cuda", verbose_build=False):
        channels, hidden = gate.shape
        if up.shape != gate.shape or down.shape != (hidden, channels):
            raise ValueError("gate/up must match [I,H] and down must have shape [H,I]")
        packed = [pack_heteromosaic_weights(w) for w in (gate, up, down)]
        self._initialize(packed, hidden, channels, 0, channels, m, device, verbose_build,
                         "canonical branch packed once using the original packer")

    @classmethod
    def from_upstream(cls, gate, up, down, hidden, intermediate, begin, end, m,
                      device="cuda", verbose_build=False):
        """Use original full packed bytes; gather suffix [begin,end) at setup."""
        obj = cls.__new__(cls)
        obj._initialize((gate, up, down), hidden, intermediate, begin, end, m,
                        device, verbose_build, "full original packed gate/up/down buffers")
        return obj

    def _initialize(self, packed, hidden, intermediate, begin, end, m, device,
                    verbose_build, source_kind):
        packed, hidden, intermediate, begin, end = _validate_packed(
            packed, hidden, intermediate, begin, end)
        self.m, self.hidden, self.channels = _aligned(m, "M"), hidden, end - begin
        self._module, self.device, metadata = load_teammate_gpu_extension(device, verbose_build)
        import torch
        self._torch = torch
        # Owned CPU snapshots avoid a writable Torch alias to read-only fixtures.
        originals = tuple(torch.from_numpy(w.copy()) for w in packed)
        prepared = self._module.prepare(*originals, hidden, intermediate, begin, end)
        prepared_hashes = {name: sha256(t.numpy().tobytes()).hexdigest()
                           for name, t in zip(("gate_up", "down"), prepared)}
        with torch.cuda.device(self.device):
            self.weights = [t.to(self.device) for t in prepared]
            self.gate_up_output = torch.empty((self.m, 2 * self.channels), dtype=torch.bfloat16, device=self.device)
            self.activation = torch.empty((self.m, self.channels), dtype=torch.bfloat16, device=self.device)
            self.x_pad = torch.empty((self.m, self.hidden), dtype=torch.bfloat16, device=self.device)
            self.output = torch.empty((self.m, self.hidden), dtype=torch.bfloat16, device=self.device)
            self._last_stream = torch.cuda.current_stream(self.device)
            self._done = torch.cuda.Event()
            self._last_stream.synchronize()
        self.metadata = dict(metadata, backend="teammate_three_kernel_gpu_ffn", m=self.m,
            hidden=self.hidden, channels=self.channels, source_intermediate=intermediate,
            source_channel_begin=begin, source_channel_end=end, source_kind=source_kind,
            source_packed_sha256={name: sha256(w.tobytes()).hexdigest()
                                 for name, w in zip(("gate", "up", "down"), packed)},
            prepared_packed_sha256=prepared_hashes,
            weight_bytes=sum(t.numel() * t.element_size() for t in prepared),
            scratch_bytes=2 * self.m * (3 * self.channels + 2 * self.hidden),
            activation="teammate_fp32_silu_times_up_single_bf16_rounding",
            gate_up_layout="interleaved_64_channels", kernels_per_prefill=3,
            setup_transform="byte-preserving packed tile gather/merge; no dequantization",
            prefill_gemm="original HeteroMosaic packed GEMM, AUTOTUNE=0")
        self._has_run = False

    def enqueue(self, x_gpu, stream=None):
        torch = self._torch
        if x_gpu.device != self.device or x_gpu.dtype != torch.bfloat16 or tuple(x_gpu.shape) != (self.m, self.hidden):
            raise ValueError(f"input must be BF16 [{self.m},{self.hidden}] on {self.device}")
        if not x_gpu.is_contiguous():
            raise ValueError("input must be compact and contiguous")
        with torch.cuda.device(self.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self.device)
            if selected.device != self.device:
                raise ValueError("stream belongs to a different GPU")
            with torch.cuda.stream(selected):
                if self._has_run and selected != self._last_stream:
                    selected.wait_event(self._done)
                self._module.forward(self.output, x_gpu, *self.weights,
                    self.gate_up_output, self.activation, self.x_pad,
                    self.hidden, self.channels, int(selected.cuda_stream))
                self._done.record(selected)
            self._last_stream, self._has_run = selected, True
        return self.output

    def synchronize(self):
        self._last_stream.synchronize()
