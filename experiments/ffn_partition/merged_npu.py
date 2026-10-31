"""Experimental single-dispatch merged gate/up/SiLU/down NPU branch.

Builds ``npu/ffn/w4a16_merged_upstream.py`` and drives one XRT kernel with
x, gate/up/down, Z and Y buffers. It is intentionally separate from the
production two-launch adapter and is not selected by default.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from .npu_backend import KERNEL_ROOT, TARGET_COMMIT, PersistentXrtRunner
from .upstream_npu import UpstreamWeightBuffer
from xrt_runner import load_manifest


GRAPH = 'w4a16_merged_upstream.py'
SOURCE = 'w4a16_prefill_upstream.cc'
DEPENDENCIES = (GRAPH, 'w4a16_upstream.py', SOURCE, 'upstream_weights.py', 'upstream_schedule.py',
                'prefill_schedule.py', 'prefill_gate_up_schedule.py',
                'prefill_swiglu_schedule.py', 'silu_mul.cc',
                'projection_arithmetic.py', 'upstream_output.py')


def _source_contract():
    return {name: sha256((KERNEL_ROOT / name).read_bytes()).hexdigest()
            for name in DEPENDENCIES}


def merged_spec(m, hidden, channels, gate, up, down, root):
    if not all(isinstance(w, UpstreamWeightBuffer) for w in (gate, up, down)):
        raise TypeError('merged NPU requires UpstreamWeightBuffer objects')
    m, hidden, channels = int(m), int(hidden), int(channels)
    if m % 128 or hidden % 128 or channels % 256:
        raise ValueError('merged NPU requires M/H multiples of 128 and channels a multiple of 256')
    gate.validate_slice(0, 0, hidden, channels)
    up.validate_slice(0, 0, hidden, channels)
    down.validate_slice(0, 0, channels, hidden)
    dependency = _source_contract()
    expected = dict(kind='w4a16_upstream_merged', mode='merged', m=m,
        hidden=hidden, channels=channels,
        weight_k=gate.k, weight_n=gate.n,
        weight_k_down=down.k, weight_n_down=down.n,
        cols=8, worker_count=32, compute_rows=4,
        m_reuse=4, activation_m_reuse=2, weight_tile_bytes=4352,
        segment_pipeline_depth=2, activation_fifo_depth=2,
        z_output_fifo_depth=1, y_output_fifo_depth=1,
        bfp16_native_layout=True, split_m32_a=True,
        preconvert_b=True, preconvert_a=False,
        vector_zero=True, mmul_m_reuse=1,
        input_layout='row_major', output_layout='row_major',
        intermediate_layout='row_major', arithmetic='bfp16',
        compute_format='bfp16', accumulator_format='bf16',
        source_sha256=dependency[SOURCE],
        graph_sha256=dependency[GRAPH],
        weight_layout_sha256=dependency['upstream_weights.py'],
        schedule_sha256=dependency['upstream_schedule.py'],
        dependency_sha256=dependency,
        target_mlir_aie_commit=TARGET_COMMIT)
    fingerprint = sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()[:16]
    directory = Path(root).resolve() / f"upstream_merged_bfp16_m{m}_h{hidden}_p{channels}_{fingerprint}"
    arguments = ['--mode', 'merged', '-M', str(m), '-K', str(hidden), '-N', str(channels),
                 '--weight-k', str(gate.k), '--weight-n', str(gate.n),
                 '--weight-k-down', str(down.k), '--weight-n-down', str(down.n),
                 '-co', '8', '--max-reuse', '4', '--arithmetic', 'bfp16', '--segment-pipeline-depth', '2',
                 '--activation-fifo-depth', '2', '--z-output-fifo-depth', '1',
                 '--y-output-fifo-depth', '1', '--vector-zero',
                 '--bfp16-native-layout', '--split-m32-a', '--preconvert-b']
    return {'directory': directory, 'expected': expected, 'arguments': arguments,
            'source_sha256': dependency}


def _validate_manifest(spec):
    directory = spec['directory']
    xclbin, insts = directory / 'final.xclbin', directory / 'insts.bin'
    manifest = load_manifest(xclbin, insts, spec['expected']['kind'])
    for key, expected in spec['expected'].items():
        if manifest.get(key) != expected:
            raise ValueError(f'{directory}: manifest {key}={manifest.get(key)!r}, expected {expected!r}')
    return manifest


def _load_artifact(spec):
    manifest = _validate_manifest(spec)
    return {'xclbin': str(spec['directory'] / 'final.xclbin'),
            'insts': str(spec['directory'] / 'insts.bin'), 'manifest': manifest}


def build_merged_artifact(m, hidden, channels, gate, up, down, root, python_executable=None):
    spec = merged_spec(m, hidden, channels, gate, up, down, root)
    try:
        return _load_artifact(spec)
    except (FileNotFoundError, ValueError, KeyError):
        pass
    directory = spec['directory']
    directory.mkdir(parents=True, exist_ok=True)
    command = [str(python_executable or sys.executable), str(KERNEL_ROOT / GRAPH),
               *spec['arguments'], '--xclbin-path', str(directory / 'final.xclbin'),
               '--insts-path', str(directory / 'insts.bin'),
               '--pdi-path', str(directory / 'final.pdi')]
    log = directory / 'compile.log'
    with log.open('w') as output:
        result = subprocess.run(command, cwd=KERNEL_ROOT, stdout=output,
                                stderr=subprocess.STDOUT, check=False)
    if result.returncode:
        raise RuntimeError(f'merged graph compilation failed ({result.returncode}); see {log}')
    _validate_manifest(spec)
    (directory / 'build_contract.json').write_text(json.dumps(
        {'version': 1, 'source_sha256': spec['source_sha256'],
         'expected_manifest': spec['expected']}, indent=2) + '\n')
    return _load_artifact(spec)


class MergedUpstreamNpuFFN:
    """One merged NPU launch per complete partial-FFN call."""

    def __init__(self, m, hidden, channels, gate, up, down, artifact_root, *,
                 python_executable=None, build=True):
        if build:
            artifact = build_merged_artifact(m, hidden, channels, gate, up, down,
                                             artifact_root, python_executable)
        else:
            artifact = _load_artifact(merged_spec(m, hidden, channels, gate, up, down, artifact_root))
        self.m, self.hidden, self.channels = int(m), int(hidden), int(channels)
        self.weights = (gate, up, down)
        self.artifacts = {'merged': artifact}
        specs = [((m * hidden,), np.uint16),
                 ((gate.nbytes,), np.uint8),
                 ((up.nbytes,), np.uint8),
                 ((down.nbytes,), np.uint8),
                 ((m * channels,), np.uint16),
                 ((m * hidden,), np.uint16)]
        self.runner = PersistentXrtRunner(artifact['xclbin'], artifact['insts'], specs,
                                          output_count=2)
        self.runner.write_input(1, gate.data)
        self.runner.write_input(2, up.data)
        self.runner.write_input(3, down.data)
        self.last_diagnostics = {}
        self.metadata = dict(backend='mlir_aie_xrt_upstream_merged', arithmetic='bfp16',
            npu_arithmetic='bfp16', compute_format='bfp16', merged_kernel=True,
            launches_per_run=1, m=self.m, hidden=self.hidden, channels=self.channels,
            weight_layout='upstream_4352', weight_tile_bytes=4352,
            weight_repacking=False, full_weight_buffers=True,
            input_layout='row_major', output_layout='row_major', intermediate_layout='row_major',
            artifact=artifact, completed_dispatches=0)

    def run(self, x_bits):
        x_bits = np.asarray(x_bits)
        if x_bits.dtype != np.uint16 or x_bits.shape != (self.m, self.hidden):
            raise ValueError(f'input must be uint16 BF16 bits with shape {(self.m, self.hidden)}')
        if np.any((x_bits & 0x7F80) == 0x7F80):
            raise ValueError('input must contain finite BF16 values')
        start = time.perf_counter_ns()
        before = time.perf_counter_ns()
        activation = np.ascontiguousarray(x_bits).reshape(-1)
        input_layout_us = (time.perf_counter_ns() - before) / 1000.0
        before = time.perf_counter_ns()
        self.runner.write_input(0, activation)
        waits = self.runner.dispatch_wait()
        y = self.runner.output_bits(index=1, copy=True).reshape(self.m, self.hidden)
        host_io_us = (time.perf_counter_ns() - before) / 1000.0
        elapsed = (time.perf_counter_ns() - start) / 1000.0
        self.last_output = y.copy()
        self.last_diagnostics = dict(branch_host_wall_us=elapsed,
            input_layout_us=input_layout_us, dispatch_io_us=host_io_us,
            dispatch_wait_us={'merged': waits},
            completed_dispatches_total=self.runner.completed_dispatches,
            merged_kernel=True, launches_per_run=1,
            input_write_counts={'x': self.runner.input_write_counts[0],
                                'gate': self.runner.input_write_counts[1],
                                'up': self.runner.input_write_counts[2],
                                'down': self.runner.input_write_counts[3]})
        return y.copy()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--m', type=int, default=512)
    ap.add_argument('--hidden', type=int, default=4096)
    ap.add_argument('--intermediate', type=int, default=14336)
    ap.add_argument('--channels', type=int, default=4352)
    ap.add_argument('--seed', type=int, default=12832)
    ap.add_argument('--artifact-root', type=Path, default=Path('experiments/ffn_partition/artifacts'))
    ap.add_argument('--iron-python')
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--warmup', type=int, default=2)
    ap.add_argument('--iterations', type=int, default=5)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--compare-two-launch', action='store_true')
    args = ap.parse_args()
    from .contract import random_weights, reference_partitioned, bf16
    from .run_upstream_partition import prepare_original_weights, array_hash
    weights = random_weights(args.hidden, args.intermediate, args.seed)
    original = prepare_original_weights(weights)
    npu = MergedUpstreamNpuFFN(args.m, args.hidden, args.channels, *original,
        args.artifact_root, python_executable=args.iron_python, build=not args.no_build)
    rng = np.random.default_rng(args.seed + 1)
    inputs = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32)) for _ in range(2)]
    refs = [reference_partitioned(x, weights, args.channels)[1]['npu'] for x in inputs]
    two = None
    if args.compare_two_launch:
        from .upstream_npu import UpstreamNpuFFN
        two = UpstreamNpuFFN(args.m, args.hidden, args.channels, *original,
            args.artifact_root, channel_start=0, copy_output_bits=False,
            swiglu_reuse=4, down_reuse=4,
            swiglu_activation_fifo_depth=2, down_activation_fifo_depth=2,
            vector_zero=True, mmul_m_reuse=1, output_layout='down_a',
            swiglu_input_layout='row_major', arithmetic='bfp16',
            down_output_layout='row_major', swiglu_output_fifo_depth=1,
            down_output_fifo_depth=2, bfp16_native_layout=True,
            split_m32_a=True, preconvert_b=True)
    records = []
    for iteration in range(-args.warmup, args.iterations):
        index = iteration % 2
        x_bits = (inputs[index].astype(np.float32).view(np.uint32) >> 16).astype(np.uint16)
        y = npu.run(x_bits).view(np.uint16)
        if y.shape != (args.m, args.hidden):
            raise RuntimeError(f'unexpected output shape {y.shape}')
        yf = (y.astype(np.uint32) << 16).view(np.float32).reshape(args.m, args.hidden)
        rf = np.asarray(refs[index], dtype=np.float32).reshape(args.m, args.hidden)
        rel = float(np.linalg.norm(yf - rf) / max(np.linalg.norm(rf), 1e-12))
        record = dict(iteration=iteration, input_index=index,
            wall_us=npu.last_diagnostics['branch_host_wall_us'],
            diagnostics=npu.last_diagnostics, relative_l2=rel,
            output_sha256=array_hash(y))
        if two is not None:
            y2 = two.run(x_bits)
            y2f = (y2.view(np.uint16).astype(np.uint32) << 16).view(np.float32).reshape(args.m, args.hidden)
            record['two_launch_relative_l2'] = float(np.linalg.norm(y2f - rf) / max(np.linalg.norm(rf), 1e-12))
            record['merged_vs_two_launch_relative_l2'] = float(
                np.linalg.norm(yf - y2f) / max(np.linalg.norm(y2f), 1e-12))
            record['merged_vs_two_launch_exact'] = bool(np.array_equal(y, y2.view(np.uint16)))
            record['two_launch_output_sha256'] = array_hash(y2.view(np.uint16))
        if iteration >= 0:
            records.append(record)
        print(json.dumps(record), flush=True)
    stats = {}
    if records:
        xs = [r['wall_us'] for r in records]
        stats = dict(count=len(xs), median_us=float(np.median(xs)), min_us=min(xs), max_us=max(xs))
    result = dict(status='measured', config=vars(args), metadata=npu.metadata,
                  stats=stats, records=records)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, default=str) + '\n')
    print(json.dumps({'stats': stats, 'metadata': {k: npu.metadata[k] for k in
        ('merged_kernel','launches_per_run','channels','m','hidden')}}, indent=2))


if __name__ == '__main__':
    main()


GATE_UP_GRAPH = 'w4a16_merged_gate_up.py'
GATE_UP_DEPENDENCIES = (GATE_UP_GRAPH, 'w4a16_upstream.py', SOURCE,
                        'upstream_weights.py', 'upstream_schedule.py',
                        'upstream_output.py', 'prefill_schedule.py',
                        'prefill_gate_up_schedule.py', 'prefill_swiglu_schedule.py',
                        'silu_mul.cc', 'projection_arithmetic.py')


def _gate_up_source_contract():
    return {name: sha256((KERNEL_ROOT / name).read_bytes()).hexdigest()
            for name in GATE_UP_DEPENDENCIES}


def merged_gate_up_spec(m, hidden, channels, gate, up, down, root):
    if not all(isinstance(w, UpstreamWeightBuffer) for w in (gate, up)):
        raise TypeError('gate/up NPU requires UpstreamWeightBuffer objects')
    m, hidden, channels = int(m), int(hidden), int(channels)
    if m % 128 or hidden % 128 or channels % 256 or channels > 8192:
        raise ValueError('gate/up NPU requires M/H multiples of 128 and 256 <= P <= 8192')
    gate.validate_slice(0, 0, hidden, channels)
    up.validate_slice(0, 0, hidden, channels)
    dependency = _gate_up_source_contract()
    expected = dict(kind='w4a16_upstream_merged_gate_up', mode='merged_gate_up',
        m=m, hidden=hidden, channels=channels, weight_k=gate.k, weight_n=gate.n,
        cols=8, worker_count=32, compute_rows=4, m_reuse=4,
        activation_m_reuse=2, weight_tile_bytes=4352,
        segment_pipeline_depth=2, activation_fifo_depth=2,
        z_output_fifo_depth=1, bfp16_native_layout=True, split_m32_a=True,
        preconvert_b=True, preconvert_a=False, vector_zero=True,
        mmul_m_reuse=1, input_layout='row_major', output_layout='row_major',
        intermediate_layout='row_major', arithmetic='bfp16',
        compute_format='bfp16', accumulator_format='bf16',
        source_sha256=dependency[SOURCE],
        graph_sha256=dependency[GATE_UP_GRAPH],
        weight_layout_sha256=dependency['upstream_weights.py'],
        schedule_sha256=dependency['upstream_schedule.py'],
        dependency_sha256=dependency, target_mlir_aie_commit=TARGET_COMMIT)
    fingerprint = sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()[:16]
    directory = Path(root).resolve() / f"upstream_merged_gate_up_bfp16_m{m}_h{hidden}_p{channels}_{fingerprint}"
    arguments = ['-M', str(m), '-K', str(hidden), '-N', str(channels),
                 '--weight-k', str(gate.k), '--weight-n', str(gate.n),
                 '-co', '8', '--max-reuse', '4', '--segment-pipeline-depth', '2',
                 '--activation-fifo-depth', '2', '--z-output-fifo-depth', '1',
                 '--vector-zero']
    return {'directory': directory, 'expected': expected, 'arguments': arguments,
            'source_sha256': dependency}


def _validate_gate_up_manifest(spec):
    directory = spec['directory']
    manifest = load_manifest(directory / 'final.xclbin', directory / 'insts.bin',
                             spec['expected']['kind'])
    for key, expected in spec['expected'].items():
        if manifest.get(key) != expected:
            raise ValueError(f'{directory}: manifest {key}={manifest.get(key)!r}, expected {expected!r}')
    return manifest


def _load_gate_up_artifact(spec):
    manifest = _validate_gate_up_manifest(spec)
    return {'xclbin': str(spec['directory'] / 'final.xclbin'),
            'insts': str(spec['directory'] / 'insts.bin'), 'manifest': manifest}


def build_merged_gate_up_artifact(m, hidden, channels, gate, up, down, root, python_executable=None):
    spec = merged_gate_up_spec(m, hidden, channels, gate, up, down, root)
    try:
        return _load_gate_up_artifact(spec)
    except (FileNotFoundError, ValueError, KeyError):
        pass
    directory = spec['directory']
    directory.mkdir(parents=True, exist_ok=True)
    command = [str(python_executable or sys.executable), str(KERNEL_ROOT / GATE_UP_GRAPH),
               *spec['arguments'], '--xclbin-path', str(directory / 'final.xclbin'),
               '--insts-path', str(directory / 'insts.bin'),
               '--pdi-path', str(directory / 'final.pdi')]
    log = directory / 'compile.log'
    with log.open('w') as output:
        result = subprocess.run(command, cwd=KERNEL_ROOT, stdout=output,
                                stderr=subprocess.STDOUT, check=False)
    if result.returncode:
        raise RuntimeError(f'gate/up merged graph compilation failed ({result.returncode}); see {log}')
    _validate_gate_up_manifest(spec)
    (directory / 'build_contract.json').write_text(json.dumps(
        {'version': 1, 'source_sha256': spec['source_sha256'],
         'expected_manifest': spec['expected']}, indent=2) + '\n')
    return _load_gate_up_artifact(spec)


class MergedGateUpNpuFFN:
    """One merged gate/up+SiLU NPU launch; returns row-major NPU Z."""

    def __init__(self, m, hidden, channels, gate, up, down, artifact_root, *,
                 python_executable=None, build=True):
        if build:
            artifact = build_merged_gate_up_artifact(m, hidden, channels, gate, up, down,
                                                     artifact_root, python_executable)
        else:
            artifact = _load_gate_up_artifact(merged_gate_up_spec(
                m, hidden, channels, gate, up, down, artifact_root))
        self.m, self.hidden, self.channels = int(m), int(hidden), int(channels)
        self.weights = (gate, up, down)
        self.artifacts = {'gate_up': artifact}
        specs = [((m * hidden,), np.uint16), ((gate.nbytes,), np.uint8),
                 ((up.nbytes,), np.uint8), ((m * channels,), np.uint16)]
        self.runner = PersistentXrtRunner(artifact['xclbin'], artifact['insts'], specs,
                                          output_count=1)
        self.runner.write_input(1, gate.data)
        self.runner.write_input(2, up.data)
        self.last_output = None
        self.last_diagnostics = {}
        self.metadata = dict(backend='mlir_aie_xrt_upstream_merged_gate_up',
            arithmetic='bfp16', npu_arithmetic='bfp16', compute_format='bfp16',
            merged_kernel=True, gate_up_only=True, launches_per_run=1,
            m=self.m, hidden=self.hidden, channels=self.channels,
            weight_layout='upstream_4352', weight_tile_bytes=4352,
            weight_repacking=False, full_weight_buffers=True,
            input_layout='row_major', output_layout='row_major',
            intermediate_layout='row_major', artifact=artifact)

    def run(self, x_bits):
        x_bits = np.asarray(x_bits)
        if x_bits.dtype != np.uint16 or x_bits.shape != (self.m, self.hidden):
            raise ValueError(f'input must be uint16 BF16 bits with shape {(self.m, self.hidden)}')
        if np.any((x_bits & 0x7F80) == 0x7F80):
            raise ValueError('input must contain finite BF16 values')
        start = time.perf_counter_ns()
        self.runner.write_input(0, np.ascontiguousarray(x_bits).reshape(-1))
        waits = self.runner.dispatch_wait()
        z = self.runner.output_bits(index=0, copy=True).reshape(self.m, self.channels)
        elapsed = (time.perf_counter_ns() - start) / 1000.0
        self.last_output = z.copy()
        self.last_diagnostics = dict(branch_host_wall_us=elapsed,
            dispatch_wait_us={'gate_up': waits},
            completed_dispatches_total=self.runner.completed_dispatches,
            merged_kernel=True, gate_up_only=True, launches_per_run=1,
            input_write_counts={'x': self.runner.input_write_counts[0],
                                'gate': self.runner.input_write_counts[1],
                                'up': self.runner.input_write_counts[2]})
        return z.copy()
