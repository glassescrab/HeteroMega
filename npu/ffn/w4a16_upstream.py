"""Eight-column FFN projections consuming upstream W4A16 bytes.

Weight BOs are the unchanged glassescrab N64/K128/4352-byte striped buffers.
Gate and up have separate inputs, so no concatenation/repacking is needed.
Compact BF16 A/Y layouts remain defaults; optional DMA layouts remove host
permutations. Worker buffers and FP32 K-group partials are retained.
Native BF16 is the default; explicit BFP16 changes only internal MMUL arithmetic.
An additional native-layout BFP16 experiment uses 8x8 activation/output tiles
and BF16 partials at K128 boundaries; it is never selected implicitly.
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

from projection_arithmetic import ProjectionArithmetic, UPSTREAM_KERNEL_COMMIT
from upstream_schedule import (plan_upstream, segment_pipeline_actions, core_segment_runs,
                               validate_segment_pipeline_depth,
                               validate_kernel_tuning, validate_upstream_buffering,
                               validate_split_m32_a, validate_preconvert_a,
                               validate_input_layout, upstream_worker_stack_size)
from upstream_output import (upstream_down_activation_tap,
                             upstream_row_major_dims_to_stream,
                             upstream_row_major_output_tap)
from upstream_weights import UPSTREAM_LAYOUT_VERSION

ROOT = Path(__file__).parent
DEPENDENCIES = ('w4a16_upstream.py', 'w4a16_prefill_upstream.cc',
                'upstream_weights.py', 'upstream_schedule.py', 'upstream_output.py',
                'prefill_schedule.py',
                'prefill_gate_up_schedule.py', 'prefill_swiglu_schedule.py',
                'silu_mul.cc', 'projection_arithmetic.py')
HASHES = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
          for name in DEPENDENCIES}
SOURCE = (ROOT / 'w4a16_prefill_upstream.cc').read_text()
FINGERPRINT = hashlib.sha256(json.dumps(HASHES, sort_keys=True).encode()).hexdigest()
TARGET_COMMIT = '7e00b57955e108fe9d8e9419f5828a0c7e650858'


def _tap(spec):
    return TensorAccessPattern((spec.buffer_elements,), offset=spec.offset,
                               sizes=list(spec.sizes), strides=list(spec.strides))


def _design(m, k, n, mode, weight_k, weight_n, k_start, n_start, cols,
            max_reuse, segment_pipeline_depth, activation_fifo_depth, output_fifo_depth,
            vector_zero, mmul_m_reuse, input_layout, output_layout, fingerprint,
            arithmetic, bfp16_native_layout, split_m32_a, preconvert_b, preconvert_a):
    if fingerprint != FINGERPRINT:
        raise ValueError('upstream graph dependency identity changed; rebuild')
    validate_segment_pipeline_depth(segment_pipeline_depth)
    validate_kernel_tuning(vector_zero, mmul_m_reuse, arithmetic, bfp16_native_layout, preconvert_b)
    validate_preconvert_a(preconvert_a, split_m32_a, preconvert_b)
    worker_stack_size = upstream_worker_stack_size(mmul_m_reuse, arithmetic)
    validate_input_layout(input_layout)
    if output_layout not in ('compact', 'down_a', 'row_major'):
        raise ValueError('output_layout must be compact, down_a or row_major')
    if mode != 'swiglu' and output_layout == 'down_a':
        raise ValueError('down_a output layout is only supported for SwiGLU')
    if mode != 'projection' and output_layout == 'row_major':
        raise ValueError('row_major output layout is only supported for projection')
    direct = plan_upstream(m, k, n, mode=mode, weight_k=weight_k,
                           weight_n=weight_n, k_start=k_start, n_start=n_start,
                           columns=cols, max_reuse=max_reuse)
    validate_split_m32_a(direct, split_m32_a, bfp16_native_layout,
                         activation_fifo_depth, output_fifo_depth)
    if not split_m32_a:
        validate_upstream_buffering(direct, activation_fifo_depth, output_fifo_depth,
                                   bfp16_native_layout)
    plan = direct.base
    device = iron.get_current_device()
    if device is None or device.cols != 8:
        raise ValueError('direct upstream graph requires the full NPU2 eight-column device')
    reuse = plan.m_reuse
    projection = ProjectionArithmetic(arithmetic, ROOT / 'w4a16_prefill_upstream.cc',
                                     SOURCE, HASHES['w4a16_prefill_upstream.cc'])
    a_tile = np.ndarray[(reuse * 2048,), np.dtype[bfloat16]]
    a_core_tile = np.ndarray[((2 if split_m32_a else reuse) * 2048,), np.dtype[bfloat16]]
    w_tile = np.ndarray[(4352,), np.dtype[np.uint8]]
    y_tile = np.ndarray[(reuse * 512,), np.dtype[bfloat16]]
    c_tile = np.ndarray[(reuse * 512,), np.dtype[bfloat16 if bfp16_native_layout else np.float32]]
    b_tile = np.ndarray[(8192 if split_m32_a else 4096,), np.dtype[bfloat16]]
    y_join = np.ndarray[(4 * reuse * 512,), np.dtype[bfloat16]]
    a_host = np.ndarray[(m * k,), np.dtype[bfloat16]]
    w_host = np.ndarray[(direct.weight_bytes,), np.dtype[np.uint8]]
    y_host = np.ndarray[(m * n,), np.dtype[bfloat16]]
    # All variants share the C++ source but must never share a compiled object.
    obj = projection.object_name(reuse).removesuffix('.o') + (
        f'_vectorzero{int(vector_zero)}_mmulmreuse{mmul_m_reuse}'
        + ('_native8_bf16partial' if bfp16_native_layout else '')
        + ('_splitm32a' if split_m32_a else '')
        + ('_preconvertb' if preconvert_b else '')
        + ('_preconverta' if preconvert_a else '') + '.o')
    include_dirs = [config.cxx_header_path(), str(Path(config.cxx_header_path()) / 'aie_kernels')]
    compile_kernel = ExternalFunction('w4a16_prefill_dequantize_pair' if split_m32_a
                                     else 'w4a16_prefill_reuse_accumulate_low',
        object_file_name=obj, source_string=SOURCE,
        arg_types=[w_tile, b_tile] if split_m32_a else [a_tile, w_tile, c_tile, b_tile],
        compile_flags=[*projection.compile_flags(reuse),
                       f'-DHETEROMEGA_VECTOR_ZERO={int(vector_zero)}',
                       f'-DHETEROMEGA_MMUL_M_REUSE={mmul_m_reuse}',
                       f'-DHETEROMEGA_BFP16_NATIVE_LAYOUT={int(bfp16_native_layout)}',
                       f'-DHETEROMEGA_SPLIT_M32_A={int(split_m32_a)}',
                       f'-DHETEROMEGA_PRECONVERT_B={int(preconvert_b)}',
                       f'-DHETEROMEGA_PRECONVERT_A={int(preconvert_a)}'],
        include_dirs=include_dirs)
    if split_m32_a:
        dequant_pair = compile_kernel
        mac_m0 = Kernel('w4a16_prefill_accumulate_pair_m0', obj,
                        [a_core_tile, c_tile, c_tile, b_tile])
        mac_m1 = Kernel('w4a16_prefill_accumulate_pair_m1', obj,
                        [a_core_tile, c_tile, c_tile, b_tile])
    else:
        low = compile_kernel
        high = Kernel('w4a16_prefill_reuse_accumulate_high', obj,
                      [a_tile, w_tile, c_tile, b_tile])
    init = Kernel('w4a16_prefill_reuse_init', obj, [c_tile])
    finish = Kernel('w4a16_prefill_reuse_finish', obj, [c_tile, y_tile])
    if mode == 'swiglu':
        pointwise = ExternalFunction('silu_mul_bf16',
            object_file_name=f'silu_mul_{HASHES["silu_mul.cc"]}_{reuse * 512}.o',
            source_string=(ROOT / 'silu_mul.cc').read_text(),
            arg_types=[y_tile, y_tile, y_tile],
            compile_flags=[f'-DHETEROMEGA_TILE_SIZE={reuse * 512}'], include_dirs=include_dirs)

    a_prods, a_broadcasts = [], []
    for lane in range(plan.m_column_groups * 4):
        source = ObjectFifo(a_tile, depth=2, name=f'direct_a_host_{lane}')
        a_prods.append(source.prod(tile=Tile(lane, 0), channel=0))
        # One-to-one links retain the larger memory-tile allocation/stream
        # permutation and deliver two M32 objects to each depth-two core.
        # The unchanged shim tap works for both compact and row-major A.
        a_broadcasts.append(source.cons().forward(tile=Tile(lane, 1), obj_type=a_core_tile,
            name=f'direct_a_broadcast_{lane}',
            dims_to_stream=list(direct.activation_dims_to_stream(input_layout, bfp16_native_layout))))
    w_prods, w_broadcasts = [], []
    for col in range(8):
        source = ObjectFifo(w_tile, depth=2, name=f'direct_w_host_{col}')
        w_prods.append(source.prod(tile=Tile(col, 0), channel=1))
        w_broadcasts.append(source.cons().forward(tile=Tile(col, 1),
                                                 name=f'direct_w_broadcast_{col}'))
    output_cols = list(range(8)) if mode == 'projection' else [1, 3, 5, 7]
    y_conses, y_workers = [], {}
    for col in output_cols:
        output_options = ({'dims_to_stream': list(upstream_row_major_dims_to_stream(direct, bfp16_native_layout))}
                          if output_layout == 'row_major' else {})
        joined = ObjectFifo(y_join, depth=2, name=f'direct_y_host_{col}', **output_options)
        y_workers[col] = joined.prod().join([r * reuse * 512 for r in range(4)],
            tile=Tile(col, 1), obj_types=[y_tile] * 4, depths=[2] * 4,
            names=[f'direct_y_worker_{col}_{r}' for r in range(4)])
        y_conses.append(joined.cons(tile=Tile(col, 0), channel=0))
    gates = {}
    if mode == 'swiglu':
        for col in (0, 2, 4, 6):
            for row in range(4):
                gates[col, row] = ObjectFifo(y_tile, depth=2,
                                           name=f'direct_gate_{col}_{row}')

    def producer_fn(segments):
        runs = core_segment_runs(segments)
        def core(a_in, w_in, y_out, c0, c1, b, zero, mac_low, mac_high, store):
            for _ in range_(plan.groups_per_column):
                # Only the half tuple affects core operations. Runtime
                # repetition keeps program size independent of local N.
                for run in runs:
                    for _ in range_(run.count):
                        accumulators = (c0, c1)
                        for index in range(len(run.halves)):
                            zero(accumulators[index])
                        for _ in range_(plan.kb):
                            a = a_in.acquire(1)
                            w = w_in.acquire(1)
                            for index, half in enumerate(run.halves):
                                mac = mac_high if half else mac_low
                                mac(a, w, accumulators[index], b)
                            a_in.release(1)
                            w_in.release(1)
                        for index in range(len(run.halves)):
                            y = y_out.acquire(1)
                            store(accumulators[index], y)
                            y_out.release(1)
        return core

    def consumer_fn(segments):
        runs = core_segment_runs(segments)
        def core(a_in, w_in, gate_in, z_out, c0, c1, b, up,
                 zero, mac_low, mac_high, store, activate):
            for _ in range_(plan.groups_per_column):
                for run in runs:
                    for _ in range_(run.count):
                        accumulators = (c0, c1)
                        for index in range(len(run.halves)):
                            zero(accumulators[index])
                        for _ in range_(plan.kb):
                            a = a_in.acquire(1)
                            w = w_in.acquire(1)
                            for index, half in enumerate(run.halves):
                                mac = mac_high if half else mac_low
                                mac(a, w, accumulators[index], b)
                            a_in.release(1)
                            w_in.release(1)
                        for index in range(len(run.halves)):
                            store(accumulators[index], up)
                            gate = gate_in.acquire(1)
                            z = z_out.acquire(1)
                            activate(gate, up, z)
                            gate_in.release(1)
                            z_out.release(1)
        return core

    def split_producer_fn(segments):
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

    def split_consumer_fn(segments):
        def core(a_in, w_in, gate_in, z_out, c0, c1, b,
                 zero, dequant, mac0, mac1, activate):
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
                        # Native8 C already has the exact BF16 pointwise ABI.
                        # Avoid the extra up tile and its finish-copy pass.
                        activate(gate, accumulator, z)
                        gate_in.release(1)
                        z_out.release(1)
        return core

    workers = []
    for col in range(8):
        logical = direct.logical_column(col)
        m_group = logical // plan.n_columns
        for row in range(4):
            c0 = Buffer(c_tile, name=f'direct_acc0_{col}_{row}')
            c1 = Buffer(c_tile, name=f'direct_acc1_{col}_{row}')
            b = Buffer(b_tile, name=f'direct_dequant_{col}_{row}')
            inputs = [a_broadcasts[m_group * 4 + row].cons(depth=activation_fifo_depth),
                      w_broadcasts[col].cons()]
            if split_m32_a and mode == 'swiglu' and col % 2:
                fn = split_consumer_fn(direct.segments[col])
                args = [*inputs, gates[col - 1, row].cons(),
                        y_workers[col][row].prod(depth=output_fifo_depth), c0, c1, b,
                        init, dequant_pair, mac_m0, mac_m1, pointwise]
            elif split_m32_a:
                fn = split_producer_fn(direct.segments[col])
                output = (gates[col, row].prod() if mode == 'swiglu' else
                          y_workers[col][row].prod(depth=output_fifo_depth))
                args = [*inputs, output, c0, c1, b, init, dequant_pair, mac_m0, mac_m1, finish]
            elif mode == 'swiglu' and col % 2:
                up = Buffer(y_tile, name=f'direct_up_{col}_{row}')
                fn = consumer_fn(direct.segments[col])
                args = [*inputs, gates[col - 1, row].cons(),
                        y_workers[col][row].prod(depth=output_fifo_depth),
                        c0, c1, b, up, init, low, high, finish, pointwise]
            else:
                fn = producer_fn(direct.segments[col])
                output = (gates[col, row].prod() if mode == 'swiglu' else
                          y_workers[col][row].prod(depth=output_fifo_depth))
                args = [*inputs, output, c0, c1, b, init, low, high, finish]
            workers.append(Worker(fn, args, tile=Tile(col, row + 2),
                                  stack_size=worker_stack_size, dynamic_objfifo_lowering=True))

    def submit(a, ws, y, a_hs, w_hs, y_hs):
        pending = {}
        for action in segment_pipeline_actions(direct, segment_pipeline_depth):
            key = (action.group, action.segment)
            if action.kind == 'finish':
                # TaskGroup.finish awaits all waited output drains before
                # freeing the group's BDs. Retire in FIFO order so completion
                # tokens from a shared shim channel cannot be misattributed.
                pending.pop(key).finish()
                continue
            tasks = TaskGroup()
            pending[key] = tasks
            # Queue every drain before any fill for this segment. The next
            # segment can then stream through the existing depth-two FIFOs
            # while this one's output drains, without adding core buffers.
            for out_index, col in enumerate(output_cols):
                if output_layout == 'down_a':
                    tap = upstream_down_activation_tap(direct, col, *key,
                                                       bfp16_native_layout=bfp16_native_layout)
                elif output_layout == 'row_major':
                    tap = upstream_row_major_output_tap(direct, col, *key)
                else:
                    tap = direct.output_tap(col, *key)
                y_hs[out_index].drain(y, _tap(tap),
                                     wait=True, group=tasks)
            for lane, handle in enumerate(a_hs):
                handle.fill(a, _tap(direct.activation_tap(lane, action.group, input_layout)), group=tasks)
            for col in range(8):
                weight = ws[col % 2] if mode == 'swiglu' else ws[0]
                w_hs[col].fill(weight, _tap(direct.weight_tap(col, action.segment)), group=tasks)
    if mode == 'swiglu':
        def sequence(a, gate_w, up_w, y, a_hs, w_hs, y_hs):
            submit(a, (gate_w, up_w), y, a_hs, w_hs, y_hs)
        types = [a_host, w_host, w_host, y_host, a_prods, w_prods, y_conses]
    else:
        def sequence(a, w, y, a_hs, w_hs, y_hs):
            submit(a, (w,), y, a_hs, w_hs, y_hs)
        types = [a_host, w_host, y_host, a_prods, w_prods, y_conses]
    return Program(device, Runtime(sequence, types), workers=workers).resolve_program()


@iron.jit(aiecc_flags=['--alloc-scheme=basic-sequential'])
def upstream_projection(a: In, w: In, y: Out, *,
    m: CompileTime[int], k: CompileTime[int], n: CompileTime[int],
    weight_k: CompileTime[int], weight_n: CompileTime[int],
    k_start: CompileTime[int] = 0, n_start: CompileTime[int] = 0,
    cols: CompileTime[int] = 8, max_reuse: CompileTime[int] = 2,
    segment_pipeline_depth: CompileTime[int] = 2,
    activation_fifo_depth: CompileTime[int] = 2,
    output_fifo_depth: CompileTime[int] = 2,
    vector_zero: CompileTime[bool] = False, mmul_m_reuse: CompileTime[int] = 1,
    input_layout: CompileTime[str] = 'compact',
    output_layout: CompileTime[str] = 'compact',
    arithmetic: CompileTime[str] = 'bf16',
    bfp16_native_layout: CompileTime[bool] = False,
    split_m32_a: CompileTime[bool] = False,
    preconvert_b: CompileTime[bool] = False,
    preconvert_a: CompileTime[bool] = False,
    fingerprint: CompileTime[str] = FINGERPRINT):
    return _design(m, k, n, 'projection', weight_k, weight_n, k_start, n_start,
                   cols, max_reuse, segment_pipeline_depth, activation_fifo_depth, output_fifo_depth,
                   vector_zero, mmul_m_reuse, input_layout, output_layout, fingerprint,
                   arithmetic, bfp16_native_layout, split_m32_a, preconvert_b, preconvert_a)


@iron.jit(aiecc_flags=['--alloc-scheme=basic-sequential'])
def upstream_swiglu(a: In, gate_w: In, up_w: In, z: Out, *,
    m: CompileTime[int], k: CompileTime[int], n: CompileTime[int],
    weight_k: CompileTime[int], weight_n: CompileTime[int],
    k_start: CompileTime[int] = 0, n_start: CompileTime[int] = 0,
    cols: CompileTime[int] = 8, max_reuse: CompileTime[int] = 2,
    segment_pipeline_depth: CompileTime[int] = 2,
    activation_fifo_depth: CompileTime[int] = 2,
    output_fifo_depth: CompileTime[int] = 2,
    vector_zero: CompileTime[bool] = False, mmul_m_reuse: CompileTime[int] = 1,
    input_layout: CompileTime[str] = 'compact',
    output_layout: CompileTime[str] = 'compact',
    arithmetic: CompileTime[str] = 'bf16',
    bfp16_native_layout: CompileTime[bool] = False,
    split_m32_a: CompileTime[bool] = False,
    preconvert_b: CompileTime[bool] = False,
    preconvert_a: CompileTime[bool] = False,
    fingerprint: CompileTime[str] = FINGERPRINT):
    return _design(m, k, n, 'swiglu', weight_k, weight_n, k_start, n_start,
                   cols, max_reuse, segment_pipeline_depth, activation_fifo_depth, output_fifo_depth,
                   vector_zero, mmul_m_reuse, input_layout, output_layout, fingerprint,
                   arithmetic, bfp16_native_layout, split_m32_a, preconvert_b, preconvert_a)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_compile_args(parser, dev_choices=('npu2',), default_dev='npu2', with_pdi=True, with_emit_mlir=True)
    parser.add_argument('--mode', choices=('projection', 'swiglu'), default='projection')
    parser.add_argument('--arithmetic', choices=('bf16', 'bfp16'), default='bf16',
                        help='internal MMUL arithmetic; BF16 buffers and packed weights are unchanged')
    parser.add_argument('--bfp16-native-layout', action='store_true',
                        help='BFP16 only: native 8x8 A/Y tiles and BF16 K128 partials')
    parser.add_argument('--split-m32-a', action='store_true',
                        help='native8/R4 only: stream depth-two M32 A while retaining M64 weight reuse')
    parser.add_argument('--preconvert-b', action='store_true',
                        help='native8 only: retain preconverted BFP16 weights in scratch')
    parser.add_argument('--preconvert-a', action='store_true',
                        help='split-M32 and preconvert-B only: reuse converted M16 A in scratch tail')
    for flag, default in (('-M', 512), ('-K', 4096), ('-N', 2560)):
        parser.add_argument(flag, type=int, default=default)
    parser.add_argument('--weight-k', type=int)
    parser.add_argument('--weight-n', type=int)
    parser.add_argument('--k-start', type=int, default=0)
    parser.add_argument('--n-start', type=int, default=0)
    parser.add_argument('-co', '--columns', type=int, default=8)
    parser.add_argument('--max-reuse', type=int, choices=(1, 2, 4), default=2)
    parser.add_argument('--segment-pipeline-depth', type=int, choices=(1, 2), default=2,
                        help='maximum in-flight N64 segments; 1 preserves serial DMA scheduling')
    parser.add_argument('--activation-fifo-depth', type=int, choices=(1, 2), default=2,
                        help='core-consumer A buffers; effective reuse 4 requires 1')
    parser.add_argument('--output-fifo-depth', type=int, choices=(1, 2), default=2,
                        help='core-producer Y/Z buffers; effective SwiGLU reuse 4 requires 1')
    parser.add_argument('--vector-zero', action='store_true',
                        help='vectorize original-format zero-point metadata loads')
    parser.add_argument('--mmul-m-reuse', type=int, choices=(1, 2), default=1,
                        help='M16 lanes sharing B loads in one MMUL register block')
    parser.add_argument('--input-layout', choices=('compact', 'row_major'), default='compact',
                        help='input BO layout; row_major moves native A packing to memory-tile DMA')
    parser.add_argument('--output-layout', choices=('compact', 'down_a', 'row_major'), default='compact',
                        help='output DMA layout: down_a for SwiGLU, row_major for projection')
    opts = parser.parse_args()
    # Validate the arithmetic/tuning combination before invoking the compiler.
    upstream_worker_stack_size(opts.mmul_m_reuse, opts.arithmetic)
    validate_kernel_tuning(opts.vector_zero, opts.mmul_m_reuse, opts.arithmetic,
                           opts.bfp16_native_layout, opts.preconvert_b)
    validate_preconvert_a(opts.preconvert_a, opts.split_m32_a, opts.preconvert_b)
    wk, wn = opts.weight_k or opts.K, opts.weight_n or opts.N
    kwargs = dict(m=opts.M, k=opts.K, n=opts.N, weight_k=wk, weight_n=wn,
                  k_start=opts.k_start, n_start=opts.n_start, cols=opts.columns,
                  max_reuse=opts.max_reuse,
                  segment_pipeline_depth=opts.segment_pipeline_depth,
                  activation_fifo_depth=opts.activation_fifo_depth,
                  output_fifo_depth=opts.output_fifo_depth,
                  vector_zero=opts.vector_zero, mmul_m_reuse=opts.mmul_m_reuse,
                  input_layout=opts.input_layout, output_layout=opts.output_layout,
                  arithmetic=opts.arithmetic,
                  bfp16_native_layout=opts.bfp16_native_layout,
                  split_m32_a=opts.split_m32_a,
                  preconvert_b=opts.preconvert_b,
                  preconvert_a=opts.preconvert_a,
                  fingerprint=FINGERPRINT)
    direct = plan_upstream(opts.M, opts.K, opts.N, mode=opts.mode,
                           weight_k=wk, weight_n=wn, k_start=opts.k_start,
                           n_start=opts.n_start, columns=opts.columns, max_reuse=opts.max_reuse)
    validate_split_m32_a(direct, opts.split_m32_a, opts.bfp16_native_layout,
                         opts.activation_fifo_depth, opts.output_fifo_depth)
    if not opts.split_m32_a:
        validate_upstream_buffering(direct, opts.activation_fifo_depth, opts.output_fifo_depth,
                                   opts.bfp16_native_layout)
    design = upstream_swiglu if opts.mode == 'swiglu' else upstream_projection
    run_design_cli(design, opts, compile_kwargs=kwargs,
                   device=lambda o: device_from_args(o, n_cols=None))
    if opts.xclbin_path and not opts.emit_mlir:
        manifest = dict(kind=f'w4a16_upstream_{opts.arithmetic}', mode=opts.mode,
            m=opts.M, k=opts.K, n=opts.N, weight_k=wk, weight_n=wn,
            k_start=opts.k_start, n_start=opts.n_start, cols=8, worker_count=32,
            compute_rows=4, m_reuse=direct.base.m_reuse, weight_tile_bytes=4352,
            segment_pipeline_depth=opts.segment_pipeline_depth,
            activation_fifo_depth=opts.activation_fifo_depth,
            output_fifo_depth=opts.output_fifo_depth,
            bfp16_native_layout=opts.bfp16_native_layout,
            split_m32_a=opts.split_m32_a,
            preconvert_b=opts.preconvert_b,
            preconvert_a=opts.preconvert_a,
            activation_m_reuse=2 if opts.split_m32_a else direct.base.m_reuse,
            accumulator_format='bf16' if opts.bfp16_native_layout else 'float32',
            vector_zero=opts.vector_zero, mmul_m_reuse=opts.mmul_m_reuse,
            input_layout=opts.input_layout,
            output_layout=opts.output_layout,
            weight_layout=UPSTREAM_LAYOUT_VERSION, arithmetic=opts.arithmetic,
            compute_format=opts.arithmetic,
            worker_stack_size=upstream_worker_stack_size(opts.mmul_m_reuse, opts.arithmetic),
            source_sha256=HASHES['w4a16_prefill_upstream.cc'],
            graph_sha256=HASHES['w4a16_upstream.py'], weight_layout_sha256=HASHES['upstream_weights.py'],
            schedule_sha256=HASHES['upstream_schedule.py'], dependency_sha256=HASHES,
            upstream_kernel_commit=UPSTREAM_KERNEL_COMMIT, target_mlir_aie_commit=TARGET_COMMIT,
            xclbin_sha256=hashlib.sha256(Path(opts.xclbin_path).read_bytes()).hexdigest(),
            insts_sha256=hashlib.sha256(Path(opts.insts_path).read_bytes()).hexdigest())
        Path(str(opts.xclbin_path) + '.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
