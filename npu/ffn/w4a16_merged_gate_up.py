"""Experimental gate/up+SiLU-only NPU graph with row-major Z output.

This is the producer half of a role-specialized GPU-down split: the NPU computes
the gate/up prefix and writes Z row-major; the GPU computes the complementary
gate/up suffix and the full down projection. It is a separate ablation, not the
production two-launch graph and not the previously measured merged full FFN.
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

from prefill_schedule import TapSpec
from projection_arithmetic import ProjectionArithmetic, UPSTREAM_KERNEL_COMMIT
from upstream_schedule import (plan_upstream, segment_pipeline_actions,
                               validate_segment_pipeline_depth,
                               validate_kernel_tuning, validate_split_m32_a,
                               validate_preconvert_a, upstream_worker_stack_size)
from upstream_output import upstream_swiglu_row_major_output_tap
from upstream_weights import UPSTREAM_LAYOUT_VERSION

ROOT = Path(__file__).parent
DEPENDENCIES = ('w4a16_merged_gate_up.py', 'w4a16_upstream.py',
                'w4a16_prefill_upstream.cc', 'upstream_weights.py',
                'upstream_schedule.py', 'upstream_output.py',
                'prefill_schedule.py', 'prefill_gate_up_schedule.py',
                'prefill_swiglu_schedule.py', 'silu_mul.cc',
                'projection_arithmetic.py')
HASHES = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
          for name in DEPENDENCIES}
SOURCE = (ROOT / 'w4a16_prefill_upstream.cc').read_text()
FINGERPRINT = hashlib.sha256(json.dumps(HASHES, sort_keys=True).encode()).hexdigest()
TARGET_COMMIT = '7e00b57955e108fe9d8e9419f5828a0c7e650858'


def _tap(spec):
    return TensorAccessPattern((spec.buffer_elements,), offset=spec.offset,
                               sizes=list(spec.sizes), strides=list(spec.strides))


def _design_gate_up(m, hidden, channels, weight_k, weight_n, max_reuse,
                    segment_pipeline_depth, activation_fifo_depth,
                    z_output_fifo_depth, vector_zero, mmul_m_reuse,
                    fingerprint):
    if fingerprint != FINGERPRINT:
        raise ValueError('gate/up graph dependency identity changed; rebuild')
    validate_segment_pipeline_depth(segment_pipeline_depth)
    validate_kernel_tuning(vector_zero, mmul_m_reuse, 'bfp16', True, True)
    worker_stack_size = upstream_worker_stack_size(mmul_m_reuse, 'bfp16')
    direct = plan_upstream(m, hidden, channels, mode='swiglu', weight_k=weight_k,
                           weight_n=weight_n, columns=8, max_reuse=max_reuse)
    validate_split_m32_a(direct, True, True, activation_fifo_depth, z_output_fifo_depth)
    plan = direct.base
    device = iron.get_current_device()
    if device is None or device.cols != 8:
        raise ValueError('gate/up graph requires the full NPU2 eight-column device')
    reuse = plan.m_reuse
    projection = ProjectionArithmetic('bfp16', ROOT / 'w4a16_prefill_upstream.cc',
                                      SOURCE, HASHES['w4a16_prefill_upstream.cc'])
    a_tile = np.ndarray[(reuse * 2048,), np.dtype[bfloat16]]
    a_core_tile = np.ndarray[(2 * 2048,), np.dtype[bfloat16]]
    w_tile = np.ndarray[(4352,), np.dtype[np.uint8]]
    y_tile = np.ndarray[(reuse * 512,), np.dtype[bfloat16]]
    c_tile = np.ndarray[(reuse * 512,), np.dtype[bfloat16]]
    b_tile = np.ndarray[(8192,), np.dtype[bfloat16]]
    z_join = np.ndarray[(4 * reuse * 512,), np.dtype[bfloat16]]
    a_host = np.ndarray[(m * hidden,), np.dtype[bfloat16]]
    w_host = np.ndarray[(direct.weight_bytes,), np.dtype[np.uint8]]
    z_host = np.ndarray[(m * channels,), np.dtype[bfloat16]]
    obj = projection.object_name(reuse).removesuffix('.o') + (
        f'_vectorzero{int(vector_zero)}_mmulmreuse{mmul_m_reuse}'
        '_native8_bf16partial_splitm32a_preconvertb.o')
    include_dirs = [config.cxx_header_path(), str(Path(config.cxx_header_path()) / 'aie_kernels')]
    dequant_pair = ExternalFunction('w4a16_prefill_dequantize_pair',
        object_file_name=obj, source_string=SOURCE, arg_types=[w_tile, b_tile],
        compile_flags=[*projection.compile_flags(reuse),
                       f'-DHETEROMEGA_VECTOR_ZERO={int(vector_zero)}',
                       f'-DHETEROMEGA_MMUL_M_REUSE={mmul_m_reuse}',
                       '-DHETEROMEGA_BFP16_NATIVE_LAYOUT=1',
                       '-DHETEROMEGA_SPLIT_M32_A=1',
                       '-DHETEROMEGA_PRECONVERT_B=1',
                       '-DHETEROMEGA_PRECONVERT_A=0'],
        include_dirs=include_dirs)
    mac_m0 = Kernel('w4a16_prefill_accumulate_pair_m0', obj, [a_core_tile, c_tile, c_tile, b_tile])
    mac_m1 = Kernel('w4a16_prefill_accumulate_pair_m1', obj, [a_core_tile, c_tile, c_tile, b_tile])
    init = Kernel('w4a16_prefill_reuse_init', obj, [c_tile])
    finish = Kernel('w4a16_prefill_reuse_finish', obj, [c_tile, y_tile])
    pointwise = ExternalFunction('silu_mul_bf16',
        object_file_name=f'silu_mul_{HASHES["silu_mul.cc"]}_{reuse * 512}.o',
        source_string=(ROOT / 'silu_mul.cc').read_text(),
        arg_types=[y_tile, y_tile, y_tile],
        compile_flags=[f'-DHETEROMEGA_TILE_SIZE={reuse * 512}'], include_dirs=include_dirs)

    a_prods, a_broadcasts = [], []
    for lane in range(plan.m_column_groups * 4):
        source = ObjectFifo(a_tile, depth=2, name=f'gu_a_host_{lane}')
        a_prods.append(source.prod(tile=Tile(lane, 0), channel=0))
        a_broadcasts.append(source.cons().forward(tile=Tile(lane, 1), obj_type=a_core_tile,
            name=f'gu_a_broadcast_{lane}',
            dims_to_stream=list(direct.activation_dims_to_stream('row_major', True))))
    w_prods, w_broadcasts = [], []
    for col in range(8):
        source = ObjectFifo(w_tile, depth=2, name=f'gu_w_host_{col}')
        w_prods.append(source.prod(tile=Tile(col, 0), channel=1))
        w_broadcasts.append(source.cons().forward(tile=Tile(col, 1), name=f'gu_w_broadcast_{col}'))
    z_cols = [1, 3, 5, 7]
    out_cons, out_workers = [], {}
    for col in z_cols:
        joined = ObjectFifo(z_join, depth=2, name=f'gu_out_{col}',
            dims_to_stream=[(plan.m_reuse * 2, 256), (8, 8), (4, 64), (8, 1)])
        out_workers[col] = joined.prod().join([r * reuse * 512 for r in range(4)],
            tile=Tile(col, 1), obj_types=[y_tile] * 4, depths=[1] * 4,
            names=[f'gu_out_worker_{col}_{r}' for r in range(4)])
        out_cons.append(joined.cons(tile=Tile(col, 0), channel=0))
    gates = {}
    for col in (0, 2, 4, 6):
        for row in range(4):
            gates[col, row] = ObjectFifo(y_tile, depth=1, name=f'gu_gate_{col}_{row}')

    def producer_fn(segments):
        def core(a_in, w_in, y_out, c0, c1, b, zero, dequant, mac0, mac1, store):
            for _ in range_(plan.groups_per_column):
                for _ in range_(len(segments)):
                    zero(c0)
                    zero(c1)
                    for _ in range_(plan.kb):
                        w = w_in.acquire(1)
                        dequant(w, b)
                        a0 = a_in.acquire(1)
                        mac0(a0, c0, c1, b)
                        a_in.release(1)
                        a1 = a_in.acquire(1)
                        mac1(a1, c0, c1, b)
                        a_in.release(1)
                        w_in.release(1)
                    for accumulator in (c0, c1):
                        y = y_out.acquire(1)
                        store(accumulator, y)
                        y_out.release(1)
        return core

    def consumer_fn(segments):
        def core(a_in, w_in, gate_in, z_out, c0, c1, b, zero, dequant, mac0, mac1, activate):
            for _ in range_(plan.groups_per_column):
                for _ in range_(len(segments)):
                    zero(c0)
                    zero(c1)
                    for _ in range_(plan.kb):
                        w = w_in.acquire(1)
                        dequant(w, b)
                        a0 = a_in.acquire(1)
                        mac0(a0, c0, c1, b)
                        a_in.release(1)
                        a1 = a_in.acquire(1)
                        mac1(a1, c0, c1, b)
                        a_in.release(1)
                        w_in.release(1)
                    for accumulator in (c0, c1):
                        gate = gate_in.acquire(1)
                        z = z_out.acquire(1)
                        activate(gate, accumulator, z)
                        gate_in.release(1)
                        z_out.release(1)
        return core

    workers = []
    for col in range(8):
        logical = direct.logical_column(col)
        m_group = logical // plan.n_columns
        for row in range(4):
            c0 = Buffer(c_tile, name=f'gu_acc0_{col}_{row}')
            c1 = Buffer(c_tile, name=f'gu_acc1_{col}_{row}')
            b = Buffer(b_tile, name=f'gu_dequant_{col}_{row}')
            a_in = a_broadcasts[m_group * 4 + row].cons(depth=activation_fifo_depth)
            w_in = w_broadcasts[col].cons()
            if col % 2 == 0:
                fn = producer_fn(direct.segments[col])
                args = [a_in, w_in, gates[col, row].prod(), c0, c1, b,
                        init, dequant_pair, mac_m0, mac_m1, finish]
            else:
                fn = consumer_fn(direct.segments[col])
                args = [a_in, w_in, gates[col - 1, row].cons(),
                        out_workers[col][row].prod(depth=z_output_fifo_depth),
                        c0, c1, b, init, dequant_pair, mac_m0, mac_m1, pointwise]
            workers.append(Worker(fn, args, tile=Tile(col, row + 2),
                                  stack_size=worker_stack_size, dynamic_objfifo_lowering=True))

    def submit(a, ws, z, a_hs, w_hs, out_hs):
        pending = {}
        for action in segment_pipeline_actions(direct, segment_pipeline_depth):
            key = (action.group, action.segment)
            if action.kind == 'finish':
                pending.pop(key).finish()
                continue
            tasks = TaskGroup()
            pending[key] = tasks
            for out_index, col in enumerate(z_cols):
                tap = upstream_swiglu_row_major_output_tap(direct, col, *key)
                out_hs[out_index].drain(z, _tap(tap), wait=True, group=tasks)
            for lane, handle in enumerate(a_hs):
                handle.fill(a, _tap(direct.activation_tap(lane, action.group, 'row_major')), group=tasks)
            for col in range(8):
                weight = ws[col % 2]
                w_hs[col].fill(weight, _tap(direct.weight_tap(col, action.segment)), group=tasks)

    def sequence(x, gate_w, up_w, z, a_hs, w_hs, out_hs):
        submit(x, (gate_w, up_w), z, a_hs, w_hs, out_hs)

    types = [a_host, w_host, w_host, z_host, a_prods, w_prods, out_cons]
    return Program(device, Runtime(sequence, types), workers=workers).resolve_program()


@iron.jit(aiecc_flags=['--alloc-scheme=basic-sequential'])
def upstream_merged_gate_up(x: In, gate_w: In, up_w: In, z: Out, *,
    m: CompileTime[int], hidden: CompileTime[int], channels: CompileTime[int],
    weight_k: CompileTime[int], weight_n: CompileTime[int],
    swiglu_max_reuse: CompileTime[int] = 4,
    segment_pipeline_depth: CompileTime[int] = 2,
    activation_fifo_depth: CompileTime[int] = 2,
    z_output_fifo_depth: CompileTime[int] = 1,
    vector_zero: CompileTime[bool] = True, mmul_m_reuse: CompileTime[int] = 1,
    fingerprint: CompileTime[str] = FINGERPRINT):
    return _design_gate_up(m, hidden, channels, weight_k, weight_n,
                           swiglu_max_reuse, segment_pipeline_depth,
                           activation_fifo_depth, z_output_fifo_depth,
                           vector_zero, mmul_m_reuse, fingerprint)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_compile_args(parser, dev_choices=('npu2',), default_dev='npu2', with_pdi=True, with_emit_mlir=True)
    parser.add_argument('-M', type=int, default=512)
    parser.add_argument('-K', type=int, default=4096)
    parser.add_argument('-N', type=int, default=6400)
    parser.add_argument('--weight-k', type=int)
    parser.add_argument('--weight-n', type=int)
    parser.add_argument('-co', '--columns', type=int, default=8)
    parser.add_argument('--max-reuse', type=int, choices=(1, 2, 4), default=4)
    parser.add_argument('--segment-pipeline-depth', type=int, choices=(1, 2), default=2)
    parser.add_argument('--activation-fifo-depth', type=int, choices=(1, 2), default=2)
    parser.add_argument('--z-output-fifo-depth', type=int, choices=(1, 2), default=1)
    parser.add_argument('--vector-zero', action='store_true')
    parser.add_argument('--mmul-m-reuse', type=int, choices=(1, 2), default=1)
    opts = parser.parse_args()
    wk, wn = opts.weight_k or opts.K, opts.weight_n or opts.N
    kwargs = dict(m=opts.M, hidden=opts.K, channels=opts.N, weight_k=wk, weight_n=wn,
                  swiglu_max_reuse=opts.max_reuse,
                  segment_pipeline_depth=opts.segment_pipeline_depth,
                  activation_fifo_depth=opts.activation_fifo_depth,
                  z_output_fifo_depth=opts.z_output_fifo_depth,
                  vector_zero=opts.vector_zero, mmul_m_reuse=opts.mmul_m_reuse,
                  fingerprint=FINGERPRINT)
    run_design_cli(upstream_merged_gate_up, opts, compile_kwargs=kwargs,
                   device=lambda o: device_from_args(o, n_cols=None))
    if opts.xclbin_path and not opts.emit_mlir:
        direct = plan_upstream(opts.M, opts.K, opts.N, mode='swiglu', weight_k=wk,
                               weight_n=wn, columns=8, max_reuse=opts.max_reuse)
        manifest = dict(kind='w4a16_upstream_merged_gate_up', mode='merged_gate_up',
            m=opts.M, hidden=opts.K, channels=opts.N, weight_k=wk, weight_n=wn,
            cols=8, worker_count=32, compute_rows=4, m_reuse=direct.base.m_reuse,
            activation_m_reuse=2, weight_tile_bytes=4352,
            segment_pipeline_depth=opts.segment_pipeline_depth,
            activation_fifo_depth=opts.activation_fifo_depth,
            z_output_fifo_depth=opts.z_output_fifo_depth,
            bfp16_native_layout=True, split_m32_a=True, preconvert_b=True,
            preconvert_a=False, vector_zero=opts.vector_zero,
            mmul_m_reuse=opts.mmul_m_reuse, input_layout='row_major',
            output_layout='row_major', intermediate_layout='row_major',
            arithmetic='bfp16', compute_format='bfp16', accumulator_format='bf16',
            worker_stack_size=upstream_worker_stack_size(opts.mmul_m_reuse, 'bfp16'),
            source_sha256=HASHES['w4a16_prefill_upstream.cc'],
            graph_sha256=HASHES['w4a16_merged_gate_up.py'],
            weight_layout_sha256=HASHES['upstream_weights.py'],
            schedule_sha256=HASHES['upstream_schedule.py'], dependency_sha256=HASHES,
            upstream_kernel_commit=UPSTREAM_KERNEL_COMMIT,
            target_mlir_aie_commit=TARGET_COMMIT,
            xclbin_sha256=hashlib.sha256(Path(opts.xclbin_path).read_bytes()).hexdigest(),
            insts_sha256=hashlib.sha256(Path(opts.insts_path).read_bytes()).hexdigest())
        Path(str(opts.xclbin_path) + '.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
