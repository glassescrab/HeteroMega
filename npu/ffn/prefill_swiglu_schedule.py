"""CPU schedule for adjacent gate/up workers with on-chip SiLU/multiply.

Reuse the wide gate/up projection schedule, but physically interleave each
gate column with its matching up column. A one-to-one ObjectFifo between
adjacent compute tiles can use shared tile memory rather than adding a third
incoming DMA stream to a worker already receiving A and W. The existing
packed weight ABI remains gate first, then up; only physical placement and
weight DMA offsets change. Odd columns return compact Z[Mb,P/32,512].

These are logical schedules and raw buffer estimates. Compiler placement,
shared-memory lowering and successful device execution require separate checks.
"""

from numbers import Integral

from prefill_gate_up_schedule import (gate_up_output_tap, gate_up_output_target,
                                     plan_gate_up)


SCHEDULE_VERSION = "prefill_array8_adjacent_swiglu_v1"


def swiglu_logical_column(physical_column):
    """Map physical gate/up pairs to the existing gate-first weight order."""
    if (isinstance(physical_column, bool) or not isinstance(physical_column, Integral)
            or not 0 <= physical_column < 8):
        raise ValueError("physical column must be an integer in 0..7")
    return physical_column // 2 + (physical_column % 2) * 4


def plan_swiglu(m, k, channels, columns=8, rows=4, max_reuse=2):
    """Plan 32 projection workers; the 16 up workers also execute pointwise."""
    if isinstance(max_reuse, bool) or max_reuse not in (1, 2):
        raise ValueError("on-chip SwiGLU supports max_reuse 1 or 2 only")
    return plan_gate_up(m, k, channels, columns, rows, max_reuse)


def swiglu_output_tap(plan, physical_column, group):
    """Scatter compact Z from an up/pointwise column without host reordering."""
    logical = swiglu_logical_column(physical_column)
    if physical_column % 2 != 1:
        raise ValueError("only odd up/pointwise columns drain SwiGLU outputs")
    return gate_up_output_tap(plan, logical, group)


def swiglu_memory_estimate(plan):
    """Conservative raw bytes if the entire shared gate pool lives on up.

    Includes the current double-buffered projection FIFOs, private scratch,
    the unchanged SiLU LUTs, and a 2KiB stack. Excludes allocator alignment,
    code/linker data, compiler-created spills and bank-placement constraints.
    A shared gate pool is counted on both workers as a per-tile upper bound,
    not as a claim that the implementation creates two copies.
    """
    gate_up_output_target(plan, 0)
    reuse = plan.m_reuse
    common = dict(activation_fifo=2 * reuse * 2048 * 2,
                  weight_fifo=2 * 2144,
                  fp32_accumulator=reuse * 512 * 4,
                  dequantized_weight_scratch=4096 * 2,
                  stack=2048)
    gate = dict(common, shared_gate_fifo=2 * reuse * 512 * 2)
    up = dict(common, shared_gate_fifo=2 * reuse * 512 * 2,
              up_bf16_scratch=reuse * 512 * 2,
              output_fifo=2 * reuse * 512 * 2,
              sigmoid_lut=4096)
    return {'gate_components_bytes': gate, 'up_components_bytes': up,
            'gate_raw_bytes': sum(gate.values()), 'up_raw_bytes': sum(up.values()),
            'compute_tile_capacity_bytes': 65536,
            'note': 'raw per-tile upper bounds; compiler alignment, spills and bank placement unverified'}


def swiglu_plan_metadata(plan):
    """Expose actual physical ownership and one-output ABI, not wide-C ABI."""
    gate_up_output_target(plan, 0)
    result = plan.to_dict()
    logical_workers = result['workers']
    workers, columns = [], []
    for physical in range(8):
        logical = swiglu_logical_column(physical)
        columns.append(dict(physical_column=physical, logical_n_column=logical,
                            projection='up' if physical % 2 else 'gate',
                            partner_column=physical ^ 1))
        for row in range(4):
            worker = dict(logical_workers[logical * 4 + row])
            worker.update(column=physical, logical_n_column=logical,
                          runs_silu_multiply=bool(physical % 2))
            workers.append(worker)
    result.update(swiglu_schedule_version=SCHEDULE_VERSION, channels=plan.n // 2,
                  output_count=1, output_order=['silu_mul'],
                  output_layout='compact Z[Mb,P/32,512]',
                  output_columns=[1, 3, 5, 7], pointwise_worker_count=16,
                  gate_handoff='adjacent_compute_tile_object_fifo',
                  physical_column_map=columns, workers=workers,
                  host_projection_elements=plan.m * plan.n,
                  host_output_elements=plan.m * (plan.n // 2),
                  memory_estimate=swiglu_memory_estimate(plan))
    return result
