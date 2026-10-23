"""Reconstruct NPU implementation costs from the October 22 hardware evidence.

CPU-only: no hardware, compilation, downloads, or timing experiments are run.
Requires NumPy and (unless --no-render) Matplotlib. From the repository root:

  /tmp/heteromega-bfp16-analysis/bin/python \
    experiments/ffn_partition/results/bfp16_20261022/trace_implementation.py

If raw/ is absent, extract the adjacent evidence.tar.gz into raw/ first.
Use --source-root to select an explicitly restored historical source tree.
Every recorded source hash and full plan must still match; no fallback is used.
Outputs plots/trace_summary.json and plots/npu_cost_breakdown.png.

The additive chart uses MEANS of disjoint per-invocation host intervals.
NPU waits include execution, runtime, DMA and stalls; the recorded probes do
not separate those causes. Logical tap bytes are not measured DRAM traffic.
"""

import argparse
from hashlib import sha256
import json
import importlib
from pathlib import Path
import re
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

PROFILE_NAMES = ('bf16_profile_p2048.json', 'bfp16_profile_p2048.json',
                 'bfp16_profile_p1792.json')
CONFIRMATION_NAMES = ('bfp16_confirm.json', 'bf16_confirm.json')


def load_source_helpers(source_root):
    """Load historical schedule helpers without falling back to this checkout."""
    global ROOT, plan_prefill, plan_swiglu, swiglu_logical_column
    global swiglu_output_tap, swiglu_plan_metadata
    ROOT = source_root.resolve(strict=True)
    names = ('prefill_schedule', 'prefill_gate_up_schedule', 'prefill_swiglu_schedule')
    for name in names:
        source = ROOT / 'npu/ffn' / f'{name}.py'
        if not source.is_file():
            raise FileNotFoundError(f'--source-root is missing {source}')
    sys.path.insert(0, str(ROOT / 'npu/ffn'))
    modules = [importlib.import_module(name) for name in names]
    for name, module in zip(names, modules):
        expected = (ROOT / 'npu/ffn' / f'{name}.py').resolve()
        actual = Path(module.__file__).resolve()
        if actual != expected:
            raise ValueError(f'source helper {name} came from {actual}, expected {expected}')
    prefill, _, swiglu = modules
    plan_prefill = prefill.plan_prefill
    plan_swiglu, swiglu_logical_column = swiglu.plan_swiglu, swiglu.swiglu_logical_column
    swiglu_output_tap, swiglu_plan_metadata = swiglu.swiglu_output_tap, swiglu.swiglu_plan_metadata


def stats(values):
    values = np.asarray(values, dtype=np.float64)
    assert values.size and np.isfinite(values).all()
    return dict(count=len(values), mean=float(values.mean()),
                median=float(np.median(values)), min=float(values.min()),
                max=float(values.max()), p10=float(np.quantile(values, .1)),
                p90=float(np.quantile(values, .9)))


def stats_us(values):
    return stats(np.asarray(values) / 1000.0)


def read_report(path):
    report = json.loads(path.read_text())
    assert report['status'] == 'passed', path
    return report


def diagnostic_sample(sample):
    npu = sample['npu']
    stages = npu['stages']
    probes = sample['npu_submit_wait_host']
    outer = sample['host_intervals']['npu_branch_call']['duration_us']
    inner = npu['branch_host_wall_us']
    assert set(probes) == {'swiglu', 'down'}
    components = {
        'swiglu_wait': probes['swiglu']['wait_host_us'],
        'down_wait': probes['down']['wait_host_us'],
        'xrt_submit': sum(value['submit_host_us'] for value in probes.values()),
        'cpu_layout': sum(value for key, value in stages.items()
                          if key.endswith('_layout_us')),
        'bo_io_and_invoke_wrapper': sum(
            stages[key + '_with_host_io_us'] - value
            for key, value in npu['dispatch_wait_us'].items()),
        'dispatch_wrapper_gaps': sum(
            npu['dispatch_wait_us'][key] - value['submit_host_us'] - value['wait_host_us']
            for key, value in probes.items()),
        'inner_uninstrumented_gaps': inner - sum(stages.values()),
        'outside_inner_validation_and_bookkeeping': outer - inner,
    }
    assert min(components.values()) >= 0
    assert abs(sum(components.values()) - outer) < 1e-7
    gpu = sample['gpu_event_intervals']
    ready = gpu['output_h2d']['end_offset_us']
    branch_end = gpu['branch']['end_offset_us']
    # Both endpoints are GPU events relative to the same branch-start event.
    # No host-clock timestamp is used to calculate this readiness difference.
    clock = dict(gpu_branch_end=branch_end, npu_output_h2d_end=ready,
                 npu_output_ready_minus_gpu_end=ready - branch_end,
                 reduction_start=gpu['reduction']['start_offset_us'],
                 reduction_duration=gpu['reduction']['duration_us'],
                 reduction_start_after_last_dependency=(
                     gpu['reduction']['start_offset_us'] - max(ready, branch_end)),
                 input_d2h_duration=gpu['input_d2h']['duration_us'],
                 output_h2d_duration=gpu['output_h2d']['duration_us'])
    assert clock['reduction_start_after_last_dependency'] >= -1.0  # event resolution
    return dict(components_us=components, outer_npu_call_us=outer,
                instrumented_wall_us=sample['instrumented_wall_us'], gpu_clock_us=clock)


def diagnose(path):
    report = read_report(path)
    samples = [diagnostic_sample(sample) for sample in report['samples']]
    components = {key: stats_us([sample['components_us'][key] for sample in samples])
                  for key in samples[0]['components_us']}
    outer = stats_us([sample['outer_npu_call_us'] for sample in samples])
    assert abs(sum(value['mean'] for value in components.values()) - outer['mean']) < 1e-10
    clock = {key: stats_us([sample['gpu_clock_us'][key] for sample in samples])
             for key in samples[0]['gpu_clock_us']}
    return dict(file=path.name, sha256=sha256(path.read_bytes()).hexdigest(),
                arithmetic=report['config']['npu_arithmetic'],
                npu_channels=report['config']['npu_channels'],
                sample_count=len(samples), additive_components_ms=components,
                outer_npu_call_ms=outer, same_gpu_clock_ms=clock,
                npu_result_arrives_after_gpu_count=sum(
                    sample['gpu_clock_us']['npu_output_ready_minus_gpu_end'] > 0
                    for sample in samples),
                instrumented_wall_ms=stats_us([s['instrumented_wall_us'] for s in samples]),
                samples=samples)


def confirmation(path):
    report = read_report(path)
    result = []
    for partition in report['partitions']:
        modes = {}
        for mode in ('baseline', 'serial', 'concurrent'):
            samples = [sample for sample in partition['samples'] if sample['mode'] == mode]
            item = dict(wall_ms=stats_us([sample['wall_us'] for sample in samples]))
            if mode != 'baseline':
                item['npu_inner_host_ms'] = stats_us([
                    sample['diagnostics']['npu']['branch_host_wall_us'] for sample in samples])
                item['npu_stages_ms'] = {
                    key: stats_us([sample['diagnostics']['npu']['stages'][key] for sample in samples])
                    for key in samples[0]['diagnostics']['npu']['stages']}
                item['npu_dispatch_wait_ms'] = {
                    key: stats_us([sample['diagnostics']['npu']['dispatch_wait_us'][key]
                                   for sample in samples])
                    for key in samples[0]['diagnostics']['npu']['dispatch_wait_us']}
            modes[mode] = item
        result.append(dict(file=path.name, sha256=sha256(path.read_bytes()).hexdigest(),
            arithmetic=report['config']['npu_arithmetic'], npu_channels=partition['npu_channels'],
            modes=modes,
            concurrent_over_serial_npu_inner_mean=(
                modes['concurrent']['npu_inner_host_ms']['mean'] /
                modes['serial']['npu_inner_host_ms']['mean'])))
    return result


def schedule_cost(plan, fused):
    """Count graph fill/drain elements, not multiplied multicast receiver bytes."""
    activation_reads = weight_reads = output_writes = 0
    for group in range(plan.groups_per_column):
        for lane in range(plan.m_column_groups * plan.compute_rows):
            m_group, row = divmod(lane, plan.compute_rows)
            column = m_group * plan.n_columns
            activation_reads += 2 * plan.activation_tap(column, row, group).element_count
        for column in range(plan.columns):
            logical = swiglu_logical_column(column) if fused else column
            weight_reads += plan.weight_tap(logical).element_count
            if fused:
                if column % 2:
                    output_writes += 2 * swiglu_output_tap(plan, column, group).element_count
            else:
                output_writes += 2 * plan.output_tap(column, group).element_count
    accumulate_calls = plan.worker_count * plan.groups_per_column * plan.local_nb * plan.kb
    # One K128/N32 dequantization outside the REUSE loop in each kernel call.
    mmul_per_call = plan.m_reuse * (16 // 8) * (32 // 8) * (128 // 8)
    mmul_count = accumulate_calls * mmul_per_call
    logical_flops = 2 * plan.m * plan.k * plan.n
    assert mmul_count * (2 * 8 * 8 * 8) == logical_flops
    assert activation_reads == 2 * plan.m * plan.k * plan.local_nb
    assert weight_reads == plan.nb * plan.kb * 2144 * plan.groups_per_column * plan.m_column_groups
    assert output_writes == 2 * plan.m * plan.n // (2 if fused else 1)
    return dict(m=plan.m, k=plan.k, n=plan.n, m_reuse=plan.m_reuse,
        worker_count=plan.worker_count, sequential_m_groups=plan.groups_per_column,
        local_n_tiles=plan.local_nb, k128_groups=plan.kb,
        logical_shim_activation_read_bytes=activation_reads,
        logical_shim_weight_read_bytes=weight_reads,
        logical_shim_total_read_bytes=activation_reads + weight_reads,
        logical_shim_output_write_bytes=output_writes,
        unique_activation_bytes=2 * plan.m * plan.k,
        unique_weight_bytes=plan.nb * plan.kb * 2144,
        activation_replay_factor=plan.local_nb,
        weight_replay_factor=plan.groups_per_column * plan.m_column_groups,
        dequant_calls=accumulate_calls,
        dequantized_weight_values=accumulate_calls * 128 * 32,
        scalar_zero_metadata_conversions=accumulate_calls * 32,
        bfp16_mmul_8x8x8_mac_calls=mmul_count,
        projection_flops=logical_flops,
        local_dequant_scratch_write_bytes=accumulate_calls * 128 * 32 * 2,
        local_dequant_scratch_read_bytes=accumulate_calls * plan.m_reuse * 128 * 32 * 2,
        local_fp32_partial_read_plus_write_bytes=(
            accumulate_calls * plan.m_reuse * 16 * 32 * 4 * 2),
        local_traffic_note='Logical kernel loads/stores; excludes init/finish, metadata, spills and banks.')


def schedules():
    result = {}
    for channels in (1792, 2048):
        gate_up = schedule_cost(plan_swiglu(512, 4096, channels), fused=True)
        down = schedule_cost(plan_prefill(512, channels, 4096), fused=False)
        keys = ('logical_shim_activation_read_bytes', 'logical_shim_weight_read_bytes',
                'logical_shim_total_read_bytes', 'logical_shim_output_write_bytes',
                'dequant_calls', 'dequantized_weight_values', 'scalar_zero_metadata_conversions',
                'bfp16_mmul_8x8x8_mac_calls', 'projection_flops',
                'local_dequant_scratch_write_bytes', 'local_dequant_scratch_read_bytes',
                'local_fp32_partial_read_plus_write_bytes')
        result[str(channels)] = dict(swiglu=gate_up, down=down,
            totals={key: gate_up[key] + down[key] for key in keys},
            host_bo_io_payload_bytes=4 * 512 * 4096 + 4 * 512 * channels)
    return result


def verify_recorded_implementations(path, source_hashes):
    """Bind selected count helpers to archived graphs, kernels and full plans.

    Compare every recorded build-contract source, the manifest's selected
    arithmetic source and schedule hashes, and the complete recorded plan
    (including worker ownership and taps' geometric inputs). This checks
    source provenance, not the remote binary's machine code or device state.
    """
    report = read_report(path)
    config = report['config']
    arithmetic = config['npu_arithmetic']
    assert arithmetic in ('bf16', 'bfp16')
    kernel = 'npu/ffn/' + ('w4a16_prefill_bfp16.cc' if arithmetic == 'bfp16'
                          else 'w4a16_prefill_reuse.cc')
    stack_size = 4096 if arithmetic == 'bfp16' else 2048
    entries = report.get('partitions', [report])
    checks = []
    for entry in entries:
        channels = entry.get('npu_channels', config['npu_channels'])
        metadata = entry['npu'] if 'partitions' in report else entry['npu_metadata']
        assert set(metadata['artifacts']) == {'swiglu', 'down'}
        plans = {
            'swiglu': swiglu_plan_metadata(plan_swiglu(config['m'], config['hidden'], channels), stack_size),
            'down': plan_prefill(config['m'], channels, config['hidden']).to_dict(),
        }
        for label, artifact in metadata['artifacts'].items():
            contract, manifest = artifact['build_contract'], artifact['manifest']
            expected_plan = plans[label]
            assert contract['plan'] == expected_plan, (path.name, channels, label, 'build plan')
            assert artifact['plan'] == expected_plan, (path.name, channels, label, 'artifact plan')
            for source, recorded_hash in contract['source_sha256'].items():
                assert source_hashes[source] == recorded_hash, (path.name, label, source)
            expected_graph = ('npu/ffn/w4a16_swiglu.py' if label == 'swiglu'
                              else 'npu/ffn/w4a16_prefill_reuse.py')
            assert kernel in contract['source_sha256']
            assert expected_graph in contract['source_sha256']
            assert manifest['source_sha256'] == source_hashes[kernel]
            assert manifest['arithmetic'] == arithmetic
            assert manifest['worker_stack_size'] == stack_size
            assert manifest['target_mlir_aie_commit'] == contract['target_mlir_aie_commit']
            for key, value in contract['expected_manifest'].items():
                assert manifest[key] == value, (path.name, channels, label, key)
            manifest_sources = {
                'schedule_sha256': 'npu/ffn/prefill_schedule.py',
                'arithmetic_source_sha256': 'npu/ffn/projection_arithmetic.py',
            }
            if label == 'swiglu':
                manifest_sources.update({
                    'gate_up_schedule_sha256': 'npu/ffn/prefill_gate_up_schedule.py',
                    'swiglu_schedule_sha256': 'npu/ffn/prefill_swiglu_schedule.py',
                    'silu_source_sha256': 'npu/ffn/silu_mul.cc',
                })
            for key, source in manifest_sources.items():
                assert manifest[key] == source_hashes[source], (path.name, label, key)
            checks.append(dict(report=path.name, arithmetic=arithmetic, npu_channels=channels,
                stage=label, full_recorded_plan_matches=True,
                contract_source_files_checked=sorted(contract['source_sha256']),
                manifest_source_fields_checked=sorted(manifest_sources) + ['source_sha256'],
                geometry={key: expected_plan[key] for key in (
                    'm', 'k', 'n', 'columns', 'compute_rows', 'm_reuse',
                    'n_columns', 'm_column_groups', 'groups_per_column', 'worker_count',
                    'tile_m', 'tile_k', 'tile_n', 'local_n_tiles')}))
    return checks


def compiler_audit(directory, profile_path, source_hashes, schedule):
    """Read saved compiler disassembly and count direct conversion-helper calls.

    Symbols beginning with a dot or dollar are local labels, not function
    boundaries. Count direct ``jl`` targets only within dequantize, resolving
    the helper address from the same file. No compiler or binary is executed.
    """
    audit_path = directory / 'audit.json'
    audit = json.loads(audit_path.read_text())
    profile = read_report(profile_path)
    assert profile['config']['npu_channels'] == 1792
    assert profile['config']['npu_arithmetic'] == 'bfp16'
    records = audit['records']
    assert len(records) == 3 and {r['role'] for r in records} == {'gate', 'up', 'down'}
    swiglu_calls = schedule['swiglu']['dequant_calls']
    assert swiglu_calls % 2 == 0
    dequant_by_role = dict(gate=swiglu_calls // 2, up=swiglu_calls // 2,
                          down=schedule['down']['dequant_calls'])
    output = []
    for record in records:
        role = record['role']
        artifact = profile['npu_metadata']['artifacts']['down' if role == 'down' else 'swiglu']
        manifest = artifact['manifest']
        assert record['xclbin_sha256'] == manifest['xclbin_sha256']
        assert record['kernel_source_sha256'] == manifest['source_sha256']
        assert record['kernel_source_sha256'] == source_hashes['npu/ffn/w4a16_prefill_bfp16.cc']
        disasm_path = directory / f'{role}.disasm'
        disasm = disasm_path.read_text()
        symbols = list(re.finditer(r'^([0-9a-fA-F]+) <(.+)>:\s*$', disasm, re.MULTILINE))
        helpers = [symbol for symbol in symbols if symbol.group(2) == '__floatunsisf']
        dequants = [symbol for symbol in symbols if '::dequantize(' in symbol.group(2)]
        assert len(helpers) == len(dequants) == 1, (role, 'ambiguous function symbols')
        helper_address = int(helpers[0].group(1), 16)
        start = dequants[0]
        following = [symbol for symbol in symbols if symbol.start() > start.start()
                     and not symbol.group(2).startswith(('.', '$'))]
        assert following, (role, 'missing dequantize function end')
        end = following[0]
        body = disasm[start.end():end.start()]
        direct_calls = [match for match in re.finditer(r'\bjl\s+#0x([0-9a-fA-F]+)', body)
                        if int(match.group(1), 16) == helper_address]
        count = len(direct_calls)
        assert count == 32 == record['dequant_floatunsisf_calls'], (role, count)
        output.append(dict(role=role, representative_core=record['core'],
            disassembly_file=str(disasm_path.relative_to(HERE)),
            disassembly_sha256=sha256(disasm_path.read_bytes()).hexdigest(),
            recorded_elf_sha256=record['elf_sha256'],
            recorded_xclbin_sha256=record['xclbin_sha256'],
            recorded_kernel_source_sha256=record['kernel_source_sha256'],
            dequant_function=start.group(2),
            dequant_start_address=hex(int(start.group(1), 16)),
            next_nonlocal_symbol=end.group(2),
            dequant_end_exclusive_address=hex(int(end.group(1), 16)),
            floatunsisf_address=hex(helper_address),
            static_direct_floatunsisf_calls_in_dequant=count,
            scheduled_dequant_invocations=dequant_by_role[role],
            inferred_dynamic_helper_calls=dequant_by_role[role] * count))
    dynamic_calls = sum(record['inferred_dynamic_helper_calls'] for record in output)
    assert dynamic_calls == schedule['totals']['scalar_zero_metadata_conversions'] == 2752512
    return dict(audit_file=str(audit_path.relative_to(HERE)),
        audit_sha256=sha256(audit_path.read_bytes()).hexdigest(),
        profile_file=profile_path.name, records=output,
        inferred_dynamic_helper_calls_per_p1792_ffn=dynamic_calls,
        interpretation=[
            'Machine-code-confirmed: each of three representative core disassemblies has 32 direct __floatunsisf calls within dequantize.',
            'Dynamic count is inferred from the verified schedule, assuming the same role-specific helper path for every worker; it is not a hardware instruction counter.',
            'Saved audit xclbin/kernel hashes match the recorded P1792 manifests and selected source tree. ELF hashes are recorded provenance; this CPU analysis does not rehash remote binaries.',
            'No cycle cost or latency fraction is assigned to these helper calls; a controlled kernel change and rerun is required.'])


def render(profiles, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none'})
    fig, (cost, lag) = plt.subplots(1, 2, figsize=(13, 6.1), width_ratios=(1.55, 1))
    labels = [f"{p['arithmetic'].upper()}\nP{p['npu_channels']} · n={p['sample_count']}" for p in profiles]
    groups = (
        ('Gate/up + SiLU wait', ('swiglu_wait',), '#0072B2'),
        ('Down wait', ('down_wait',), '#56B4E9'),
        ('CPU layouts', ('cpu_layout',), '#E69F00'),
        ('BO I/O + invoke wrapper', ('bo_io_and_invoke_wrapper',), '#009E73'),
        ('XRT submission', ('xrt_submit',), '#CC79A7'),
        ('Outside inner timer + other gaps', ('outside_inner_validation_and_bookkeeping',
            'dispatch_wrapper_gaps', 'inner_uninstrumented_gaps'), '#777777'),
    )
    bottom = np.zeros(len(profiles))
    for label, keys, color in groups:
        values = np.asarray([sum(p['additive_components_ms'][key]['mean'] for key in keys)
                             for p in profiles])
        cost.bar(range(len(profiles)), values, bottom=bottom, color=color, width=.64, label=label)
        if keys in (('swiglu_wait',), ('down_wait',), ('cpu_layout',)):
            for i, value in enumerate(values):
                cost.text(i, bottom[i] + value / 2, f'{value:.2f}', ha='center', va='center',
                          color='white' if keys != ('cpu_layout',) else '#222222', fontsize=10)
        bottom += values
    for i, total in enumerate(bottom):
        assert abs(total - profiles[i]['outer_npu_call_ms']['mean']) < 1e-10
        cost.text(i, total + .35, f'{total:.3f} ms', ha='center', weight='bold')
    cost.set_xticks(range(len(profiles)), labels)
    cost.set(ylabel='Outer NPU host call (ms)', ylim=(0, 27),
             title='Disjoint host intervals: additive sample means')
    for i, profile in enumerate(profiles):
        values = [sample['gpu_clock_us']['npu_output_ready_minus_gpu_end'] / 1000
                  for sample in profile['samples']]
        offsets = np.linspace(-.11, .11, len(values))
        lag.scatter(np.full(len(values), i) + offsets, values, s=24, color='#0072B2', alpha=.65)
        median = np.median(values)
        lag.plot([i - .25, i + .25], [median, median], color='#222222', linewidth=2)
        lag.text(i, max(values) + .35, f'median +{median:.3f} ms', ha='center', fontsize=9)
    lag.axhline(0, color='#555555', linewidth=1, linestyle='--')
    lag.set_xticks(range(len(profiles)), labels)
    lag.set(ylabel='NPU result ready − GPU branch complete (ms)',
            title='Critical path: same GPU event clock', ylim=(-1.5, 8.8))
    for axis in (cost, lag):
        axis.grid(axis='y', linewidth=.6, alpha=.22)
        axis.set_axisbelow(True)
        axis.spines[['top', 'right']].set_visible(False)
    fig.suptitle('NPU FFN trace: execution waits and host staging dominate',
                 fontsize=15, weight='bold', y=.98)
    fig.text(.5, .925, 'M512 / H4096 / I14336 · HX370 · eight columns · NPU default power mode',
             ha='center', color='#555555')
    handles, legends = cost.get_legend_handles_labels()
    fig.legend(handles, legends, loc='lower center', bbox_to_anchor=(.5, .07),
               ncol=3, frameon=False, fontsize=9)
    fig.text(.03, .015,
        'Waits include runtime, compute, DMA and stalls; these probes do not separate them. '
        'BO residuals also include Python wrappers.\n'
        'Right: H2D-complete event minus GPU-branch-complete event; positive means the NPU path arrives later. '
        'Separate diagnostic runs, not ordinary latency.', fontsize=8)
    fig.subplots_adjust(top=.83, bottom=.26, wspace=.31)
    destination = output / 'npu_cost_breakdown.png'
    fig.savefig(destination, dpi=180, bbox_inches='tight')
    plt.close(fig)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=HERE / 'raw/evidence/bfp16_20261022')
    parser.add_argument('--output-dir', type=Path, default=HERE / 'plots')
    parser.add_argument('--source-root', type=Path, default=ROOT,
                        help='Source tree whose helpers and kernel hashes must match archived artifacts')
    parser.add_argument('--no-render', action='store_true')
    args = parser.parse_args()
    load_source_helpers(args.source_root)
    profiles = [diagnose(args.input_dir / name) for name in PROFILE_NAMES]
    ordinary = [item for name in CONFIRMATION_NAMES for item in confirmation(args.input_dir / name)]
    schedule = schedules()
    sources = ['npu/ffn/prefill_schedule.py', 'npu/ffn/prefill_gate_up_schedule.py',
               'npu/ffn/prefill_swiglu_schedule.py', 'npu/ffn/w4a16_swiglu.py',
               'npu/ffn/w4a16_prefill_reuse.py', 'npu/ffn/w4a16_prefill_bfp16.cc',
               'npu/ffn/w4a16_prefill_reuse.cc', 'npu/ffn/projection_arithmetic.py',
               'npu/ffn/silu_mul.cc',
               'experiments/ffn_partition/npu_backend.py',
               'experiments/ffn_partition/profile_timeline.py']
    source_hashes = {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in sources}
    provenance_checks = [check for name in (*PROFILE_NAMES, *CONFIRMATION_NAMES)
                         for check in verify_recorded_implementations(args.input_dir / name, source_hashes)]
    compiler = compiler_audit(HERE / 'compiler_trace', args.input_dir / 'bfp16_profile_p1792.json',
                              source_hashes, schedule['1792'])
    summary = dict(schema_version=1, source_root=str(ROOT), diagnostic_profiles=profiles, ordinary_confirmation=ordinary,
        logical_schedule_cost=schedule, source_sha256=source_hashes,
        recorded_implementation_verification=provenance_checks,
        compiler_disassembly_audit=compiler,
        archive_sha256=sha256((HERE / 'evidence.tar.gz').read_bytes()).hexdigest(),
        verified_disjoint_interval_sums=True,
        interpretation=[
            'Measured: disjoint NPU host intervals are checked per sample, then averaged for additive totals.',
            'Measured: readiness lag uses two GPU events on the same clock; CPU offsets are never overlaid.',
            'The outer-minus-inner interval contains finite-input validation before the inner timer and return bookkeeping; it is not a separately timed validation cost.',
            'BO/invoke residual subtracts the full dispatch/wait timer from the stage timer; it includes BO writes, syncs, reads, copies and Python wrapper work.',
            'Waits include device work, runtime, DMA and stalls. This is not a device-cycle trace or a compute/DMA decomposition.',
            'Code-derived logical shim bytes include tap replay but exclude multicast fanout; they are not measured DRAM transactions or bandwidth.',
            'Selected graph/kernel/schedule sources and complete generated plans are checked against archived build contracts and manifest hashes for every analyzed artifact; remote machine code is not rehashed.',
            'Kernel counts assume the verified REUSE=2 M16/K128/N32 kernel and are algorithmic counts, not compiler instruction counts.',
            'Ordinary serial/concurrent runs are separate from instrumented diagnostic runs; concurrency differences do not isolate shared-DRAM contention.',
            'The evidence is synthetic isolated FFN on HX370 with default NPU power mode, not full-model prefill.'])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    target = args.output_dir / 'trace_summary.json'
    target.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    figure = None if args.no_render else render(profiles, args.output_dir)
    print(json.dumps(dict(summary=str(target), figure=str(figure) if figure else None,
                         profiles=len(profiles), diagnostic_samples=sum(p['sample_count'] for p in profiles),
                         all_additive_sums_verified=True,
                         logical_p1792=schedule['1792']['totals']), indent=2))


if __name__ == '__main__':
    main()
