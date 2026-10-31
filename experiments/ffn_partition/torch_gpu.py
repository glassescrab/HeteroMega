"""Experimental pre-dequantized BF16 GPU suffix using PyTorch matmul.

Setup converts the complementary W4A16 weights to contiguous BF16 once,
outside the timed FFN boundary. Timed execution is three BF16 matmuls plus a
BF16 SiLU*up. This is a GPU optimization experiment, not the strict packed
W4A16 baseline; the original GPU control remains unchanged.
"""

from hashlib import sha256
from pathlib import Path
import time

import numpy as np

from .gpu_backend import ROOT


class TorchBF16GPUBranch:
    """Reuse preallocated BF16 buffers; non-reentrant."""

    def __init__(self, gate, up, down, m, device='cuda', verbose_build=False):
        import torch
        self.torch = torch
        self.device = torch.device(device)
        if self.device.type == 'cuda' and self.device.index is None:
            self.device = torch.device('cuda', torch.cuda.current_device())
        self.m = int(m)
        if gate.shape[0] != up.shape[0] or gate.shape[1] != up.shape[1] or down.shape != (gate.shape[1], gate.shape[0]):
            raise ValueError('gate/up [P,H] and down [H,P] are required')
        self.channels, self.hidden = gate.shape
        self.gate = torch.from_numpy(gate.dequantize(True)).to(self.device, dtype=torch.bfloat16).t().contiguous()
        self.up = torch.from_numpy(up.dequantize(True)).to(self.device, dtype=torch.bfloat16).t().contiguous()
        self.down = torch.from_numpy(down.dequantize(True)).to(self.device, dtype=torch.bfloat16).t().contiguous()
        with torch.cuda.device(self.device):
            self.gate_buf = torch.empty((self.m, self.channels), dtype=torch.bfloat16, device=self.device)
            self.up_buf = torch.empty_like(self.gate_buf)
            self.z_buf = torch.empty_like(self.gate_buf)
            self.out = torch.empty((self.m, self.hidden), dtype=torch.bfloat16, device=self.device)
            self._last_stream = torch.cuda.current_stream(self.device)
            self._done = torch.cuda.Event()
            self._last_stream.synchronize()
        self._has_run = False
        self.metadata = dict(backend='torch_bf16_dequantized_gpu_ffn',
            m=self.m, hidden=self.hidden, channels=self.channels,
            weight_bytes=int(self.channels * self.hidden * 2 * 3),
            weight_layout='predequantized_bf16_contiguous',
            activation='torch_bfloat16_silu_times_up',
            kernels_per_prefill=4, source_sha256={str(Path(__file__).relative_to(ROOT)): sha256(Path(__file__).read_bytes()).hexdigest()},
            setup='dequantize W4A16 to BF16 once; excluded from timing')

    @classmethod
    def from_weights(cls, weights, m, device='cuda', verbose_build=False):
        return cls(weights.gate, weights.up, weights.down, m, device, verbose_build)

    def enqueue(self, x_gpu, stream=None):
        torch = self.torch
        if x_gpu.device != self.device or x_gpu.dtype != torch.bfloat16 or tuple(x_gpu.shape) != (self.m, self.hidden):
            raise ValueError(f'input must be BF16 [{self.m},{self.hidden}] on {self.device}')
        if not x_gpu.is_contiguous():
            raise ValueError('input must be contiguous')
        with torch.cuda.device(self.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self.device)
            if selected.device != self.device:
                raise ValueError('stream belongs to a different GPU')
            with torch.cuda.stream(selected):
                if self._has_run and selected != self._last_stream:
                    selected.wait_event(self._done)
                torch.mm(x_gpu, self.gate, out=self.gate_buf)
                torch.mm(x_gpu, self.up, out=self.up_buf)
                torch.nn.functional.silu(self.gate_buf, inplace=True)
                torch.mul(self.gate_buf, self.up_buf, out=self.z_buf)
                torch.mm(self.z_buf, self.down, out=self.out)
                self._done.record(selected)
            self._last_stream, self._has_run = selected, True
        return self.out

    @property
    def output(self):
        return self.out

    def synchronize(self):
        self._last_stream.synchronize()


class TorchBF16SplitDownBranch:
    """GPU gate/up suffix + full down with an external Z prefix.

    The NPU supplies Z columns [0, p1); this branch computes Z columns
    [p1, I) and the full down projection. Weights are pre-dequantized BF16.
    Setup is outside the timed boundary. Experimental role-specialized path.
    """

    def __init__(self, gate_suffix, up_suffix, down_full, m, p1, hidden, device='cuda'):
        import torch
        self.torch = torch
        self.device = torch.device(device)
        if self.device.type == 'cuda' and self.device.index is None:
            self.device = torch.device('cuda', torch.cuda.current_device())
        self.m = int(m); self.p1 = int(p1); self.hidden = int(hidden)
        self.channels = int(gate_suffix.shape[0])
        if gate_suffix.shape != up_suffix.shape or gate_suffix.shape[1] != self.hidden:
            raise ValueError('split gate/up suffix shapes differ')
        if down_full.shape != (self.hidden, self.p1 + self.channels):
            raise ValueError('full down weights do not cover [0, I)')
        self.gate = torch.from_numpy(gate_suffix.dequantize(True)).to(self.device, dtype=torch.bfloat16).t().contiguous()
        self.up = torch.from_numpy(up_suffix.dequantize(True)).to(self.device, dtype=torch.bfloat16).t().contiguous()
        self.down = torch.from_numpy(down_full.dequantize(True)).to(self.device, dtype=torch.bfloat16).t().contiguous()
        with torch.cuda.device(self.device):
            self.gate_buf = torch.empty((self.m, self.channels), dtype=torch.bfloat16, device=self.device)
            self.up_buf = torch.empty_like(self.gate_buf)
            self.z_suffix = torch.empty_like(self.gate_buf)
            self.z_full = torch.empty((self.m, self.p1 + self.channels), dtype=torch.bfloat16, device=self.device)
            self.y = torch.empty((self.m, self.hidden), dtype=torch.bfloat16, device=self.device)
            self._last_stream = torch.cuda.current_stream(self.device)
            self._done = torch.cuda.Event()
            self._last_stream.synchronize()
        self._has_run = False
        self.metadata = dict(backend='torch_bf16_split_down_gpu_ffn',
            m=self.m, hidden=self.hidden, p1=self.p1, suffix_channels=self.channels,
            weight_bytes=int((2 * self.channels + self.hidden) * self.hidden * 2),
            weight_layout='predequantized_bf16_contiguous',
            activation='torch_bfloat16_silu_times_up', kernels_per_prefill=4,
            down_scope='full [0,I)', gate_up_scope=f'[{self.p1},{self.p1 + self.channels})',
            setup='dequantize W4A16 to BF16 once; excluded from timing')

    def enqueue_gate_up(self, x_gpu, stream=None):
        torch = self.torch
        if x_gpu.device != self.device or x_gpu.dtype != torch.bfloat16 or tuple(x_gpu.shape) != (self.m, self.hidden):
            raise ValueError('split input must be BF16 [M,H] on the selected GPU')
        if not x_gpu.is_contiguous():
            raise ValueError('split input must be contiguous')
        with torch.cuda.device(self.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self.device)
            with torch.cuda.stream(selected):
                if self._has_run and selected != self._last_stream:
                    selected.wait_event(self._done)
                torch.mm(x_gpu, self.gate, out=self.gate_buf)
                torch.mm(x_gpu, self.up, out=self.up_buf)
                torch.nn.functional.silu(self.gate_buf, inplace=True)
                torch.mul(self.gate_buf, self.up_buf, out=self.z_suffix)
                self._done.record(selected)
            self._last_stream, self._has_run = selected, True
        return self.z_suffix

    def enqueue_down(self, z_full, stream=None):
        torch = self.torch
        if z_full is not self.z_full:
            raise ValueError('down requires this branch z_full buffer')
        with torch.cuda.device(self.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self.device)
            with torch.cuda.stream(selected):
                torch.mm(self.z_full, self.down, out=self.y)
        return self.y

    @property
    def output(self):
        return self.y


class PackedSplitDownBranch:
    """GPU packed gate/up suffix + packed full down with external Z prefix."""

    def __init__(self, original, hidden, intermediate, p1, m, device='cuda',
                 verbose_build=False):
        import torch
        from .teammate_gpu import load_teammate_gpu_extension
        self.torch = torch
        self._module, self.device, metadata = load_teammate_gpu_extension(device, verbose_build)
        self.m, self.hidden, self.intermediate, self.p1 = int(m), int(hidden), int(intermediate), int(p1)
        self.channels = self.intermediate - self.p1
        if self.channels <= 0:
            raise ValueError('packed split requires a nonempty GPU suffix')
        cpu = tuple(torch.from_numpy(w.data.copy()) for w in original)
        suffix_gate_up, _ = self._module.prepare(*cpu, self.hidden, self.intermediate, self.p1, self.intermediate)
        _, down_full = self._module.prepare(*cpu, self.hidden, self.intermediate, 0, self.intermediate)
        with torch.cuda.device(self.device):
            self.gate_up_w = suffix_gate_up.to(self.device)
            self.down_w = down_full.to(self.device)
            self.gate_up = torch.empty((self.m, 2 * self.channels), dtype=torch.bfloat16, device=self.device)
            self.act = torch.empty((self.m, self.channels), dtype=torch.bfloat16, device=self.device)
            self.z_full = torch.empty((self.m, self.intermediate), dtype=torch.bfloat16, device=self.device)
            self.y = torch.empty((self.m, self.hidden), dtype=torch.bfloat16, device=self.device)
            self._last_stream = torch.cuda.current_stream(self.device)
            self._done = torch.cuda.Event()
            self._last_stream.synchronize()
        self._has_run = False
        self.metadata = dict(metadata, backend='packed_w4a16_split_down_gpu_ffn',
            m=self.m, hidden=self.hidden, intermediate=self.intermediate,
            p1=self.p1, suffix_channels=self.channels,
            weight_layout='original_packed_w4a16', setup='prepare both packed slices once; excluded from timing')

    def enqueue_gate_up(self, x_gpu, stream=None):
        torch = self.torch
        if x_gpu.device != self.device or x_gpu.dtype != torch.bfloat16 or tuple(x_gpu.shape) != (self.m, self.hidden):
            raise ValueError('packed split input must be BF16 [M,H] on the selected GPU')
        with torch.cuda.device(self.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self.device)
            if selected.device != self.device:
                raise ValueError('stream belongs to a different GPU')
            with torch.cuda.stream(selected):
                if self._has_run and selected != self._last_stream:
                    selected.wait_event(self._done)
                self._module.linear(self.gate_up, x_gpu, self.gate_up_w,
                    self.hidden, 2 * self.channels, self.hidden, 2 * self.channels,
                    int(selected.cuda_stream))
                self._module.silu_mul(self.gate_up, self.act, 1, int(selected.cuda_stream))
                self._done.record(selected)
            self._last_stream, self._has_run = selected, True
        return self.act

    def enqueue_down(self, z_full, stream=None):
        torch = self.torch
        if z_full is not self.z_full:
            raise ValueError('packed split down requires this branch z_full buffer')
        with torch.cuda.device(self.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self.device)
            with torch.cuda.stream(selected):
                self._module.linear(self.y, self.z_full, self.down_w,
                    self.intermediate, self.hidden, self.intermediate, self.hidden,
                    int(selected.cuda_stream))
        return self.y

    @property
    def output(self):
        return self.y
