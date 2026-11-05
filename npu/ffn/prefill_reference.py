"""Compact tiled host ABI and NumPy oracle for the prefill W4A16 kernel.

Logical inputs: A[M,K], unsigned-int4 W[N,K], metadata[N,K/128].
Host buffers contain A[Mb,Kb,2048], W[Nb,Kb,2144], C[Mb,Nb,512].
No host activation/weight tile is replicated for another output tile.
The graph repeats DMA reads in mblock, nblock, kblock order.

Within each 16x128 A tile: [m_micro=4,k_micro=16,mi=4,ki=8].
Within each 128x32 W tile: uint4 [k_micro=16,n_micro=4,ki=8,ni=8],
packed low-even/high-odd along ni, then BF16 scales[32], uint8 zeros[32].
Within each 16x32 C tile: [m_micro=4,n_micro=4,mi=4,ni=8].
BF16 arrays are represented as uint16 bits so host tests need only NumPy.
"""

from numbers import Integral

import numpy as np

from reference import W4A16, bf16, pack_int4, unpack_int4


TILE_M, TILE_K, TILE_N = 16, 128, 32
A_TILE_ELEMENTS, C_TILE_ELEMENTS = 2048, 512
WEIGHT_TILE_BYTES = 2144
LAYOUT_VERSION = "prefill_m16_k128_n32_mmul4x8x8_v1"


def validate_shape(m, k, n):
    for value, multiple, name in ((m, TILE_M, "M"), (k, TILE_K, "K"), (n, TILE_N, "N")):
        if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0 or value % multiple:
            raise ValueError(f"{name} must be a positive multiple of {multiple}")
    return m // TILE_M, k // TILE_K, n // TILE_N


def bf16_bits(values):
    return (bf16(values).view(np.uint32) >> 16).astype("<u2")


def bf16_from_bits(bits):
    bits = np.asarray(bits)
    if bits.dtype.kind != "u" or bits.dtype.itemsize != 2:
        raise ValueError("BF16 bit arrays must use uint16")
    return (bits.astype(np.uint32) << 16).view(np.float32)


def pack_activations(x):
    """Return flat BF16 uint16 bits, compact across output-channel blocks."""
    x = np.asarray(x, dtype=np.float32)
    if x.ndim != 2 or not np.all(np.isfinite(x)):
        raise ValueError("A must be a finite two-dimensional matrix")
    m, k = x.shape
    mb, kb, _ = validate_shape(m, k, TILE_N)
    tiles = bf16_bits(x).reshape(mb, TILE_M, kb, TILE_K).transpose(0, 2, 1, 3)
    return np.ascontiguousarray(tiles.reshape(mb, kb, 4, 4, 16, 8).transpose(0, 1, 2, 4, 3, 5)).reshape(-1)


def unpack_activations(packed, m, k):
    mb, kb, _ = validate_shape(m, k, TILE_N)
    packed = np.asarray(packed)
    if packed.shape != (m * k,):
        raise ValueError("activation buffer has the wrong shape")
    logical = packed.reshape(mb, kb, 4, 16, 4, 8).transpose(0, 2, 4, 1, 3, 5).reshape(m, k)
    return bf16_from_bits(logical)


def pack_weights(weight):
    """Return compact uint8 W[Nb,Kb,2144], with one metadata group per tile."""
    n, k = weight.shape
    _, kb, nb = validate_shape(TILE_M, k, n)
    if weight.group_size != TILE_K:
        raise ValueError("prefill weights require group_size=128")
    q = unpack_int4(weight.packed)
    result = np.empty((nb, kb, WEIGHT_TILE_BYTES), dtype=np.uint8)
    scale_bits = bf16_bits(weight.scales)
    for ni in range(nb):
        ns = slice(ni * TILE_N, (ni + 1) * TILE_N)
        for ki in range(kb):
            ks = slice(ki * TILE_K, (ki + 1) * TILE_K)
            native = q[ns, ks].T.reshape(16, 8, 4, 8).transpose(0, 2, 1, 3)
            packed_q = native[..., 0::2] | (native[..., 1::2] << 4)
            result[ni, ki, :2048] = packed_q.reshape(-1)
            result[ni, ki, 2048:2112] = np.ascontiguousarray(scale_bits[ns, ki]).view(np.uint8)
            result[ni, ki, 2112:] = weight.zeros[ns, ki].astype(np.uint8)
    return result.reshape(-1)


def unpack_weights(packed, k, n):
    _, kb, nb = validate_shape(TILE_M, k, n)
    packed = np.asarray(packed)
    if packed.dtype != np.uint8 or packed.shape != (nb * kb * WEIGHT_TILE_BYTES,):
        raise ValueError("weight buffer has the wrong dtype or shape")
    tiles = packed.reshape(nb, kb, WEIGHT_TILE_BYTES)
    q = np.empty((n, k), dtype=np.uint8)
    scales, zeros = np.empty((n, kb), np.float32), np.empty((n, kb), np.uint8)
    for ni in range(nb):
        ns = slice(ni * TILE_N, (ni + 1) * TILE_N)
        for ki in range(kb):
            ks = slice(ki * TILE_K, (ki + 1) * TILE_K)
            src = tiles[ni, ki, :2048].reshape(16, 4, 8, 4)
            native = np.empty((16, 4, 8, 8), dtype=np.uint8)
            native[..., 0::2], native[..., 1::2] = src & 15, src >> 4
            q[ns, ks] = native.transpose(0, 2, 1, 3).reshape(TILE_K, TILE_N).T
            scales[ns, ki] = bf16_from_bits(tiles[ni, ki, 2048:2112].copy().view("<u2"))
            zeros[ns, ki] = tiles[ni, ki, 2112:]
    return W4A16(pack_int4(q), scales, zeros, TILE_K)


def pack_output(y):
    y = np.asarray(y, dtype=np.float32)
    if y.ndim != 2:
        raise ValueError("C must be a matrix")
    m, n = y.shape
    mb, _, nb = validate_shape(m, TILE_K, n)
    tiles = bf16_bits(y).reshape(mb, TILE_M, nb, TILE_N).transpose(0, 2, 1, 3)
    return np.ascontiguousarray(tiles.reshape(mb, nb, 4, 4, 4, 8).transpose(0, 1, 2, 4, 3, 5)).reshape(-1)


def unpack_output(packed, m, n):
    mb, _, nb = validate_shape(m, TILE_K, n)
    packed = np.asarray(packed)
    if packed.shape != (m * n,):
        raise ValueError("output buffer has the wrong shape")
    logical = packed.reshape(mb, nb, 4, 4, 4, 8).transpose(0, 2, 4, 1, 3, 5).reshape(m, n)
    return bf16_from_bits(logical)


def projection_reference(x, weight):
    """BF16 input/dequantized weight, FP32 accumulation, BF16 final output.

    This is a numerical oracle, not an emulation of AIE2P BFP16 hardware.
    There is no intermediate BF16 rounding between K=128 blocks.
    """
    x = np.asarray(x, dtype=np.float32)
    if x.ndim != 2 or x.shape[1] != weight.shape[1]:
        raise ValueError("input and weight dimensions do not match")
    return bf16(bf16(x) @ weight.dequantize(True).T)


def tiled_reference(a_packed, w_packed, m, k, n):
    """Execute the stream ABI with FP32 accumulation across every K tile."""
    _, kb, _ = validate_shape(m, k, n)
    x = unpack_activations(a_packed, m, k)
    weights = unpack_weights(w_packed, k, n).dequantize(True)
    result = np.zeros((m, n), np.float32)
    for ki in range(kb):
        ks = slice(ki * TILE_K, (ki + 1) * TILE_K)
        result += x[:, ks] @ weights[:, ks].T
    return pack_output(result)


def error_metrics(actual, expected, rtol=0.03, atol=0.05, l2_limit=0.02):
    """Check finite output, relative L2 error, and normalized maximum error.

    Maximum error uses the tensor's maximum reference magnitude, avoiding
    unstable elementwise relative errors near cancellation zeros. Exact-zero
    reference tensors require exact-zero output.
    """
    actual, expected = np.asarray(actual, np.float32), np.asarray(expected, np.float32)
    if actual.shape != expected.shape:
        raise ValueError("actual and expected shapes differ")
    if not np.all(np.isfinite(expected)):
        raise ValueError("reference output must be finite")
    finite = bool(np.all(np.isfinite(actual)))
    if not finite:
        return {"correctness": "failed", "finite": False, "max_abs_error": None,
                "relative_l2_error": None, "rms_error": None}
    delta = actual.astype(np.float64) - expected.astype(np.float64)
    norm = float(np.linalg.norm(expected.astype(np.float64)))
    max_error = float(np.max(np.abs(delta)))
    max_ref = float(np.max(np.abs(expected)))
    relative_l2 = float(np.linalg.norm(delta) / norm) if norm else (0.0 if max_error == 0 else None)
    passed = max_error == 0 if norm == 0 else (relative_l2 <= l2_limit and max_error <= atol + rtol * max_ref)
    return {"correctness": "passed" if passed else "failed", "finite": True,
            "max_abs_error": max_error, "relative_l2_error": relative_l2,
            "rms_error": float(np.sqrt(np.mean(delta * delta))), "reference_max_abs": max_ref,
            "max_error_limit": atol + rtol * max_ref,
            "elementwise_close_fraction": float(np.mean(np.isclose(actual, expected, rtol=rtol, atol=atol)))}
