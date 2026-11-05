"""NumPy oracle for a channel-partitioned, bias-free SwiGLU FFN.

The portable weight format is row-major uint8 [N, K/2], with even K in the
low nibble, plus scales/zero points [N, K/group_size]. This describes logical
AWQ weights, not an XRT buffer layout or an AWQ checkpoint loader. Weights
dequantize as (unsigned_int4 - zero) * scale, grouped along K.

BF16 mode emulates storage boundaries using FP32 NumPy arrays; accumulation
and SiLU evaluation use FP32. SiLU is rounded to BF16 before multiplying by
up, matching separate BF16 silu_ and mul_ operations. The final product is
rounded again. This is a correctness oracle, not bitwise AIE simulation.
"""

from dataclasses import dataclass
from math import floor, isfinite, lcm
from numbers import Integral

import numpy as np


def _positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def bf16(values):
    """Round FP32 to BF16, ties to even; return the values in an FP32 array."""
    values = np.asarray(values, dtype=np.float32)
    bits = values.view(np.uint32)
    rounded = (bits + np.uint32(0x7FFF) + ((bits >> 16) & 1)) & np.uint32(0xFFFF0000)
    # Preserve infinities and preserve NaNs as NaNs, including small payloads.
    special = (bits & np.uint32(0x7F800000)) == np.uint32(0x7F800000)
    special_bits = bits & np.uint32(0xFFFF0000)
    special_bits = np.where(np.isnan(values), special_bits | np.uint32(0x00400000), special_bits)
    return np.where(special, special_bits, rounded).astype(np.uint32).view(np.float32)


def pack_int4(values):
    """Pack a two-dimensional unsigned-int4 matrix along its K dimension."""
    values = np.asarray(values)
    if values.ndim != 2 or values.shape[1] % 2:
        raise ValueError("int4 values must have shape [N, even K]")
    if not np.issubdtype(values.dtype, np.integer) or np.any((values < 0) | (values > 15)):
        raise ValueError("int4 values must be integers in [0, 15]")
    values = values.astype(np.uint8)
    return values[:, 0::2] | (values[:, 1::2] << 4)


def unpack_int4(packed):
    """Unpack portable [N, K/2] bytes into [N, K] unsigned int4 values."""
    packed = np.asarray(packed)
    if packed.ndim != 2 or packed.dtype != np.uint8:
        raise ValueError("packed weights must be a uint8 matrix")
    values = np.empty((packed.shape[0], packed.shape[1] * 2), dtype=np.uint8)
    values[:, 0::2] = packed & 15
    values[:, 1::2] = packed >> 4
    return values


@dataclass(frozen=True)
class W4A16:
    """A portable quantized linear weight, with output-major [N, K] layout."""

    packed: np.ndarray
    scales: np.ndarray
    zeros: np.ndarray
    group_size: int

    def __post_init__(self):
        _positive_int(self.group_size, "group_size")
        packed, scales, zeros = map(np.asarray, (self.packed, self.scales, self.zeros))
        if packed.ndim != 2 or packed.dtype != np.uint8 or 0 in packed.shape:
            raise ValueError("packed weights must be a nonempty uint8 [N, K/2] matrix")
        n, half_k = packed.shape
        k = 2 * half_k
        if k % self.group_size:
            raise ValueError("K must be divisible by group_size")
        expected = (n, k // self.group_size)
        if scales.shape != expected or zeros.shape != expected:
            raise ValueError(f"scales and zeros must have shape {expected}")
        if not np.issubdtype(scales.dtype, np.floating) or not np.all(np.isfinite(scales)) or np.any(scales <= 0):
            raise ValueError("scales must be finite, positive floating-point values")
        if not np.issubdtype(zeros.dtype, np.integer) or np.any((zeros < 0) | (zeros > 15)):
            raise ValueError("zeros must be integers in [0, 15]")
        object.__setattr__(self, "packed", packed)
        object.__setattr__(self, "scales", scales)
        object.__setattr__(self, "zeros", zeros)

    @property
    def shape(self):
        return self.packed.shape[0], self.packed.shape[1] * 2

    def dequantize(self, bf16_io=False):
        scales = bf16(self.scales) if bf16_io else self.scales.astype(np.float32)
        scales = np.repeat(scales, self.group_size, axis=1)
        zeros = np.repeat(self.zeros, self.group_size, axis=1).astype(np.float32)
        weights = (unpack_int4(self.packed).astype(np.float32) - zeros) * scales
        return bf16(weights) if bf16_io else weights

    def output_slice(self, start, stop):
        """Slice matching gate/up output channels; arrays remain views."""
        _validate_slice(start, stop, self.shape[0], 1)
        return W4A16(self.packed[start:stop], self.scales[start:stop], self.zeros[start:stop], self.group_size)

    def input_slice(self, start, stop):
        """Slice down K channels without splitting a byte or quantization group."""
        _validate_slice(start, stop, self.shape[1], lcm(2, self.group_size))
        groups = slice(start // self.group_size, stop // self.group_size)
        return W4A16(self.packed[:, start // 2:stop // 2], self.scales[:, groups], self.zeros[:, groups], self.group_size)


def _validate_slice(start, stop, size, alignment):
    if any(isinstance(x, bool) or not isinstance(x, Integral) for x in (start, stop)):
        raise ValueError("slice boundaries must be integers")
    if not 0 <= start < stop <= size:
        raise ValueError("slice must be nonempty and lie within the weight dimension")
    if start % alignment or stop % alignment:
        raise ValueError(f"slice boundaries must be aligned to {alignment}")


@dataclass(frozen=True)
class FFNPartition:
    """NPU owns [0, npu_channels); GPU owns the remaining FFN channels."""

    intermediate_channels: int
    npu_channels: int
    alignment: int = 128

    def __post_init__(self):
        _positive_int(self.intermediate_channels, "intermediate_channels")
        _positive_int(self.alignment, "alignment")
        if isinstance(self.npu_channels, bool) or not isinstance(self.npu_channels, Integral):
            raise ValueError("npu_channels must be an integer")
        if not 0 <= self.npu_channels <= self.intermediate_channels:
            raise ValueError("npu_channels must lie within the FFN width")
        if self.intermediate_channels % self.alignment or self.npu_channels % self.alignment:
            raise ValueError("FFN width and NPU channel count must satisfy alignment")

    @classmethod
    def from_ratio(cls, intermediate_channels, npu_ratio, alignment=128):
        """Round the requested NPU share to nearest aligned width, ties upward."""
        _positive_int(intermediate_channels, "intermediate_channels")
        _positive_int(alignment, "alignment")
        if not isfinite(npu_ratio) or not 0 <= npu_ratio <= 1:
            raise ValueError("npu_ratio must be finite and in [0, 1]")
        npu_channels = floor(intermediate_channels * npu_ratio / alignment + 0.5) * alignment
        return cls(intermediate_channels, npu_channels, alignment)

    @property
    def slices(self):
        return {"npu": (0, self.npu_channels), "gpu": (self.npu_channels, self.intermediate_channels)}


def silu_multiply(gate, up, bf16_io=False):
    """Local SwiGLU; BF16 mode rounds gate/up, SiLU, and final product.

    The intermediate rounding preserves the existing torch::silu_(gate);
    gate.mul_(up) numerical boundary even when executed in one AIE kernel.
    """
    gate, up = np.asarray(gate, dtype=np.float32), np.asarray(up, dtype=np.float32)
    if gate.shape != up.shape:
        raise ValueError("gate and up activations must have identical shapes")
    if bf16_io:
        gate, up = bf16(gate), bf16(up)
    exponent = np.exp(-np.abs(gate))
    sigmoid = np.where(gate >= 0, 1 / (1 + exponent), exponent / (1 + exponent))
    silu = gate * sigmoid
    if bf16_io:
        silu = bf16(silu)
    result = silu * up
    return bf16(result) if bf16_io else result


def _validate_ffn(x, gate, up, down):
    x = np.asarray(x, dtype=np.float32)
    if x.ndim != 2 or 0 in x.shape or not np.all(np.isfinite(x)):
        raise ValueError("input must be a finite, nonempty [tokens, hidden] matrix")
    intermediate, hidden = gate.shape
    if up.shape != (intermediate, hidden) or down.shape != (hidden, intermediate) or x.shape[1] != hidden:
        raise ValueError("expected gate/up [intermediate, hidden], down [hidden, intermediate], input [tokens, hidden]")
    return x


def _local_ffn(x, gate, up, down, bf16_io):
    gate_values = x @ gate.dequantize(bf16_io).T
    up_values = x @ up.dequantize(bf16_io).T
    local = silu_multiply(gate_values, up_values, bf16_io)
    # Keep partial results FP32 until both devices have contributed.
    return local @ down.dequantize(bf16_io).T


def ffn_reference(x, gate, up, down, bf16_io=False):
    """Evaluate an unpartitioned W4A16 SwiGLU FFN (FP32 by default)."""
    x = _validate_ffn(x, gate, up, down)
    x = bf16(x) if bf16_io else x
    result = _local_ffn(x, gate, up, down, bf16_io)
    return bf16(result) if bf16_io else result


def ffn_partitioned(x, gate, up, down, partition, bf16_io=False):
    """Return (reduced_output, partials), retaining each local FFN partition.

    Gate/up use identical output slices and down uses the same input slice.
    Empty device slices emit a zero partial. Views select existing weights;
    each device's dequantization is only a CPU-oracle implementation detail.
    """
    x = _validate_ffn(x, gate, up, down)
    if partition.intermediate_channels != gate.shape[0]:
        raise ValueError("partition width must equal the intermediate FFN width")
    required = lcm(partition.alignment, down.group_size, 2)
    if partition.intermediate_channels % required or partition.npu_channels % required:
        raise ValueError(f"partition must align to down-projection groups/bytes and tile width ({required})")
    x = bf16(x) if bf16_io else x
    partials = {}
    for device, (start, stop) in partition.slices.items():
        if start == stop:
            partials[device] = np.zeros_like(x)
        else:
            partials[device] = _local_ffn(x, gate.output_slice(start, stop), up.output_slice(start, stop), down.input_slice(start, stop), bf16_io)
    result = partials["npu"] + partials["gpu"]
    return (bf16(result) if bf16_io else result), partials
