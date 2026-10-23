"""Audit and plot the October 22 W4A16 FFN optimization experiment.

This reads saved hardware reports; it runs no device workload. Ordinary
latencies and instrumented diagnostics remain separate, and repeated runs
are never pooled. Example (run from the repository root):

  /tmp/heteromega-bfp16-analysis/bin/python \
    experiments/ffn_partition/results/optimization_20261022/analyze.py \
    --raw-root experiments/ffn_partition/results/optimization_20261022/raw \
    --output-dir experiments/ffn_partition/results/optimization_20261022/plots

--raw-root may name the unpacked archive root or its evidence/optimization_20261022
subdirectory. Six primary reports are required by default; --report explicitly
selects reports for an independent partial audit. Repeats in the same directory
are included automatically when their names begin control_ or optimized_.
Reported BFP16 deviations require --allow-accuracy-deviations and stay labeled.
Source/binary hashes are checked for internal consistency and retained; this
script does not independently establish that remote binary files match them.
"""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import sys
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from experiments.ffn_partition.sweep_partition import validate_report_data

REQUIRED = ('control_sweep.json', 'optimized_sweep.json', 'optimized_owned_2048.json',
            'control_timeline_2048.json', 'optimized_timeline_2048.json', 'smoke.json')
MATCH_CONFIG = ('m', 'hidden', 'intermediate', 'seed', 'npu_arithmetic', 'accuracy_policy',
                'columns', 'npu_design', 'fuse_gate_up', 'fuse_swiglu')
LIMITS = [
    'Synthetic isolated prefill FFN; these are not full-model or TTFT measurements.',
    'Each ordinary partition retains its own fresh HeteroMosaic GPU-only control.',
    'Native heterogeneous HeteroMosaic is not measured by these reports.',
    'Bars show sample p10–p90, not confidence intervals; independent runs are not pooled.',
    'Instrumented diagnostics do not supply ordinary-latency or speedup claims.',
    'Host waits include device compute, DMA, stalls and runtime; they are not pure data movement.',
    'Host stages can overlap GPU execution; independent stage medians are not additive.',
    'Recorded source/binary hashes are internally checked, not rehashed against remote binaries.',
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stats(values):
    values = np.asarray(list(values), dtype=np.float64)
    require(values.ndim == 1 and values.size > 0 and np.all(np.isfinite(values))
            and np.all(values >= 0), 'timings must be finite, nonnegative and nonempty')
    return dict(count=int(values.size), median_us=float(np.median(values)),
                p10_us=float(np.percentile(values, 10)), p90_us=float(np.percentile(values, 90)),
                min_us=float(values.min()), max_us=float(values.max()))


def metrics_in(value, path=''):
    if isinstance(value, dict):
        if 'relative_l2_error' in value and 'max_abs_error' in value:
            yield path, value
        else:
            for key, child in value.items():
                yield from metrics_in(child, path + '/' + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from metrics_in(child, path + '/' + str(index))


def audit_metrics(value):
    checks = list(metrics_in(value))
    require(bool(checks), 'report has no numerical error metrics')
    for path, check in checks:
        require(check.get('finite') is True and check.get('accepted') is True and
                check.get('structural_failures') == [], f'{path}: failed finite/integrity acceptance')
        require(all(check.get(k) == v for k, v in [('rtol', .03), ('atol', .05), ('l2_limit', .02)]),
                f'{path}: numerical tolerance was changed')
        for key in ('relative_l2_error', 'max_abs_error', 'normalized_max_error',
                    'rms_error', 'reference_max_abs', 'max_error_limit'):
            item = check.get(key)
            require(type(item) in (int, float) and math.isfinite(item) and item >= 0,
                    f'{path}/{key}: missing or invalid error magnitude')
        limit = .05 + .03 * check['reference_max_abs']
        passed = (check['max_abs_error'] == 0 if check['reference_max_abs'] == 0 else
                  check['relative_l2_error'] <= .02 and check['max_abs_error'] <= limit)
        require(math.isclose(check['max_error_limit'], limit, rel_tol=1e-12) and
                check.get('passed') is passed, f'{path}: recorded tolerance status disagrees with errors')
        require(check.get('correctness') == ('passed' if passed else 'failed') and
                check.get('accuracy_status') == ('within_tolerance' if passed else 'reported_deviation'),
                f'{path}: relabeled numerical status')
        if '/gpu_accuracy' in path or path.endswith('_gpu_partial') or 'baseline_input_' in path:
            require(check.get('accuracy_policy') == 'strict' and passed,
                    f'{path}: GPU control must pass strict bounds')
    result = {'stored_metric_occurrences': len(checks),
              'all_within_original_tolerances': all(check['passed'] for _, check in checks),
              'outside_tolerance_occurrences': sum(not check['passed'] for _, check in checks)}
    for key in ('relative_l2_error', 'max_abs_error', 'normalized_max_error', 'rms_error'):
        path, check = max(checks, key=lambda pair: pair[1][key])
        result[key] = {'value': check[key], 'location': path}
    return result


def artifact_identity(metadata):
    require(metadata.get('cpu_activation_fallback') is False, 'CPU fallback is not an NPU measurement')
    require(metadata.get('launches_per_run') == 2 and set(metadata.get('artifacts', {})) == {'swiglu', 'down'},
            'optimization comparison requires the two-launch SwiGLU/down graph')
    result = {}
    for stage, artifact in metadata['artifacts'].items():
        manifest, contract = artifact['manifest'], artifact['build_contract']
        for key, value in contract['expected_manifest'].items():
            require(manifest.get(key) == value, f'{stage}: build contract disagrees with manifest {key}')
        source = contract['source_sha256']['npu/ffn/w4a16_prefill_bfp16.cc']
        require(source == manifest['source_sha256'], f'{stage}: kernel source hashes differ')
        require(manifest['target_mlir_aie_commit'] == contract['target_mlir_aie_commit'],
                f'{stage}: graph compiler revision differs')
        for key in ('xclbin_sha256', 'insts_sha256'):
            require(re.fullmatch('[0-9a-f]{64}', manifest[key]) is not None, f'{stage}: invalid {key}')
        result[stage] = {'kernel_source_sha256': source, 'build_source_sha256': contract['source_sha256'],
                         'xclbin_sha256_recorded': manifest['xclbin_sha256'],
                         'insts_sha256_recorded': manifest['insts_sha256']}
    return result


def ordinary_host(samples):
    records = [sample['diagnostics']['npu'] for sample in samples if sample['mode'] == 'concurrent']
    result = {'branch_host_wall': stats(row['branch_host_wall_us'] for row in records)}
    for key in records[0]['stages']:
        result[key.removesuffix('_us')] = stats(row['stages'][key] for row in records)
    for stage in records[0]['dispatch_wait_us']:
        result[stage + '_dispatch_wait'] = stats(row['dispatch_wait_us'][stage] for row in records)
        # Per-sample residual, not a difference between independently rounded
        # medians. Includes BO IO/wrappers outside dispatch_wait, not pure DMA.
        stage_key = stage + '_with_host_io_us'
        if stage_key in records[0]['stages']:
            result[stage + '_bo_io_and_wrapper_residual'] = stats(
                row['stages'][stage_key] - row['dispatch_wait_us'][stage] for row in records)
    result['cpu_layout_sum'] = stats(sum(v for k, v in row['stages'].items()
                                        if k.endswith('_layout_us')) for row in records)
    return result


def diagnostic_stages(samples):
    result = {'instrumented_wall': stats(sample['instrumented_wall_us'] for sample in samples),
              'npu_branch_host_wall': stats(sample['npu']['branch_host_wall_us'] for sample in samples)}
    for key in samples[0]['npu']['stages']:
        result['npu_' + key.removesuffix('_us')] = stats(sample['npu']['stages'][key] for sample in samples)
    for stage in samples[0]['npu_submit_wait_host']:
        for field in ('submit_host_us', 'wait_host_us'):
            result[stage + '_' + field.removesuffix('_us')] = stats(
                sample['npu_submit_wait_host'][stage][field] for sample in samples)
        stage_key = stage + '_with_host_io_us'
        result[stage + '_bo_io_and_wrapper_residual'] = stats(
            sample['npu']['stages'][stage_key] - sample['npu']['dispatch_wait_us'][stage]
            for sample in samples)
    for group in ('gpu_event_intervals', 'host_intervals'):
        for key in samples[0][group]:
            result[group + '/' + key] = stats(sample[group][key]['duration_us'] for sample in samples)
    return result


def audit_report(path, allow_deviations):
    report = json.loads(path.read_text())
    require(report.get('status') in ('passed', 'completed_with_accuracy_deviations'),
            f'{path.name}: report is incomplete or failed ({report.get("status")})')
    require(allow_deviations or report['status'] == 'passed',
            f'{path.name}: use --allow-accuracy-deviations to retain explicitly labeled BFP16 deviations')
    config = report['config']
    require(config.get('npu_arithmetic') == 'bfp16' and config.get('fuse_swiglu') is True,
            'this analysis is for fused BFP16 FFN reports')
    ordinary = 'partitions' in report
    result = {'report': path.name, 'sha256': sha256(path.read_bytes()).hexdigest(),
              'status': report['status'], 'mode': 'ordinary' if ordinary else 'diagnostic',
              'config': config, 'accuracy': audit_metrics(report), 'partitions': [],
              'explicit_named_checks': (len(report.get('correctness', {})) + len(report.get('checks', {}))
                                       + sum(len(row.get('correctness', {})) for row in report.get('partitions', []))),
              'provenance': {k: report.get('provenance', {}).get(k) for k in
                             ('started_at_utc', 'cpu_model', 'numpy', 'source_sha256')},
              'gpu_baseline_metadata': report.get('gpu_baseline')}
    for entry in report['partitions'] if ordinary else [report]:
        channels = entry['npu_channels'] if ordinary else config['npu_channels']
        job = {'mode': result['mode'], 'm': config['m'], 'npu_channels': channels,
               'iterations': config['iterations'], 'fuse_gate_up': True, 'fuse_swiglu': True}
        candidate = report
        if ordinary:
            accuracy = dict(entry['accuracy'], accuracy_policy=config['accuracy_policy'])
            entry_status = entry.get('status', 'passed' if accuracy['passed']
                                     else 'completed_with_accuracy_deviations')
            candidate = dict(report, partitions=[entry], status=entry_status, accuracy=accuracy)
        validation = validate_report_data(candidate, job, SimpleNamespace(**config))
        samples = entry['samples']
        expected_modes = ('baseline', 'serial', 'concurrent') if ordinary else (None,)
        for mode in expected_modes:
            selected = [s for s in samples if not ordinary or s['mode'] == mode]
            require(sorted(s['iteration'] for s in selected) == list(range(config['iterations'])),
                    f'{path.name}: duplicate or missing timed iterations')
        npu_samples = [s['diagnostics']['npu'] if ordinary else s['npu'] for s in samples
                       if not ordinary or s['mode'] != 'baseline']
        counts = [s['completed_dispatches_total'] for s in npu_samples]
        require(all(b - a == 2 for a, b in zip(counts, counts[1:])),
                f'{path.name}: NPU completion counters must advance by two per invocation')
        metadata = entry['npu'] if ordinary else entry['npu_metadata']
        item = {'report': path.name, 'npu_channels': channels,
                'npu_fraction': channels / config['intermediate'],
                'shape': [config[k] for k in ('m', 'hidden', 'intermediate')],
                'validation': validation, 'artifact_identity': artifact_identity(metadata),
                'host_output_readback': metadata.get('host_output_readback', 'owned_copy_legacy'),
                'timed_gpu_partial_metrics_present': all('gpu_accuracy' in s for s in samples
                    if not ordinary or s['mode'] != 'baseline'),
                'accuracy': audit_metrics(entry)}
        if ordinary:
            item['wall_us'] = {mode: stats(s['wall_us'] for s in samples if s['mode'] == mode)
                               for mode in expected_modes}
            for mode, actual in item['wall_us'].items():
                require(actual['min_us'] > 0, 'ordinary latency must be positive')
                for key, value in actual.items():
                    require(math.isclose(entry['stats'][mode][key], value, rel_tol=1e-12),
                            f'{path.name}: stored {mode} {key} differs from samples')
            item['concurrent_host_us'] = ordinary_host(samples)
            gpu = item['wall_us']['baseline']['median_us']
            concurrent = item['wall_us']['concurrent']['median_us']
            item['latency_ratio_vs_own_gpu'] = gpu / concurrent
            item['latency_reduction_pct_vs_own_gpu'] = 100 * (1 - concurrent / gpu)
            item['speedup_vs_own_gpu'] = (gpu / concurrent if item['accuracy']['all_within_original_tolerances'] else None)
        else:
            item['instrumented_stages_us'] = diagnostic_stages(samples)
        result['partitions'].append(item)
    require(report['accuracy']['passed'] is result['accuracy']['all_within_original_tolerances'],
            f'{path.name}: report-wide numerical status differs from stored metrics')
    return result


def comparable(control, candidate):
    return all(control['config'][key] == candidate['config'][key] for key in MATCH_CONFIG)


def comparisons(audits):
    ordinary = [audit for audit in audits if audit['mode'] == 'ordinary']
    controls = [audit for audit in ordinary if audit['report'].startswith('control_')]
    optimized = [audit for audit in ordinary if audit['report'].startswith('optimized_')]
    same_partition, copy_ablation = [], []

    def comparison(a, b, x, y):
        old, new = x['wall_us']['concurrent']['median_us'], y['wall_us']['concurrent']['median_us']
        return {'control_report': a['report'], 'candidate_report': b['report'],
                'npu_channels': x['npu_channels'], 'control_median_us': old, 'candidate_median_us': new,
                'latency_reduction_pct': 100 * (1 - new / old), 'latency_ratio': old / new,
                'control_relative_to_own_gpu': 1 / x['latency_ratio_vs_own_gpu'],
                'candidate_relative_to_own_gpu': 1 / y['latency_ratio_vs_own_gpu'],
                'own_gpu_normalized_reduction_pct': 100 * (1 - x['latency_ratio_vs_own_gpu'] / y['latency_ratio_vs_own_gpu']),
                'all_within_original_tolerances': (x['accuracy']['all_within_original_tolerances'] and
                                                  y['accuracy']['all_within_original_tolerances'])}
    for a in controls:
        for b in optimized:
            if not comparable(a, b):
                continue
            for x in a['partitions']:
                for y in b['partitions']:
                    if x['npu_channels'] == y['npu_channels']:
                        same_partition.append(comparison(a, b, x, y))
    for a in optimized:
        for b in optimized:
            if a is b or not comparable(a, b):
                continue
            for x in a['partitions']:
                for y in b['partitions']:
                    if (x['npu_channels'] == y['npu_channels'] and x['host_output_readback'] == 'owned_copy'
                            and y['host_output_readback'] == 'borrowed_until_consumed'):
                        require(x['artifact_identity'] == y['artifact_identity'],
                                'readback ablation must use identical compiled artifacts')
                        copy_ablation.append(comparison(a, b, x, y))
    return {'same_partition': same_partition, 'owned_vs_borrowed': copy_ablation}


def plot(summary, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    audits = [a for a in summary['reports'] if a['mode'] == 'ordinary' and
              a['config']['m'] == 512 and a['report'] != 'smoke.json']
    require(bool(audits), 'no M512 ordinary reports available to plot')
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.7))
    colors = {'control': '#D55E00', 'optimized': '#0072B2', 'owned': '#009E73', 'other': '#777777'}
    for index, audit in enumerate(audits):
        rows = sorted(audit['partitions'], key=lambda row: row['npu_channels'])
        family = ('owned' if all(row['host_output_readback'] == 'owned_copy' for row in rows)
                  and audit['report'].startswith('optimized') else
                  'control' if audit['report'].startswith('control') else
                  'optimized' if audit['report'].startswith('optimized') else 'other')
        color = colors[family]
        description = {'control': 'Prior BFP16 + owned readback', 'optimized': 'Optimized BFP16 + borrowed readback',
                       'owned': 'Optimized BFP16 + owned readback', 'other': 'Additional report'}[family]
        label = f'{description}\n{Path(audit["report"]).stem} · n={audit["config"]["iterations"]}'
        x = [r['npu_channels'] for r in rows]
        y = [r['wall_us']['concurrent']['median_us'] / 1000 for r in rows]
        yerr = [[(r['wall_us']['concurrent']['median_us'] - r['wall_us']['concurrent']['p10_us']) / 1000 for r in rows],
                [(r['wall_us']['concurrent']['p90_us'] - r['wall_us']['concurrent']['median_us']) / 1000 for r in rows]]
        marker = ['o', 's', '^', 'D', 'v', 'P'][index % 6]
        axes[0].errorbar(x, y, yerr=yerr, label=label, marker=marker, color=color,
                         linewidth=1.5, capsize=3, linestyle='--' if family == 'control' else '-')
        axes[0].scatter(x, [r['wall_us']['baseline']['median_us']/1000 for r in rows],
                        marker='x', color=color, alpha=.65, s=30)
        axes[1].plot(x, [r['latency_ratio_vs_own_gpu'] for r in rows], marker=marker, color=color,
                     linewidth=1.5, linestyle='--' if family == 'control' else '-')
    axes[0].set(title='Ordinary complete FFN latency', xlabel='NPU intermediate channels P', ylabel='Latency (ms)')
    axes[1].set(title='Ratio against each point’s fresh GPU control', xlabel='NPU intermediate channels P',
                ylabel='GPU-only median / concurrent median')
    axes[1].axhline(1, color='#777777', linewidth=.8, linestyle=':')
    for ax in axes:
        ax.grid(axis='y', color='#DFE3E7', linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)
        partitions = sorted({row['npu_channels'] for audit in audits for row in audit['partitions']})
        if len(partitions) <= 10:
            ax.set_xticks(partitions)
    fig.suptitle('W4A16 BFP16 FFN: zero-point conversion and host readback optimization',
                 fontsize=14, weight='bold')
    fig.text(.5, .91, 'M512 / H4096 / I14336 · shared GPU–NPU FFN partition · final sum on GPU',
             ha='center', color='#555555')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, -.06),
               ncol=min(3, len(handles)), frameon=False, fontsize=8)
    fig.text(.01, -.14,
             'Error bars: sample p10–p90; × markers: matched GPU-only medians. Each repeated run remains separate.\n'
             'Synthetic isolated FFN using HeteroMosaic GPU kernels, not native heterogeneous or full-model prefill. '
             'NPU power is only established by recorded snapshots.', fontsize=8)
    fig.subplots_adjust(top=.80, bottom=.22, wspace=.27)
    paths = []
    for ext in ('png', 'pdf', 'svg'):
        path = output / ('partition_latency.' + ext)
        fig.savefig(path, dpi=180, bbox_inches='tight')
        paths.append(path.name)
    plt.close(fig)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--raw-root', type=Path, default=HERE / 'raw')
    parser.add_argument('--output-dir', type=Path, default=HERE / 'plots')
    parser.add_argument('--report', action='append', default=[], help='Explicit report path or basename; repeatable')
    parser.add_argument('--allow-accuracy-deviations', action='store_true')
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args()
    raw = args.raw_root
    if (raw / 'evidence/optimization_20261022').is_dir():
        raw = raw / 'evidence/optimization_20261022'
    if args.report:
        paths = [Path(p) if Path(p).is_file() else raw / p for p in args.report]
    else:
        for name in REQUIRED:
            require((raw / name).is_file(), f'missing primary report {raw / name}')
        paths = sorted(path for path in raw.glob('*.json') if path.name in REQUIRED or
                       path.name.startswith(('control_', 'optimized_')))
    require(len(paths) == len(set(p.resolve() for p in paths)), 'duplicate report path')
    audits = [audit_report(path, args.allow_accuracy_deviations) for path in paths]
    power = {}
    for path in sorted(raw.glob('*power*.txt')):
        text = path.read_text()
        matches = re.findall(r'Power Mode\s*:\s*(\w+)', text)
        if matches:
            power[path.name] = {'modes': sorted(set(matches)), 'sha256': sha256(path.read_bytes()).hexdigest()}
    summary = {'schema_version': 1, 'scope': LIMITS[0], 'raw_report_directory': str(raw.resolve()),
               'reports': audits, 'comparisons': comparisons(audits), 'power_snapshots': power,
               'all_reports_completed': True,
               'all_within_original_tolerances': all(a['accuracy']['all_within_original_tolerances'] for a in audits),
               'successful_npu_completions': sum(p['validation']['completed_npu_dispatches'] for a in audits for p in a['partitions']),
               'timed_invocations': sum(p['validation']['timed_invocations'] for a in audits for p in a['partitions']),
               'explicit_named_checks': sum(a['explicit_named_checks'] for a in audits),
               'limits': LIMITS,
               'analysis_source_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
               'validator_source_sha256': sha256((ROOT / 'experiments/ffn_partition/sweep_partition.py').read_bytes()).hexdigest()}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary['figures'] = [] if args.no_render else plot(summary, args.output_dir)
    destination = args.output_dir / 'summary.json'
    destination.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'summary': str(destination), 'reports': len(audits),
                      'successful_npu_completions': summary['successful_npu_completions'],
                      'all_within_original_tolerances': summary['all_within_original_tolerances'],
                      'same_partition_comparisons': summary['comparisons']['same_partition'],
                      'owned_vs_borrowed': summary['comparisons']['owned_vs_borrowed']}, indent=2))


if __name__ == '__main__':
    main()
