"""Recompute the October 22 BFP16 FFN audit and figures from raw hardware JSONs.

Run from the repository root with the isolated analysis Python. The default
inputs exclude failed invocation records and keep the small smoke out of plots.
Extra reports are accepted explicitly; separate runs are never pooled.
This script performs no hardware execution and does not rehash remote binaries.
Use --source-root for an explicitly restored historical source tree; source
contracts are still required to match every archived artifact. There is no
automatic fallback to another source tree.

Recreate the ignored raw directory first if needed:
  mkdir -p experiments/ffn_partition/results/bfp16_20261022/raw
  tar -xzf experiments/ffn_partition/results/bfp16_20261022/evidence.tar.gz \
      -C experiments/ffn_partition/results/bfp16_20261022/raw
"""

import argparse
from hashlib import sha256
import json
import importlib
from pathlib import Path
import re
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]

HERE = Path(__file__).resolve().parent
DEFAULT_REPORTS = ('bfp16_m512.json', 'bfp16_wider.json', 'bf16_control.json',
                   'bfp16_profile_p2048.json', 'bf16_profile_p2048.json', 'smoke.json',
                   'bfp16_refine.json', 'bfp16_confirm.json', 'bf16_confirm.json',
                   'bfp16_profile_p1792.json')


def load_source_helpers(source_root):
    """Import audit helpers only from the explicitly selected source tree."""
    global ROOT, _artifact_specs, _build_contract, collect, render, statistics
    global write_tables, validate_report_data
    ROOT = source_root.resolve(strict=True)
    modules = ('npu_backend', 'plot_partition_sweep', 'sweep_partition')
    for name in modules:
        source = ROOT / 'experiments/ffn_partition' / f'{name}.py'
        if not source.is_file():
            raise FileNotFoundError(f'--source-root is missing {source}')
    sys.path.insert(0, str(ROOT))
    loaded = [importlib.import_module(f'experiments.ffn_partition.{name}')
              for name in modules]
    verify_helper_origins()
    backend, plots, sweep = loaded
    _artifact_specs, _build_contract = backend._artifact_specs, backend._build_contract
    collect, render, statistics, write_tables = (plots.collect, plots.render,
                                                plots.statistics, plots.write_tables)
    validate_report_data = sweep.validate_report_data


def verify_helper_origins():
    """Reject package/cache fallbacks outside --source-root, including lazy imports."""
    for name, module in tuple(sys.modules.items()):
        relative = None
        if name.startswith('experiments.ffn_partition.'):
            relative = Path(*name.split('.')).with_suffix('.py')
        elif (ROOT / 'npu/ffn' / f'{name}.py').is_file():
            relative = Path('npu/ffn') / f'{name}.py'
        if relative is not None:
            expected = (ROOT / relative).resolve()
            actual = Path(getattr(module, '__file__', '')).resolve()
            if actual != expected:
                raise ValueError(f'source helper {name} came from {actual}, expected {expected}')


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


def accuracy_extrema(value):
    checks = list(metrics_in(value))
    assert checks and all(check['passed'] and check.get('accepted', True)
                          and check['finite'] for _, check in checks)
    result = {'stored_metric_occurrences': len(checks), 'all_within_fixed_limits': True}
    for key in ('relative_l2_error', 'max_abs_error', 'normalized_max_error', 'rms_error'):
        eligible = [(path, check) for path, check in checks if check.get(key) is not None]
        path, check = max(eligible, key=lambda item: item[1][key])
        result[key] = {'value': check[key], 'location': path}
    return result


def source_audit(config, channels, metadata):
    specs = _artifact_specs(config['m'], config['hidden'], channels, HERE / 'not_loaded',
        columns=config['columns'], design=config['npu_design'],
        fuse_gate_up=config['fuse_gate_up'], fuse_swiglu=config['fuse_swiglu'],
        arithmetic=config.get('npu_arithmetic', 'bf16'))
    verified = {}
    assert set(metadata['artifacts']) == set(specs)
    for label, artifact in metadata['artifacts'].items():
        expected_contract = _build_contract(specs[label])
        assert artifact['build_contract'] == expected_contract, ('stale build contract', label)
        manifest = artifact['manifest']
        for key, expected in specs[label]['expected'].items():
            assert manifest.get(key) == expected, ('manifest', label, key)
        kernel = ('w4a16_prefill_bfp16.cc' if config.get('npu_arithmetic') == 'bfp16'
                  else 'w4a16_prefill_reuse.cc')
        assert manifest['source_sha256'] == sha256((ROOT / 'npu/ffn' / kernel).read_bytes()).hexdigest()
        assert manifest['target_mlir_aie_commit'] == expected_contract['target_mlir_aie_commit']
        verified[label] = {'source_sha256': expected_contract['source_sha256'],
                           'worker_stack_size': manifest['worker_stack_size'],
                           'xclbin_sha256_recorded': manifest['xclbin_sha256'],
                           'insts_sha256_recorded': manifest['insts_sha256']}
    return verified


def stats_ms(values):
    return statistics([value / 1000 for value in values])


def ordinary_stages(entry):
    samples = [sample for sample in entry['samples'] if sample['mode'] == 'concurrent']
    npu = [sample['diagnostics']['npu'] for sample in samples]
    result = {'npu_branch': stats_ms([sample['branch_host_wall_us'] for sample in npu])}
    result['cpu_layout_sum'] = stats_ms([sum(value for key, value in sample['stages'].items()
                                            if key.endswith('_layout_us')) for sample in npu])
    for key in npu[0]['stages']:
        result[key.removesuffix('_us')] = stats_ms([sample['stages'][key] for sample in npu])
    for key in npu[0]['dispatch_wait_us']:
        result[key + '_dispatch_wait'] = stats_ms([sample['dispatch_wait_us'][key] for sample in npu])
    for key in ('input_gpu_to_host_us', 'output_stage_and_boundary_wait_us'):
        result[key.removesuffix('_us')] = stats_ms([sample['diagnostics'][key] for sample in samples])
    return result


def compact_figures(summary, audits, output):
    """Readable scientific overviews; every marker retains one independent run."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    descriptions = {
        'bfp16_m512': ('BFP16 initial · n=30', '#009E73', 'o', '-'),
        'bfp16_wider': ('BFP16 wider · n=30', '#56B4E9', 'v', '-'),
        'bfp16_refine': ('BFP16 refinement · n=40', '#E69F00', 's', '-'),
        'bfp16_confirm': ('BFP16 confirmation · n=50', '#0072B2', 'D', '-'),
        'bf16_control': ('BF16 control · n=30', '#CC79A7', '^', '--'),
        'bf16_confirm': ('BF16 confirmation · n=50', '#D55E00', 'P', '--'),
    }
    for row in summary['ordinary']:
        descriptions.setdefault(row['series'], (row['series'], '#555555', 'x', ':'))
    figure_paths = []

    def line(ax, rows, values, style):
        label, color, marker, linestyle = style
        ordered = sorted(zip(rows, values), key=lambda pair: pair[0]['npu_channels'])
        x = [row['npu_channels'] for row, _ in ordered]
        y = [value['median'] for _, value in ordered]
        bounds = [[value['median'] - value['p10'] for _, value in ordered],
                  [value['p90'] - value['median'] for _, value in ordered]]
        ax.errorbar(x, y, yerr=bounds, label=label, color=color, marker=marker,
                    linestyle=linestyle, linewidth=1.5, capsize=3, markersize=5)

    def clean(ax):
        ax.grid(axis='y', color='#DFE3E7', linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)

    def save(fig, stem):
        for extension in ('png', 'svg', 'pdf'):
            destination = output / f'{stem}.{extension}'
            fig.savefig(destination, dpi=180, bbox_inches='tight')
            figure_paths.append(str(destination))
        plt.close(fig)

    fig, (ax, confirmation) = plt.subplots(1, 2, figsize=(13, 5.6), width_ratios=(1.45, 1))
    for series, style in descriptions.items():
        rows = [row for row in summary['ordinary'] if row['series'] == series]
        line(ax, rows, [row['timing_ms']['concurrent'] for row in rows], style)
    ax.scatter([row['npu_channels'] for row in summary['ordinary']],
               [row['timing_ms']['baseline']['median'] for row in summary['ordinary']],
               marker='x', s=22, color='#777777', label='Matched GPU-only controls')
    ax.set(xlabel='NPU intermediate channels P', ylabel='Complete FFN latency (ms)',
           title='Partition sweep: independent runs remain separate')
    selected = [next(row for row in summary['ordinary'] if row['series'] == series
                     and row['npu_channels'] == channels)
                for series, channels in (('bfp16_confirm', 1792), ('bf16_confirm', 1152),
                                         ('bfp16_confirm', 1536), ('bfp16_confirm', 1792))]
    values = [row['timing_ms']['baseline' if i == 0 else 'concurrent']
              for i, row in enumerate(selected)]
    colors = ['#777777', '#D55E00', '#56B4E9', '#0072B2']
    confirmation.bar(range(4), [value['median'] for value in values], color=colors, width=.65)
    confirmation.errorbar(range(4), [value['median'] for value in values],
        yerr=[[value['median'] - value['p10'] for value in values],
              [value['p90'] - value['median'] for value in values]],
        fmt='none', color='#333333', capsize=4)
    for i, value in enumerate(values):
        confirmation.text(i, value['p90'] + .3, f"{value['median']:.3f}", ha='center')
    confirmation.set_xticks(range(4), ['GPU-only\nmatched control', 'BF16\nP1152',
                                       'BFP16\nP1536', 'BFP16\nP1792'])
    confirmation.set(ylabel='Complete FFN latency (ms)', title='Confirmation: 50 samples per mode', ylim=(0, 25))
    for axis in (ax, confirmation):
        clean(axis)
    fig.suptitle('BFP16 W4A16 FFN: best sampled partition P1792 (12.5% NPU)',
                 fontsize=14, weight='bold', y=1.01)
    fig.text(.5, .94, 'M512 / H4096 / I14336 · HX370 / Radeon 890M · NPU default in batch snapshots',
             ha='center', color='#555555')
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, -.07), ncol=3,
               frameon=False, fontsize=9)
    fig.text(.01, -.12, 'Bars: sample p10–p90, not confidence intervals. Timings include host staging and GPU reduction.\n'
             'Synthetic FFN with HeteroMosaic GPU kernels; these are not native heterogeneous or full-model timings.', fontsize=8)
    fig.subplots_adjust(top=.80, bottom=.18, wspace=.28)
    save(fig, 'comparison_overview')

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    for audit in audits:
        if audit['mode'] != 'ordinary' or audit['config']['m'] != 512:
            continue
        series = Path(audit['file']).stem
        parts = audit['partitions']
        for axis, key in zip(axes, ('swiglu_with_host_io', 'down_with_host_io', 'cpu_layout_sum')):
            line(axis, parts, [part['ordinary_concurrent_host_stages_ms'][key] for part in parts],
                 descriptions[series])
    for axis, title in zip(axes, ('Gate/up + SiLU × up', 'Down projection', 'CPU layout conversions')):
        axis.set(xlabel='NPU intermediate channels P', ylabel='Host interval (ms)', title=title)
        clean(axis)
    fig.suptitle('NPU stage scaling during ordinary concurrent FFN calls', weight='bold', fontsize=14)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, -.05), ncol=3,
               frameon=False, fontsize=9)
    fig.text(.01, -.10, 'Host stages include BO I/O, submission, device execution and waits; they are not pure compute or DMA.\n'
             'Layout times are summed per invocation before aggregation. Bars: sample p10–p90. Independent medians are not additive.', fontsize=8)
    fig.subplots_adjust(top=.83, bottom=.22, wspace=.3)
    save(fig, 'npu_stage_scaling')
    return figure_paths


def audit_report(path):
    report = json.loads(path.read_text())
    config = report['config']
    assert report['status'] == 'passed', path
    ordinary = 'partitions' in report
    entries = report['partitions'] if ordinary else [report]
    result = {'file': str(path.relative_to(HERE)), 'sha256': sha256(path.read_bytes()).hexdigest(),
              'status': report['status'], 'mode': 'ordinary' if ordinary else 'diagnostic',
              'config': config, 'partitions': [], 'accuracy': accuracy_extrema(report)}
    result['explicit_named_check_count'] = (len(report.get('correctness', {}))
        + len(report.get('checks', {}))
        + sum(len(entry['correctness']) for entry in report.get('partitions', [])))
    result['declared_check_count_including_warmups'] = (
        report.get('accuracy', {}).get('check_count', 0)
        + sum(entry['accuracy']['check_count'] for entry in report.get('partitions', [])))
    for entry in entries:
        channels = entry['npu_channels'] if ordinary else config['npu_channels']
        job = dict(mode=result['mode'], m=config['m'], npu_channels=channels,
                   iterations=config['iterations'], fuse_gate_up=config['fuse_gate_up'],
                   fuse_swiglu=config['fuse_swiglu'])
        view = dict(report, partitions=[entry]) if ordinary else report
        validation = validate_report_data(view, job, SimpleNamespace(**config))
        samples = entry['samples']
        assert all(sample['correctness_passed'] for sample in samples)
        metadata = entry['npu'] if ordinary else entry['npu_metadata']
        item = {'npu_channels': channels, 'validation': validation,
                'source_validation': source_audit(config, channels, metadata),
                'accuracy': accuracy_extrema(entry)}
        if ordinary:
            item['timing_ms'] = {mode: stats_ms([s['wall_us'] for s in samples if s['mode'] == mode])
                                 for mode in ('baseline', 'serial', 'concurrent')}
            item['ordinary_concurrent_host_stages_ms'] = ordinary_stages(entry)
            item['speedup_vs_own_gpu'] = (item['timing_ms']['baseline']['median'] /
                                        item['timing_ms']['concurrent']['median'])
        result['partitions'].append(item)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=HERE / 'raw/evidence/bfp16_20261022')
    parser.add_argument('--extra-report', action='append', default=[])
    parser.add_argument('--source-root', type=Path, default=ROOT,
                        help='Source tree whose helpers and kernel hashes must match archived artifacts')
    parser.add_argument('--output-dir', type=Path, default=HERE / 'plots')
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args()
    load_source_helpers(args.source_root)
    paths = [args.input_dir / name for name in (*DEFAULT_REPORTS, *args.extra_report)]
    audits = [audit_report(path) for path in paths]
    verify_helper_origins()
    summary = collect(paths, m_filter=512)
    assert not summary['ignored_inputs'], summary['ignored_inputs']
    power = {}
    for name in ('power_before.txt', 'power_after.txt', 'power_final.txt'):
        path = args.input_dir / name
        text = path.read_text()
        assert 'NPU Strix' in text
        power[name] = {'mode': re.search(r'Power Mode\s*:\s*(\w+)', text).group(1),
                       'sha256': sha256(path.read_bytes()).hexdigest()}
    assert {snapshot['mode'] for snapshot in power.values()} == {'default'}
    for row in summary['ordinary'] + summary['diagnostic']:
        # These snapshots surround the measured batches, including confirmation.
        # They do not establish continuously monitored power-state residency.
        if Path(row['report']).name in DEFAULT_REPORTS:
            row['power'] = {'mode': 'default (batch snapshots)', 'snapshots': power}
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    if not args.no_render:
        render(summary, output)
        summary.setdefault('figures', []).extend(compact_figures(summary, audits, output))
    write_tables(summary, output)
    diagnostic = [{key: row[key] for key in
                   ('report', 'npu_arithmetic', 'npu_channels', 'metrics_ms')}
                  for row in summary['diagnostic']]
    complete = {'source_root': str(ROOT), 'reports': audits, 'diagnostic_stages': diagnostic, 'power_snapshots': power,
        'archive_sha256': sha256((HERE / 'evidence.tar.gz').read_bytes()).hexdigest(),
        'all_reports_passed': True,
        'successful_npu_completions': sum(part['validation']['completed_npu_dispatches']
                                         for audit in audits for part in audit['partitions']),
        'timed_invocations': sum(part['validation']['timed_invocations']
                                for audit in audits for part in audit['partitions']),
        'explicit_named_check_count': sum(audit['explicit_named_check_count'] for audit in audits),
        'declared_check_count_including_warmups': sum(
            audit['declared_check_count_including_warmups'] for audit in audits),
        'accuracy': accuracy_extrema({path.name: json.loads(path.read_text()) for path in paths}),
        'limits': ['Synthetic isolated FFN, not full-model prefill or TTFT.',
                   'GPU-only HeteroMosaic kernels; native heterogeneous baseline is not measured here.',
                   'NPU waits include runtime/device execution and stalls, not pure DMA.',
                   'Stage diagnostics use separate instrumented runs; medians are not additive.',
                   'Source contracts matched the explicitly selected source tree; remote binary digests are recorded, not rehashed here.',
                   'Stored metric occurrence count includes repeated serialized diagnostics, not distinct invocations.']}
    (output / 'audit.json').write_text(json.dumps(complete, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: complete[key] for key in
        ('all_reports_passed', 'successful_npu_completions', 'timed_invocations', 'accuracy')}, indent=2))


if __name__ == '__main__':
    main()
