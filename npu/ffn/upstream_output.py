"""DMA-only output permutations from selected native BF16 output tiles.

SwiGLU can scatter directly into the down projection's compact A layout.
Projection outputs can instead leave the memory-tile join in row-major order
and scatter directly into a row-major host matrix. Weights, BF16 bits, worker
buffers and the number of runtime tasks are unchanged.
The explicit native8 mode follows its 8x8 output ABI; the default is 4x8.
"""

from numbers import Integral

from prefill_schedule import TapSpec
from upstream_schedule import validate_bfp16_native_layout


def upstream_row_major_dims_to_stream(direct, bfp16_native_layout=False):
    """Permute one joined participant's C tile, not the entire joined object.

    Default C is [M16 tile, mm4, nm4, mi4, ni8]. Each worker's output becomes
    [M16 tile, mm4, mi4, nm4, ni8], or [16*reuse rows, 32 columns]. The four
    memory-tile join BDs apply these same dimensions to their own worker
    slices; the compiler adds each slice's offset independently. Walking
    across all four workers here would exceed the join verifier's bound.

    This is a logical four-dimensional layout in BF16 elements. It leaves
    adjacent BF16 pairs intact and needs no additional FIFO storage.
    Native8 instead has two M8 blocks per M16 tile and 64-value C blocks.
    """
    if direct.mode != 'projection':
        raise ValueError('row-major output layout is only supported for projection')
    if validate_bfp16_native_layout(bfp16_native_layout):
        # Native8 C [R*2,nm4,mi8,ni8] -> [R*2,mi8,nm4,ni8].
        return ((direct.base.m_reuse * 2, 256), (8, 8), (4, 64), (8, 1))
    return ((direct.base.m_reuse * 4, 128), (4, 8), (4, 32), (8, 1))


def upstream_row_major_output_tap(direct, col, group, segment):
    """Scatter a row-major stream of one/two N32 halves into host [M,N].

    This tap must be paired with ``upstream_row_major_dims_to_stream`` on
    the joined output FIFO. Each half contains four contiguous worker row
    slices. Source-weight N offsets affect ownership, but output coordinates
    always start at zero in the selected logical projection.
    """
    if direct.mode != 'projection':
        raise ValueError('row-major output layout is only supported for projection')
    if (isinstance(segment, bool) or not isinstance(segment, Integral)
            or not 0 <= segment < direct.segment_count):
        raise ValueError('segment must lie within the direct upstream schedule')
    plan = direct.base
    m_start = plan.group_m_start(col, group)
    item = direct.segments[int(col)][int(segment)]
    count = len(item.halves)
    if count not in (1, 2):
        raise ValueError('a direct upstream segment must contain one or two N32 halves')
    local_nt = plan.n_start(col) + item.first_local_tile
    if local_nt + count > direct.n // 32:
        raise ValueError('segment output leaves the selected projection')
    return TapSpec(plan.m * direct.n, m_start * 16 * direct.n + local_nt * 32,
                   (1, count, plan.compute_rows * plan.m_reuse * 16, 32),
                   (0, 32, direct.n, 1))


def upstream_down_activation_tap(direct, col, group, segment, bfp16_native_layout=False):
    """Return one four-dimensional scatter for a SwiGLU segment.

    The joined worker stream is [N32 half, M16 tile, mm4, 128 values].
    The last 128 values already have the down-A [km4, mi4, ki8] order.
    Four adjacent N32 tiles occupy one K128 tile. A segment has at most two
    halves, so even a pair crossing that K128 boundary has one constant
    N-axis stride (1664 instead of 128). This also supports source N offsets
    that are only N32 aligned; no extra source-buffer alignment is assumed.
    With native8, the contiguous blocks hold 256 values and two M8 blocks
    use a 1024-element stride. Both endpoints then use the native8 ABI.

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

    native8 = validate_bfp16_native_layout(bfp16_native_layout)
    row_blocks = 2 if native8 else 4
    block_elements = 256 if native8 else 128

    def channel_offset(nt):
        return (nt // 4) * 2048 + (nt % 4) * block_elements

    m_stride = (direct.n // 128) * 2048
    n_stride = channel_offset(local_nt + 1) - channel_offset(local_nt) if count == 2 else 0
    return TapSpec(plan.m * direct.n,
                   m_start * m_stride + channel_offset(local_nt),
                   (count, plan.compute_rows * plan.m_reuse, row_blocks, block_elements),
                   (n_stride, m_stride, 2048 // row_blocks, 1))
