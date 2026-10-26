"""Native-BF16 FFN execution from existing glassescrab packed weight BO data.

This adapter uploads the supplied complete 4,352-byte-tile weight buffers
unchanged. Graph DMA selects the requested FFN channel slice; there is no
weight conversion, compact-tile fallback or gate/up concatenation here.
Weights are uploaded once at construction. Activations still use the existing
host-staged compact A/Y layouts and the Z-to-down CPU layout permutation.
No zero-copy or on-chip-residency claim is made across the two launches.
"""

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

try:
    from .npu_backend import (KERNEL_ROOT, TARGET_COMMIT, PersistentXrtRunner,
                              _geometry, _pack_activation_bits, _unpack_output_bits)
    from .contract import packed_output_to_activation
except ImportError:
    from npu_backend import (KERNEL_ROOT, TARGET_COMMIT, PersistentXrtRunner,
                             _geometry, _pack_activation_bits, _unpack_output_bits)
    from contract import packed_output_to_activation

from upstream_weights import UpstreamWeightBuffer, UPSTREAM_LAYOUT_VERSION, WEIGHT_TILE_BYTES
from upstream_schedule import plan_upstream, validate_segment_pipeline_depth
from projection_arithmetic import UPSTREAM_KERNEL_COMMIT
from xrt_runner import load_manifest


BUILD_CONTRACT_VERSION = 1
GRAPH = "w4a16_upstream.py"
SOURCE = "w4a16_prefill_upstream.cc"
DEPENDENCIES = (GRAPH, SOURCE, "upstream_weights.py", "upstream_schedule.py",
                "prefill_schedule.py", "prefill_gate_up_schedule.py",
                "prefill_swiglu_schedule.py", "silu_mul.cc", "projection_arithmetic.py")


def _source_contract():
    return {name: sha256((KERNEL_ROOT / name).read_bytes()).hexdigest()
            for name in DEPENDENCIES}


def _artifact_spec(mode, m, k, n, weight, root, *, k_start=0, n_start=0,
                   segment_pipeline_depth=2):
    if mode not in ("projection", "swiglu"):
        raise ValueError("upstream graph mode must be projection or swiglu")
    if not isinstance(weight, UpstreamWeightBuffer):
        raise TypeError("weights must be an UpstreamWeightBuffer; implicit packing is unsupported")
    segment_pipeline_depth = validate_segment_pipeline_depth(segment_pipeline_depth)
    weight.validate_slice(k_start, n_start, k, n)
    plan = plan_upstream(m, k, n, mode=mode, weight_k=weight.k, weight_n=weight.n,
                         k_start=k_start, n_start=n_start, columns=8, max_reuse=2)
    dependency = _source_contract()
    expected = dict(kind="w4a16_upstream_bf16", mode=mode, m=m, k=k, n=n,
        weight_k=weight.k, weight_n=weight.n, k_start=k_start, n_start=n_start,
        cols=8, compute_rows=4, worker_count=32,
        m_reuse=plan.base.m_reuse, worker_stack_size=2048,
        segment_pipeline_depth=segment_pipeline_depth,
        weight_layout=UPSTREAM_LAYOUT_VERSION, weight_tile_bytes=WEIGHT_TILE_BYTES,
        arithmetic="bf16", compute_format="bf16",
        upstream_kernel_commit=UPSTREAM_KERNEL_COMMIT,
        target_mlir_aie_commit=TARGET_COMMIT,
        source_sha256=dependency[SOURCE], graph_sha256=dependency[GRAPH],
        weight_layout_sha256=dependency["upstream_weights.py"],
        schedule_sha256=dependency["upstream_schedule.py"], dependency_sha256=dependency)
    fingerprint = sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()[:16]
    directory = Path(root).resolve() / f"upstream_bf16_{mode}_m{m}_k{k}_n{n}_{fingerprint}"
    arguments = ["--mode", mode, "-M", str(m), "-K", str(k), "-N", str(n),
                 "--weight-k", str(weight.k), "--weight-n", str(weight.n),
                 "--k-start", str(k_start), "--n-start", str(n_start),
                 "-co", "8", "--max-reuse", "2",
                 "--segment-pipeline-depth", str(segment_pipeline_depth)]
    return {"directory": directory, "expected": expected,
            "source_sha256": dependency, "arguments": arguments}


def _ffn_specs(m, hidden, channels, gate, up, down, root, channel_start=0,
               *, segment_pipeline_depth=2):
    m, hidden, channels, _ = _geometry(m, hidden, channels, 8)
    if any(not isinstance(w, UpstreamWeightBuffer) for w in (gate, up, down)):
        raise TypeError("gate/up/down must be UpstreamWeightBuffer objects; implicit packing is unsupported")
    if (gate.k != hidden or up.k != hidden or down.n != hidden
            or gate.n != up.n or gate.n != down.k):
        raise ValueError("full gate/up must be [intermediate, hidden] and down [hidden, intermediate]")
    # Down's K128 group boundary also constrains the shared channel start.
    gate.validate_slice(0, channel_start, hidden, channels)
    up.validate_slice(0, channel_start, hidden, channels)
    down.validate_slice(channel_start, 0, channels, hidden)
    return {
        "swiglu": _artifact_spec("swiglu", m, hidden, channels, gate, root,
                                 n_start=channel_start,
                                 segment_pipeline_depth=segment_pipeline_depth),
        "down": _artifact_spec("projection", m, channels, hidden, down, root,
                               k_start=channel_start,
                               segment_pipeline_depth=segment_pipeline_depth),
    }


def _build_contract(spec):
    return {"version": BUILD_CONTRACT_VERSION,
            "source_sha256": spec["source_sha256"],
            "expected_manifest": spec["expected"],
            "target_mlir_aie_commit": TARGET_COMMIT}


def _validate_manifest(spec):
    directory = spec["directory"]
    xclbin, insts = directory / "final.xclbin", directory / "insts.bin"
    manifest = load_manifest(xclbin, insts, "w4a16_upstream_bf16")
    for key, expected in spec["expected"].items():
        if manifest.get(key) != expected:
            raise ValueError(f"{directory}: manifest {key}={manifest.get(key)!r}, expected {expected!r}")
    return manifest


def _load_artifact(spec):
    manifest = _validate_manifest(spec)
    directory = spec["directory"]
    contract = json.loads((directory / "build_contract.json").read_text())
    if contract != _build_contract(spec):
        raise ValueError(f"{directory}: stale or missing upstream graph build provenance")
    return {"xclbin": str(directory / "final.xclbin"),
            "insts": str(directory / "insts.bin"), "manifest": manifest,
            "build_contract": contract}


def build_upstream_artifacts(m, hidden, channels, gate, up, down, artifact_root,
                             *, channel_start=0, python_executable=None,
                             segment_pipeline_depth=2):
    """Compile missing/stale native-BF16 artifacts for unchanged full buffers.

    ``python_executable`` should name the configured IRON environment. This
    function never edits, slices, concatenates or repacks a weight buffer.
    """
    specs = _ffn_specs(m, hidden, channels, gate, up, down, artifact_root, channel_start,
                       segment_pipeline_depth=segment_pipeline_depth)
    artifacts = {}
    for label, spec in specs.items():
        try:
            artifacts[label] = _load_artifact(spec)
            continue
        except (FileNotFoundError, ValueError, KeyError):
            pass
        directory = spec["directory"]
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "build_contract.json").unlink(missing_ok=True)
        command = [str(python_executable or sys.executable), str(KERNEL_ROOT / GRAPH),
                   *spec["arguments"], "--xclbin-path", str(directory / "final.xclbin"),
                   "--insts-path", str(directory / "insts.bin"),
                   "--pdi-path", str(directory / "final.pdi")]
        log = directory / "compile.log"
        with log.open("w") as output:
            result = subprocess.run(command, cwd=KERNEL_ROOT, stdout=output,
                                    stderr=subprocess.STDOUT, check=False)
        if result.returncode:
            raise RuntimeError(f"upstream {label} compilation failed ({result.returncode}); see {log}")
        _validate_manifest(spec)
        temporary = directory / "build_contract.json.tmp"
        temporary.write_text(json.dumps(_build_contract(spec), indent=2) + "\n")
        temporary.replace(directory / "build_contract.json")
        artifacts[label] = _load_artifact(spec)
    return artifacts


class UpstreamNpuFFN:
    """Non-reentrant two-launch FFN over a slice of existing packed weights.

    Construction loads already-built artifacts and uploads the exact provided
    weight bytes once. ``run`` accepts/returns row-major uint16 BF16 bits and
    includes all activation layouts, BO writes/reads, waits and synchronization.
    GPU transfers and the GPU/NPU partial-output sum remain caller operations.
    """

    def __init__(self, m, hidden, channels, gate, up, down, artifact_root, *,
                 channel_start=0, copy_output_bits=True, segment_pipeline_depth=2):
        specs = _ffn_specs(m, hidden, channels, gate, up, down, artifact_root, channel_start,
                           segment_pipeline_depth=segment_pipeline_depth)
        artifacts = {label: _load_artifact(spec) for label, spec in specs.items()}
        self.m, self.hidden, self.channels, _ = _geometry(m, hidden, channels, 8)
        self.channel_start = int(channel_start)
        self.copy_output_bits = bool(copy_output_bits)
        self.weights = (gate, up, down)  # Keep the caller's original buffers alive.
        swiglu = artifacts["swiglu"]
        self.swiglu = PersistentXrtRunner(swiglu["xclbin"], swiglu["insts"],
            [((self.m * self.hidden,), np.uint16),
             ((gate.nbytes,), np.uint8), ((up.nbytes,), np.uint8),
             ((self.m * self.channels,), np.uint16)])
        projection = artifacts["down"]
        self.down = PersistentXrtRunner(projection["xclbin"], projection["insts"],
            [((self.m * self.channels,), np.uint16), ((down.nbytes,), np.uint8),
             ((self.m * self.hidden,), np.uint16)])
        # Pass the original arrays directly. The XRT upload is a BO copy, not
        # a weight-format conversion; no temporary packed weights are made.
        self.swiglu.write_input(1, gate.data)
        self.swiglu.write_input(2, up.data)
        self.down.write_input(1, down.data)
        self.runners = {"swiglu": self.swiglu, "down": self.down}
        self.projection_runners = self.runners
        self.last_diagnostics = {}
        self.metadata = dict(backend="mlir_aie_xrt_upstream_weight_ffn", arithmetic="bf16",
            npu_arithmetic="bf16", compute_format="bf16", npu_design="array8",
            weight_layout=UPSTREAM_LAYOUT_VERSION, weight_tile_bytes=WEIGHT_TILE_BYTES,
            weight_repacking=False, full_weight_buffers=True, m=self.m, hidden=self.hidden,
            channels=self.channels, channel_start=self.channel_start,
            segment_pipeline_depth=segment_pipeline_depth,
            full_intermediate=gate.n, columns_requested=8, worker_count=32,
            fuse_gate_up=True, fuse_swiglu=True, launches_per_run=2,
            fixed_weight_uploads=3, fixed_weight_bytes=sum(w.nbytes for w in self.weights),
            artifacts=artifacts, cpu_activation_fallback=False,
            host_output_readback="owned_copy" if self.copy_output_bits else "borrowed_until_consumed",
            intermediates="gate/up on-chip through SiLU/multiply; Z host-staged with CPU layout conversion before down",
            host_bo_io_bytes_per_run_estimate=4 * self.m * (self.hidden + self.channels),
            timing_note="whole FFN timing must additionally include GPU transfers and boundary sum")

    def run(self, x_bits):
        x_bits = np.asarray(x_bits)
        if x_bits.dtype != np.uint16 or x_bits.shape != (self.m, self.hidden):
            raise ValueError(f"input must be uint16 BF16 bits with shape {(self.m, self.hidden)}")
        if np.any((x_bits & 0x7F80) == 0x7F80):
            raise ValueError("NPU branch input must contain finite BF16 values")
        start = time.perf_counter_ns()
        stages, waits = {}, {}
        before = time.perf_counter_ns()
        activation = _pack_activation_bits(x_bits)
        stages["input_layout_us"] = (time.perf_counter_ns() - before) / 1000.0

        def invoke(label, runner, values):
            before = time.perf_counter_ns()
            runner.write_input(0, values)
            waits[label] = runner.dispatch_wait()
            result = runner.output_bits(copy=self.copy_output_bits)
            stages[f"{label}_with_host_io_us"] = (time.perf_counter_ns() - before) / 1000.0
            return result

        z = invoke("swiglu", self.swiglu, activation)
        before = time.perf_counter_ns()
        down_a = packed_output_to_activation(z, self.m, self.channels)
        stages["down_input_layout_us"] = (time.perf_counter_ns() - before) / 1000.0
        y = invoke("down", self.down, down_a)
        before = time.perf_counter_ns()
        output = _unpack_output_bits(y, self.m, self.hidden)
        stages["output_layout_us"] = (time.perf_counter_ns() - before) / 1000.0
        self.last_diagnostics = {
            "branch_host_wall_us": (time.perf_counter_ns() - start) / 1000.0,
            "stages": stages, "dispatch_wait_us": waits,
            "completed_dispatches_total": sum(r.completed_dispatches for r in self.runners.values()),
            "weight_upload_counts": {"gate": self.swiglu.input_write_counts[1],
                                     "up": self.swiglu.input_write_counts[2],
                                     "down": self.down.input_write_counts[1]},
        }
        return output
