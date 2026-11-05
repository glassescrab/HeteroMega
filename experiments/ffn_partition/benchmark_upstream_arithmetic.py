"""Bounded direct-weight BF16/BFP16 NPU FFN comparison in fresh processes.

Both sides use the selected reuse/layout profile and original packed weights.
Each arithmetic has a separate deterministic structural reference. Cross-format
error magnitudes retain the original tolerances; explicit BFP16 report mode
permits finite numerical differences, never execution/structural failures.
CPU-reference correctness must be checked separately before interpreting timing.
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
import tempfile
import time
import traceback
from types import SimpleNamespace

import numpy as np

from .benchmark_upstream_optimizations import (
    artifact_profile, block_order, resolve_profile, _fixture_files, _stats)
from .check_upstream import _build, _hash, _inputs, prepare_weights
from .npu_backend import ROOT
from .upstream_npu import UpstreamNpuFFN, _ffn_specs
from prefill_reference import bf16_bits, bf16_from_bits, error_metrics
from upstream_weights import UpstreamWeightBuffer, UPSTREAM_LAYOUT_VERSION


PROFILE_NAME = 'combo_mmul1_row_major'
ARITHMETICS = {1: 'bf16', 2: 'bfp16'}
LABELS = ('signed_a', 'signed_b', 'zero', 'repeat_a')
TOLERANCES = dict(rtol=0.03, atol=0.05, relative_l2_limit=0.02)


def _output_record(label, result, diagnostics):
    if result.dtype != np.uint16:
        raise RuntimeError('NPU output must contain BF16 uint16 bits')
    return dict(input=label, output_sha256=_hash(result),
        finite=bool(np.all((result & 0x7F80) != 0x7F80)),
        nonzero=bool(np.any(result & 0x7FFF)), diagnostics=deepcopy(diagnostics))


def _structural_checks(records, expected=None):
    """A/B/zero/A catches nonfinite, stale, zero and cross-call state failures."""
    by_label = {item['input']: item for item in records}
    complete = tuple(item['input'] for item in records) == LABELS
    checks = dict(complete_sequence=complete,
        all_finite=all(item['finite'] for item in records))
    if complete:
        checks.update(repeat_after_changed_and_zero_exact=
            by_label['signed_a']['output_sha256'] == by_label['repeat_a']['output_sha256'],
            changed_input_changes_output=by_label['signed_a']['output_sha256'] != by_label['signed_b']['output_sha256'],
            exact_zero=not by_label['zero']['nonzero'],
            both_signed_outputs_nonzero=all(by_label[label]['nonzero'] for label in LABELS[:2]))
    if expected is not None:
        checks['exact_same_arithmetic_reference'] = all(
            item['output_sha256'] == expected.get(item['input']) for item in records)
    return checks


def _run_block(args, weights, inputs, entry):
    """Own all runners inside one child; copies and checking stay outside timing."""
    branch = None
    payload = dict(preflight=[], timed=[])
    entry.update(status='initializing', preflight=[], warmup=[], runs=[])
    original_hashes = [_hash(w.data) for w in weights]
    input_hashes = {label: _hash(x) for label, x in inputs}
    if tuple(label for label, _ in inputs) != LABELS:
        raise ValueError('fixtures must contain signed_a, signed_b, zero, repeat_a')
    expected = entry.get('expected_output_sha256')
    try:
        branch = UpstreamNpuFFN(args.m, args.hidden, args.channels, *weights,
            args.artifact_root, channel_start=args.channel_start,
            segment_pipeline_depth=2, arithmetic=entry['arithmetic'], **entry['profile'])
        entry['runner_metadata'] = branch.metadata
        if branch.metadata['arithmetic'] != entry['arithmetic']:
            raise RuntimeError('runner arithmetic differs from requested profile')
        entry['status'] = 'structural_preflight'
        for label, x in inputs:
            result = branch.run(x)
            item = _output_record(label, result, branch.last_diagnostics)
            entry['preflight'].append(item)
            if not item['finite']:
                raise RuntimeError(f'nonfinite {label} preflight; timing was not started')
            payload['preflight'].append(result.copy())
        entry['preflight_checks'] = _structural_checks(entry['preflight'], expected)
        if not all(entry['preflight_checks'].values()):
            raise RuntimeError('structural/same-arithmetic preflight failed; timing was not started')
        if entry.get('excluded_from_summary'):
            entry['status'] = 'completed'
            return payload
        if expected is None:
            raise ValueError('timed blocks require a same-arithmetic reference')
        signed = inputs[:2]
        entry['status'] = 'warming_up'
        for index in range(args.warmup):
            label, x = signed[index % 2]
            result = branch.run(x)
            item = _output_record(label, result, branch.last_diagnostics)
            entry['warmup'].append(item)
            if not item['finite'] or item['output_sha256'] != expected[label]:
                raise RuntimeError('warmup differs from finite same-arithmetic reference; timing was not started')
        entry['status'] = 'timing'
        for index in range(args.iterations):
            label, x = signed[index % 2]
            before = time.perf_counter_ns()
            result = branch.run(x)
            elapsed = (time.perf_counter_ns() - before) / 1000.0
            item = _output_record(label, result, branch.last_diagnostics)
            item.update(index=index, wall_us=elapsed)
            entry['runs'].append(item)
            if not item['finite'] or item['output_sha256'] != expected[label]:
                raise RuntimeError('timed output differs from finite same-arithmetic reference')
            payload['timed'].append(result.copy())
        entry['status'] = 'completed'
        return payload
    finally:
        if branch is not None:
            entry['completed_dispatches'] = {
                name: runner.completed_dispatches for name, runner in branch.runners.items()}
            entry['fixed_weight_upload_counts'] = dict(gate=branch.swiglu.input_write_counts[1],
                up=branch.swiglu.input_write_counts[2], down=branch.down.input_write_counts[1])
        entry['original_weight_bytes_unchanged'] = all(_hash(w.data) == h for w, h in zip(weights, original_hashes))
        entry['input_bytes_unchanged'] = all(_hash(x) == input_hashes[label] for label, x in inputs)
        del branch
        gc.collect()


def _compare_outputs(entry, payload, controls, native_controls, numerics):
    """Bitwise within arithmetic; cross-arithmetic tolerance failures stay visible."""
    if numerics not in ('strict', 'report'):
        raise ValueError('bfp16 numerics must be strict or report')
    for field, outputs in (('preflight', payload['preflight']), ('runs', payload['timed'])):
        if len(entry[field]) != len(outputs):
            raise ValueError('returned output count does not match report')
        for item, output in zip(entry[field], outputs):
            label = item['input']
            if label not in controls:
                if not entry.get('excluded_from_summary') or not item['finite']:
                    raise ValueError('finite same-arithmetic reference must precede timing')
                controls[label] = output.copy()
            item['identical_to_same_arithmetic_control'] = bool(np.array_equal(output, controls[label]))
            item['errors_vs_native_control'] = error_metrics(
                bf16_from_bits(output), bf16_from_bits(native_controls[label]))
            if _hash(output) != item['output_sha256']:
                raise ValueError('returned output does not match child hash')
    records = entry['preflight'] + entry['warmup'] + entry['runs']
    numerical_pass = all(item['errors_vs_native_control']['correctness'] == 'passed'
                         for item in entry['preflight'] + entry['runs'])
    calls = len(records)
    checks = dict(structural_preflight=all(_structural_checks(entry['preflight']).values()),
        finite_same_arithmetic_outputs=all(item['finite'] and
            item['output_sha256'] == _hash(controls[item['input']]) for item in records),
        both_runners_completed=entry['completed_dispatches'] == dict(swiglu=calls, down=calls),
        fixed_weights_uploaded_once=entry['fixed_weight_upload_counts'] == dict(gate=1, up=1, down=1),
        original_weight_bytes_unchanged=entry['original_weight_bytes_unchanged'],
        input_bytes_unchanged=entry['input_bytes_unchanged'])
    entry['numerical_checks'] = dict(original_tolerances_vs_native_control=numerical_pass,
        cross_arithmetic_error_is_hard_gate=entry['arithmetic'] == 'bf16' or numerics == 'strict')
    if entry['numerical_checks']['cross_arithmetic_error_is_hard_gate']:
        checks['original_tolerances_vs_native_control'] = numerical_pass
    entry['checks'] = checks
    entry['status'] = 'passed' if all(checks.values()) else 'failed'


def _worker_main(config_path):
    config = json.loads(config_path.read_text())
    args = SimpleNamespace(**config['args'])
    weights = tuple(UpstreamWeightBuffer(np.load(x['path'], mmap_mode='r'), x['k'], x['n'])
                    for x in config['weights'])
    inputs = [(x['label'], np.load(x['path'], mmap_mode='r')) for x in config['inputs']]
    entry = config['entry']
    try:
        payload = _run_block(args, weights, inputs, entry)
        for field, outputs in payload.items():
            for index, output in enumerate(outputs):
                np.save(config_path.parent / f'{field}_{index}.npy', output)
    except Exception as error:
        entry.update(status='failed', error=str(error), traceback=traceback.format_exc())
    finally:
        (config_path.parent / 'result.json').write_text(json.dumps(entry, indent=2, allow_nan=False) + '\n')
    return 0 if entry['status'] == 'completed' else 1


def _subprocess_block(args, fixture_paths, entry, directory):
    directory.mkdir()
    config = dict(entry=entry, weights=fixture_paths['weights'], inputs=fixture_paths['inputs'],
        args={key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()})
    config['args']['artifact_root'] = str(args.artifact_root.resolve())
    path = directory / 'config.json'
    path.write_text(json.dumps(config))
    result = subprocess.run([sys.executable, '-m', 'experiments.ffn_partition.benchmark_upstream_arithmetic',
        '--worker-config', str(path)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=args.block_timeout, check=False)
    result_path = directory / 'result.json'
    if result_path.exists():
        entry.update(json.loads(result_path.read_text()))
    entry.update(child_process_returncode=result.returncode, child_process_output=result.stdout[-8000:])
    if result.returncode or entry.get('status') != 'completed':
        raise RuntimeError(f"isolated block failed: {entry.get('error', result.stdout[-2000:])}")
    return {field: [np.load(directory / f'{field}_{index}.npy') for index in range(count)]
            for field, count in (('preflight', 4), ('timed', len(entry['runs'])))}


def _summarize(blocks):
    result = {}
    for index, arithmetic in ARITHMETICS.items():
        runs = [r for b in blocks if b['profile_index'] == index for r in b['runs']]
        result[str(index)] = dict(arithmetic=arithmetic, wall=_stats([r['wall_us'] for r in runs]),
            dispatch_wait={name: _stats([r['diagnostics']['dispatch_wait_us'][name] for r in runs])
                           for name in ('swiglu', 'down')},
            host_stages={name: _stats([r['diagnostics']['stages'][name] for r in runs])
                         for name in runs[0]['diagnostics']['stages']},
            original_tolerances_vs_native_control=all(r['errors_vs_native_control']['correctness'] == 'passed' for r in runs),
            max_relative_l2_vs_native=max(r['errors_vs_native_control']['relative_l2_error'] for r in runs),
            max_absolute_error_vs_native=max(r['errors_vs_native_control']['max_abs_error'] for r in runs))
    a, b = (result[str(index)]['wall']['median_us'] for index in (1, 2))
    result.update(candidate_over_baseline_speedup=a / b, candidate_latency_reduction_percent=100 * (a - b) / a)
    return result


def run_benchmark(args):
    profile = resolve_profile(PROFILE_NAME)
    report = dict(status='preparing', evidence_kind='direct-weight arithmetic NPU branch timing',
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        scope='synthetic NPU FFN branch with host staging; no GPU, whole-model or model-accuracy claim',
        arithmetic_profiles={'1': 'bf16', '2': 'bfp16'}, profile_name=PROFILE_NAME,
        profile_definitions={str(i): dict(profile, arithmetic=a) for i, a in ARITHMETICS.items()},
        bfp16_numerics=args.bfp16_numerics, tolerances=TOLERANCES,
        weight_layout=UPSTREAM_LAYOUT_VERSION, weight_repacking=False, segment_pipeline_depth=2,
        order=f'{args.order}: A=native BF16, B=BFP16; fresh subprocess per reference/timed block',
        comparison_reference='Separate per-arithmetic A/B/zero/repeat-A references; exact within arithmetic; cross arithmetic compared to native hardware, not a CPU oracle',
        timing_boundary='UpstreamNpuFFN.run including validation, host layouts, BO I/O, both launches/waits and final unpacking',
        dispatch_wait_note='host launch-plus-wait intervals, not device-only phase times',
        excluded_from_timing=['construction', 'fixed-weight uploads', 'structural preflight', 'warmup', 'output copies', 'hashing', 'comparisons'],
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        environment=dict(python=sys.version, numpy=np.__version__, platform=platform.platform(),
            thread_limits={k: os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')}),
        artifacts={}, reference_blocks=[], blocks=[], completed_npu_dispatches=0)
    sources = ('benchmark_upstream_arithmetic.py', 'benchmark_upstream_optimizations.py',
               'check_upstream.py', 'upstream_npu.py', 'npu_backend.py')
    paths = [f'experiments/ffn_partition/{x}' for x in sources] + [
        'npu/ffn/xrt_runner.py', 'npu/ffn/prefill_reference.py', 'npu/ffn/upstream_weights.py']
    report['source_sha256'] = {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        report['completed_npu_dispatches'] = sum(sum(b.get('completed_dispatches', {}).values())
            for b in report['reference_blocks'] + report['blocks'])
        temp = args.output.with_name(args.output.name + '.tmp')
        temp.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        temp.replace(args.output)

    try:
        order = block_order(args.rounds, args.order)
        if args.warmup < 2 or args.iterations < 2 or args.bfp16_numerics not in ('report', 'strict'):
            raise ValueError('warmup/iterations must be >=2; bfp16-numerics must be report or strict')
        weights = tuple(prepare_weights(k, n, args.seed + i).weight for i, (k, n) in enumerate(
            ((args.hidden, args.intermediate), (args.hidden, args.intermediate), (args.intermediate, args.hidden))))
        original_hashes = [_hash(w.data) for w in weights]
        report['original_weight_sha256'] = dict(zip(('gate', 'up', 'down'), original_hashes))
        report['weight_bytes'] = dict(zip(('gate', 'up', 'down'), [w.nbytes for w in weights]))
        inputs = [(label, bf16_bits(x)) for label, x in _inputs(args.m, args.hidden, args.seed + 3)]
        for _, x in inputs:
            x.flags.writeable = False
        report['input_sha256'] = {label: _hash(x) for label, x in inputs}
        report['status'] = 'building'
        save()
        for index, arithmetic in ARITHMETICS.items():
            specs = _ffn_specs(args.m, args.hidden, args.channels, *weights, args.artifact_root,
                args.channel_start, segment_pipeline_depth=2, arithmetic=arithmetic, **artifact_profile(profile))
            report['artifacts'][str(index)] = {name: _build(spec, args) for name, spec in specs.items()}
            save()
        if args.build_only:
            report['status'] = 'built_not_executed'
        else:
            controls = {1: {}, 2: {}}
            with tempfile.TemporaryDirectory(prefix='heteromega-arithmetic-abba-') as temporary:
                directory = Path(temporary)
                fixture_paths = _fixture_files(directory, weights, inputs)
                report['status'] = 'running'
                for index, arithmetic in ARITHMETICS.items():
                    entry = dict(profile_index=index, arithmetic=arithmetic, profile=profile,
                                 excluded_from_summary=True, status='pending')
                    report['reference_blocks'].append(entry)
                    payload = _subprocess_block(args, fixture_paths, entry, directory / f'reference_{index}')
                    _compare_outputs(entry, payload, controls[index], controls[1], args.bfp16_numerics)
                    del payload
                    save()
                    if entry['status'] != 'passed':
                        raise RuntimeError(f'{arithmetic} reference failed')
                for ordinal, (round_index, position, index) in enumerate(order):
                    entry = dict(round=round_index, position=position, profile_index=index,
                        arithmetic=ARITHMETICS[index], profile=profile, status='pending',
                        expected_output_sha256={label: _hash(x) for label, x in controls[index].items()})
                    report['blocks'].append(entry)
                    save()
                    block_dir = directory / f'block_{ordinal}'
                    payload = _subprocess_block(args, fixture_paths, entry, block_dir)
                    _compare_outputs(entry, payload, controls[index], controls[1], args.bfp16_numerics)
                    del payload
                    for path in block_dir.glob('*.npy'):
                        path.unlink()
                    save()
                    if entry['status'] != 'passed':
                        raise RuntimeError(f'block {round_index}/{position} failed')
            expected_count = 16 + 8 * args.rounds * (4 + args.warmup + args.iterations)
            save()
            report['checks'] = dict(all_references_and_blocks_passed=all(b['status'] == 'passed'
                for b in report['reference_blocks'] + report['blocks']),
                expected_dispatch_count=report['completed_npu_dispatches'] == expected_count,
                original_weight_bytes_unchanged=all(_hash(w.data) == h for w, h in zip(weights, original_hashes)),
                input_bytes_unchanged=all(_hash(x) == report['input_sha256'][label] for label, x in inputs))
            report['summary'] = _summarize(report['blocks'])
            report['status'] = 'passed' if all(report['checks'].values()) else 'failed'
    except Exception as error:
        report.update(status='failed', error=str(error), traceback=traceback.format_exc())
    finally:
        save()
    return report


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--worker-config':
        raise SystemExit(_worker_main(Path(sys.argv[2])))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--artifact-root', type=Path, required=True)
    parser.add_argument('--iron-python', default=sys.executable)
    for name, default in (('seed', 251025), ('m', 512), ('hidden', 4096), ('intermediate', 14336),
                          ('channels', 2560), ('channel-start', 0), ('rounds', 1), ('warmup', 5), ('iterations', 25)):
        parser.add_argument('--' + name, type=int, default=default)
    parser.add_argument('--order', choices=('ABBA', 'BAAB'), default='ABBA')
    parser.add_argument('--bfp16-numerics', choices=('report', 'strict'), default='report')
    parser.add_argument('--compile-timeout', type=float, default=900)
    parser.add_argument('--block-timeout', type=float, default=180)
    parser.add_argument('--environment-note', default='')
    builds = parser.add_mutually_exclusive_group()
    builds.add_argument('--build-only', action='store_true')
    builds.add_argument('--no-build', action='store_true')
    args = parser.parse_args()
    if args.rounds < 1 or args.warmup < 2 or args.iterations < 2:
        parser.error('rounds must be >=1 and warmup/iterations >=2')
    if any(not np.isfinite(x) or x <= 0 for x in (args.compile_timeout, args.block_timeout)):
        parser.error('timeouts must be finite and positive')
    report = run_benchmark(args)
    print(json.dumps({key: report.get(key) for key in
        ('status', 'completed_npu_dispatches', 'summary', 'error')}, indent=2))
    raise SystemExit(0 if report['status'] in ('passed', 'built_not_executed') else 1)


if __name__ == '__main__':
    main()
