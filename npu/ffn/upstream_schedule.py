"""Direct reads from glassescrab's striped N64/K128 packed weight buffers.

The existing A/Y layouts are retained. Adjacent N32 halves owned by one
worker share one A/W acquisition and separate FP32 partial buffers. Only a
column ownership boundary can cause two columns to read the same N64 tile.
"""
from dataclasses import dataclass, replace

from prefill_schedule import TapSpec, plan_prefill
from prefill_swiglu_schedule import (plan_swiglu, swiglu_logical_column,
                                     swiglu_output_tap)
from upstream_weights import upstream_weight_bytes, weight_tile_offset


@dataclass(frozen=True)
class WeightSegment:
    first_local_tile: int
    n64_tile: int
    halves: tuple


@dataclass(frozen=True)
class SegmentPipelineAction:
    kind: str
    group: int
    segment: int


def validate_segment_pipeline_depth(depth):
    if isinstance(depth, bool) or not isinstance(depth, int) or depth not in (1, 2):
        raise ValueError('segment_pipeline_depth must be 1 or 2')
    return depth


def validate_activation_fifo_depth(depth):
    if isinstance(depth, bool) or not isinstance(depth, int) or depth not in (1, 2):
        raise ValueError('activation_fifo_depth must be 1 or 2')
    return depth


def validate_input_layout(input_layout):
    if input_layout not in ('compact', 'row_major'):
        raise ValueError('input_layout must be compact or row_major')
    return input_layout


def validate_kernel_tuning(vector_zero, mmul_m_reuse, arithmetic='bf16'):
    if arithmetic not in ('bf16', 'bfp16'):
        raise ValueError('arithmetic must be bf16 or bfp16')
    if not isinstance(vector_zero, bool):
        raise ValueError('vector_zero must be a bool')
    if (isinstance(mmul_m_reuse, bool) or not isinstance(mmul_m_reuse, int)
            or mmul_m_reuse not in (1, 2)):
        raise ValueError('mmul_m_reuse must be 1 or 2')
    if arithmetic == 'bfp16' and mmul_m_reuse != 1:
        raise ValueError('bfp16 requires mmul_m_reuse=1')


def upstream_worker_stack_size(mmul_m_reuse, arithmetic='bf16'):
    """Keep native stacks and reserve 4 KiB for explicit BFP16 arithmetic.

    The paired-M kernel's full model core has 2,112 bytes across nested
    frames, exceeding the original 2 KiB reservation. Keep that reservation
    for the baseline kernel and use 4 KiB for the paired-M ablation. BFP16
    also reserves 4 KiB; its actual allocation still needs compiler checks.
    """
    validate_kernel_tuning(False, mmul_m_reuse, arithmetic)
    return 4096 if arithmetic == 'bfp16' or mmul_m_reuse == 2 else 2048


def validate_upstream_buffering(schedule, activation_fifo_depth):
    """Reject the known oversized reuse-four core-buffer configuration.

    Projection reuse four needs 76,288 raw bytes with depth-two A buffers,
    or 59,904 with depth-one consumers, including the baseline 2 KiB stack.
    A paired-M or BFP16 4 KiB stack raises the latter to 61,952 bytes.
    Actual compiler placement/spills still need build and hardware checks.
    Host and memory-tile A buffers remain double-buffered in either case.
    """
    depth = validate_activation_fifo_depth(activation_fifo_depth)
    if schedule.base.m_reuse == 4 and depth != 1:
        raise ValueError('effective M reuse 4 requires activation_fifo_depth=1')


def segment_pipeline_actions(schedule, segment_pipeline_depth=2):
    """Submit at most two segments, finishing the oldest before the next.

    Segment order stays identical on every A/W/Y channel, including the
    transition between M waves. A segment is retired only after all of its
    output drains complete, which also proves its A/W transfers completed.
    The current graph has one transfer per channel per segment: depth two
    therefore uses at most two queue entries per channel and six live shim
    BDs (A, W, Y), below AIE2's four-entry queues and sixteen-BD shim limit.
    Depth one retains the serial control. This is a logical schedule; the
    MLIR compiler and device still have to verify/execute its lowering.
    """
    depth = validate_segment_pipeline_depth(segment_pipeline_depth)
    pending, actions = [], []
    for group in range(schedule.base.groups_per_column):
        for segment in range(schedule.segment_count):
            if len(pending) == depth:
                old_group, old_segment = pending.pop(0)
                actions.append(SegmentPipelineAction('finish', old_group, old_segment))
            actions.append(SegmentPipelineAction('submit', group, segment))
            pending.append((group, segment))
    actions.extend(SegmentPipelineAction('finish', group, segment)
                   for group, segment in pending)
    return tuple(actions)


@dataclass(frozen=True)
class UpstreamSchedule:
    base: object
    mode: str
    n: int
    weight_k: int
    weight_n: int
    k_start: int
    n_start: int
    segments: tuple

    @property
    def weight_bytes(self):
        return upstream_weight_bytes(self.weight_k, self.weight_n)

    @property
    def segment_count(self):
        return len(self.segments[0])

    def logical_column(self, col):
        return swiglu_logical_column(col) if self.mode == 'swiglu' else col

    def weight_tap(self, col, segment):
        item = self.segments[col][segment]
        offset = weight_tile_offset(self.weight_k, self.weight_n,
                                   self.k_start // 128, item.n64_tile)
        # K128 payloads belonging to a given N64 tile are contiguous even
        # when only a K slice of the full packed weight matrix is selected.
        return TapSpec(self.weight_bytes, offset,
                       (1, 1, 1, self.base.kb * 4352), (0, 0, 0, 1))

    def activation_tap(self, lane, group, input_layout='compact'):
        validate_input_layout(input_layout)
        col = (lane // 4) * self.base.n_columns
        tap = self.base.activation_tap(col, lane % 4, group)
        if input_layout == 'row_major':
            # Each shim object is [reuse*16 rows, 128 K values]. Its source
            # rows retain the full logical K stride. The memory-tile stream
            # permutation below restores exactly the existing core A ABI.
            return replace(tap, sizes=(1, self.base.kb, self.base.m_reuse * 16, 128),
                           strides=(0, 128, self.base.k, 1))
        return replace(tap, sizes=(1, *tap.sizes[1:]))

    def activation_dims_to_stream(self, input_layout='compact'):
        validate_input_layout(input_layout)
        if input_layout == 'compact':
            return self.base.activation_dims_to_stream
        # Row-major [R*16,128] -> native [R*4,16,4,8]. Strides refer to
        # BF16 elements within one unchanged R*2048-element FIFO object.
        # Four dimensions fit the AIE2 memory-tile DMA addressing limit.
        return ((self.base.m_reuse * 4, 512), (16, 8), (4, 128), (8, 1))

    def output_tap(self, col, group, segment):
        tap = (swiglu_output_tap(self.base, col, group) if self.mode == 'swiglu'
               else self.base.output_tap(col, group))
        item = self.segments[col][segment]
        return replace(tap, offset=tap.offset + item.first_local_tile * 512,
                       sizes=(1, len(item.halves), *tap.sizes[2:]))


def plan_upstream(m, k, n, *, mode='projection', weight_k=None, weight_n=None,
                  k_start=0, n_start=0, columns=8, max_reuse=2):
    if mode not in ('projection', 'swiglu'):
        raise ValueError('mode must be projection or swiglu')
    if (isinstance(max_reuse, bool) or not isinstance(max_reuse, int)
            or max_reuse not in (1, 2, 4)):
        raise ValueError('direct upstream weights support max_reuse 1, 2 or 4')
    if mode == 'swiglu' and max_reuse == 4:
        raise ValueError('SwiGLU reuse 4 exceeds the current core-buffer budget')
    base = (plan_swiglu(m, k, n, columns=columns, max_reuse=max_reuse)
            if mode == 'swiglu' else
            plan_prefill(m, k, n, columns=columns, max_reuse=max_reuse))
    weight_k = k if weight_k is None else weight_k
    weight_n = n if weight_n is None else weight_n
    upstream_weight_bytes(weight_k, weight_n)
    for value, name, align in ((k_start, 'k_start', 128), (n_start, 'n_start', 32)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value % align:
            raise ValueError(f'{name} must be a nonnegative multiple of {align}')
    if k_start + k > weight_k or n_start + n > weight_n:
        raise ValueError('selected projection leaves the full upstream weight buffer')
    segments = []
    for physical in range(8):
        logical = swiglu_logical_column(physical) if mode == 'swiglu' else physical
        first = base.n_start(logical) % (n // 32)
        col_segments = []
        local = 0
        while local < base.local_nb:
            absolute = n_start // 32 + first + local
            halves = (0, 1) if absolute % 2 == 0 and local + 1 < base.local_nb else (absolute % 2,)
            col_segments.append(WeightSegment(local, absolute // 2, halves))
            local += len(halves)
        segments.append(tuple(col_segments))
    if len({len(items) for items in segments}) != 1:
        raise ValueError('all multicast columns must consume the same number of A tiles')
    return UpstreamSchedule(base, mode, n, weight_k, weight_n, k_start,
                            n_start, tuple(segments))
