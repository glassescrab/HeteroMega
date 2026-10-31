"""Eight-column, four-row W4A16 prefill with multicast and M-tile reuse.

Host A/W/C buffers retain the original compact M16/K128/N32 ABI. Four A
streams (eight for a narrow N128 shard) multicast horizontally; eight packed
weight streams multicast vertically to four workers each. A worker reuses
one dequantized weight tile across a pair of M16 blocks when geometry allows.
The graph never silently reduces the requested eight physical columns.
Native BF16 is the default; --arithmetic bfp16 selects the opt-in block-float
projection kernel while retaining the same host buffers and FIFO schedule.

The FIFO topology follows AMD's pinned MLIR-AIE whole_array matmul example
(7e00b57955e108fe9d8e9419f5828a0c7e650858, Apache-2.0 WITH LLVM-exception).
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

from prefill_schedule import plan_prefill


SOURCE = Path(__file__).with_suffix('.cc').read_text()
SOURCE_SHA = hashlib.sha256(SOURCE.encode()).hexdigest()
SCHEDULE_SHA = hashlib.sha256(Path(__file__).with_name('prefill_schedule.py').read_bytes()).hexdigest()
TARGET_COMMIT = '7e00b57955e108fe9d8e9419f5828a0c7e650858'


def _tap(spec):
    return TensorAccessPattern((spec.buffer_elements,), offset=spec.offset,
                               sizes=list(spec.sizes), strides=list(spec.strides))


@iron.jit(aiecc_flags=['--alloc-scheme=basic-sequential'])
def w4a16_prefill_reuse(
    activations: In, weights: In, output: Out, *,
    m: CompileTime[int] = 512, k: CompileTime[int] = 4096,
    n: CompileTime[int] = 512, cols: CompileTime[int] = 8,
    max_reuse: CompileTime[int] = 2,
    arithmetic: CompileTime[str] = 'bf16',
    arithmetic_source_sha256: CompileTime[str] = ARITHMETIC_SOURCE_SHA,
    source_sha256: CompileTime[str] = SOURCE_SHA,
    schedule_sha256: CompileTime[str] = SCHEDULE_SHA,
):
    projection = projection_arithmetic(arithmetic)
    validate_projection_identity(projection, source_sha256, arithmetic_source_sha256)
    plan = plan_prefill(m, k, n, columns=cols, rows=4, max_reuse=max_reuse)
    if source_sha256 != projection.source_sha256 or schedule_sha256 != SCHEDULE_SHA:
        raise ValueError('kernel or schedule source hash changed; rebuild the graph')
    device = iron.get_current_device()
    if device is None or device.cols != 8:
        raise ValueError('array8 requires the full eight-column NPU2 device')
    reuse = plan.m_reuse
    a_tile = np.ndarray[(reuse * 2048,), np.dtype[bfloat16]]
    w_tile = np.ndarray[(2144,), np.dtype[np.uint8]]
    y_tile = np.ndarray[(reuse * 512,), np.dtype[bfloat16]]
    c_tile = np.ndarray[(reuse * 512,), np.dtype[np.float32]]
    b_tile = np.ndarray[(4096,), np.dtype[bfloat16]]
    y_join = np.ndarray[(4 * reuse * 512,), np.dtype[bfloat16]]
    a_host = np.ndarray[(m * k,), np.dtype[bfloat16]]
    w_host = np.ndarray[(plan.nb * plan.kb * 2144,), np.dtype[np.uint8]]
    y_host = np.ndarray[(m * n,), np.dtype[bfloat16]]

    obj = projection.object_name(reuse)
    accumulate = ExternalFunction('w4a16_prefill_reuse_accumulate',
        object_file_name=obj, source_string=projection.source,
        arg_types=[a_tile, w_tile, c_tile, b_tile],
        compile_flags=projection.compile_flags(reuse),
        include_dirs=[config.cxx_header_path(), str(Path(config.cxx_header_path()) / 'aie_kernels')])
    init = Kernel('w4a16_prefill_reuse_init', obj, [c_tile])
    finish = Kernel('w4a16_prefill_reuse_finish', obj, [c_tile, y_tile])

    # Pin shim endpoints on their first creation: .prod() handles are cached.
    # Every physical column has at most two input and one output shim channels.
    a_sources, a_prods, a_broadcasts = [], [], []
    for lane in range(plan.m_column_groups * 4):
        source = ObjectFifo(a_tile, depth=2, name=f'array_a_host_{lane}')
        a_sources.append(source)
        a_prods.append(source.prod(tile=Tile(lane, 0), channel=0))
        # The pinned DMA verifier limits each object-FIFO dimension to 512.
        # Stream 512-BF16 quarters in [quarter,reuse,512] order; memtile
        # MM2S restores [reuse,quarter,512] without an extra host copy.
        a_broadcasts.append(source.cons().forward(tile=Tile(lane, 1),
            name=f'array_a_broadcast_{lane}',
            dims_to_stream=list(plan.activation_dims_to_stream)))
    w_prods, w_broadcasts, y_conses, y_workers = [], [], [], []
    for col in range(8):
        source = ObjectFifo(w_tile, depth=2, name=f'array_w_host_{col}')
        w_prods.append(source.prod(tile=Tile(col, 0), channel=1))
        w_broadcasts.append(source.cons().forward(tile=Tile(col, 1),
                                                name=f'array_w_broadcast_{col}'))
        joined = ObjectFifo(y_join, depth=2, name=f'array_y_host_{col}')
        y_workers.append(joined.prod().join([r * reuse * 512 for r in range(4)],
            tile=Tile(col, 1), obj_types=[y_tile] * 4, depths=[2] * 4,
            names=[f'array_y_worker_{col}_{r}' for r in range(4)]))
        y_conses.append(joined.cons(tile=Tile(col, 0), channel=0))

    def core_fn(a_in, w_in, y_out, c, b, zero, mac, store):
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
            y = y_out.acquire(1)
            store(c, y)
            y_out.release(1)

    workers = []
    for col in range(8):
        m_group = col // plan.n_columns
        for row in range(4):
            c = Buffer(c_tile, name=f'array_acc_{col}_{row}')
            b = Buffer(b_tile, name=f'array_dequant_{col}_{row}')
            workers.append(Worker(core_fn,
                [a_broadcasts[m_group * 4 + row].cons(), w_broadcasts[col].cons(),
                 y_workers[col][row].prod(), c, b, init, accumulate, finish],
                tile=Tile(col, row + 2), stack_size=projection.stack_size, dynamic_objfifo_lowering=True))

    def sequence(a, w, y, a_hs, w_hs, y_hs):
        for group_index in range(plan.groups_per_column):
            task_group = TaskGroup()
            for col in range(8):
                y_hs[col].drain(y, _tap(plan.output_tap(col, group_index)),
                               wait=True, group=task_group)
            for lane in range(plan.m_column_groups * 4):
                m_group, row = divmod(lane, 4)
                col = m_group * plan.n_columns
                a_hs[lane].fill(a, _tap(plan.activation_tap(col, row, group_index)),
                                group=task_group)
            for col in range(8):
                w_hs[col].fill(w, _tap(plan.weight_tap(col)), group=task_group)
            task_group.finish()

    runtime = Runtime(sequence, [a_host, w_host, y_host, a_prods, w_prods, y_conses])
    return Program(device, runtime, workers=workers).resolve_program()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_compile_args(parser, dev_choices=('npu2',), default_dev='npu2', with_pdi=True, with_emit_mlir=True)
    parser.add_argument('-M', type=int, default=512)
    parser.add_argument('-K', type=int, default=4096)
    parser.add_argument('-N', type=int, default=512)
    parser.add_argument('-co', '--columns', type=int, default=8)
    parser.add_argument('--max-reuse', type=int, choices=(1, 2, 4), default=2)
    parser.add_argument('--arithmetic', choices=ARITHMETIC_CHOICES, default='bf16')
    opts = parser.parse_args()
    projection = projection_arithmetic(opts.arithmetic)
    plan = plan_prefill(opts.M, opts.K, opts.N, columns=opts.columns, rows=4, max_reuse=opts.max_reuse)
    run_design_cli(w4a16_prefill_reuse, opts,
        compile_kwargs=dict(m=opts.M, k=opts.K, n=opts.N, cols=opts.columns,
                            max_reuse=opts.max_reuse, arithmetic=opts.arithmetic,
                            arithmetic_source_sha256=ARITHMETIC_SOURCE_SHA,
                            source_sha256=projection.source_sha256,
                            schedule_sha256=SCHEDULE_SHA),
        device=lambda o: device_from_args(o, n_cols=None))
    if opts.xclbin_path and not opts.emit_mlir:
        manifest = dict(kind='w4a16_prefill_bf16', design='array8',
            m=opts.M, k=opts.K, n=opts.N, cols=8, compute_rows=4,
            m_reuse=plan.m_reuse, worker_count=32,
            m_column_groups=plan.m_column_groups, n_columns=plan.n_columns,
            tile_m=16, tile_k=128, tile_n=32, group_size=128, weight_tile_bytes=2144,
            source_sha256=projection.source_sha256, schedule_sha256=SCHEDULE_SHA,
            target_mlir_aie_commit=TARGET_COMMIT,
            xclbin_sha256=hashlib.sha256(Path(opts.xclbin_path).read_bytes()).hexdigest(),
            insts_sha256=hashlib.sha256(Path(opts.insts_path).read_bytes()).hexdigest())
        manifest.update(projection.manifest_fields())
        Path(str(opts.xclbin_path) + '.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
