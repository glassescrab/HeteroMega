"""Check combined gate/up against separate NPU projections and the CPU oracle.

This is a correctness diagnostic, not a latency benchmark. It builds/loads
both array8 graph variants, uses identical fixed W4A16 weights and four input
cases (random A, random B, zero, repeat A), then compares native gate/up BF16
bits exactly. Complete NPU FFN outputs must also pass the existing fixed CPU
reference tolerances. No GPU or model download is required.
"""

import argparse
from datetime import datetime, timezone
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

import numpy as np

from .contract import bf16, error_metrics, random_weights, reference_full, validate_shape
from .npu_backend import NPUBranch, ROOT, _artifact_specs, build_artifacts
from prefill_reference import bf16_bits, bf16_from_bits, unpack_output


def _array_hash(value):
    return sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def _exact(actual, expected):
    actual, expected = np.asarray(actual), np.asarray(expected)
    same_shape = actual.shape == expected.shape
    same_dtype = actual.dtype == expected.dtype
    mismatch = int(np.count_nonzero(actual != expected)) if same_shape else None
    return {"passed": bool(same_shape and same_dtype and mismatch == 0),
            "comparison": "exact BF16 bits", "shape": list(actual.shape),
            "dtype": str(actual.dtype), "mismatched_elements": mismatch,
            "actual_sha256": _array_hash(actual), "expected_sha256": _array_hash(expected)}


def _git_value(*arguments):
    process = subprocess.run(['git', *arguments], cwd=ROOT, text=True,
                             capture_output=True, check=False)
    return process.stdout.strip() if process.returncode == 0 else None


def _run_variant(weights, inputs, args, fused):
    """Release one variant's XRT contexts before constructing the other."""
    branch = NPUBranch(weights.gate, weights.up, weights.down, args.m,
                       args.artifact_root, columns=8, npu_design='array8',
                       fuse_gate_up=fused)
    outputs = []
    try:
        for label, x in inputs:
            before = sum(r.completed_dispatches for r in branch.runners.values())
            result = branch.run(bf16_bits(x))
            if fused:
                gate, up = branch.gate_up.output_bits(0), branch.gate_up.output_bits(1)
            else:
                gate, up = branch.gate.output_bits(), branch.up.output_bits()
            after = sum(r.completed_dispatches for r in branch.runners.values())
            outputs.append({'input': label, 'gate': gate, 'up': up, 'ffn': result,
                            'dispatch_delta': after - before,
                            'diagnostics': branch.last_diagnostics})
        metadata = branch.metadata
        completion_counts = {name: runner.completed_dispatches
                             for name, runner in branch.runners.items()}
        weight_counts = {name: runner.input_write_counts[1]
                         for name, runner in branch.projection_runners.items()}
        return outputs, {'metadata': metadata,
                         'completed_dispatches': completion_counts,
                         'weight_upload_counts': weight_counts}
    finally:
        del branch
        gc.collect()


def run_check(args):
    report = {'status': 'preparing',
              'scope': 'NPU-only gate/up and complete branch correctness; not performance',
              'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'config': {key: str(value) if isinstance(value, Path) else value
                         for key, value in vars(args).items()},
              'environment': {'python': sys.version, 'numpy': np.__version__,
                              'platform': platform.platform()},
              'git': {'head': _git_value('rev-parse', 'HEAD'),
                      'status': _git_value('status', '--porcelain')},
              'cases': [], 'checks': {}}
    sources = ('experiments/ffn_partition/check_gate_up.py',
               'experiments/ffn_partition/npu_backend.py',
               'experiments/ffn_partition/contract.py',
               'npu/ffn/xrt_runner.py', 'npu/ffn/reference.py',
               'npu/ffn/prefill_reference.py')
    report['source_sha256'] = {name: sha256((ROOT / name).read_bytes()).hexdigest()
                               for name in sources}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        temporary = args.output.with_name(args.output.name + '.tmp')
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        temporary.replace(args.output)

    def check(name, metrics):
        report['checks'][name] = metrics

    try:
        save()
        for channels in args.channels:
            validate_shape(args.m, args.hidden, channels, channels)
            # Validate both graph shape contracts before allocating XRT BOs.
            for fused in (False, True):
                _artifact_specs(args.m, args.hidden, channels, args.artifact_root,
                                columns=8, design='array8', fuse_gate_up=fused)
                if not args.no_build:
                    build_artifacts(args.m, args.hidden, channels, args.artifact_root,
                                    columns=8, python_executable=args.iron_python,
                                    npu_design='array8', fuse_gate_up=fused)
            weights = random_weights(args.hidden, channels, args.seed)
            rng = np.random.default_rng(args.input_seed)
            first, second = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32))
                             for _ in range(2)]
            inputs = [('random_a', first), ('random_b', second),
                      ('zero', np.zeros_like(first)), ('repeat_a', first.copy())]
            refs = {label: reference_full(x, weights) for label, x in inputs[:3]}
            refs['repeat_a'] = refs['random_a']
            case = {'m': args.m, 'hidden': args.hidden, 'channels': channels,
                    'inputs_sha256': {label: _array_hash(bf16_bits(x)) for label, x in inputs},
                    'weights_sha256': {projection: {component: _array_hash(getattr(getattr(weights, projection), component))
                        for component in ('packed', 'scales', 'zeros')}
                        for projection in ('gate', 'up', 'down')},
                    'variants': {}}
            report['cases'].append(case)
            save()
            observed = {}
            for fused in (False, True):
                name = 'combined' if fused else 'separate'
                values, metadata = _run_variant(weights, inputs, args, fused)
                observed[name] = values
                case['variants'][name] = metadata
                case['variants'][name]['diagnostics'] = [value['diagnostics'] for value in values]
                expected_launches = 3 if fused else 4
                check(f'p{channels}/{name}/launches_per_run', {
                    'passed': all(value['dispatch_delta'] == expected_launches for value in values),
                    'expected': expected_launches,
                    'actual': [value['dispatch_delta'] for value in values]})
                check(f'p{channels}/{name}/one_fixed_weight_upload', {
                    'passed': all(count == 1 for count in metadata['weight_upload_counts'].values()),
                    'actual': metadata['weight_upload_counts']})
                for value in values:
                    prefix = f'p{channels}/{name}/{value["input"]}'
                    check(prefix + '/ffn_vs_cpu', error_metrics(bf16_from_bits(value['ffn']),
                                                                refs[value['input']]))
                    if value['input'] == 'zero':
                        for stage in ('gate', 'up'):
                            logical = unpack_output(value[stage], args.m, channels)
                            check(prefix + f'/{stage}_zero', {'passed': bool(np.all(logical == 0)),
                                                              'comparison': 'exact numeric zero'})
                for stage in ('gate', 'up', 'ffn'):
                    check(f'p{channels}/{name}/{stage}_repeat', _exact(values[3][stage], values[0][stage]))
                    check(f'p{channels}/{name}/{stage}_changed_input', {
                        'passed': not np.array_equal(values[1][stage], values[0][stage]),
                        'comparison': 'random B differs from random A'})
                save()
            for separate, combined in zip(observed['separate'], observed['combined']):
                if separate['input'] != combined['input']:
                    raise RuntimeError('variant inputs were compared out of order')
                for stage in ('gate', 'up', 'ffn'):
                    check(f'p{channels}/{combined["input"]}/{stage}_combined_vs_separate',
                          _exact(combined[stage], separate[stage]))
            save()
            print(json.dumps({'channels': channels, 'checks_so_far': len(report['checks']),
                              'passed_so_far': all(c['passed'] for c in report['checks'].values())}), flush=True)
        report['status'] = ('passed' if all(c['passed'] for c in report['checks'].values())
                            else 'mismatch')
    except Exception as error:
        report['status'] = 'error'
        report['error'] = str(error)
        report['traceback'] = traceback.format_exc()
        save()
        raise
    save()
    print(json.dumps({'status': report['status'], 'checks': len(report['checks']),
                      'output': str(args.output)}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--m', type=int, default=128)
    parser.add_argument('--hidden', type=int, default=256)
    parser.add_argument('--channels', type=int, nargs='+', default=[128, 384, 512])
    parser.add_argument('--seed', type=int, default=12832)
    parser.add_argument('--input-seed', type=int, default=12833)
    parser.add_argument('--iron-python', default=os.environ.get('IRON_PYTHON'))
    parser.add_argument('--artifact-root', type=Path, default=Path('experiments/ffn_partition/artifacts'))
    parser.add_argument('--no-build', action='store_true', help='require current cached artifacts')
    parser.add_argument('--output', type=Path, default=Path('experiments/ffn_partition/results/gate_up_correctness.json'))
    args = parser.parse_args()
    if len(set(args.channels)) != len(args.channels):
        parser.error('--channels values must be unique')
    report = run_check(args)
    if report['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
