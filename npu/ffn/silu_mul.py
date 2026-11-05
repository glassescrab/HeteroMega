"""Two-input BF16 SiLU-and-multiply array design for MLIR-AIE NPU2.

Targets the IRON API shipped in MLIR-AIE revision
7e00b57955e108fe9d8e9419f5828a0c7e650858. Adapted from its SwiGLU
programming example (AMD, Apache-2.0 WITH LLVM-exception).
All host buffers are flat contiguous BF16 with exactly ``size`` elements.
Each column receives a contiguous channel shard and streams fixed-size tiles.
"""

from pathlib import Path
import argparse
import hashlib
import json

import aie.iron as iron
import numpy as np
from aie.helpers.taplib.tensortiler2d import TensorTiler2D
from aie.iron import (
    CompileTime,
    ExternalFunction,
    In,
    ObjectFifo,
    Out,
    Program,
    Runtime,
    TaskGroup,
    Worker,
)
from aie.utils import config
from aie.utils.hostruntime.argparse import add_compile_args, device_from_args
from aie.utils.hostruntime.cli import run_design_cli
from ml_dtypes import bfloat16


MLIR_AIE_COMMIT = "7e00b57955e108fe9d8e9419f5828a0c7e650858"
KERNEL_SOURCE = Path(__file__).with_name("silu_mul.cc").read_text()
KERNEL_SOURCE_SHA256 = hashlib.sha256(KERNEL_SOURCE.encode()).hexdigest()


def write_manifest(opts):
    """Bind the host shape contract to the successfully compiled binaries."""
    xclbin = Path(opts.xclbin_path)
    instructions = Path(opts.insts_path)
    manifest = {
        "kind": "silu_mul_bf16",
        "size": opts.length,
        "tile_size": opts.tile_size,
        "num_columns": opts.columns,
        "device": opts.dev,
        "xclbin_sha256": hashlib.sha256(xclbin.read_bytes()).hexdigest(),
        "insts_sha256": hashlib.sha256(instructions.read_bytes()).hexdigest(),
        "target_mlir_aie_commit": MLIR_AIE_COMMIT,
        "source_sha256": KERNEL_SOURCE_SHA256,
    }
    path = Path(str(xclbin) + ".json")
    temporary_path = path.with_name(path.name + ".tmp")
    temporary_path.write_text(json.dumps(manifest, indent=2) + "\n")
    temporary_path.replace(path)
    print(f"Artifact manifest: {path}")


def validate_shape(size, tile_size, num_columns):
    if tile_size <= 0 or tile_size % 16:
        raise ValueError("tile_size must be a positive multiple of 16")
    # Three double-buffered FIFOs use 12 * tile_size bytes per worker.
    # Keep room for stack, code data, and the placer on a 64-KiB core.
    if tile_size > 2048:
        raise ValueError("bring-up design supports tile_size <= 2048")
    if num_columns < 1 or num_columns > 8:
        raise ValueError("num_columns must be between 1 and 8")
    if size <= 0 or size % (tile_size * num_columns):
        raise ValueError("size must be a positive multiple of tile_size * num_columns")


@iron.jit
def silu_mul(
    gate_in: In,
    up_in: In,
    output: Out,
    *,
    size: CompileTime[int] = 14336,
    tile_size: CompileTime[int] = 1024,
    num_columns: CompileTime[int] = 1,
    source_sha256: CompileTime[str] = KERNEL_SOURCE_SHA256,
):
    # Default-path JIT builds can reuse whole-design artifacts before source
    # discovery. The explicit-output CLI instead reuses final.prj objects;
    # the content-and-geometry object filename below protects that path.
    # Include source content here to protect the default-path recipe too.
    if source_sha256 != KERNEL_SOURCE_SHA256:
        raise ValueError("source_sha256 does not match this imported kernel source")
    validate_shape(size, tile_size, num_columns)
    device = iron.get_current_device()
    if device is None:
        raise ValueError("select --dev npu2 before constructing the design")
    if num_columns > device.cols:
        raise ValueError("num_columns exceeds the selected device's columns")

    tile_ty = np.ndarray[(tile_size,), np.dtype[bfloat16]]
    transfer_ty = np.ndarray[(size,), np.dtype[bfloat16]]
    kernel = ExternalFunction(
        "silu_mul_bf16",
        # Explicit-output IRON builds reuse final.prj; compile_external_kernel
        # skips any existing object filename without checking its contents.
        # Encode both source and compiler geometry flags in that filename.
        object_file_name=f"silu_mul_{source_sha256}_t{tile_size}.o",
        source_string=KERNEL_SOURCE,
        arg_types=[tile_ty, tile_ty, tile_ty],
        include_dirs=[
            config.cxx_header_path(),
            str(Path(config.cxx_header_path()) / "aie_kernels"),
        ],
        compile_flags=[f"-DHETEROMEGA_TILE_SIZE={tile_size}"],
    )
    gates = [ObjectFifo(tile_ty, depth=2, name=f"gate{i}") for i in range(num_columns)]
    ups = [ObjectFifo(tile_ty, depth=2, name=f"up{i}") for i in range(num_columns)]
    outs = [ObjectFifo(tile_ty, depth=2, name=f"out{i}") for i in range(num_columns)]

    def core_fn(gate, up, out, fn):
        g = gate.acquire(1)
        u = up.acquire(1)
        y = out.acquire(1)
        fn(g, u, y)
        gate.release(1)
        up.release(1)
        out.release(1)

    workers = [
        Worker(core_fn, [gates[i].cons(), ups[i].cons(), outs[i].prod(), kernel])
        for i in range(num_columns)
    ]
    taps = TensorTiler2D.simple_tiler((1, size), (1, size // num_columns))

    def sequence(g, u, y, gate_prods, up_prods, out_conses):
        group = TaskGroup()
        for i in range(num_columns):
            gate_prods[i].fill(g, taps[i], group=group)
            up_prods[i].fill(u, taps[i], group=group)
        for i in range(num_columns):
            out_conses[i].drain(y, taps[i], wait=True, group=group)
        group.finish()

    runtime = Runtime(
        sequence,
        [
            transfer_ty,
            transfer_ty,
            transfer_ty,
            [fifo.prod() for fifo in gates],
            [fifo.prod() for fifo in ups],
            [fifo.cons() for fifo in outs],
        ],
    )
    return Program(device, runtime, workers=workers).resolve_program()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_compile_args(
        parser, dev_choices=("npu2",), default_dev="npu2",
        with_pdi=True, with_emit_mlir=True,
    )
    parser.add_argument("-l", "--length", type=int, default=14336)
    parser.add_argument("--tile-size", type=int, default=1024)
    parser.add_argument("-co", "--columns", type=int, default=1)
    opts = parser.parse_args()
    validate_shape(opts.length, opts.tile_size, opts.columns)
    run_design_cli(
        silu_mul,
        opts,
        compile_kwargs={
            "size": opts.length,
            "tile_size": opts.tile_size,
            "num_columns": opts.columns,
            "source_sha256": KERNEL_SOURCE_SHA256,
        },
        device=lambda o: device_from_args(o, n_cols=None),
    )
    if opts.xclbin_path and not opts.emit_mlir:
        write_manifest(opts)


if __name__ == "__main__":
    main()
