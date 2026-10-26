"""ABBA comparison of serial and two-segment native-BF16 NPU FFN schedules.

Each block owns one FFN runner, uploads identical original-format weights,
warms up, and times repeated run() calls. Context creation, fixed uploads,
hashing and numerical comparisons are outside the timed interval. This
measures the NPU branch including activation staging, not GPU+NPU inference.
Run check_upstream first for independent strict CPU-reference correctness.
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
import tempfile
import time
import traceback
from types import SimpleNamespace

import numpy as np

from .check_upstream import _build, _hash, _inputs, prepare_weights
from .npu_backend import ROOT
from .upstream_npu import UpstreamNpuFFN, _ffn_specs
from prefill_reference import bf16_bits, bf16_from_bits, error_metrics
from upstream_weights import UpstreamWeightBuffer, UPSTREAM_LAYOUT_VERSION


def block_order(rounds, order='ABBA'):
    """Repeated ABBA balances a linear drift within each four-block round."""
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 1:
        raise ValueError('rounds must be a positive integer')
    if order not in ('ABBA', 'BAAB'):
        raise ValueError('order must be ABBA or BAAB')
    return [(round_index, position, depth) for round_index in range(rounds)
            for position, depth in enumerate((1 if letter == 'A' else 2) for letter in order)]


def _run_block(args, weights, inputs, entry):
    """Release both XRT runners before the caller opens the next block."""
    branch = None
    timed_outputs = []
    entry.update(status='initializing', warmup=[], runs=[])
    try:
        branch = UpstreamNpuFFN(args.m, args.hidden, args.channels, *weights,
            args.artifact_root, channel_start=args.channel_start,
            segment_pipeline_depth=entry['segment_pipeline_depth'], copy_output_bits=True)
        entry['runner_metadata'] = branch.metadata
        entry['status'] = 'warming_up'
        for index in range(args.warmup):
            label, x = inputs[index % len(inputs)]
            result = branch.run(x)
            entry['warmup'].append(dict(input=label, output_sha256=_hash(result),
                finite=bool(np.all((result & 0x7F80) != 0x7F80)),
                diagnostics=branch.last_diagnostics))
        entry['status'] = 'timing'
        for index in range(args.iterations):
            label, x = inputs[index % len(inputs)]
            before = time.perf_counter_ns()
            result = branch.run(x)
            elapsed = (time.perf_counter_ns() - before) / 1000.0
            entry['runs'].append(dict(index=index, input=label, wall_us=elapsed,
                                      diagnostics=branch.last_diagnostics))
            # run() returns an owned output; retain it until timing has ended.
            timed_outputs.append(result)
        entry['status'] = 'completed'
        return timed_outputs
    finally:
        if branch is not None:
            entry['completed_dispatches'] = {
                name: runner.completed_dispatches for name, runner in branch.runners.items()}
            entry['fixed_weight_upload_counts'] = {
                'gate': branch.swiglu.input_write_counts[1],
                'up': branch.swiglu.input_write_counts[2],
                'down': branch.down.input_write_counts[1]}
        # No branch or runner object escapes this function. Releasing the
        # previous contexts avoids accumulating competing XRT contexts.
        del branch
        gc.collect()


def _compare_outputs(entry, outputs, controls):
    if len(entry['runs']) != len(outputs):
        raise ValueError('timed output count does not match recorded runs')
    for item, output in zip(entry['runs'], outputs):
        label = item['input']
        finite = bool(np.all((output & 0x7F80) != 0x7F80))
        if label not in controls:
            if entry['segment_pipeline_depth'] != 1 or not finite:
                raise ValueError('a finite serial-control output must precede each candidate input')
            controls[label] = output.copy()
        item.update(output_sha256=_hash(output), finite=finite,
            nonzero=bool(np.any(output & 0x7FFF)),
            identical_to_serial_control=bool(np.array_equal(output, controls[label])),
            errors_vs_serial_control=error_metrics(bf16_from_bits(output),
                                                    bf16_from_bits(controls[label])))
    expected_dispatches = len(entry['warmup']) + len(entry['runs'])
    entry['checks'] = dict(
        all_finite=all(item['finite'] for item in entry['warmup'] + entry['runs']),
        warmup_identical_to_serial_control=all(item['output_sha256'] == _hash(controls[item['input']])
                                               for item in entry['warmup']),
        all_nonzero=all(item['nonzero'] for item in entry['runs']),
        all_identical_to_serial_control=all(item['identical_to_serial_control']
                                            for item in entry['runs']),
        original_tolerances_vs_serial_control=all(
            item['errors_vs_serial_control']['correctness'] == 'passed' for item in entry['runs']),
        both_runners_completed=entry['completed_dispatches'] == {
            'swiglu': expected_dispatches, 'down': expected_dispatches},
        fixed_weights_uploaded_once=entry['fixed_weight_upload_counts'] == {
            'gate': 1, 'up': 1, 'down': 1})
    entry['status'] = 'passed' if all(entry['checks'].values()) else 'failed'


def _worker_main(config_path):
    """Private child entry point; process exit releases all XRT resources."""
    config = json.loads(config_path.read_text())
    args = SimpleNamespace(**config['args'])
    weights = tuple(UpstreamWeightBuffer(np.load(item['path'], mmap_mode='r'), item['k'], item['n'])
                    for item in config['weights'])
    inputs = [(item['label'], np.load(item['path'], mmap_mode='r')) for item in config['inputs']]
    entry = config['entry']
    try:
        outputs = _run_block(args, weights, inputs, entry)
        for index, output in enumerate(outputs):
            np.save(config_path.parent / f'output_{index}.npy', output)
    except Exception as error:
        entry.update(status='failed', error=str(error), traceback=traceback.format_exc())
    finally:
        (config_path.parent / 'result.json').write_text(json.dumps(entry, indent=2, allow_nan=False) + '\n')
    return 0 if entry['status'] == 'completed' else 1


def _subprocess_block(args, fixture_paths, entry, directory):
    directory.mkdir()
    config = dict(entry=entry, weights=fixture_paths['weights'], inputs=fixture_paths['inputs'],
        args={key: str(value) if isinstance(value, Path) else value
              for key, value in vars(args).items()})
    config['args']['artifact_root'] = str(args.artifact_root.resolve())
    path = directory / 'config.json'
    path.write_text(json.dumps(config))
    result = subprocess.run([sys.executable, '-m', 'experiments.ffn_partition.benchmark_upstream_pipeline',
        '--worker-config', str(path)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=args.block_timeout, check=False)
    result_path = directory / 'result.json'
    if result_path.exists():
        entry.update(json.loads(result_path.read_text()))
    entry['child_process_returncode'] = result.returncode
    entry['child_process_output'] = result.stdout[-8000:]
    if result.returncode or entry.get('status') != 'completed':
        raise RuntimeError(f"isolated block failed: {entry.get('error', result.stdout[-2000:])}")
    return [np.load(directory / f'output_{index}.npy') for index in range(args.iterations)]


def _fixture_files(directory, weights, inputs):
    """Transport the same synthetic packed bytes unchanged to child processes."""
    result = dict(weights=[], inputs=[])
    for label, weight in zip(('gate', 'up', 'down'), weights):
        path = directory / f'{label}_weight.npy'
        np.save(path, weight.data)
        result['weights'].append(dict(path=str(path), k=weight.k, n=weight.n))
    for label, x in inputs:
        path = directory / f'{label}.npy'
        np.save(path, x)
        result['inputs'].append(dict(path=str(path), label=label))
    return result


def _stats(values):
    values = np.asarray(values, dtype=np.float64)
    return dict(count=int(values.size), median_us=float(np.median(values)),
        mean_us=float(np.mean(values)), min_us=float(np.min(values)),
        max_us=float(np.max(values)), p10_us=float(np.percentile(values, 10)),
        p90_us=float(np.percentile(values, 90)))


def _summarize(blocks):
    summary = {}
    for depth in (1, 2):
        runs = [run for block in blocks if block['segment_pipeline_depth'] == depth
                for run in block['runs']]
        summary[str(depth)] = dict(wall=_stats([r['wall_us'] for r in runs]),
            dispatch_wait={name: _stats([r['diagnostics']['dispatch_wait_us'][name]
                for r in runs]) for name in ('swiglu', 'down')})
    serial = summary['1']['wall']['median_us']
    candidate = summary['2']['wall']['median_us']
    summary.update(candidate_over_serial_speedup=serial / candidate,
                   candidate_latency_reduction_percent=100 * (serial - candidate) / serial)
    return summary


def run_benchmark(args):
    report = dict(status='preparing', evidence_kind='NPU branch ABBA timing and control equivalence',
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        scope='native BF16 NPU FFN branch with host staging; no GPU, whole-model or accuracy claim',
        arithmetic='bf16', weight_layout=UPSTREAM_LAYOUT_VERSION, weight_repacking=False,
        order=f'{args.order}: A=serial1, B=pipelined2; each block is an isolated process',
        comparison_reference='separate untimed serial-control block, then exact equality for every timed output; not a CPU oracle',
        timing_boundary='UpstreamNpuFFN.run only, including input validation, layouts, BO I/O, waits and output unpack',
        dispatch_wait_note='host launch+wait intervals, not device-cycle or kernel-only timings',
        excluded_from_timing=['construction', 'fixed-weight uploads', 'warmup', 'hashing', 'numerical comparisons'],
        config={key: str(value) if isinstance(value, Path) else value
                for key, value in vars(args).items()},
        environment=dict(python=sys.version, numpy=np.__version__, platform=platform.platform(),
            thread_limits={key: os.environ.get(key) for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS')}),
        completed_npu_dispatches=0, artifacts={}, blocks=[])
    sources = ('experiments/ffn_partition/benchmark_upstream_pipeline.py',
               'experiments/ffn_partition/check_upstream.py',
               'experiments/ffn_partition/upstream_npu.py',
               'experiments/ffn_partition/npu_backend.py', 'npu/ffn/xrt_runner.py')
    report['source_sha256'] = {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        report['completed_npu_dispatches'] = sum(sum(b.get('completed_dispatches', {}).values())
            for b in [*report['blocks'], report.get('reference_block', {})])
        temporary = args.output.with_name(args.output.name + '.tmp')
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        temporary.replace(args.output)

    try:
        order = block_order(args.rounds, args.order)
        save()
        # Retain only the original read-only packed arrays, not fixture oracle
        # matrices. Both variants receive these exact same array objects.
        weights = (prepare_weights(args.hidden, args.intermediate, args.seed).weight,
                   prepare_weights(args.hidden, args.intermediate, args.seed + 1).weight,
                   prepare_weights(args.intermediate, args.hidden, args.seed + 2).weight)
        original_hashes = [_hash(w.data) for w in weights]
        report['original_weight_sha256'] = dict(zip(('gate', 'up', 'down'), original_hashes))
        report['weight_bytes'] = dict(zip(('gate', 'up', 'down'), [w.nbytes for w in weights]))
        inputs = [(label, bf16_bits(x)) for label, x in
                  _inputs(args.m, args.hidden, args.seed + 3)[:2]]
        for _, x in inputs:
            x.flags.writeable = False
        report['input_sha256'] = {label: _hash(x) for label, x in inputs}
        report['status'] = 'building'
        save()
        for depth in (1, 2):
            specs = _ffn_specs(args.m, args.hidden, args.channels, *weights,
                args.artifact_root, args.channel_start, segment_pipeline_depth=depth)
            report['artifacts'][str(depth)] = {name: _build(spec, args) for name, spec in specs.items()}
            save()
        if args.build_only:
            report['status'] = 'built_not_executed'
        else:
            report['status'] = 'running'
            controls = {}
            with tempfile.TemporaryDirectory(prefix='heteromega-pipeline-abba-') as temporary:
                directory = Path(temporary)
                fixture_paths = _fixture_files(directory, weights, inputs)
                # Establish references before either ABBA or BAAB. Its timings
                # are explicitly excluded from every comparison statistic.
                reference = dict(round=-1, position=-1, segment_pipeline_depth=1,
                                 status='pending', excluded_from_summary=True)
                report['reference_block'] = reference
                reference_args = SimpleNamespace(**vars(args))
                reference_args.warmup, reference_args.iterations = 2, 2
                outputs = _subprocess_block(reference_args, fixture_paths, reference, directory / 'reference')
                _compare_outputs(reference, outputs, controls)
                del outputs
                save()
                if reference['status'] != 'passed':
                    raise RuntimeError('serial reference block failed')
                for index, (round_index, position, depth) in enumerate(order):
                    entry = dict(round=round_index, position=position, segment_pipeline_depth=depth,
                                 status='pending')
                    report['blocks'].append(entry)
                    save()
                    block_dir = directory / f'block_{index}'
                    outputs = _subprocess_block(args, fixture_paths, entry, block_dir)
                    _compare_outputs(entry, outputs, controls)
                    del outputs
                    # Outputs can be large at model shape; retain only hashes,
                    # errors and raw times after each block has been checked.
                    for path in block_dir.glob('output_*.npy'):
                        path.unlink()
                    save()
                    if entry['status'] != 'passed':
                        raise RuntimeError(f'block {round_index}/{position} failed execution or control equivalence')
            report['checks'] = dict(
                all_blocks_passed=all(b['status'] == 'passed' for b in report['blocks']),
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
    parser.add_argument('--seed', type=int, default=251025)
    parser.add_argument('--m', type=int, default=512)
    parser.add_argument('--hidden', type=int, default=4096)
    parser.add_argument('--intermediate', type=int, default=14336)
    parser.add_argument('--channels', type=int, default=2560)
    parser.add_argument('--channel-start', type=int, default=0)
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--order', choices=('ABBA', 'BAAB'), default='ABBA')
    parser.add_argument('--warmup', type=int, default=2)
    parser.add_argument('--iterations', type=int, default=10)
    parser.add_argument('--compile-timeout', type=float, default=900)
    parser.add_argument('--block-timeout', type=float, default=120)
    parser.add_argument('--environment-note', default='', help='observed hardware/power/contention context')
    builds = parser.add_mutually_exclusive_group()
    builds.add_argument('--build-only', action='store_true')
    builds.add_argument('--no-build', action='store_true')
    args = parser.parse_args()
    if args.rounds < 1 or args.warmup < 2 or args.iterations < 2:
        parser.error('rounds must be >=1; warmup and iterations must be >=2 to cover both signed inputs')
    if not np.isfinite(args.compile_timeout) or args.compile_timeout <= 0:
        parser.error('--compile-timeout must be finite and positive')
    if not np.isfinite(args.block_timeout) or args.block_timeout <= 0:
        parser.error('--block-timeout must be finite and positive')
    report = run_benchmark(args)
    print(json.dumps({key: report.get(key) for key in
        ('status', 'completed_npu_dispatches', 'summary', 'error')}, indent=2))
    raise SystemExit(0 if report['status'] in ('passed', 'built_not_executed') else 1)


if __name__ == '__main__':
    main()
