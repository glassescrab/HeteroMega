"""CPU-only schedule for eight columns and four compute rows per column.

The compact host ABI remains A[Mb,Kb,2048], W[Nb,Kb,2144], C[Mb,Nb,512].
N tiles partition columns; when only four N32 tiles exist, a second group of
four columns owns different M tiles. Four workers per column own interleaved
groups of contiguous M16 tiles. Within each K128 step a worker reuses one W
tile for ``m_reuse`` A tiles. No host input or weight replication is needed.

Tap dimensions/strides are in buffer elements (BF16 for A/C, bytes for W).
These are pure logical schedules, not proof that a device DMA encoding or
local-memory placement compiles. The graph compiler must check those limits.
The A shim sends 512-element quarters because the pinned AIE dialect checks
every DMA dimension against512, despite an error message referring to1023.
A memory-tile stream permutation restores each worker's native [reuse,2048]
A object before it reaches the compute core.
"""

from dataclasses import asdict, dataclass
import json
from math import gcd
from numbers import Integral

import numpy as np


TILE_M, TILE_K, TILE_N = 16, 128, 32
A_ELEMENTS, C_ELEMENTS, WEIGHT_BYTES = 2048, 512, 2144
SCHEDULE_VERSION = "prefill_array8_rows4_interleaved_m_v1"


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    return int(value)


@dataclass(frozen=True)
class TapSpec:
    """A logical four-dimensional gather/scatter over one compact host BO."""

    buffer_elements: int
    offset: int
    sizes: tuple
    strides: tuple

    @property
    def element_count(self):
        return int(np.prod(self.sizes))

    def indices(self):
        """Materialize offsets for CPU validation; graph construction needs no array."""
        addresses = np.full(self.sizes, self.offset, dtype=np.int64)
        for axis, (size, stride) in enumerate(zip(self.sizes, self.strides)):
            shape = [1] * len(self.sizes)
            shape[axis] = size
            addresses += np.arange(size, dtype=np.int64).reshape(shape) * stride
        result = addresses.reshape(-1)
        if result.size and (int(result.min()) < 0 or int(result.max()) >= self.buffer_elements):
            raise ValueError("tap addresses leave the compact host buffer")
        return result


@dataclass(frozen=True)
class WorkerSchedule:
    column: int
    row: int
    row_index: int
    m_column_group: int
    n_column: int
    n_tiles: tuple
    m_groups: tuple


@dataclass(frozen=True)
class PrefillSchedule:
    m: int
    k: int
    n: int
    columns: int
    compute_rows: int
    m_reuse: int
    n_columns: int
    m_column_groups: int
    groups_per_column: int
    workers: tuple

    @property
    def mb(self):
        return self.m // TILE_M

    @property
    def kb(self):
        return self.k // TILE_K

    @property
    def nb(self):
        return self.n // TILE_N

    @property
    def local_nb(self):
        return self.nb // self.n_columns

    @property
    def worker_count(self):
        return len(self.workers)

    @property
    def reuse(self):
        return self.m_reuse

    @property
    def activation_dims_to_stream(self):
        """Memory-tile permutation: shim [quarter,R,512] to core [R,quarter,512].

        Offsets refer to one R*2048-element A object. The shim's original
        2048-element inner dimension and a1024-element half both exceed the
        pinned dialect's512-element dimension bound. Splitting into quarters
        changes transfer order, so this permutation is required even though
        the compact host A ABI and core's expected A layout are unchanged.
        """
        return ((self.m_reuse, 512), (4, self.m_reuse * 512), (512, 1))

    def _column(self, column):
        column = _integer(column, "column")
        if not 0 <= column < self.columns:
            raise ValueError("column must lie within the eight-column array")
        return column

    def _group(self, group):
        group = _integer(group, "group")
        if not 0 <= group < self.groups_per_column:
            raise ValueError("group must lie within groups_per_column")
        return group

    def worker(self, column, row_index):
        column = self._column(column)
        row_index = _integer(row_index, "row_index")
        if not 0 <= row_index < self.compute_rows:
            raise ValueError("row_index must be 0..3 (physical compute rows 2..5)")
        return self.workers[column * self.compute_rows + row_index]

    def group_m_start(self, column, group):
        """First M16 tile of the contiguous four-row aggregate for this group."""
        column, group = self._column(column), self._group(group)
        m_column_group = column // self.n_columns
        return (m_column_group * (self.mb // self.m_column_groups)
                + group * self.compute_rows * self.m_reuse)

    def n_start(self, column):
        return (self._column(column) % self.n_columns) * self.local_nb

    def activation_tap(self, column, row_index, group):
        """One row shim stream: local N replay, K/quarter, reused M,512 elements.

        A row's stream can be broadcast horizontally to columns with the same
        m_column_group. N128 therefore uses two sets of four row streams;
        N256 and other widths divisible by256 use one set across all columns.
        """
        worker = self.worker(column, row_index)
        group = self._group(group)
        m_start = worker.m_groups[group][0]
        return TapSpec(self.m * self.k, m_start * self.kb * A_ELEMENTS,
                       (self.local_nb, self.kb * 4, self.m_reuse, A_ELEMENTS // 4),
                       (0, A_ELEMENTS // 4, self.kb * A_ELEMENTS, 1))

    def weight_tap(self, column):
        """One compact local-N/K stream, broadcast vertically to all four rows."""
        return TapSpec(self.nb * self.kb * WEIGHT_BYTES,
                       self.n_start(column) * self.kb * WEIGHT_BYTES,
                       (1, 1, 1, self.local_nb * self.kb * WEIGHT_BYTES),
                       (0, 0, 0, 1))

    def output_tap(self, column, group):
        """Scatter joined output stream [local N, row, reuse, native C elements]."""
        m_start = self.group_m_start(column, group)
        return TapSpec(self.m * self.n,
                       (m_start * self.nb + self.n_start(column)) * C_ELEMENTS,
                       (1, self.local_nb, self.compute_rows * self.m_reuse, C_ELEMENTS),
                       (0, C_ELEMENTS, self.nb * C_ELEMENTS, 1))

    def to_dict(self):
        """JSON-native provenance, stable after serialization and reloading."""
        result = asdict(self)
        result.update(schedule_version=SCHEDULE_VERSION, worker_count=self.worker_count,
                      tile_m=TILE_M, tile_k=TILE_K, tile_n=TILE_N,
                      host_weight_elements=self.nb * self.kb * WEIGHT_BYTES,
                      host_activation_elements=self.m * self.k,
                      host_output_elements=self.m * self.n,
                      local_n_tiles=self.local_nb,
                      activation_dims_to_stream=self.activation_dims_to_stream)
        return json.loads(json.dumps(result))


def plan_prefill(m, k, n, columns=8, rows=4, max_reuse=2):
    """Plan exactly 32 nonempty workers with automatic effective M reuse.

    M/K/N are multiples of128. The N-column factor is gcd(8,N/32), leaving
    one or two M-column groups while keeping every physical column active.
    Reuse is the largest of1/2/4 dividing each worker's total M tiles and not
    exceeding max_reuse. Default2 avoids assuming reuse4 fits core-local SRAM.
    """
    m, k, n, columns, rows, max_reuse = (
        _integer(value, name) for value, name in
        ((m, "M"), (k, "K"), (n, "N"), (columns, "columns"),
         (rows, "rows"), (max_reuse, "max_reuse")))
    for value, name in ((m, "M"), (k, "K"), (n, "N")):
        if value < 128 or value % 128:
            raise ValueError(f"{name} must be >=128 and divisible by128")
    if m > 4096 or k > 16384 or n > 16384:
        raise ValueError("geometry exceeds the existing M4096/K16384/N16384 source bounds")
    if columns != 8 or rows != 4:
        raise ValueError("this schedule requires exactly eight columns and four compute rows")
    if max_reuse not in (1, 2, 4):
        raise ValueError("max_reuse must be1,2,or4")
    mb, nb = m // TILE_M, n // TILE_N
    n_columns = gcd(columns, nb)
    m_column_groups = columns // n_columns
    if mb % (m_column_groups * rows):
        raise ValueError("M tiles must divide evenly across column groups and rows")
    per_worker_m = mb // (m_column_groups * rows)
    m_reuse = max(reuse for reuse in (1, 2, 4)
                  if reuse <= max_reuse and per_worker_m % reuse == 0)
    groups = per_worker_m // m_reuse
    local_nb = nb // n_columns
    if local_nb > 64:
        raise ValueError("local N tile count must be <=64 per N column")
    workers = []
    for column in range(columns):
        m_group, n_column = divmod(column, n_columns)
        n_tiles = tuple(range(n_column * local_nb, (n_column + 1) * local_nb))
        for row_index in range(rows):
            m_groups = tuple(tuple(m_group * (mb // m_column_groups)
                                   + group * rows * m_reuse + row_index * m_reuse + r
                                   for r in range(m_reuse)) for group in range(groups))
            workers.append(WorkerSchedule(column, row_index + 2, row_index,
                                          m_group, n_column, n_tiles, m_groups))
    return PrefillSchedule(m, k, n, columns, rows, m_reuse, n_columns,
                           m_column_groups, groups, tuple(workers))
