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
