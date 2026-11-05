"""Compile a small source-level W4A16 decode projection for MLIR-AIE NPU2.

Pinned IRON API: 7e00b57955e108fe9d8e9419f5828a0c7e650858.
The scalar core computes M=1 with K-group size 128 and output channels N.
It is intended for correctness and sliced-weight bring-up, not performance.
"""

import argparse
import hashlib
import json
from pathlib import Path

import aie.iron as iron
import numpy as np
from aie.iron import CompileTime, ExternalFunction, In, ObjectFifo, Out, Program, Runtime, TaskGroup, Worker
from aie.utils import config
from aie.utils.hostruntime.argparse import add_compile_args, device_from_args
from aie.utils.hostruntime.cli import run_design_cli
from ml_dtypes import bfloat16


KERNEL_SOURCE = Path(__file__).with_name("w4a16_linear.cc").read_text()
KERNEL_SOURCE_SHA256 = hashlib.sha256(KERNEL_SOURCE.encode()).hexdigest()


def write_manifest(opts):
    manifest = {
        "kind": "w4a16_linear_bf16", "k": opts.K, "n": opts.N,
        "group_size": 128,
        "target_mlir_aie_commit": "7e00b57955e108fe9d8e9419f5828a0c7e650858",
        "source_sha256": KERNEL_SOURCE_SHA256,
        "xclbin_sha256": hashlib.sha256(Path(opts.xclbin_path).read_bytes()).hexdigest(),
        "insts_sha256": hashlib.sha256(Path(opts.insts_path).read_bytes()).hexdigest(),
    }
    Path(str(opts.xclbin_path) + ".json").write_text(json.dumps(manifest, indent=2) + "\n")


def validate_shape(k, n):
    if k <= 0 or k % 128 or n <= 0 or n % 64:
        raise ValueError("K must be a positive multiple of 128 and N a positive multiple of 64")
    payload_bytes = k * n // 2 + 3 * n * (k // 128)
    # All three FIFOs are double-buffered on one core; leave 16 KiB for
    # stack and placement headroom in a 64-KiB tile.
    if 2 * (payload_bytes + 2 * k + 2 * n) > 48 * 1024:
        raise ValueError("shape exceeds this single-core bring-up design's 48-KiB FIFO budget")
    return payload_bytes


@iron.jit
def w4a16_linear(
    x: In, weights: In, y: Out, *, k: CompileTime[int] = 128,
    n: CompileTime[int] = 64,
    source_sha256: CompileTime[str] = KERNEL_SOURCE_SHA256,
):
    # Source contents protect default-path JIT recipe caching. The CLI uses
    # explicit output paths and reuses final.prj objects by filename; the
    # content-and-geometry object filename below protects that separate path.
    if source_sha256 != KERNEL_SOURCE_SHA256:
        raise ValueError("source_sha256 does not match this imported kernel source")
    payload_bytes = validate_shape(k, n)
    x_ty = np.ndarray[(k,), np.dtype[bfloat16]]
    weights_ty = np.ndarray[(payload_bytes,), np.dtype[np.uint8]]
    y_ty = np.ndarray[(n,), np.dtype[bfloat16]]
    kernel = ExternalFunction(
        "w4a16_linear_bf16",
        # The explicit-output build directory has an existence-only object
        # cache. Source and geometry must distinguish the object filename.
        object_file_name=f"w4a16_linear_{source_sha256}_k{k}_n{n}.o",
        source_string=KERNEL_SOURCE,
        arg_types=[x_ty, weights_ty, y_ty],
        include_dirs=[config.cxx_header_path()],
        compile_flags=[f"-DHETEROMEGA_K={k}", f"-DHETEROMEGA_N={n}"],
    )
    xs = ObjectFifo(x_ty, depth=2, name="linear_x")
    ws = ObjectFifo(weights_ty, depth=2, name="linear_weights")
    ys = ObjectFifo(y_ty, depth=2, name="linear_y")

    def core_fn(x_in, w_in, y_out, fn):
        x_obj = x_in.acquire(1)
        w_obj = w_in.acquire(1)
        y_obj = y_out.acquire(1)
        fn(x_obj, w_obj, y_obj)
        x_in.release(1)
        w_in.release(1)
        y_out.release(1)

    worker = Worker(core_fn, [xs.cons(), ws.cons(), ys.prod(), kernel])

    def sequence(x_in, w_in, y_out, x_prod, w_prod, y_cons):
        group = TaskGroup()
        x_prod.fill(x_in, group=group)
        w_prod.fill(w_in, group=group)
        y_cons.drain(y_out, wait=True, group=group)
        group.finish()

    runtime = Runtime(sequence, [x_ty, weights_ty, y_ty, xs.prod(), ws.prod(), ys.cons()])
    return Program(iron.get_current_device(), runtime, workers=[worker]).resolve_program()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_compile_args(parser, dev_choices=("npu2",), default_dev="npu2", with_pdi=True, with_emit_mlir=True)
    parser.add_argument("-K", type=int, default=128)
    parser.add_argument("-N", type=int, default=64)
    opts = parser.parse_args()
    validate_shape(opts.K, opts.N)
    run_design_cli(w4a16_linear, opts,
                   compile_kwargs={"k": opts.K, "n": opts.N,
                                   "source_sha256": KERNEL_SOURCE_SHA256},
                   device=lambda o: device_from_args(o, n_cols=None))
    if opts.xclbin_path and not opts.emit_mlir:
        write_manifest(opts)


if __name__ == "__main__":
    main()
