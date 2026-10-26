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

    def activation_tap(self, lane, group):
        col = (lane // 4) * self.base.n_columns
        tap = self.base.activation_tap(col, lane % 4, group)
        return replace(tap, sizes=(1, *tap.sizes[1:]))

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
    if isinstance(max_reuse, bool) or max_reuse not in (1, 2):
        raise ValueError('direct upstream weights support max_reuse 1 or 2')
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
