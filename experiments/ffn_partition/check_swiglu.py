"""Check on-chip SwiGLU against gate/up fusion followed by standalone SiLU.

This is a correctness diagnostic, not a performance benchmark. Identical
fixed W4A16 weights and random A/B/zero/repeat-A inputs exercise both array8
paths. Native packed Z and complete NPU FFN outputs must match exactly in
BF16 bits; both stages also face the existing fixed CPU-reference tolerances.
The comparison retains BF16 rounding after gate/up, SiLU and multiplication.
No GPU or model download is required. Real XRT execution is required.
"""

import argparse
from copy import deepcopy
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
from reference import silu_multiply


def _array_hash(value):
    return sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def _exact(actual, expected):
    actual, expected = np.asarray(actual), np.asarray(expected)
    same_shape = actual.shape == expected.shape
    native_bits = actual.dtype == expected.dtype == np.dtype(np.uint16)
    mismatch = int(np.count_nonzero(actual != expected)) if same_shape else None
    return {"passed": bool(native_bits and same_shape and mismatch == 0),
            "comparison": "exact native BF16 bits", "shape": list(actual.shape),
            "expected_shape": list(expected.shape), "dtype": str(actual.dtype),
            "expected_dtype": str(expected.dtype), "mismatched_elements": mismatch,
            "actual_sha256": _array_hash(actual), "expected_sha256": _array_hash(expected)}


def _git_value(*arguments):
    process = subprocess.run(['git', *arguments], cwd=ROOT, text=True,
                             capture_output=True, check=False)
    return process.stdout.strip() if process.returncode == 0 else None


def _reference_z(x, weights):
    """CPU oracle only: preserve every BF16 storage/rounding boundary."""
    x = bf16(x)
    gate = bf16(x @ weights.gate.dequantize(True).T)
    up = bf16(x @ weights.up.dequantize(True).T)
    return silu_multiply(gate, up, bf16_io=True)


def _run_variant(weights, inputs, args, fuse_swiglu):
    """Retain independent snapshots; release one variant before loading next."""
    branch = NPUBranch(weights.gate, weights.up, weights.down, args.m,
                       args.artifact_root, columns=8, npu_design='array8',
                       fuse_gate_up=not fuse_swiglu, fuse_swiglu=fuse_swiglu)
    outputs = []
    try:
        for label, x in inputs:
            before = {name: runner.completed_dispatches
                      for name, runner in branch.runners.items()}
            result = branch.run(bf16_bits(x))
            z = (branch.swiglu if fuse_swiglu else branch.silu).output_bits()
            after = {name: runner.completed_dispatches
                     for name, runner in branch.runners.items()}
            outputs.append({
                'input': label, 'z': z.copy(), 'ffn': result.copy(),
                'dispatch_deltas': {name: after[name] - before[name] for name in after},
                'weight_upload_counts': {name: runner.input_write_counts[1]
                                         for name, runner in branch.projection_runners.items()},
                'diagnostics': deepcopy(branch.last_diagnostics),
            })
        return outputs, {
            'metadata': deepcopy(branch.metadata),
            'output_sha256': {value['input']: {stage: _array_hash(value[stage])
                                               for stage in ('z', 'ffn')} for value in outputs},
            'completed_dispatches': {name: runner.completed_dispatches
                                     for name, runner in branch.runners.items()},
            'weight_upload_counts': {name: runner.input_write_counts[1]
                                     for name, runner in branch.projection_runners.items()},
        }
    finally:
        del branch
        gc.collect()


def _variant_checks(values, metadata, references, m, hidden, channels, fuse_swiglu):
    """Check each stage and runner, including reuse failures hidden by totals."""
    expected_inputs = ['random_a', 'random_b', 'zero', 'repeat_a']
    if [value['input'] for value in values] != expected_inputs:
        raise ValueError('expected ordered random A/B/zero/repeat A snapshots')
    stages = {'swiglu', 'down'} if fuse_swiglu else {'gate_up', 'silu_mul', 'down'}
    projections = stages - {'silu_mul'}
    checks = {}
    deltas = [value['dispatch_deltas'] for value in values]
    checks['launches_per_run'] = {
        'passed': all(set(delta) == stages and all(v == 1 for v in delta.values())
                      for delta in deltas),
        'expected': len(stages), 'expected_stages': sorted(stages), 'actual': deltas}
    completion_counts = metadata['completed_dispatches']
    checks['completed_dispatches'] = {
        'passed': (set(completion_counts) == stages and
                   all(count == len(values) for count in completion_counts.values())),
        'expected_per_runner': len(values), 'actual': completion_counts}
    uploads = [value['weight_upload_counts'] for value in values]
    uploads.append(metadata['weight_upload_counts'])
    checks['one_fixed_weight_upload'] = {
        'passed': all(set(counts) == projections and all(v == 1 for v in counts.values())
                      for counts in uploads), 'actual': uploads}
    branch_metadata = metadata['metadata']
    checks['branch_contract'] = {
        'passed': (branch_metadata.get('fuse_swiglu', False) is fuse_swiglu and
                   branch_metadata.get('fuse_gate_up') is True and
                   branch_metadata.get('launches_per_run') == len(stages) and
                   branch_metadata.get('fixed_weight_uploads') == len(projections) and
                   branch_metadata.get('cpu_activation_fallback') is False),
        'expected_fuse_swiglu': fuse_swiglu,
        'actual': {key: branch_metadata.get(key) for key in
                   ('fuse_swiglu', 'fuse_gate_up', 'launches_per_run',
                    'fixed_weight_uploads', 'cpu_activation_fallback')}}
    for value in values:
        label = value['input']
        for stage, shape in (('z', (m * channels,)), ('ffn', (m, hidden))):
            data = value[stage]
            valid = data.dtype == np.dtype(np.uint16) and data.shape == shape
            checks[f'{label}/{stage}_buffer_contract'] = {
                'passed': bool(valid), 'dtype': str(data.dtype), 'shape': list(data.shape),
                'expected_dtype': 'uint16', 'expected_shape': list(shape)}
            if not valid:
                continue
            actual = unpack_output(data, m, channels) if stage == 'z' else bf16_from_bits(data)
            checks[f'{label}/{stage}_vs_cpu'] = error_metrics(actual, references[label][stage])
            if label == 'zero':
                checks[f'{label}/{stage}_zero'] = {
                    'passed': bool(np.all(actual == 0)), 'comparison': 'exact numeric zero'}
    for stage in ('z', 'ffn'):
        checks[f'{stage}_repeat'] = _exact(values[3][stage], values[0][stage])
        checks[f'{stage}_changed_input'] = {
            'passed': not np.array_equal(values[1][stage], values[0][stage]),
            'comparison': 'random B differs from random A'}
    return checks


def run_check(args):
    report = {'status': 'preparing', 'evidence_kind': 'NPU hardware correctness',
              'scope': 'on-chip SwiGLU packed Z and complete NPU FFN; not performance',
              'timestamp_utc': datetime.now(timezone.utc).isoformat(),
              'config': {key: str(value) if isinstance(value, Path) else value
                         for key, value in vars(args).items()},
              'environment': {'python': sys.version, 'numpy': np.__version__,
                              'platform': platform.platform()},
              'git': {'head': _git_value('rev-parse', 'HEAD'),
                      'status': _git_value('status', '--porcelain')},
              'cases': [], 'checks': {}}
    sources = ('experiments/ffn_partition/check_swiglu.py',
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

    try:
        save()
        if not args.channels or len(set(args.channels)) != len(args.channels):
            raise ValueError('channels must be a nonempty list of unique aligned sizes')
        for channels in args.channels:
            validate_shape(args.m, args.hidden, channels, channels)
            for fuse_swiglu in (False, True):
                flags = {'fuse_gate_up': not fuse_swiglu, 'fuse_swiglu': fuse_swiglu}
                _artifact_specs(args.m, args.hidden, channels, args.artifact_root,
                                columns=8, design='array8', **flags)
                if not args.no_build:
                    build_artifacts(args.m, args.hidden, channels, args.artifact_root,
                                    columns=8, python_executable=args.iron_python,
                                    npu_design='array8', **flags)
            weights = random_weights(args.hidden, channels, args.seed)
            rng = np.random.default_rng(args.input_seed)
            first, second = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32))
                             for _ in range(2)]
            inputs = [('random_a', first), ('random_b', second),
                      ('zero', np.zeros_like(first)), ('repeat_a', first.copy())]
            references = {label: {'z': _reference_z(x, weights),
                                  'ffn': reference_full(x, weights)}
                          for label, x in inputs[:3]}
            references['repeat_a'] = references['random_a']
            case = {'m': args.m, 'hidden': args.hidden, 'channels': channels,
                    'inputs_sha256': {label: _array_hash(bf16_bits(x)) for label, x in inputs},
                    'weights_sha256': {projection: {
                        component: _array_hash(getattr(getattr(weights, projection), component))
                        for component in ('packed', 'scales', 'zeros')}
                        for projection in ('gate', 'up', 'down')},
                    'variants': {}}
            report['cases'].append(case)
            save()
            observed = {}
            for fuse_swiglu in (False, True):
                name = 'onchip_swiglu' if fuse_swiglu else 'gate_up_then_silu'
                values, metadata = _run_variant(weights, inputs, args, fuse_swiglu)
                observed[name] = values
                case['variants'][name] = dict(metadata, diagnostics=[v['diagnostics'] for v in values])
                checks = _variant_checks(values, metadata, references, args.m,
                                         args.hidden, channels, fuse_swiglu)
                report['checks'].update({f'p{channels}/{name}/{key}': value
                                         for key, value in checks.items()})
                save()
            for baseline, candidate in zip(observed['gate_up_then_silu'], observed['onchip_swiglu']):
                if baseline['input'] != candidate['input']:
                    raise RuntimeError('variant inputs were compared out of order')
                for stage in ('z', 'ffn'):
                    name = f'p{channels}/{candidate["input"]}/{stage}_onchip_vs_gate_up_then_silu'
                    report['checks'][name] = _exact(candidate[stage], baseline[stage])
            save()
            print(json.dumps({'channels': channels, 'checks_so_far': len(report['checks']),
                              'passed_so_far': all(c['passed'] for c in report['checks'].values())}), flush=True)
        report['status'] = ('passed' if report['checks'] and
                            all(c['passed'] for c in report['checks'].values()) else 'mismatch')
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
    parser.add_argument('--output', type=Path, default=Path('experiments/ffn_partition/results/swiglu_correctness.json'))
    args = parser.parse_args()
    if len(set(args.channels)) != len(args.channels):
        parser.error('--channels values must be unique')
    if run_check(args)['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
