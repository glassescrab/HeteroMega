"""Complete, explicitly host-staged NPU FFN branch for the partition experiment.

The four launches are gate, up, fused SiLU/multiply, and down. All three
quantized weights are packed and uploaded once. Intermediate activations return
to host DRAM between launches; the down-input layout conversion runs on CPU.
This preserves logical channel ownership, not NPU on-chip residency. There is
no CPU arithmetic fallback and no claim of shared GPU/XRT buffer zero-copy.

Only NumPy is needed to import this module. Artifact compilation uses the
explicitly selected IRON Python, while execution imports pyxrt lazily.
"""

from hashlib import sha256
from numbers import Integral
from pathlib import Path
import json
import subprocess
import sys
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
KERNEL_ROOT = ROOT / "npu/ffn"
if str(KERNEL_ROOT) not in sys.path:
    sys.path.insert(0, str(KERNEL_ROOT))
from prefill_reference import LAYOUT_VERSION, WEIGHT_TILE_BYTES, pack_weights
from xrt_runner import XrtRunner, load_manifest


TARGET_COMMIT = "7e00b57955e108fe9d8e9419f5828a0c7e650858"
BUILD_CONTRACT_VERSION = 1


def _positive_aligned(value, name, multiple):
    if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0 or value % multiple:
        raise ValueError(f"{name} must be a positive multiple of {multiple}")
    return int(value)


def _geometry(m, hidden, channels, columns):
    # The shared GPU/CPU-layout contract currently requires M in blocks of 128.
    m = _positive_aligned(m, "M", 128)
    hidden = _positive_aligned(hidden, "hidden size", 128)
    channels = _positive_aligned(channels, "NPU branch channels", 128)
    if m > 4096 or hidden > 16384 or channels > 16384:
        raise ValueError("NPU streaming bounds are M<=4096 and hidden/channels<=16384")
    if isinstance(columns, bool) or not isinstance(columns, Integral) or not 1 <= columns <= 8:
        raise ValueError("columns must be an integer from 1 to 8")
    return m, hidden, channels, int(columns)


def effective_columns(n, maximum=4):
    """Largest supported column count dividing the output N tile count."""
    n = _positive_aligned(n, "projection N", 32)
    if isinstance(maximum, bool) or not isinstance(maximum, Integral) or not 1 <= maximum <= 8:
        raise ValueError("maximum columns must be an integer from 1 to 8")
    nt = n // 32
    for count in range(int(maximum), 0, -1):
        if nt % count == 0 and nt // count <= 64:
            return count
    raise ValueError(f"N={n} needs more columns than maximum={maximum}; at most 64 N tiles per column")


def _source_contract(stem):
    paths = [KERNEL_ROOT / f"{stem}.py", KERNEL_ROOT / f"{stem}.cc"]
    if stem == "w4a16_prefill_reuse":
        paths.append(KERNEL_ROOT / "prefill_schedule.py")
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
            for path in paths}


def _artifact_specs(m, hidden, channels, root, columns=8, design="array8"):
    """CPU-only geometry/provenance description shared by build and load."""
    m, hidden, channels, columns = _geometry(m, hidden, channels, columns)
    if design not in ("array8", "legacy"):
        raise ValueError("NPU design must be 'array8' or 'legacy'")
    if design == "array8" and columns != 8:
        raise ValueError("array8 requires exactly eight columns; select legacy explicitly for another column count")
    root = Path(root).resolve()
    specs = {}
    for label, k, n in (("gate_up", hidden, channels), ("down", channels, hidden)):
        if design == "legacy":
            cols, stem, plan = effective_columns(n, columns), "w4a16_prefill", None
        else:
            from prefill_schedule import plan_prefill
            plan = plan_prefill(m, k, n, columns=8, rows=4, max_reuse=2)
            if plan.columns != 8 or plan.compute_rows != 4 or plan.worker_count != 32:
                raise ValueError("array8 planner must assign all eight columns and 32 compute workers")
            cols, stem = 8, "w4a16_prefill_reuse"
        source = _source_contract(stem)
        fingerprint = sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()[:12]
        name = (f"build_prefill_m{m}_k{k}_n{n}_c{cols}_{fingerprint}" if plan is None else
                f"build_prefill_array8_m{m}_k{k}_n{n}_c8_r{plan.m_reuse}_{fingerprint}")
        expected = {"kind": "w4a16_prefill_bf16", "m": m, "k": k, "n": n,
                    "cols": cols, "tile_m": 16, "tile_k": 128, "tile_n": 32,
                    "group_size": 128, "weight_tile_bytes": WEIGHT_TILE_BYTES}
        arguments = ["-M", str(m), "-K", str(k), "-N", str(n), "-co", str(cols)]
        if plan is not None:
            expected.update(design="array8", compute_rows=4, m_reuse=plan.m_reuse,
                            worker_count=32, m_column_groups=plan.m_column_groups,
                            n_columns=plan.n_columns,
                            schedule_sha256=source["npu/ffn/prefill_schedule.py"])
            arguments.extend(["--max-reuse", "2"])
        specs[label] = {
            "directory": root / name, "stem": stem, "source_sha256": source,
            "expected": expected, "arguments": arguments,
        }
        if plan is not None:
            # Round-trip ensures tuples from dataclass implementations have
            # the same JSON-native representation when provenance is reloaded.
            specs[label]["plan"] = json.loads(json.dumps(plan.to_dict()))
    size = m * channels
    # Array8 must also use all eight SiLU columns. The common M/P>=128
    # contract makes 1024-element tiles divisible across eight columns.
    allowed_columns = (8,) if design == "array8" else range(columns, 0, -1)
    tile, silu_cols = next((tile, cols) for tile in (1024, 512)
                           for cols in allowed_columns if size % (tile * cols) == 0)
    source = _source_contract("silu_mul")
    fingerprint = sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()[:12]
    specs["silu_mul"] = {
        "directory": root / f"build_silu_l{size}_t{tile}_c{silu_cols}_{fingerprint}",
        "stem": "silu_mul", "source_sha256": source,
        "expected": {"kind": "silu_mul_bf16", "size": size, "tile_size": tile,
                     "num_columns": silu_cols, "device": "npu2"},
        "arguments": ["-l", str(size), "--tile-size", str(tile), "-co", str(silu_cols)],
    }
    return specs


def _build_contract(spec):
    contract = {"version": BUILD_CONTRACT_VERSION, "source_sha256": spec["source_sha256"],
                "expected_manifest": spec["expected"], "target_mlir_aie_commit": TARGET_COMMIT}
    if "plan" in spec:
        contract["plan"] = spec["plan"]
    return contract


def _load_artifact(spec):
    directory = spec["directory"]
    xclbin, insts = directory / "final.xclbin", directory / "insts.bin"
    manifest = load_manifest(xclbin, insts, spec["expected"]["kind"])
    expected = dict(spec["expected"], target_mlir_aie_commit=TARGET_COMMIT,
                    source_sha256=spec["source_sha256"][f"npu/ffn/{spec['stem']}.cc"])
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"{directory}: manifest {key}={manifest.get(key)!r}, expected {value!r}")
    contract = json.loads((directory / "build_contract.json").read_text())
    if contract != _build_contract(spec):
        raise ValueError(f"{directory}: stale or missing graph/kernel build provenance")
    artifact = {"xclbin": str(xclbin), "insts": str(insts), "manifest": manifest,
                "build_contract": contract}
    if "plan" in spec:
        artifact["plan"] = spec["plan"]
    return artifact


def build_artifacts(m, hidden, channels, root, columns=8, python_executable=None,
                    npu_design="array8"):
    """Compile missing/stale artifacts, otherwise verify and reuse them.

    ``python_executable`` must name the Python with the pinned MLIR-AIE IRON
    package (for example ironenv/bin/python); the ROCm Torch Python need not
    contain it. Compiler diagnostics are saved in each build directory. Source
    hashes include both the graph and kernel, preventing cross-version reuse.
    Array8 additionally binds the CPU planner and requires exactly eight
    columns. Select ``npu_design='legacy'`` to reproduce the original graph.
    """
    specs = _artifact_specs(m, hidden, channels, root, columns, npu_design)
    python = str(python_executable or sys.executable)
    result = {}
    for label, spec in specs.items():
        try:
            result[label] = _load_artifact(spec)
            continue
        except (FileNotFoundError, ValueError, KeyError):
            pass
        directory = spec["directory"]
        directory.mkdir(parents=True, exist_ok=True)
        command = [python, str(KERNEL_ROOT / f"{spec['stem']}.py"), *spec["arguments"],
                   "--xclbin-path", str(directory / "final.xclbin"),
                   "--insts-path", str(directory / "insts.bin"),
                   "--pdi-path", str(directory / "final.pdi")]
        # Invalid provenance cannot survive a failed or interrupted compilation.
        (directory / "build_contract.json").unlink(missing_ok=True)
        log = directory / "compile.log"
        with log.open("w") as output:
            process = subprocess.run(command, cwd=KERNEL_ROOT, stdout=output,
                                     stderr=subprocess.STDOUT, check=False)
        if process.returncode:
            raise RuntimeError(f"{label} compilation failed ({process.returncode}); see {log}")
        # Validate binary hashes and current kernel before certifying the graph.
        manifest = load_manifest(directory / "final.xclbin", directory / "insts.bin", spec["expected"]["kind"])
        if manifest.get("source_sha256") != spec["source_sha256"][f"npu/ffn/{spec['stem']}.cc"]:
            raise ValueError(f"{label} compiler produced a stale kernel manifest")
        temporary = directory / "build_contract.json.tmp"
        temporary.write_text(json.dumps(_build_contract(spec), indent=2) + "\n")
        temporary.replace(directory / "build_contract.json")
        result[label] = _load_artifact(spec)
    return result


class PersistentXrtRunner(XrtRunner):
    """Allocate BOs once; independently update dynamic inputs and dispatch.

    Instruction length remains BYTES, matching the pinned XRTHostRuntime.
    Timing is host enqueue/wait time, not an NPU device-cycle measurement.
    """

    def __init__(self, xclbin, insts, specs):
        super().__init__(xclbin, insts, specs)
        self.input_write_counts = [0] * (len(self.buffers) - 1)
        self.completed_dispatches = 0

    def write_input(self, index, array):
        if not 0 <= index < len(self.buffers) - 1:
            raise ValueError("input index must refer to an input BO")
        shape, dtype = self.specs[index]
        array = np.asarray(array)
        if array.shape != shape or array.dtype != dtype:
            raise ValueError(f"expected {shape} {dtype}; got {array.shape} {array.dtype}")
        self.buffers[index].write(np.ascontiguousarray(array).view(np.uint8).reshape(-1), 0)
        self.buffers[index].sync(self.xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_TO_DEVICE)
        self.input_write_counts[index] += 1

    def dispatch_wait(self):
        if any(count == 0 for count in self.input_write_counts):
            raise RuntimeError("every input BO must be initialized before dispatch")
        start = time.perf_counter_ns()
        handle = self.kernel(3, self.instruction_bo, self.instruction_bytes, *self.buffers)
        state = handle.wait(10000)
        elapsed_us = (time.perf_counter_ns() - start) / 1000.0
        if state != self.xrt.ert_cmd_state.ERT_CMD_STATE_COMPLETED:
            raise RuntimeError(f"NPU execution failed or timed out: {state}")
        self.completed_dispatches += 1
        return elapsed_us

    def output_bits(self):
        self.buffers[-1].sync(self.xrt.xclBOSyncDirection.XCL_BO_SYNC_BO_FROM_DEVICE)
        shape, dtype = self.specs[-1]
        nbytes = int(np.prod(shape)) * dtype.itemsize
        raw = np.asarray(self.buffers[-1].read(nbytes, 0))
        # The notebook's prebuilt pyxrt under NumPy 2.5.4 produced a zero-
        # stride byte array: every element appeared to equal its first byte.
        # Making that array contiguous silently preserves corrupted values.
        # Reject an invalid byte-buffer ABI before any reinterpretation.
        if (raw.dtype.kind not in "iu" or raw.dtype.itemsize != 1 or raw.shape != (nbytes,)
                or raw.strides[0] <= 0):
            raise RuntimeError(
                "Invalid pyxrt BO.read byte-buffer ABI "
                f"(dtype={raw.dtype}, shape={raw.shape}, strides={raw.strides}); "
                "the notebook's prebuilt pyxrt requires compatible NumPy 1.26.4. "
                "Install numpy==1.26.4 in the isolated runtime and restart Python."
            )
        # A genuine positive-strided byte buffer is safe to copy. Host
        # readback/layout costs remain inside complete FFN timing.
        return np.ascontiguousarray(raw).view(np.uint8).view(dtype).reshape(shape).copy()


def _pack_activation_bits(bits):
    m, k = bits.shape
    return np.ascontiguousarray(bits.reshape(m // 16, 16, k // 128, 128)
        .transpose(0, 2, 1, 3).reshape(m // 16, k // 128, 4, 4, 16, 8)
        .transpose(0, 1, 2, 4, 3, 5)).reshape(-1)


def _unpack_output_bits(bits, m, n):
    return np.ascontiguousarray(bits.reshape(m // 16, n // 32, 4, 4, 4, 8)
        .transpose(0, 2, 4, 1, 3, 5).reshape(m, n))


class NPUBranch:
    """One non-reentrant, reusable FFN channel partition with fixed weights.

    Constructor setup and weight transfers are excluded from inference timing.
    ``run`` includes every host layout conversion, input BO write/sync, four
    completed NPU launches and intermediate/output BO read/sync. It receives
    and returns CPU uint16 arrays encoding logical row-major BF16 matrices.
    The caller must include GPU-to-host/host-to-GPU transfers and output
    reduction when timing a complete heterogeneous FFN.
    """

    def __init__(self, gate, up, down, m, artifact_root, columns=8,
                 npu_design="array8"):
        self.channels, self.hidden = gate.shape
        self.m, self.hidden, self.channels, columns = _geometry(m, self.hidden, self.channels, columns)
        if up.shape != gate.shape or down.shape != (self.hidden, self.channels):
            raise ValueError("gate/up must match [I,H] and down must have shape [H,I]")
        if any(weight.group_size != 128 for weight in (gate, up, down)):
            raise ValueError("NPU branch requires quantization group_size=128")
        specs = _artifact_specs(self.m, self.hidden, self.channels, artifact_root, columns, npu_design)
        artifacts = {label: _load_artifact(spec) for label, spec in specs.items()}
        packed = [pack_weights(weight) for weight in (gate, up, down)]

        def projection(artifact, k, n, weight):
            runner = PersistentXrtRunner(artifact["xclbin"], artifact["insts"],
                [((self.m * k,), np.uint16), ((weight.size,), np.uint8),
                 ((self.m * n,), np.uint16)])
            runner.write_input(1, weight)
            return runner

        self.gate = projection(artifacts["gate_up"], self.hidden, self.channels, packed[0])
        self.up = projection(artifacts["gate_up"], self.hidden, self.channels, packed[1])
        self.down = projection(artifacts["down"], self.channels, self.hidden, packed[2])
        pointwise = artifacts["silu_mul"]
        self.silu = PersistentXrtRunner(pointwise["xclbin"], pointwise["insts"],
            [((self.m * self.channels,), np.uint16)] * 3)
        self.last_diagnostics = {}
        self.metadata = {
            "backend": "mlir_aie_xrt_host_staged_ffn", "layout": LAYOUT_VERSION,
            "npu_design": npu_design,
            "m": self.m, "hidden": self.hidden, "channels": self.channels,
            "columns_requested": columns, "artifacts": artifacts,
            "fixed_weight_uploads": 3, "fixed_weight_bytes": sum(int(w.nbytes) for w in packed),
            "launches_per_run": 4, "cpu_activation_fallback": False,
            "intermediates": "host-staged BF16; CPU layout conversion before down",
            "host_bo_io_bytes_per_run_estimate": 6 * self.m * self.hidden + 12 * self.m * self.channels,
            "host_bo_io_estimate_note": "BO write/read payload bytes, excludes layout copies, instruction reads and device DMA traffic",
            "timing_note": "dispatch/wait intervals are host times; whole-FFN timing must include GPU transfers and boundary sum",
        }

    def run(self, x_bits):
        try:
            from .contract import packed_output_to_activation
        except ImportError:
            from contract import packed_output_to_activation
        x_bits = np.asarray(x_bits)
        if x_bits.dtype != np.uint16 or x_bits.shape != (self.m, self.hidden):
            raise ValueError(f"input must be uint16 BF16 bits with shape {(self.m, self.hidden)}")
        if np.any((x_bits & 0x7F80) == 0x7F80):
            raise ValueError("NPU branch input must contain finite BF16 values")
        start = time.perf_counter_ns()
        stages, waits = {}, {}
        before = time.perf_counter_ns()
        a = _pack_activation_bits(x_bits)
        stages["input_layout_us"] = (time.perf_counter_ns() - before) / 1000.0

        def invoke(label, runner, inputs):
            before = time.perf_counter_ns()
            for index, value in inputs:
                runner.write_input(index, value)
            waits[label] = runner.dispatch_wait()
            result = runner.output_bits()
            stages[f"{label}_with_host_io_us"] = (time.perf_counter_ns() - before) / 1000.0
            return result

        gate = invoke("gate", self.gate, [(0, a)])
        up = invoke("up", self.up, [(0, a)])
        # Both projection buffers have identical packed layouts. Elementwise
        # SiLU/multiply may operate directly on their flat physical ordering.
        z = invoke("silu_mul", self.silu, [(0, gate), (1, up)])
        before = time.perf_counter_ns()
        down_a = packed_output_to_activation(z, self.m, self.channels)
        stages["down_input_layout_us"] = (time.perf_counter_ns() - before) / 1000.0
        y = invoke("down", self.down, [(0, down_a)])
        before = time.perf_counter_ns()
        output = _unpack_output_bits(y, self.m, self.hidden)
        stages["output_layout_us"] = (time.perf_counter_ns() - before) / 1000.0
        self.last_diagnostics = {
            "branch_host_wall_us": (time.perf_counter_ns() - start) / 1000.0,
            "stages": stages, "dispatch_wait_us": waits,
            "completed_dispatches_total": sum(r.completed_dispatches for r in (self.gate, self.up, self.silu, self.down)),
            "weight_upload_counts": {label: runner.input_write_counts[1]
                                     for label, runner in (("gate", self.gate), ("up", self.up), ("down", self.down))},
        }
        return output
