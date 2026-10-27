"""CPU schedule for one array8 projection with separate compact gate/up outputs.

Weights retain the native W[Nb,Kb,2144] layout, concatenating the packed gate
then packed up matrices along Nb. The underlying projection has N=2P, where
P is the branch's intermediate-channel count. Every supported P is divisible
by128, so the output boundary lies exactly between physical columns3 and4.
The two output BOs each retain C[Mb,P/32,512], ready for the existing SiLU
kernel without splitting or compacting a wide output on the CPU.

This changes projection dispatch and output routing only. The native MMUL,
M-tile reuse, and local-N activation replay are the existing array8 design.
"""

from numbers import Integral

from prefill_schedule import C_ELEMENTS, TapSpec, plan_prefill


SCHEDULE_VERSION = "prefill_array8_gate_up_separate_outputs_v1"


def plan_gate_up(m, k, channels, columns=8, rows=4, max_reuse=2):
    """Plan a wide projection while retaining all32 nonempty workers.

    P<=8192 follows the existing N<=16384 and local-N<=64 bounds. In
    particular P128 does not fall back to fewer columns: all eight columns
    share the same M rows and half compute each projection.
    """
    if (isinstance(channels, bool) or not isinstance(channels, Integral)
            or channels < 128 or channels % 128):
        raise ValueError("gate/up channels must be >=128 and divisible by128")
    if channels > 8192:
        raise ValueError("combined gate/up supports channels<=8192 (total N<=16384)")
    plan = plan_prefill(m, k, 2 * int(channels), columns, rows, max_reuse)
    if plan.n_columns != 8 or plan.m_column_groups != 1:
        raise ValueError("combined gate/up must use one eight-column M group")
    return plan


def gate_up_output_target(plan, column):
    """Name the compact output BO owned by this physical column."""
    # worker() also checks integer type and column range without coercion.
    plan.worker(column, 0)
    if (plan.columns != 8 or plan.compute_rows != 4 or plan.n_columns != 8
            or plan.m_column_groups != 1 or plan.n % 256):
        raise ValueError("plan must be an eight-column combined gate/up projection")
    return "gate" if column < 4 else "up"


def gate_up_output_tap(plan, column, group):
    """Scatter one column's joined stream directly into compact gate or up."""
    gate_up_output_target(plan, column)
    m_start = plan.group_m_start(column, group)
    branch_nb = plan.nb // 2
    branch_n_start = plan.n_start(column) % branch_nb
    return TapSpec(plan.m * (plan.n // 2),
                   (m_start * branch_nb + branch_n_start) * C_ELEMENTS,
                   (1, plan.local_nb, plan.compute_rows * plan.m_reuse, C_ELEMENTS),
                   (0, C_ELEMENTS, branch_nb * C_ELEMENTS, 1))


def gate_up_plan_metadata(plan):
    """Augment the shared projection provenance with the two-output ABI."""
    gate_up_output_target(plan, 0)
    result = plan.to_dict()
    result.update(gate_up_schedule_version=SCHEDULE_VERSION,
                  channels=plan.n // 2, output_count=2,
                  output_layout="separate gate/up C[Mb,P/32,512]",
                  output_columns={"gate": list(range(4)), "up": list(range(4, 8))},
                  host_output_elements_per_buffer=plan.m * (plan.n // 2))
    return result
