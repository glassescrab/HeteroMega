"""DMA-only SwiGLU output permutation into the down projection's A layout.

Workers still emit native C tiles. This changes only the shim scatter: each
N32 half is placed directly in the existing compact K128 activation layout.
Weights, BF16 bits, worker buffers and the number of runtime tasks are unchanged.
"""

from numbers import Integral

from prefill_schedule import TapSpec


def upstream_down_activation_tap(direct, col, group, segment):
    """Return one four-dimensional scatter for a SwiGLU segment.

    The joined worker stream is [N32 half, M16 tile, mm4, 128 values].
    The last 128 values already have the down-A [km4, mi4, ki8] order.
    Four adjacent N32 tiles occupy one K128 tile. A segment has at most two
    halves, so even a pair crossing that K128 boundary has one constant
    N-axis stride (1664 instead of 128). This also supports source N offsets
    that are only N32 aligned; no extra source-buffer alignment is assumed.

    This is a logical address plan. The graph compiler must still validate
    the target DMA encoding and hardware runs must validate completion.
    """
    if direct.mode != 'swiglu':
        raise ValueError('down-A output layout is only supported for SwiGLU')
    if (isinstance(col, bool) or not isinstance(col, Integral)
            or not 0 <= col < 8 or col % 2 != 1):
        raise ValueError('only odd SwiGLU output columns can drain down-A tiles')
    if (isinstance(segment, bool) or not isinstance(segment, Integral)
            or not 0 <= segment < direct.segment_count):
        raise ValueError('segment must lie within the direct upstream schedule')
    plan = direct.base
    logical = direct.logical_column(int(col))
    m_start = plan.group_m_start(logical, group)
    item = direct.segments[int(col)][int(segment)]
    count = len(item.halves)
    if count not in (1, 2):
        raise ValueError('a direct upstream segment must contain one or two N32 halves')
    n_tiles = direct.n // 32
    local_nt = plan.n_start(logical) % n_tiles + item.first_local_tile
    if local_nt + count > n_tiles:
        raise ValueError('segment output leaves the selected FFN channel slice')

    def channel_offset(nt):
        return (nt // 4) * 2048 + (nt % 4) * 128

    m_stride = (direct.n // 128) * 2048
    n_stride = channel_offset(local_nt + 1) - channel_offset(local_nt) if count == 2 else 0
    return TapSpec(plan.m * direct.n,
                   m_start * m_stride + channel_offset(local_nt),
                   (count, plan.compute_rows * plan.m_reuse, 4, 128),
                   (n_stride, m_stride, 512, 1))
