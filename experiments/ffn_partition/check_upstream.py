"""Bounded device checks for native BF16 with unchanged upstream W4A16 bytes.

Run with ``python -m experiments.ffn_partition.check_upstream --help``.
Synthetic fixtures are produced directly by an independent transcription of
glassescrab's original N64/K128 packer. No compact weight conversion is used.
The CPU oracle retains BF16 input/dequantization/output boundaries and FP32
K-group partials; it is not a bitwise AIE simulator. Original strict error
bounds apply. This is a correctness check, not a performance benchmark.
"""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import gc
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

import numpy as np

from .npu_backend import KERNEL_ROOT, ROOT
from .upstream_npu import (GRAPH, UpstreamNpuFFN, _artifact_spec, _build_contract,
                           _ffn_specs, _load_artifact, _validate_manifest)
from prefill_reference import (bf16_bits, bf16_from_bits, error_metrics,
                               pack_activations, unpack_output, unpack_activations)
from reference import bf16, silu_multiply
from upstream_weights import UpstreamWeightBuffer, UPSTREAM_LAYOUT_VERSION
from xrt_runner import XrtRunner


def _hash(value):
    return sha256(np.ascontiguousarray(value).view(np.uint8)).hexdigest()


@dataclass
class WeightFixture:
    weight: UpstreamWeightBuffer
    q: np.ndarray
    scales: np.ndarray
    zeros: np.ndarray

    def dense_slice(self, k_start, n_start, k, n):
        self.weight.validate_slice(k_start, n_start, k, n)
        ns = slice(n_start, n_start + n)
        groups = slice(k_start // 128, (k_start + k) // 128)
        scales = np.repeat(self.scales[groups, ns], 128, axis=0)
        zeros = np.repeat(self.zeros[groups, ns], 128, axis=0)
        q = self.q[k_start:k_start + k, ns].astype(np.float32)
        return bf16((q - zeros.astype(np.float32)) * scales)


def prepare_weights(k, n, seed, scale_divisor=1024.0):
    """Create original-format test data, without calling a production packer.

    The upstream order is col_mod, N64 tile, K128 group, K8 tile, N8 tile,
    K lane, N pair. INT4 nibbles are low-even/high-odd along N. Each N8 zero
    vector is duplicated in place, rather than duplicating the whole N64 row.
    q and zero values cover [0, 15]; scales vary by channel and K group.
    Returned original weight bytes are read-only so accidental mutation fails.
    """
    if k <= 0 or n <= 0 or k % 128 or n % 64:
        raise ValueError("fixture K/N must be positive multiples of 128/64")
    if not np.isfinite(scale_divisor) or scale_divisor <= 0:
        raise ValueError("fixture scale divisor must be finite and positive")
    rng = np.random.default_rng(seed)
    q = rng.integers(0, 16, size=(k, n), dtype=np.uint8)
    zeros = rng.integers(0, 16, size=(k // 128, n), dtype=np.uint8)
    scales = bf16(rng.uniform(0.5, 2.5, size=zeros.shape).astype(np.float32)
                  / scale_divisor)
    data = np.empty((k // 128) * (n // 64) * 4352, np.uint8)
    cursor = 0
    for col_mod in range(8):
        for nt in range(col_mod, n // 64, 8):
            ns = slice(nt * 64, (nt + 1) * 64)
            for kg in range(k // 128):
                payload = data[cursor:cursor + 4352]
                # Vectorized transcription of upstream's K8/N8 microtile loops.
                blocks = q[kg * 128:(kg + 1) * 128, ns].reshape(
                    16, 8, 8, 8).transpose(0, 2, 1, 3)
                payload[:4096] = (blocks[..., 0::2]
                                  | (blocks[..., 1::2] << 4)).reshape(-1)
                payload[4096:4224] = bf16_bits(scales[kg, ns]).view(np.uint8)
                payload[4224:] = np.repeat(
                    zeros[kg, ns].reshape(8, 1, 8), 2, axis=1).reshape(-1)
                cursor += 4352
    data.flags.writeable = False
    return WeightFixture(UpstreamWeightBuffer(data, k, n), q, scales, zeros)


def _build(spec, args):
    try:
        return _load_artifact(spec)
    except (FileNotFoundError, ValueError, KeyError):
        if args.no_build:
            raise
    directory = spec['directory']
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'build_contract.json').unlink(missing_ok=True)
    command = [args.iron_python, str(KERNEL_ROOT / GRAPH), *spec['arguments'],
               '--xclbin-path', str(directory / 'final.xclbin'),
               '--insts-path', str(directory / 'insts.bin'),
               '--pdi-path', str(directory / 'final.pdi')]
    log = directory / 'compile.log'
    with log.open('w') as output:
        result = subprocess.run(command, cwd=KERNEL_ROOT, stdout=output,
                                stderr=subprocess.STDOUT, check=False,
                                timeout=args.compile_timeout)
    if result.returncode:
        raise RuntimeError(f"compilation failed ({result.returncode}); see {log}")
    _validate_manifest(spec)
    temporary = directory / 'build_contract.json.tmp'
    temporary.write_text(json.dumps(_build_contract(spec), indent=2) + '\n')
    temporary.replace(directory / 'build_contract.json')
    return _load_artifact(spec)


def _inputs(m, k, seed):
    rng = np.random.default_rng(seed)
    first, second = [bf16(rng.normal(0, 0.5, size=(m, k)).astype(np.float32))
                     for _ in range(2)]
    # Repeating after changed/zero inputs also catches state leaking across runs.
    return [('signed_a', first), ('signed_b', second),
            ('zero', np.zeros_like(first)), ('repeat_a', first.copy())]


def _checks(entry, run, reference, m, k, seed, save, report, launches):
    outputs = {}
    entry['runs'] = []
    for label, x in _inputs(m, k, seed):
        item = dict(input=label, status='running', input_sha256=_hash(bf16_bits(x)))
        entry['runs'].append(item)
        save()
        expected = reference(x)
        before = time.perf_counter_ns()
        actual, diagnostics = run(x)
        item['host_wall_us'] = (time.perf_counter_ns() - before) / 1000.0
        report['completed_npu_dispatches'] += launches
        item.update(status='completed', completed_npu_dispatches=launches,
                    output_sha256=_hash(bf16_bits(actual)),
                    reference_sha256=_hash(bf16_bits(expected)),
                    errors=error_metrics(actual, expected), diagnostics=diagnostics)
        outputs[label] = actual.copy()
        save()
    checks = {
        'original_numerical_tolerances': all(
            item['errors']['correctness'] == 'passed' for item in entry['runs']),
        'repeat_exact': bool(np.array_equal(bf16_bits(outputs['signed_a']),
                                           bf16_bits(outputs['repeat_a']))),
        'changed_input_changes_output': not np.array_equal(outputs['signed_a'], outputs['signed_b']),
        'exact_zero': bool(np.all(outputs['zero'] == 0)),
        'nonzero_signed_inputs': all(bool(np.any(outputs[label] != 0))
                                    for label in ('signed_a', 'signed_b')),
    }
    entry['checks'] = checks
    entry['status'] = 'passed' if all(checks.values()) else 'failed'
    save()


def _case_list(args):
    if args.suite == 'smoke':
        return [dict(name='projection_slice', mode='projection', m=128, k=256, n=256,
                     weight_k=512, weight_n=1024, k_start=128, n_start=32),
                dict(name='projection_paired', mode='projection', m=128, k=512, n=512,
                     weight_k=512, weight_n=1024, k_start=0, n_start=0),
                dict(name='projection_narrow', mode='projection', m=128, k=256, n=128,
                     weight_k=512, weight_n=1024, k_start=128, n_start=64),
                dict(name='swiglu', mode='swiglu', m=128, k=512, n=256,
                     weight_k=512, weight_n=1024, k_start=0, n_start=128),
                dict(name='ffn', mode='ffn', m=128, hidden=512, channels=256,
                     intermediate=1024, channel_start=128)]
    return [dict(name='ffn', mode='ffn', m=args.m, hidden=args.hidden,
                 channels=args.channels, intermediate=args.intermediate,
                 channel_start=args.channel_start)]


def kernel_options(args):
    """Shared options for correctness and separately timed ablations."""
    defaults = dict(swiglu_reuse=2, down_reuse=2, swiglu_activation_fifo_depth=2,
        down_activation_fifo_depth=2, vector_zero=False, mmul_m_reuse=1, output_layout='compact',
        swiglu_input_layout='compact')
    return {name: getattr(args, name, value) for name, value in defaults.items()}


def add_kernel_options(parser):
    parser.add_argument('--swiglu-reuse', type=int, choices=(1, 2), default=2)
    parser.add_argument('--down-reuse', type=int, choices=(1, 2, 4), default=2)
    parser.add_argument('--swiglu-activation-fifo-depth', type=int, choices=(1, 2), default=2)
    parser.add_argument('--down-activation-fifo-depth', type=int, choices=(1, 2), default=2)
    parser.add_argument('--vector-zero', action='store_true')
    parser.add_argument('--mmul-m-reuse', type=int, choices=(1, 2), default=1)
    parser.add_argument('--output-layout', choices=('compact', 'down_a'), default='compact')
    parser.add_argument('--swiglu-input-layout', choices=('compact', 'row_major'), default='compact')
    parser.add_argument('--borrow-npu-readback', action='store_true')


def run_check(args):
    options = kernel_options(args)
    report = dict(status='preparing', evidence_kind='NPU hardware correctness',
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        scope='native BF16, unchanged original-format weights; no performance claim',
        arithmetic='bf16', weight_layout=UPSTREAM_LAYOUT_VERSION, weight_repacking=False,
        tolerances=dict(rtol=0.03, atol=0.05, relative_l2_limit=0.02),
        npu_wait_timeout_ms=10000, completed_npu_dispatches=0,
        config={key: str(value) if isinstance(value, Path) else value
                for key, value in vars(args).items()},
        environment=dict(python=sys.version, numpy=np.__version__, platform=platform.platform()),
        cases=[])
    sources = ('experiments/ffn_partition/check_upstream.py',
               'experiments/ffn_partition/upstream_npu.py',
               'experiments/ffn_partition/npu_backend.py',
               'experiments/ffn_partition/contract.py', 'npu/ffn/xrt_runner.py',
               'npu/ffn/reference.py', 'npu/ffn/prefill_reference.py')
    report['source_sha256'] = {name: sha256((ROOT / name).read_bytes()).hexdigest()
                               for name in sources}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        temporary = args.output.with_name(args.output.name + '.tmp')
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        temporary.replace(args.output)

    try:
        save()
        cases = _case_list(args)
        case_seeds = {case['name']: args.seed + index * 10
                      for index, case in enumerate(cases)}
        if args.cases:
            selected = args.cases.split(',')
            unknown = set(selected) - {case['name'] for case in cases}
            if unknown or len(selected) != len(set(selected)):
                raise ValueError(f"unknown or duplicated cases: {args.cases}")
            cases = [case for case in cases if case['name'] in selected]
        for case in cases:
            entry = dict(config=case, status='preparing')
            report['cases'].append(entry)
            save()
            seed = case_seeds[case['name']]
            if case['mode'] == 'ffn':
                m, h, p, intermediate, start = (case[key] for key in
                    ('m', 'hidden', 'channels', 'intermediate', 'channel_start'))
                gate = prepare_weights(h, intermediate, seed)
                up = prepare_weights(h, intermediate, seed + 1)
                down = prepare_weights(intermediate, h, seed + 2)
                fixtures = dict(gate=gate, up=up, down=down)
                specs = _ffn_specs(m, h, p, gate.weight, up.weight, down.weight,
                                   args.artifact_root, start,
                                   segment_pipeline_depth=args.segment_pipeline_depth, **options)
            else:
                m, k, n, wk, wn, ks, ns = (case[key] for key in
                    ('m', 'k', 'n', 'weight_k', 'weight_n', 'k_start', 'n_start'))
                fixtures = {'gate': prepare_weights(wk, wn, seed)}
                if case['mode'] == 'swiglu':
                    fixtures['up'] = prepare_weights(wk, wn, seed + 1)
                specs = {'projection': _artifact_spec(case['mode'], m, k, n,
                    fixtures['gate'].weight, args.artifact_root, k_start=ks, n_start=ns,
                    segment_pipeline_depth=args.segment_pipeline_depth,
                    max_reuse=options['swiglu_reuse' if case['mode'] == 'swiglu' else 'down_reuse'],
                    activation_fifo_depth=options['swiglu_activation_fifo_depth' if case['mode'] == 'swiglu'
                                                   else 'down_activation_fifo_depth'],
                    vector_zero=options['vector_zero'], mmul_m_reuse=options['mmul_m_reuse'],
                    input_layout=options['swiglu_input_layout'] if case['mode'] == 'swiglu' else 'compact',
                    output_layout=options['output_layout'] if case['mode'] == 'swiglu' else 'compact')}
            original_hashes = {label: _hash(f.weight.data) for label, f in fixtures.items()}
            entry['original_weight_sha256'] = original_hashes
            entry['weight_bytes'] = {label: f.weight.nbytes for label, f in fixtures.items()}
            entry['status'] = 'building'
            save()
            entry['artifacts'] = {label: _build(spec, args) for label, spec in specs.items()}
            if args.build_only:
                entry['status'] = 'built_not_executed'
                save()
                continue
            entry['status'] = 'running'
            save()
            if case['mode'] == 'ffn':
                dense_gate = gate.dense_slice(0, start, h, p)
                dense_up = up.dense_slice(0, start, h, p)
                dense_down = down.dense_slice(start, 0, p, h)
                branch = UpstreamNpuFFN(m, h, p, gate.weight, up.weight, down.weight,
                                        args.artifact_root, channel_start=start,
                                        segment_pipeline_depth=args.segment_pipeline_depth,
                                        copy_output_bits=not getattr(args, 'borrow_npu_readback', False),
                                        **options)

                def reference(x):
                    z = silu_multiply(bf16(x @ dense_gate), bf16(x @ dense_up), bf16_io=True)
                    return bf16(z @ dense_down)

                def run(x):
                    try:
                        result = bf16_from_bits(branch.run(bf16_bits(x)))
                        return result, branch.last_diagnostics
                    finally:
                        # Preserve any successful first launch if down fails.
                        entry['runner_completed_dispatches'] = {
                            name: runner.completed_dispatches
                            for name, runner in branch.runners.items()}

                _checks(entry, run, reference, m, h, seed + 3, save, report, launches=2)
                entry['runner_completed_dispatches'] = {
                    name: runner.completed_dispatches for name, runner in branch.runners.items()}
                entry['checks']['each_runner_completed_four'] = all(
                    count == 4 for count in entry['runner_completed_dispatches'].values())
                entry['checks']['fixed_weights_uploaded_once'] = (
                    branch.swiglu.input_write_counts[1:3] == [1, 1]
                    and branch.down.input_write_counts[1] == 1)
                del branch
            else:
                artifact = entry['artifacts']['projection']
                shapes = [((m * k,), np.uint16)] + [((f.weight.nbytes,), np.uint8)
                    for f in fixtures.values()] + [((m * n,), np.uint16)]
                runner = XrtRunner(artifact['xclbin'], artifact['insts'], shapes)
                dense = {label: fixture.dense_slice(ks, ns, k, n)
                         for label, fixture in fixtures.items()}

                def reference(x):
                    gate_output = bf16(x @ dense['gate'])
                    if case['mode'] == 'swiglu':
                        return silu_multiply(gate_output, bf16(x @ dense['up']), bf16_io=True)
                    return gate_output

                def run(x):
                    a = (bf16_bits(x).reshape(-1) if case['mode'] == 'swiglu'
                         and options['swiglu_input_layout'] == 'row_major' else pack_activations(x))
                    raw, launch_us = runner.run([a]
                        + [f.weight.data for f in fixtures.values()])
                    unpack = (unpack_activations if case['mode'] == 'swiglu'
                              and options['output_layout'] == 'down_a' else unpack_output)
                    return unpack(raw, m, n), {'dispatch_wait_us': launch_us}

                _checks(entry, run, reference, m, k, seed + 3, save, report, launches=1)
                del runner
            entry['checks']['original_weight_bytes_unchanged'] = all(
                _hash(f.weight.data) == original_hashes[label] for label, f in fixtures.items())
            entry['status'] = 'passed' if all(entry['checks'].values()) else 'failed'
            save()
            gc.collect()
        report['status'] = ('built_not_executed' if args.build_only else
                            'passed' if all(c['status'] == 'passed' for c in report['cases'])
                            else 'failed')
    except Exception as error:
        report.update(status='failed', error=str(error), traceback=traceback.format_exc())
        if report['cases']:
            report['cases'][-1]['status'] = 'failed'
    finally:
        save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifact-root', type=Path, required=True)
    parser.add_argument('--iron-python', default=sys.executable)
    parser.add_argument('--suite', choices=('smoke', 'model'), default='smoke')
    parser.add_argument('--cases', help='comma-separated case names; default runs the whole suite')
    parser.add_argument('--seed', type=int, default=251025)
    parser.add_argument('--compile-timeout', type=float, default=900)
    parser.add_argument('--segment-pipeline-depth', type=int, choices=(1, 2), default=2,
                        help='1: serial control; 2: queue two consecutive segments')
    add_kernel_options(parser)
    builds = parser.add_mutually_exclusive_group()
    builds.add_argument('--build-only', action='store_true')
    builds.add_argument('--no-build', action='store_true')
    parser.add_argument('--m', type=int, default=512, help='model suite only')
    parser.add_argument('--hidden', type=int, default=4096, help='model suite only')
    parser.add_argument('--intermediate', type=int, default=14336, help='model suite only')
    parser.add_argument('--channels', type=int, default=2560, help='model suite only')
    parser.add_argument('--channel-start', type=int, default=0, help='model suite only')
    args = parser.parse_args()
    if not np.isfinite(args.compile_timeout) or args.compile_timeout <= 0:
        parser.error('--compile-timeout must be finite and positive')
    report = run_check(args)
    print(json.dumps({'status': report['status'], 'output': str(args.output),
                      'completed_npu_dispatches': report['completed_npu_dispatches'],
                      'error': report.get('error')}, indent=2))
    raise SystemExit(0 if report['status'] in ('passed', 'built_not_executed') else 1)


if __name__ == '__main__':
    main()
