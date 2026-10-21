"""CPU check of the W4A16 tile layout and the FFN channel split. Needs only numpy.

It packs weights the same way as src/pack_w4a16.cpp (a port of HeteroMosaic
_pack_weights_packed), then reads them back with the same addressing as
HeteroMosaic w4a16_gemv_kernel_packed. It checks:

1. packed GEMV == dense matmul (full matrix, N-slice, K-slice, gate|up concat);
2. HeteroMosaic GEMV start_col addressing on a full matrix;
3. FFN split: Y_G + Y_N == full FFN for several split points;
4. slices are tiles of the full packed buffers, so a load-time split needs no AWQ tensors.

Run: python3 kernels/gpu/tools/check_packing.py
"""

import numpy as np

TILE_K, TILE_N, TILE_BYTES = 128, 64, 4352
rng = np.random.default_rng(0)


def to_bf16_bits(x):
    u = np.asarray(x, np.float32).view(np.uint32).astype(np.uint64)
    return ((u + 0x7FFF + ((u >> 16) & 1)) >> 16).astype(np.uint16)


def from_bf16_bits(b):
    return (b.astype(np.uint32) << 16).view(np.float32)


def random_quant(k, n):
    q = rng.integers(0, 16, (k, n), dtype=np.uint8)
    s = to_bf16_bits(rng.uniform(0.002, 0.02, (k // TILE_K, n)))
    z = rng.integers(6, 10, (k // TILE_K, n), dtype=np.int8)
    return q, s, z


def dequant(q, s, z):
    zs = np.repeat(z.astype(np.float64), TILE_K, axis=0)
    ss = np.repeat(from_bf16_bits(s).astype(np.float64), TILE_K, axis=0)
    return (q.astype(np.float64) - zs) * ss


# Byte b of a tile holds row ROW[b], columns COL_LO[b] (low nibble) and COL_LO[b] + 1 (high nibble).
_a, _c, _b, _j = np.meshgrid(np.arange(16), np.arange(8), np.arange(8), np.arange(4), indexing="ij")
_order = ((_a * 8 + _c) * 8 + _b) * 4 + _j
ROW = np.empty(4096, np.int64)
COL_LO = np.empty(4096, np.int64)
ROW[_order.ravel()] = (_a * 8 + _b).ravel()
COL_LO[_order.ravel()] = (_c * 8 + 2 * _j).ravel()
ZERO_POS = (np.arange(64) // 8) * 16 + np.arange(64) % 8


def pack(q, s, z):
    k, n = q.shape
    assert k % TILE_K == 0 and n % TILE_N == 0
    tiles_k, tiles_n = k // TILE_K, n // TILE_N
    out = np.empty((tiles_k * tiles_n, TILE_BYTES), np.uint8)
    t = 0
    for g in range(8):
        for c in range(g, tiles_n, 8):
            for r in range(tiles_k):
                blk = q[r * 128:(r + 1) * 128, c * 64:(c + 1) * 64]
                out[t, :4096] = (blk[ROW, COL_LO] & 0xF) | ((blk[ROW, COL_LO + 1] & 0xF) << 4)
                out[t, 4096:4224] = s[r, c * 64:(c + 1) * 64].view(np.uint8)
                zr = z[r, c * 64:(c + 1) * 64].view(np.uint8)
                out[t, 4224 + ZERO_POS] = zr
                out[t, 4224 + ZERO_POS + 8] = zr
                t += 1
    return out.ravel()


def pack_heteromosaic_literal(qw, s, z):
    """Line-by-line numpy translation of HeteroMosaic _pack_weights_packed (no padding)."""
    k, n = qw.shape
    scale_flat, zero_flat = s.reshape(-1), z.reshape(-1)
    num_scales = scale_flat.size
    group_size = k * n // num_scales
    ntr, ntc = k // 128, n // 64
    w_tiles = qw.reshape(ntr, 128, ntc, 64).transpose(0, 2, 1, 3).reshape(-1, 128, 64)
    idx = np.array([r * ntc + c for cm in range(8) for c in range(cm, ntc, 8) for r in range(ntr)])
    w_perm = w_tiles[idx].reshape(len(idx), 16, 8, 8, 8).transpose(0, 1, 3, 2, 4)
    packed_w = ((w_perm[..., 0::2] & 0xF) | ((w_perm[..., 1::2] & 0xF) << 4)).astype(np.uint8).reshape(-1, 4096)
    cols = (idx % ntc)[:, None] * 64 + np.arange(64)
    group_idx = ((idx // ntc)[:, None] * 128) // group_size
    sidx = np.clip(group_idx * n + cols, 0, num_scales - 1).ravel()
    scales_u8 = scale_flat[sidx].reshape(-1, 64).view(np.uint8).reshape(-1, 128)
    zeros_dup = np.repeat(zero_flat[sidx].reshape(-1, 64).view(np.uint8).reshape(-1, 8, 8), 2, axis=1).reshape(-1, 128)
    return np.concatenate([packed_w, scales_u8, zeros_dup], 1).ravel()


def gemv_packed(packed, x, k, n_work, total_n=None, start_col=0):
    """Same addressing as HeteroMosaic w4a16_gemv_kernel_packed, math in float64."""
    total_n = n_work if total_n is None else total_n
    tiles_k, tiles_n, start_tile = k // TILE_K, (total_n + 63) // 64, start_col // 64
    tiles = packed.reshape(-1, TILE_BYTES)
    y = np.zeros(n_work)
    for bx in range(n_work // 64):
        abs_bx = bx + start_tile
        col_group, col_offset = abs_bx % 8, abs_bx // 8
        tbg = sum(((tiles_n + 7 - g) // 8) * tiles_k for g in range(col_group))
        base_z = tbg + col_offset * tiles_k
        acc = np.zeros(64)
        for kt in range(tiles_k):
            tile = tiles[base_z + kt]
            w = np.empty((128, 64))
            w[ROW, COL_LO] = tile[:4096] & 0xF
            w[ROW, COL_LO + 1] = tile[:4096] >> 4
            scale = from_bf16_bits(tile[4096:4224].view(np.uint16)).astype(np.float64)
            zero = tile[4224 + ZERO_POS].view(np.int8).astype(np.float64)
            acc += x[kt * 128:(kt + 1) * 128] @ ((w - zero) * scale)
        y[bx * 64:(bx + 1) * 64] = acc
    return y


def silu(v):
    return v / (1.0 + np.exp(-v))


def check(name, got, ref, tol=1e-10):
    err = np.abs(got - ref).max() / (np.abs(ref).max() + 1e-30)
    status = "PASS" if err <= tol else "FAIL"
    print(f"{name:<44} {status}  max_rel={err:.1e}")
    return err <= tol


def packed_order(n, k):
    """(tile column, tile row) of each tile, in packed order."""
    return [(c, r) for g in range(8) for c in range(g, n // TILE_N, 8) for r in range(k // TILE_K)]


def report(name, same):
    print(f"{name:<44} {'PASS' if same else 'FAIL'}")
    return same


def check_tile_selection():
    """With s % 512 == 0 (docs/weight-layout.md §4):
    - N-slice [s, N) and K-slice [s, K): the full buffer's tiles under a mask, in the same order;
    - gate|up slice: a permutation of tiles from the two full buffers.
    """
    ok = True
    k, n, s = 256, 2048, 512
    gq, gs, gz = random_quant(k, n)
    uq, us, uz = random_quant(k, n)
    full_g = pack(gq, gs, gz).reshape(-1, TILE_BYTES)
    full_u = pack(uq, us, uz).reshape(-1, TILE_BYTES)
    pos = {t: i for i, t in enumerate(packed_order(n, k))}

    sel = [pos[(c + s // TILE_N, r)] for c, r in packed_order(n - s, k)]
    got = pack(gq[:, s:], gs[:, s:], gz[:, s:]).reshape(-1, TILE_BYTES)
    ok &= report("N-slice [512, N) == full tiles under a mask", np.array_equal(got, full_g[sel]) and sel == sorted(sel))

    m = n - s
    src = [full_g[pos[(c + s // TILE_N, r)]] if c < m // TILE_N else full_u[pos[(c - m // TILE_N + s // TILE_N, r)]]
           for c, r in packed_order(2 * m, k)]
    got = pack(np.concatenate([gq[:, s:], uq[:, s:]], 1), np.concatenate([gs[:, s:], us[:, s:]], 1),
               np.concatenate([gz[:, s:], uz[:, s:]], 1)).reshape(-1, TILE_BYTES)
    ok &= report("gate|up slice == permuted full tiles", np.array_equal(got, np.stack(src)))

    kd, nd = 1024, 512
    dq, ds, dz = random_quant(kd, nd)
    full_d = pack(dq, ds, dz).reshape(-1, TILE_BYTES)
    pos_d = {t: i for i, t in enumerate(packed_order(nd, kd))}
    sel = [pos_d[(c, r + s // TILE_K)] for c, r in packed_order(nd, kd - s)]
    got = pack(dq[s:], ds[s // TILE_K:], dz[s // TILE_K:]).reshape(-1, TILE_BYTES)
    ok &= report("K-slice [512, K) == full tiles under a mask", np.array_equal(got, full_d[sel]) and sel == sorted(sel))
    return ok


def main():
    ok = True
    k, n = 512, 1024
    q, s, z = random_quant(k, n)
    w = dequant(q, s, z)
    x = rng.standard_normal(k)
    y = x @ w
    same = np.array_equal(pack(q, s, z), pack_heteromosaic_literal(q, s, z))
    print(f"{'pack() bytes == HeteroMosaic packer':<44} {'PASS' if same else 'FAIL'}")
    ok &= same
    ok &= check("full matrix", gemv_packed(pack(q, s, z), x, k, n), y)

    b, e = 192, 832  # 10 tile columns: not a multiple of 8
    ok &= check("N-slice [192, 832) packed alone", gemv_packed(pack(q[:, b:e], s[:, b:e], z[:, b:e]), x, k, e - b), y[b:e])
    ok &= check("N-slice via start_col on full pack", gemv_packed(pack(q, s, z), x, k, e - b, total_n=n, start_col=b), y[b:e])

    kb, ke = 128, 384
    gk = slice(kb // TILE_K, ke // TILE_K)
    part = gemv_packed(pack(q[kb:ke], s[gk], z[gk]), x[kb:ke], ke - kb, n)
    ok &= check("K-slice [128, 384) packed alone", part, x[kb:ke] @ w[kb:ke])

    # FFN split with Llama shape ratios (H x 3.5H), scaled down for speed.
    h, inter = 512, 1792
    gq, gs, gz = random_quant(h, inter)
    uq, us, uz = random_quant(h, inter)
    dq, ds, dz = random_quant(inter, h)
    wg, wu, wd = dequant(gq, gs, gz), dequant(uq, us, uz), dequant(dq, ds, dz)
    xn = 0.5 * rng.standard_normal(h)
    y_full = (silu(xn @ wg) * (xn @ wu)) @ wd

    def slice_forward(b, e):
        gu = pack(np.concatenate([gq[:, b:e], uq[:, b:e]], 1),
                  np.concatenate([gs[:, b:e], us[:, b:e]], 1),
                  np.concatenate([gz[:, b:e], uz[:, b:e]], 1))
        g_u = gemv_packed(gu, xn, h, 2 * (e - b))
        act = silu(g_u[:e - b]) * g_u[e - b:]
        grp = slice(b // TILE_K, e // TILE_K)
        return gemv_packed(pack(dq[b:e], ds[grp], dz[grp]), act, e - b, h)

    for split in (512, 1024, 1280):
        y_split = slice_forward(0, split) + slice_forward(split, inter)
        ok &= check(f"FFN split s={split}: Y_G + Y_N == full", y_split, y_full)

    ok &= check_tile_selection()

    print("ALL PASS" if ok else "SOME CHECKS FAILED")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
