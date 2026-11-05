"""Eight-column gate/up projections with on-chip SiLU/multiply handoff.

Even physical columns compute gate; adjacent odd columns compute matching up
and then SiLU(gate)*up. All 32 workers perform projections. Gate tiles travel
through adjacent ObjectFifos; only compact Z is drained to a host BO. Down
projection remains a separate graph/dispatch. Native BF16 projection is the
default; --arithmetic bfp16 selects block-float matrix computation. Both modes
retain BF16 projection outputs and the unchanged SiLU rounding boundaries.

The projection FIFO topology follows AMD's pinned MLIR-AIE whole_array matmul
example (7e00b57955e108fe9d8e9419f5828a0c7e650858,
Apache-2.0 WITH LLVM-exception).
"""

import argparse
import hashlib
import json
from pathlib import Path

import aie.iron as iron
import numpy as np
from aie.helpers.taplib import TensorAccessPattern
from aie.iron import Buffer, CompileTime, ExternalFunction, In, Kernel, ObjectFifo, Out, Program, Runtime, TaskGroup, Worker
from aie.iron.controlflow import range_
from aie.iron.device import Tile
from aie.utils import config
from aie.utils.hostruntime.argparse import add_compile_args, device_from_args
from aie.utils.hostruntime.cli import run_design_cli
from ml_dtypes import bfloat16

from projection_arithmetic import (ARITHMETIC_CHOICES, ARITHMETIC_SOURCE_SHA,
                                   projection_arithmetic, validate_projection_identity)

from prefill_swiglu_schedule import (plan_swiglu, swiglu_logical_column,
                                    swiglu_output_tap)


SOURCE = Path(__file__).with_name('w4a16_prefill_reuse.cc').read_text()
SILU_SOURCE = Path(__file__).with_name('silu_mul.cc').read_text()
SOURCE_SHA = hashlib.sha256(SOURCE.encode()).hexdigest()
SILU_SOURCE_SHA = hashlib.sha256(SILU_SOURCE.encode()).hexdigest()
SCHEDULE_SHA = hashlib.sha256(Path(__file__).with_name('prefill_schedule.py').read_bytes()).hexdigest()
GATE_UP_SCHEDULE_SHA = hashlib.sha256(Path(__file__).with_name('prefill_gate_up_schedule.py').read_bytes()).hexdigest()
SWIGLU_SCHEDULE_SHA = hashlib.sha256(Path(__file__).with_name('prefill_swiglu_schedule.py').read_bytes()).hexdigest()
TARGET_COMMIT = '7e00b57955e108fe9d8e9419f5828a0c7e650858'


def _tap(spec):
    return TensorAccessPattern((spec.buffer_elements,), offset=spec.offset,
                               sizes=list(spec.sizes), strides=list(spec.strides))


@iron.jit(aiecc_flags=['--alloc-scheme=basic-sequential'])
def w4a16_swiglu(
    activations: In, weights: In, output: Out, *,
    m: CompileTime[int] = 512, k: CompileTime[int] = 4096,
    channels: CompileTime[int] = 512, cols: CompileTime[int] = 8,
    max_reuse: CompileTime[int] = 2,
    arithmetic: CompileTime[str] = 'bf16',
    arithmetic_source_sha256: CompileTime[str] = ARITHMETIC_SOURCE_SHA,
    source_sha256: CompileTime[str] = SOURCE_SHA,
    silu_source_sha256: CompileTime[str] = SILU_SOURCE_SHA,
    schedule_sha256: CompileTime[str] = SCHEDULE_SHA,
    gate_up_schedule_sha256: CompileTime[str] = GATE_UP_SCHEDULE_SHA,
    swiglu_schedule_sha256: CompileTime[str] = SWIGLU_SCHEDULE_SHA,
):
    projection = projection_arithmetic(arithmetic)
    validate_projection_identity(projection, source_sha256, arithmetic_source_sha256)
    plan = plan_swiglu(m, k, channels, columns=cols, rows=4, max_reuse=max_reuse)
    if (source_sha256 != projection.source_sha256 or silu_source_sha256 != SILU_SOURCE_SHA
            or schedule_sha256 != SCHEDULE_SHA
            or gate_up_schedule_sha256 != GATE_UP_SCHEDULE_SHA
            or swiglu_schedule_sha256 != SWIGLU_SCHEDULE_SHA):
        raise ValueError('arithmetic or schedule source hash changed; rebuild the graph')
    device = iron.get_current_device()
    if device is None or device.cols != 8:
        raise ValueError('SwiGLU requires the full eight-column NPU2 device')
    reuse = plan.m_reuse
    a_tile = np.ndarray[(reuse * 2048,), np.dtype[bfloat16]]
    w_tile = np.ndarray[(2144,), np.dtype[np.uint8]]
    y_tile = np.ndarray[(reuse * 512,), np.dtype[bfloat16]]
    c_tile = np.ndarray[(reuse * 512,), np.dtype[np.float32]]
    b_tile = np.ndarray[(4096,), np.dtype[bfloat16]]
    y_join = np.ndarray[(4 * reuse * 512,), np.dtype[bfloat16]]
    a_host = np.ndarray[(m * k,), np.dtype[bfloat16]]
    w_host = np.ndarray[(plan.nb * plan.kb * 2144,), np.dtype[np.uint8]]
    y_host = np.ndarray[(m * channels,), np.dtype[bfloat16]]
    include_dirs = [config.cxx_header_path(), str(Path(config.cxx_header_path()) / 'aie_kernels')]

    obj = projection.object_name(reuse)
    accumulate = ExternalFunction('w4a16_prefill_reuse_accumulate',
        object_file_name=obj, source_string=projection.source,
        arg_types=[a_tile, w_tile, c_tile, b_tile],
        compile_flags=projection.compile_flags(reuse), include_dirs=include_dirs)
    init = Kernel('w4a16_prefill_reuse_init', obj, [c_tile])
    finish = Kernel('w4a16_prefill_reuse_finish', obj, [c_tile, y_tile])
    pointwise = ExternalFunction('silu_mul_bf16',
        object_file_name=f'silu_mul_{SILU_SOURCE_SHA}_t{reuse * 512}.o',
        source_string=SILU_SOURCE, arg_types=[y_tile, y_tile, y_tile],
        compile_flags=[f'-DHETEROMEGA_TILE_SIZE={reuse * 512}'], include_dirs=include_dirs)

    a_prods, a_broadcasts = [], []
    for row in range(4):
        source = ObjectFifo(a_tile, depth=2, name=f'swiglu_a_host_{row}')
        a_prods.append(source.prod(tile=Tile(row, 0), channel=0))
        a_broadcasts.append(source.cons().forward(tile=Tile(row, 1),
            name=f'swiglu_a_broadcast_{row}',
            dims_to_stream=list(plan.activation_dims_to_stream)))
    w_prods, w_broadcasts = [], []
    for col in range(8):
        source = ObjectFifo(w_tile, depth=2, name=f'swiglu_w_host_{col}')
        w_prods.append(source.prod(tile=Tile(col, 0), channel=1))
        w_broadcasts.append(source.cons().forward(tile=Tile(col, 1),
                                                name=f'swiglu_w_broadcast_{col}'))

    # Each gate/up pair has one producer and one adjacent consumer. Default
    # ObjectFifo lowering can use their shared memory without a third inbound
    # DMA channel on the up tile. Keep the pair on the same physical row.
    gates = [[ObjectFifo(y_tile, depth=2, name=f'swiglu_gate_{pair}_{row}')
              for row in range(4)] for pair in range(4)]
    y_conses, y_workers = [], []
    for pair in range(4):
        col = 2 * pair + 1
        joined = ObjectFifo(y_join, depth=2, name=f'swiglu_z_host_{col}')
        y_workers.append(joined.prod().join([r * reuse * 512 for r in range(4)],
            tile=Tile(col, 1), obj_types=[y_tile] * 4, depths=[2] * 4,
            names=[f'swiglu_z_worker_{col}_{r}' for r in range(4)]))
        y_conses.append(joined.cons(tile=Tile(col, 0), channel=0))

    def gate_fn(a_in, w_in, gate_out, c, b, zero, mac, store):
        count = plan.groups_per_column * plan.local_nb
        loop = range(1) if count == 1 else range_(count)
        for _ in loop:
            zero(c)
            for _ in range_(plan.kb):
                a = a_in.acquire(1)
                w = w_in.acquire(1)
                mac(a, w, c, b)
                a_in.release(1)
                w_in.release(1)
            gate = gate_out.acquire(1)
            store(c, gate)
            gate_out.release(1)

    def up_fn(a_in, w_in, gate_in, z_out, c, b, up, zero, mac, store, activate):
        count = plan.groups_per_column * plan.local_nb
        loop = range(1) if count == 1 else range_(count)
        for _ in loop:
            zero(c)
            for _ in range_(plan.kb):
                a = a_in.acquire(1)
                w = w_in.acquire(1)
                mac(a, w, c, b)
                a_in.release(1)
                w_in.release(1)
            # Both producers release every A/W object before the gate wait.
            # This avoids waiting on gate while pinning a multicast A object.
            # Preserve the full-K FP32 -> BF16 boundary before SiLU/multiply.
            store(c, up)
            gate = gate_in.acquire(1)
            z = z_out.acquire(1)
            activate(gate, up, z)
            gate_in.release(1)
            z_out.release(1)

    workers = []
    for col in range(8):
        pair = col // 2
        for row in range(4):
            c = Buffer(c_tile, name=f'swiglu_acc_{col}_{row}')
            b = Buffer(b_tile, name=f'swiglu_dequant_{col}_{row}')
            if col % 2 == 0:
                fn = gate_fn
                args = [a_broadcasts[row].cons(), w_broadcasts[col].cons(),
                        gates[pair][row].prod(), c, b, init, accumulate, finish]
            else:
                fn = up_fn
                up = Buffer(y_tile, name=f'swiglu_up_bf16_{col}_{row}')
                args = [a_broadcasts[row].cons(), w_broadcasts[col].cons(),
                        gates[pair][row].cons(), y_workers[pair][row].prod(),
                        c, b, up, init, accumulate, finish, pointwise]
            workers.append(Worker(fn, args, tile=Tile(col, row + 2),
                                  stack_size=projection.stack_size, dynamic_objfifo_lowering=True))

    def sequence(a, w, z, a_hs, w_hs, y_hs):
        for group_index in range(plan.groups_per_column):
            task_group = TaskGroup()
            # Arm final drains before feeding producers; completing every Z
            # stream also proves that its corresponding gate stream was read.
            for pair in range(4):
                col = 2 * pair + 1
                y_hs[pair].drain(z, _tap(swiglu_output_tap(plan, col, group_index)),
                                wait=True, group=task_group)
            for row in range(4):
                a_hs[row].fill(a, _tap(plan.activation_tap(0, row, group_index)),
                               group=task_group)
            for col in range(8):
                logical = swiglu_logical_column(col)
                w_hs[col].fill(w, _tap(plan.weight_tap(logical)), group=task_group)
            task_group.finish()

    runtime = Runtime(sequence, [a_host, w_host, y_host, a_prods, w_prods, y_conses])
    return Program(device, runtime, workers=workers).resolve_program()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_compile_args(parser, dev_choices=('npu2',), default_dev='npu2', with_pdi=True, with_emit_mlir=True)
    parser.add_argument('-M', type=int, default=512)
    parser.add_argument('-K', type=int, default=4096)
    parser.add_argument('-P', '--channels', type=int, default=512)
    parser.add_argument('-co', '--columns', type=int, default=8)
    parser.add_argument('--max-reuse', type=int, choices=(1, 2), default=2)
    parser.add_argument('--arithmetic', choices=ARITHMETIC_CHOICES, default='bf16')
    opts = parser.parse_args()
    projection = projection_arithmetic(opts.arithmetic)
    plan = plan_swiglu(opts.M, opts.K, opts.channels, columns=opts.columns,
                       rows=4, max_reuse=opts.max_reuse)
    run_design_cli(w4a16_swiglu, opts,
        compile_kwargs=dict(m=opts.M, k=opts.K, channels=opts.channels, cols=opts.columns,
                            max_reuse=opts.max_reuse, arithmetic=opts.arithmetic,
                            arithmetic_source_sha256=ARITHMETIC_SOURCE_SHA,
                            source_sha256=projection.source_sha256,
                            silu_source_sha256=SILU_SOURCE_SHA,
                            schedule_sha256=SCHEDULE_SHA,
                            gate_up_schedule_sha256=GATE_UP_SCHEDULE_SHA,
                            swiglu_schedule_sha256=SWIGLU_SCHEDULE_SHA),
        device=lambda o: device_from_args(o, n_cols=None))
    if opts.xclbin_path and not opts.emit_mlir:
        manifest = dict(kind='w4a16_swiglu_bf16', design='array8_swiglu',
            m=opts.M, k=opts.K, n=2 * opts.channels, channels=opts.channels,
            output_count=1, output_order=['silu_mul'], cols=8, compute_rows=4,
            m_reuse=plan.m_reuse, worker_count=32, pointwise_worker_count=16,
            m_column_groups=plan.m_column_groups, n_columns=plan.n_columns,
            physical_to_logical_columns=[swiglu_logical_column(col) for col in range(8)],
            output_columns=[1, 3, 5, 7], gate_handoff='adjacent_compute_tile_object_fifo',
            tile_m=16, tile_k=128, tile_n=32, group_size=128, weight_tile_bytes=2144,
            silu_tile_size=plan.m_reuse * 512,
            source_sha256=projection.source_sha256, silu_source_sha256=SILU_SOURCE_SHA,
            schedule_sha256=SCHEDULE_SHA, gate_up_schedule_sha256=GATE_UP_SCHEDULE_SHA,
            swiglu_schedule_sha256=SWIGLU_SCHEDULE_SHA,
            target_mlir_aie_commit=TARGET_COMMIT,
            xclbin_sha256=hashlib.sha256(Path(opts.xclbin_path).read_bytes()).hexdigest(),
            insts_sha256=hashlib.sha256(Path(opts.insts_path).read_bytes()).hexdigest())
        manifest.update(projection.manifest_fields())
        Path(str(opts.xclbin_path) + '.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
