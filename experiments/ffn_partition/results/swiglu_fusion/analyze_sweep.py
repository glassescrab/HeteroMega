"""Audit saved fusion sweep evidence and derive ordinary/stage summaries.

No hardware execution or measurement-source edits occur. Example::

    python experiments/ffn_partition/results/swiglu_fusion/analyze_sweep.py \
        experiments/ffn_partition/results/swiglu_fusion/sweep_m512 \
        --output experiments/ffn_partition/results/swiglu_fusion/sweep_analysis.json

The numerical arrays and compiled NPU binaries are not stored in these reports;
this validates recorded evidence and current source contracts, not those bytes.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from experiments.ffn_partition.npu_backend import _artifact_specs, _build_contract
from experiments.ffn_partition.plot_partition_sweep import collect, statistics


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def audit(directory):
    directory = Path(directory).resolve()
    manifest_path = directory / 'sweep_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    failures, jobs, source_files = [], [], set()
    raw_diagnostics = {}
    counts = Counter()

    def check(condition, label):
        if not condition:
            failures.append(label)

    def sources(mapping, label):
        for path, expected in mapping.items():
            source_files.add(path)
            actual_path = ROOT / path
            check(actual_path.is_file() and digest(actual_path) == expected, label + '/source/' + path)

    check(manifest['status'] == 'passed', 'manifest/status')
    sources(manifest['source_sha256'], 'manifest')
    for job in manifest['jobs']:
        name, evidence = job['id'], job['evidence']
        report_path = directory / job['report_path']
        report = json.loads(report_path.read_text())
        config = report['config']
        check(job['status'] == report['status'] == 'passed' and job['returncode'] == 0, name + '/status')
        check(digest(report_path) == evidence['report_sha256'], name + '/report_sha256')
        sources(report['provenance']['source_sha256'], name)
        swiglu = job.get('fuse_swiglu', False)
        stages = {'swiglu', 'down'} if swiglu else {'gate_up', 'silu_mul', 'down'}
        projections = stages - {'silu_mul'}
        launches = len(stages)
        check(config.get('fuse_swiglu', False) is swiglu and config['fuse_gate_up'] is True,
              name + '/fusion_configuration')
        for key in ('m', 'iterations'):
            check(config[key] == job[key], name + '/configuration/' + key)
        for key in ('hidden', 'intermediate', 'seed', 'warmup'):
            check(config[key] == manifest['config'][key], name + '/configuration/' + key)
        check(config['npu_design'] == 'array8' and config['columns'] == 8, name + '/array8')
        n = config['iterations']
        if job['mode'] == 'ordinary':
            check(len(report['partitions']) == 1, name + '/one_partition')
            part = report['partitions'][0]
            check(part['npu_channels'] == job['npu_channels'], name + '/partition')
            samples = part['samples']
            check(Counter(s['mode'] for s in samples) == {'baseline': n, 'serial': n, 'concurrent': n},
                  name + '/timed_mode_counts')
            checks = [*report['correctness'].values(), *part['correctness'].values()]
            npu_samples = [s['diagnostics']['npu'] for s in samples if s['mode'] != 'baseline']
            metadata = part['npu']
            gpu_metadata = [report['gpu_baseline'], part['gpu']]
            expected_completed = launches * (8 + 2 * config['warmup'] + 2 * n)
            expected_first = launches * (8 + 2 * config['warmup'] + 1)
        else:
            check(config['npu_channels'] == job['npu_channels'], name + '/partition')
            samples = report['samples']
            check(len(samples) == n and len(report['warmup_samples']) == config['warmup'], name + '/sample_counts')
            checks = list(report['checks'].values())
            npu_samples = [s['npu'] for s in samples]
            metadata = report['npu_metadata']
            gpu_metadata = [report['gpu_metadata']]
            expected_completed = launches * (4 + config['warmup'] + n)
            expected_first = launches * (4 + config['warmup'] + 1)
            check(report['completed_npu_dispatches'] == report['expected_npu_dispatches'] == expected_completed,
                  name + '/report_completion_totals')
            check(set(report['npu_stage_sequence']) == stages, name + '/reported_stage_sequence')
            raw_diagnostics[(job['npu_channels'], swiglu)] = report
        check(len(samples) == evidence['timed_invocations'], name + '/timed_invocations')
        check(len(checks) == evidence['explicit_checks'] and all(c.get('passed') is True for c in checks),
              name + '/explicit_correctness_checks')
        check(all(s.get('correctness_passed') is True and s['input_index'] == s['iteration'] % 2
                  for s in samples), name + '/timed_correctness_alternating_inputs')
        for index, sample in enumerate(npu_samples):
            check(set(sample['dispatch_wait_us']) == stages, name + f'/sample{index}/stages')
            check(sample['weight_upload_counts'] == {s: 1 for s in projections}, name + f'/sample{index}/fixed_weights')
            check(sample['completed_dispatches_total'] == expected_first + index * launches,
                  name + f'/sample{index}/completion_progression')
        completed = npu_samples[-1]['completed_dispatches_total']
        check(completed == expected_completed == evidence['completed_npu_dispatches'], name + '/completed_count')
        check(metadata['launches_per_run'] == launches and metadata['fixed_weight_uploads'] == 2
              and metadata['cpu_activation_fallback'] is False, name + '/backend_metadata')
        for gpu in gpu_metadata:
            sources(gpu['source_sha256'], name + '/gpu')
        specs = _artifact_specs(config['m'], config['hidden'], job['npu_channels'], directory / 'not_loaded',
                                columns=8, design='array8', fuse_gate_up=True, fuse_swiglu=swiglu)
        check(set(metadata['artifacts']) == set(specs), name + '/artifact_set')
        for label, artifact in metadata['artifacts'].items():
            contract = artifact['build_contract']
            check(contract == _build_contract(specs[label]), name + '/' + label + '/build_contract')
            sources(contract['source_sha256'], name + '/' + label)
            check(all(artifact['manifest'].get(k) == v for k, v in contract['expected_manifest'].items()),
                  name + '/' + label + '/manifest')
            check(artifact['manifest']['target_mlir_aie_commit'] == contract['target_mlir_aie_commit'],
                  name + '/' + label + '/compiler_commit')
            for key in ('xclbin_sha256', 'insts_sha256'):
                check(re.fullmatch('[0-9a-f]{64}', artifact['manifest'][key]) is not None,
                      name + '/' + label + '/' + key)
        power_modes = []
        for when in ('before', 'after'):
            path = directory / job['power_' + when]
            power = json.loads(path.read_text())
            saved = job['power_' + when + '_summary']
            check(digest(path) == saved['sha256'], name + '/power_' + when + '/sha256')
            platforms = [(device['device_id'], platform) for device in power['devices']
                         for platform in device['platforms']]
            check(len(platforms) == 1, name + '/power_' + when + '/single_platform')
            device, platform = platforms[0]
            mode = platform['status']['power_mode']
            check(device == manifest['config']['power_device'] and platform['static_region']['total_columns'] == '8',
                  name + '/power_' + when + '/device')
            check(mode == saved['mode'], name + '/power_' + when + '/mode')
            power_modes.append(mode)
            counts['power_snapshots'] += 1
        check(power_modes == ['default', 'default'], name + '/unchanged_default_mode')
        before = datetime.fromisoformat(job['power_before_summary']['completed_at_utc'])
        start = datetime.fromisoformat(report['provenance']['started_at_utc'])
        after = datetime.fromisoformat(job['power_after_summary']['queried_at_utc'])
        check(before <= start <= after, name + '/power_snapshot_report_start_order')
        counts[job['mode'] + '_reports'] += 1
        counts['timed_invocations'] += len(samples)
        counts['explicit_checks'] += len(checks)
        counts['completed_npu_dispatches'] += completed
        jobs.append({'id': name, 'report_sha256': digest(report_path), 'completed_npu_dispatches': completed,
                     'timed_invocations': len(samples), 'explicit_checks': len(checks), 'power_modes': power_modes})

    normalized = collect([directory])
    check(not normalized['ignored_inputs'], 'plot_parser/no_exclusions')
    ordinary = []
    for row in sorted(normalized['ordinary'], key=lambda r: (r['npu_channels'], r['fuse_swiglu'])):
        ordinary.append({'npu_channels': row['npu_channels'], 'npu_percent': row['npu_percent'],
                         'variant': 'swiglu' if row['fuse_swiglu'] else 'fused',
                         'concurrent_ms': row['timing_ms']['concurrent'],
                         'gpu_baseline_ms': row['timing_ms']['baseline'],
                         'speedup': row['speedup'], 'paired_speedup': row['paired_speedup'],
                         'paired_wins': row['paired_wins'], 'paired_count': row['paired_count'],
                         'report': str(Path(row['report']).relative_to(directory)),
                         'started_utc': row['started_utc']})
    best = {}
    for variant in ('fused', 'swiglu'):
        rows = [row for row in ordinary if row['variant'] == variant]
        if rows:
            latency = min(rows, key=lambda r: r['concurrent_ms']['median'])
            speed = max(rows, key=lambda r: r['speedup'])
            best[variant] = {'lowest_sampled_latency': latency, 'highest_matched_speedup': speed}
    fixed = []
    for p in sorted({r['npu_channels'] for r in ordinary}):
        rows = {r['variant']: r for r in ordinary if r['npu_channels'] == p}
        if len(rows) == 2:
            old, new = rows['fused']['concurrent_ms']['median'], rows['swiglu']['concurrent_ms']['median']
            fixed.append({'npu_channels': p, 'fused_ms': old, 'swiglu_ms': new,
                          'latency_saved_ms': old - new, 'fused_over_swiglu': old / new,
                          'latency_reduction_percent': 100 * (old - new) / old})
    diagnostics = []
    for row in sorted(normalized['diagnostic'], key=lambda r: (r['npu_channels'], r['fuse_swiglu'])):
        data = row['metrics_ms']
        samples = raw_diagnostics[(row['npu_channels'], row['fuse_swiglu'])]['samples']
        summed_gpu = statistics([sum(s['gpu_event_intervals'][key]['duration_us']
                                     for key in ('gate', 'up', 'down')) / 1000 for s in samples])
        diagnostics.append({'npu_channels': row['npu_channels'], 'variant': 'swiglu' if row['fuse_swiglu'] else 'fused',
                            'sample_count': len(samples), 'report': str(Path(row['report']).relative_to(directory)),
                            'gpu_three_projection_event_sum_ms': summed_gpu,
                            'median_ms': {category: {name: values['median'] for name, values in data[category].items()}
                                          for category in ('gpu_event', 'npu_frontend_stage_host_io',
                                                           'npu_frontend_wait', 'npu_components', 'wall')},
                            'gpu_submit_median_us': {k: v['median'] * 1000 for k, v in data['gpu_submit'].items()},
                            'npu_submit_median_us': {k: v['median'] * 1000 for k, v in data['npu_submit'].items()}})
    retuned = None
    if len(best) == 2:
        old, new = (best[v]['lowest_sampled_latency'] for v in ('fused', 'swiglu'))
        retuned = {'fused_channels': old['npu_channels'], 'swiglu_channels': new['npu_channels'],
                   'fused_over_swiglu': old['concurrent_ms']['median'] / new['concurrent_ms']['median'],
                   'latency_reduction_percent': 100 * (1 - new['concurrent_ms']['median'] / old['concurrent_ms']['median']),
                   'interpretation': 'separate configurations/runs at their sampled latency minima; not a controlled fixed-partition fusion effect'}
    return {'status': 'passed' if not failures else 'failed', 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
            'manifest': str(manifest_path.relative_to(ROOT)), 'manifest_sha256': digest(manifest_path),
            'auditor_script': str(Path(__file__).relative_to(ROOT)), 'auditor_sha256': digest(__file__),
            'counts': dict(counts), 'source_files_verified': sorted(source_files), 'jobs': jobs,
            'ordinary': ordinary, 'sampled_best': best, 'fixed_partition_comparison': fixed,
            'retuned_best_comparison': retuned, 'diagnostics': diagnostics, 'failures': failures,
            'interpretation': ['Complete FFN timing includes GPU transfers, host layouts, NPU/GPU branches and GPU boundary reduction.',
                               'All variability ranges are sample p10-p90, not confidence intervals; independent reports are not pooled.',
                               'SwiGLU frontend stages are compared against each invocation of gate/up plus SiLU/multiply; internal fused costs are not separated.',
                               'GPU HIP events and NPU CPU-host intervals use different clocks; branch-duration comparisons are descriptive, not exact overlap or causal attribution.',
                               'Independent medians are not additive. CPU submission includes runtime work and is not driver-only launch overhead.',
                               'Power before/after snapshots establish default at those boundaries; no performance-mode, continuous-clock or energy claim.',
                               'Raw outputs and NPU binaries are absent; reported numerical checks and recorded binary hashes were not independently rerun/rehashable.',
                               'These isolated FFN microbenchmarks do not establish whole-model prefill or TTFT acceleration.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.directory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'counts': result['counts'], 'failures': result['failures'],
                      'retuned_best_comparison': result['retuned_best_comparison']}, indent=2))
    if result['failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
