"""Stream a multi-token W4A16 projection through AIE2P matrix-multiply cores.

Fixed core tile 16x128x32. Each column owns a contiguous output-channel
range. A and quantized weights are packed once; strided/repeated shim DMA
reuses them across N and M tiles without replicating host buffers. K tiles
accumulate in a core-local FP32 buffer before one BF16 output conversion.
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

TILE_M, TILE_K, TILE_N = 16, 128, 32
A_ELEMS, W_BYTES, C_ELEMS = 2048, 2144, 512
SOURCE = Path(__file__).with_suffix('.cc').read_text()
SOURCE_SHA = hashlib.sha256(SOURCE.encode()).hexdigest()
TARGET_COMMIT = '7e00b57955e108fe9d8e9419f5828a0c7e650858'


def validate_shape(m, k, n, cols):
    if m < 16 or m % TILE_M or k <= 0 or k % TILE_K or n <= 0 or n % TILE_N:
        raise ValueError('prefill requires M divisible by 16, K by 128, N by 32')
    if not 1 <= cols <= 8 or (n // TILE_N) % cols:
        raise ValueError('columns must be 1..8 and divide the N tile count')
    if n // TILE_N // cols > 64:
        raise ValueError('at most 64 N tiles per column; increase columns or use a smaller shard')
    # Keep outer DMA repeat counts bounded for this first streaming design.
    if m > 4096 or k > 16384 or n > 16384:
        raise ValueError('bring-up shape bounds: M<=4096, K/N<=16384')


@iron.jit
def w4a16_prefill(
    activations: In, weights: In, output: Out, *,
    m: CompileTime[int] = 128, k: CompileTime[int] = 4096,
    n: CompileTime[int] = 2048, cols: CompileTime[int] = 4,
    source_sha256: CompileTime[str] = SOURCE_SHA,
):
    validate_shape(m, k, n, cols)
    if source_sha256 != SOURCE_SHA:
        raise ValueError('source hash does not match the imported kernel')
    device = iron.get_current_device()
    if device is None or cols > device.cols:
        raise ValueError('select an NPU2 device with enough columns')
    mb, kb, nb = m // TILE_M, k // TILE_K, n // TILE_N
    local_nb = nb // cols
    a_tile = np.ndarray[(A_ELEMS,), np.dtype[bfloat16]]
    w_tile = np.ndarray[(W_BYTES,), np.dtype[np.uint8]]
    y_tile = np.ndarray[(C_ELEMS,), np.dtype[bfloat16]]
    c_tile = np.ndarray[(C_ELEMS,), np.dtype[np.float32]]
    b_tile = np.ndarray[(TILE_K * TILE_N,), np.dtype[bfloat16]]
    a_host = np.ndarray[(mb * kb * A_ELEMS,), np.dtype[bfloat16]]
    w_host = np.ndarray[(nb * kb * W_BYTES,), np.dtype[np.uint8]]
    y_host = np.ndarray[(mb * nb * C_ELEMS,), np.dtype[bfloat16]]

    # The pinned explicit-output compiler reuses .o files by name. Include
    # the C++ content hash; all three symbols share this one translation unit.
    obj = f'w4a16_prefill_{source_sha256}_16x128x32.o'
    accumulate = ExternalFunction(
        'w4a16_prefill_accumulate', object_file_name=obj, source_string=SOURCE,
        arg_types=[a_tile, w_tile, c_tile, b_tile],
        include_dirs=[config.cxx_header_path(), str(Path(config.cxx_header_path()) / 'aie_kernels')],
    )
    init = Kernel('w4a16_prefill_init', obj, [c_tile])
    finish = Kernel('w4a16_prefill_finish', obj, [c_tile, y_tile])
    af = [ObjectFifo(a_tile, depth=2, name=f'prefill_a_{i}') for i in range(cols)]
    wf = [ObjectFifo(w_tile, depth=2, name=f'prefill_w_{i}') for i in range(cols)]
    yf = [ObjectFifo(y_tile, depth=2, name=f'prefill_y_{i}') for i in range(cols)]

    def core_fn(a_in, w_in, y_out, c, b, zero, mac, store):
        for _ in range_(mb * local_nb):
            zero(c)
            for _ in range_(kb):
                a = a_in.acquire(1)
                w = w_in.acquire(1)
                mac(a, w, c, b)
                a_in.release(1)
                w_in.release(1)
            y = y_out.acquire(1)
            store(c, y)
            y_out.release(1)

    workers = []
    for i in range(cols):
        c = Buffer(c_tile, name=f'prefill_acc_{i}')
        b = Buffer(b_tile, name=f'prefill_dequant_{i}')
        workers.append(Worker(core_fn,
            [af[i].cons(), wf[i].cons(), yf[i].prod(), c, b, init, accumulate, finish],
            tile=Tile(i, 2), stack_size=2048, dynamic_objfifo_lowering=True))

    # Stream order at every core is [M block, local N block, K block].
    # All offsets/strides are elements of the associated host buffer dtype.
    # Only the outer shim DMA dimension supports repetition with stride 0.
    # Emit one task group per M tile, so repeated A spans the outer dimension.
    a_taps = [TensorAccessPattern((mb * kb * A_ELEMS,), offset=j * kb * A_ELEMS,
        sizes=[local_nb, 1, 1, kb * A_ELEMS], strides=[0, 0, 0, 1]) for j in range(mb)]
    w_taps = [TensorAccessPattern((nb * kb * W_BYTES,),
        offset=i * local_nb * kb * W_BYTES,
        sizes=[1, 1, 1, local_nb * kb * W_BYTES], strides=[0, 0, 0, 1]) for i in range(cols)]

    def sequence(a, w, y, a_prods, w_prods, y_cons):
        for j in range(mb):
            group = TaskGroup()
            for i in range(cols):
                a_prods[i].fill(a, a_taps[j], group=group)
                w_prods[i].fill(w, w_taps[i], group=group)
            for i in range(cols):
                y_tap = TensorAccessPattern((mb * nb * C_ELEMS,),
                    offset=(j * nb + i * local_nb) * C_ELEMS,
                    sizes=[1, 1, 1, local_nb * C_ELEMS], strides=[0, 0, 0, 1])
                y_cons[i].drain(y, y_tap, wait=True, group=group)
            group.finish()

    runtime = Runtime(sequence, [a_host, w_host, y_host,
        [f.prod() for f in af], [f.prod() for f in wf], [f.cons() for f in yf]])
    return Program(device, runtime, workers=workers).resolve_program()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    add_compile_args(p, dev_choices=('npu2',), default_dev='npu2', with_pdi=True, with_emit_mlir=True)
    p.add_argument('-M', type=int, default=128)
    p.add_argument('-K', type=int, default=4096)
    p.add_argument('-N', type=int, default=2048)
    p.add_argument('-co', '--columns', type=int, default=4)
    opts = p.parse_args()
    validate_shape(opts.M, opts.K, opts.N, opts.columns)
    run_design_cli(w4a16_prefill, opts,
        compile_kwargs=dict(m=opts.M, k=opts.K, n=opts.N, cols=opts.columns, source_sha256=SOURCE_SHA),
        device=lambda o: device_from_args(o, n_cols=None))
    if opts.xclbin_path and not opts.emit_mlir:
        manifest = dict(kind='w4a16_prefill_bf16', m=opts.M, k=opts.K, n=opts.N,
            cols=opts.columns, tile_m=TILE_M, tile_k=TILE_K, tile_n=TILE_N,
            group_size=128, weight_tile_bytes=W_BYTES,
            source_sha256=SOURCE_SHA, target_mlir_aie_commit=TARGET_COMMIT,
            xclbin_sha256=hashlib.sha256(Path(opts.xclbin_path).read_bytes()).hexdigest(),
            insts_sha256=hashlib.sha256(Path(opts.insts_path).read_bytes()).hexdigest())
        Path(str(opts.xclbin_path) + '.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
