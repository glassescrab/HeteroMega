"""Explicit diagnostic event timing around one complete GPU FFN branch.

This wrapper is opt-in: event recording changes the diagnostic workload and
must not be enabled for ordinary headline latency measurements. It wraps
either GPU implementation without changing its math or source. No per-stage
or pure-compute claim is made: the interval can include stream dependency
stalls and interference from other work on the device.
"""

from hashlib import sha256
import math
from pathlib import Path


class DiagnosticGPUBranch:
    """Delegate the branch contract and retain the latest enqueue's events.

    The caller supplies ready input and completes the ordinary FFN boundary
    before calling collect(). Subsequent enqueues replace the previous timing;
    collecting every sample is the caller's responsibility. Like the wrapped
    branch, this object is not reentrant.
    """

    def __init__(self, branch):
        self._branch = branch
        self._torch = branch._torch
        with self._torch.cuda.device(branch.device):
            self._start = self._torch.cuda.Event(enable_timing=True)
            self._stop = self._torch.cuda.Event(enable_timing=True)
        self._recorded = False
        self._enqueue_count = 0
        self.metadata = dict(branch.metadata,
            gpu_device_diagnostics={
                "enabled": True,
                "kind": "whole_branch_stream_events",
                "ordinary_headline_eligible": False,
                "includes": "branch kernels and intervening stream dependency stalls",
                "excludes": "host staging, NPU wait, partial-output transfer and boundary reduction",
                "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            })

    def __getattr__(self, name):
        return getattr(self._branch, name)

    def enqueue(self, x_gpu, stream=None):
        torch = self._torch
        with torch.cuda.device(self._branch.device):
            selected = stream if stream is not None else torch.cuda.current_stream(self._branch.device)
            if selected.device != self._branch.device:
                raise ValueError("stream belongs to a different GPU")
            self._recorded = False
            with torch.cuda.stream(selected):
                self._start.record(selected)
                output = self._branch.enqueue(x_gpu, selected)
                self._stop.record(selected)
            self._enqueue_count += 1
            self._recorded = True
        return output

    def collect(self):
        """Read completed events without adding a device/stream synchronization."""
        if not self._recorded:
            raise RuntimeError("no successful diagnostic GPU enqueue to collect")
        with self._torch.cuda.device(self._branch.device):
            if not self._start.query() or not self._stop.query():
                raise RuntimeError("complete the FFN boundary before collecting GPU diagnostics")
            elapsed_us = float(self._start.elapsed_time(self._stop)) * 1000.0
        if not math.isfinite(elapsed_us) or elapsed_us < 0:
            raise RuntimeError("GPU event timing returned an invalid interval")
        return {"device_elapsed_us": elapsed_us,
                "enqueue_count": self._enqueue_count,
                "scope": "whole GPU branch including stream dependency stalls",
                "ordinary_headline_eligible": False}
