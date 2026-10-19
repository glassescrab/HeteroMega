"""Compare independently measured SwiGLU candidates without pooling samples.

Run with NumPy and matplotlib. Re-audits both saved sweep manifests, writes a
combined verification JSON and renders chronological candidate medians/ranges.
The original main and confirmation figures and raw reports remain unchanged.
"""

import argparse
from collections import Counter
from datetime import datetime
import csv
import json
from pathlib import Path

from analyze_sweep import ROOT, audit, digest


def compare(directories, output, channels):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    runs, totals, verified_sources = [], Counter(), set()
    shape, device = None, None
    for directory in directories:
        evidence = audit(directory)
        if evidence['status'] != 'passed':
            raise ValueError(f'audit failed: {evidence["failures"]}')
        candidates = [row for row in evidence['ordinary']
                      if row['variant'] == 'swiglu' and row['npu_channels'] in channels]
        if len(candidates) != len(channels) or {row['npu_channels'] for row in candidates} != set(channels):
            raise ValueError('each independent sweep must contain exactly one of every requested SwiGLU candidate')
        manifest = json.loads((Path(directory)/'sweep_manifest.json').read_text())
        first = json.loads((Path(directory)/candidates[0]['report']).read_text())
        this_shape = tuple(first['config'][key] for key in ('m', 'hidden', 'intermediate'))
        this_device = first['provenance']['gpu_name']
        if shape is not None and (shape != this_shape or device != this_device):
            raise ValueError('candidate runs must use the same shape and GPU')
        shape, device = this_shape, this_device
        candidates.sort(key=lambda row: channels.index(row['npu_channels']))
        chronological = sorted(candidates, key=lambda row: datetime.fromisoformat(row['started_utc']))
        runs.append({'series': Path(directory).name, 'started_utc': chronological[0]['started_utc'],
                     'candidate_order': [row['npu_channels'] for row in chronological],
                     'candidates': candidates, 'counts': evidence['counts'],
                     'manifest_sha256': evidence['manifest_sha256'],
                     'sampled_best': evidence['sampled_best'],
                     'retuned_best_comparison': evidence['retuned_best_comparison'],
                     'fixed_partition_comparison': evidence['fixed_partition_comparison'],
                     'partition_order': manifest['config']['npu_channels']})
        totals.update(evidence['counts'])
        verified_sources.update(evidence['source_files_verified'])
    runs.sort(key=lambda run: datetime.fromisoformat(run['started_utc']))
    finalists = sorted(runs[-1]['candidates'], key=lambda row: row['concurrent_ms']['median'])[:2]
    gap = finalists[1]['concurrent_ms']['median'] - finalists[0]['concurrent_ms']['median']
    exact_path = Path(__file__).with_name('exact_verification.json')
    exact = json.loads(exact_path.read_text())
    if exact['status'] != 'passed' or any(digest(exact_path.parent/report['file']) != report['sha256']
                                        for report in exact['reports']):
        raise ValueError('exact correctness evidence does not match its saved successful audit')
    combined = {'status': 'passed', 'auditor_script': str(Path(__file__).relative_to(ROOT)),
                'auditor_sha256': digest(__file__), 'shape': list(shape), 'gpu': device,
                'variant': 'swiglu', 'channels': channels, 'independent_runs': runs,
                'sweep_counts': dict(totals), 'source_files_verified': sorted(verified_sources),
                'exact_correctness': {'verification_sha256': digest(exact_path),
                                     'checks': exact['total_completed_report_checks'],
                                     'completed_npu_dispatches': exact['completed_npu_dispatches']},
                'total_npu_dispatches_including_exact': totals['completed_npu_dispatches'] + exact['completed_npu_dispatches'],
                'last_run_two_lowest_latency_candidates': [row['npu_channels'] for row in finalists],
                'last_run_two_lowest_latency_gap_ms': gap,
                'interpretation': ['Independent main and reverse-order confirmation runs; no pooled samples or global optimum.',
                                   f'The last run has only {gap:.6f} ms between its two lowest sampled candidate medians; a unique optimum is not established.',
                                   'Retuned-best comparisons are distinct from controlled fixed-partition fusion effects.',
                                   'Default power mode at every boundary snapshot; results are isolated FFN latency, not whole-model prefill.']}

    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    colors = ('#0072B2', '#D55E00', '#009E73', '#CC79A7')
    for i, p in enumerate(channels):
        rows = [next(row for row in run['candidates'] if row['npu_channels'] == p) for run in runs]
        xs = [index + .11 * (i - (len(channels)-1)/2) for index in range(len(runs))]
        for ax, speedup in zip(axes, (False, True)):
            stats = [dict(row['paired_speedup'], median=row['speedup']) if speedup else row['concurrent_ms']
                     for row in rows]
            ax.errorbar(xs, [(s['p10']+s['p90'])/2 for s in stats],
                        yerr=[(s['p90']-s['p10'])/2 for s in stats], fmt='none',
                        color=colors[i % len(colors)], capsize=3, elinewidth=1)
            ax.plot(xs, [s['median'] for s in stats], color=colors[i % len(colors)],
                    marker=('o', 's', '^', 'D')[i % 4], linewidth=1.4,
                    label=f'P={p} ({100*p/shape[2]:.2f}% NPU)')
    tick_labels = []
    for index, run in enumerate(runs):
        counts = {r['concurrent_ms']['count'] for r in run['candidates']}
        order = '→'.join(map(str, run['candidate_order']))
        tick_labels.append(f'Run {index+1} · n={"/".join(map(str, sorted(counts)))}\n'
                           f'{datetime.fromisoformat(run["started_utc"]):%m-%d %H:%M} UTC\norder {order}')
    for ax in axes:
        ax.set_xticks(range(len(runs)), tick_labels)
        ax.set_xlim(-.5, len(runs)-.5)
        ax.grid(axis='y', color='#DCE1E6', linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_xlabel('Independent runs, ordered by actual start', labelpad=10)
        ax.legend(loc='upper center', ncol=2, bbox_to_anchor=(.5, -.27), frameon=False)
    axes[0].set_ylabel('Ordinary complete FFN latency (ms)')
    axes[0].set_title('On-chip SwiGLU: candidate latency', weight='bold', pad=12)
    axes[1].set_ylabel('Speedup vs matched GPU-only control (×)')
    axes[1].set_title('Each point retains its own GPU baseline', weight='bold', pad=12)
    axes[1].axhline(1, color='#666666', linestyle=':', linewidth=1)
    m, h, intermediate = shape
    fig.suptitle(f'Independent SwiGLU partition repeats · M={m}, H={h}, I={intermediate}',
                 fontsize=14, weight='bold', y=1.06)
    fig.text(.5, 1.005, f'GPU: {device}  |  NPU power snapshots: default',
             ha='center', va='top', fontsize=9, color='#555555')
    fig.text(.01, .005, 'Bars: sample p10–p90, not confidence intervals. Runs remain independent; no pooled winner or global optimum is inferred.\n'
             'Speedup points use matched median ratios; bars use paired sample ratios. The confirmation reverses partition order.', fontsize=8)
    fig.tight_layout()
    stem = f'repeat_candidates_m{m}_h{h}_i{intermediate}'
    combined['figures'] = []
    for extension in ('svg', 'png', 'pdf'):
        path = output / (stem+'.'+extension)
        fig.savefig(path, dpi=220, facecolor='white', bbox_inches='tight')
        combined['figures'].append(str(path.relative_to(ROOT) if path.is_absolute() else path))
    plt.close(fig)
    (output/'combined_verification.json').write_text(json.dumps(combined, indent=2, allow_nan=False)+'\n')
    with (output/'repeat_comparison.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['series', 'npu_channels', 'count', 'median_ms', 'p10_ms',
                                                    'p90_ms', 'gpu_baseline_median_ms', 'speedup', 'report'])
        writer.writeheader()
        for run in runs:
            for row in run['candidates']:
                stats = row['concurrent_ms']
                writer.writerow({'series': run['series'], 'npu_channels': row['npu_channels'], 'count': stats['count'],
                                 **{key+'_ms': stats[key] for key in ('median', 'p10', 'p90')},
                                 'gpu_baseline_median_ms': row['gpu_baseline_ms']['median'],
                                 'speedup': row['speedup'], 'report': row['report']})
    print(json.dumps({'status': combined['status'], 'sweep_counts': combined['sweep_counts'],
                      'total_npu_dispatches_including_exact': combined['total_npu_dispatches_including_exact'],
                      'figures': combined['figures']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--channels', type=int, nargs='+', default=[896, 1024, 1152, 1280])
    args = parser.parse_args()
    if len(args.channels) < 2 or len(set(args.channels)) != len(args.channels) or min(args.channels) <= 0:
        parser.error('--channels requires at least two distinct positive values')
    compare(args.directories, args.output, args.channels)
