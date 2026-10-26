"""Zero-copy descriptor for original glassescrab TileFuse W4A16 buffers.

The ABI is pinned to mlir-aie revision
121dd54abc68f84d89a7074372ebf82be2db62d5, gemm_w4a16/test.cpp.
Each K128/N64 tile holds 4096 INT4 bytes, 128 BF16 scale bytes, and
128 zero-point bytes (each N8 zero vector is duplicated). Tiles are
ordered by N64 column modulo eight, then N64 column, then K128 group.

This module accepts an already packed full-source buffer. It deliberately
provides no conversion from HeteroMega's older compact N32 weight ABI.
"""

from dataclasses import dataclass
from numbers import Integral

import numpy as np


UPSTREAM_LAYOUT_VERSION = "glassescrab_w4a16_k128_n64_colmod8_4352_v1"
WEIGHT_TILE_BYTES = 4352


def _integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return int(value)


def _full_shape(k, n):
    k, n = _integer(k, "K", 1), _integer(n, "N", 1)
    if k % 128 or n % 64:
        raise ValueError("upstream source K and N must be multiples of 128 and 64")
    return k, n


def upstream_weight_bytes(k, n):
    """Exact byte count for a full upstream K-by-N packed weight buffer."""
    k, n = _full_shape(k, n)
    return (k // 128) * (n // 64) * WEIGHT_TILE_BYTES


def weight_tile_offset(full_k, full_n, k_group, n64_tile):
    """Byte offset of an original tile, retaining full-source striped order.

    Shape arguments describe the buffer before partitioning. Unequal stripe
    lengths are supported when the source N is not a multiple of 512.
    """
    full_k, full_n = _full_shape(full_k, full_n)
    kg, nt = _integer(k_group, "K group"), _integer(n64_tile, "N64 tile")
    groups, tiles = full_k // 128, full_n // 64
    if kg >= groups or nt >= tiles:
        raise ValueError("weight tile lies outside the full source shape")
    stripe, within_stripe = nt % 8, nt // 8
    preceding_tiles = stripe * (tiles // 8) + min(stripe, tiles % 8)
    ordinal = (preceding_tiles + within_stripe) * groups + kg
    return ordinal * WEIGHT_TILE_BYTES


@dataclass(frozen=True)
class UpstreamWeightBuffer:
    """Original packed storage plus its FULL logical K/N dimensions.

    ``data`` remains the exact caller-owned ndarray, including read-only
    arrays and memmap views. No dtype coercion, contiguous copy, metadata
    conversion, or tile reorder occurs. Content validity remains the
    upstream producer's contract; this descriptor validates storage/shape.
    """

    data: np.ndarray
    k: int
    n: int

    def __post_init__(self):
        k, n = _full_shape(self.k, self.n)
        if (not isinstance(self.data, np.ndarray) or self.data.dtype != np.uint8
                or self.data.ndim != 1 or not self.data.flags.c_contiguous):
            raise ValueError("upstream weights require a flat C-contiguous uint8 ndarray")
        if self.data.nbytes != upstream_weight_bytes(k, n):
            raise ValueError("upstream weight byte count does not match full source K/N")
        object.__setattr__(self, "k", k)
        object.__setattr__(self, "n", n)

    @property
    def nbytes(self):
        return self.data.nbytes

    def tile_offset(self, k_group, n64_tile):
        return weight_tile_offset(self.k, self.n, k_group, n64_tile)

    def validate_slice(self, k_start, n_start, k, n):
        """Validate a logical slice; N32 halves still reference full N64 tiles."""
        k_start, n_start = (_integer(k_start, "K start"),
                            _integer(n_start, "N start"))
        k, n = _integer(k, "slice K", 1), _integer(n, "slice N", 1)
        if k_start % 128 or k % 128 or n_start % 32 or n % 32:
            raise ValueError("weight slices require K128 and N32 alignment")
        if k_start + k > self.k or n_start + n > self.n:
            raise ValueError("weight slice lies outside the full source shape")
