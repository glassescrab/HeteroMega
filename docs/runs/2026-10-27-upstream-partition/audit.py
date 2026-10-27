#!/usr/bin/env python3
"""Independently audit exported direct-weight GPU/NPU partition evidence.

Usage: python audit.py --evidence-root EXTRACTED_TREE --output audit.json
This checks saved records and bytes; it does not execute GPU/NPU work. Raw
outputs are absent, so numerical error magnitudes cannot be recomputed from
arrays. Their tolerance decisions, policy, hash repeatability, counters and
all timing statistics are independently recomputed here.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import tarfile

import numpy as np


SUCCESS = ('passed', 'completed_with_accuracy_deviations')
TOLERANCES = dict(rtol=0.03, atol=0.05, l2_limit=0.02)
SOURCE_MARKERS = ('experiments/ffn_partition/', 'npu/ffn/', 'src/', 'include/')
SOURCE_EXTENSIONS = {'.py', '.cc', '.cpp', '.cu', '.h', '.hpp'}


def load(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def source_name(name):
    name = str(name).replace('\\', '/')
    for marker in SOURCE_MARKERS:
        if marker in name:
            return name[name.index(marker):]
    return None


def close(actual, expected):
    assert math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-8), (actual, expected)


def valid_hash(value):
    assert isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), value


def audit_metrics(value, policy):
    """Re-evaluate unchanged error thresholds and structural acceptance."""
    assert value['accuracy_policy'] == policy
    for key, expected in TOLERANCES.items():
        assert value[key] == expected, (key, value[key], expected)
    finite = value['finite']
    if finite:
        maximum, reference_max = value['max_abs_error'], value['reference_max_abs']
        assert math.isfinite(maximum) and maximum >= 0
        assert math.isfinite(reference_max) and reference_max >= 0
        close(value['max_error_limit'], .05 + .03 * reference_max)
        assert math.isfinite(value['rms_error']) and value['rms_error'] >= 0
        assert 0 <= value['elementwise_close_fraction'] <= 1
        if reference_max == 0:
            passed = maximum == 0
            assert value['relative_l2_error'] == (0. if maximum == 0 else None)
            assert value['normalized_max_error'] == (0. if maximum == 0 else None)
        else:
            assert math.isfinite(value['relative_l2_error']) and value['relative_l2_error'] >= 0
            close(value['normalized_max_error'], maximum / reference_max)
            passed = value['relative_l2_error'] <= .02 and maximum <= .05 + .03 * reference_max
    else:
        passed = False
    assert value['passed'] == passed
    assert value['correctness'] == ('passed' if passed else 'failed')
    failures = value['structural_failures']
    accepted = not failures and (passed or policy == 'report')
    assert value['accepted'] == accepted
    status = ('structural_failure' if failures else 'within_tolerance' if passed else
              'reported_deviation' if accepted else 'outside_tolerance')
    assert value['accuracy_status'] == status
    # Every report admitted as successful must have genuinely successful
    # execution and zero/stale/repeat guards, even in numerical report mode.
    assert finite and not failures and accepted
    return passed


def summary_metrics(values):
    values = list(values)
    passed, accepted = all(x['passed'] for x in values), all(x['accepted'] for x in values)
    return dict(passed=passed, accepted=accepted, check_count=len(values),
        outside_tolerance_count=sum(not x['passed'] for x in values),
        accuracy_status='failed' if not accepted else 'within_tolerance' if passed else 'reported_deviations')


def statistics(samples):
    values = np.asarray(samples, dtype=np.float64)
    assert values.ndim == 1 and values.size and np.all(np.isfinite(values)) and np.all(values > 0)
    return dict(count=int(values.size), median_us=float(np.median(values)),
        p10_us=float(np.percentile(values, 10)), p90_us=float(np.percentile(values, 90)),
        min_us=float(np.min(values)), max_us=float(np.max(values)))


def run(root):
    root = root.resolve()
    audit = dict(status='running', evidence_root=str(root), checksums={}, source_versions={},
        artifacts={}, gpu_builds={}, reports={}, retained_nonbenchmark_reports=[], retained_failed_reports={},
        fixture_groups={}, totals={}, limitations=[
            'No hardware work is repeated by this audit.',
            'Raw output arrays are not exported; error magnitudes are retained, while tolerance/policy decisions are recalculated.',
            'Combined-output and timed-GPU hashes are checked independently; partial GPU/NPU repeat/zero evidence consists of recorded structural checks without partial hashes.',
            'Initial input hashes can be compared across reports; the driver does not export final input hashes.',
            'GPU extension files are archive-hashed and source-fingerprint matched; the runtime report does not contain a loaded .so byte hash.',
            'Host launch/wait and overlapping staging intervals are not device phase measurements.',
            'This is synthetic complete-FFN evidence, not whole-model or attention-overlap inference.'])
    checksum_path = root / 'SHA256SUMS.json'
    checksum_table = load(checksum_path)
    assert isinstance(checksum_table, dict) and checksum_table
    actual_files = {str(p.relative_to(root)) for p in root.rglob('*')
                    if p.is_file() and p.name != 'SHA256SUMS.json'}
    assert set(checksum_table) == actual_files, ('checksum coverage', set(checksum_table) ^ actual_files)
    for name, expected in checksum_table.items():
        path = (root / name).resolve()
        assert path.is_relative_to(root) and path.is_file()
        assert digest(path) == expected, ('checksum mismatch', name)
    audit['checksums'] = dict(manifest_sha256=digest(checksum_path), verified_files=len(checksum_table),
                              complete_file_coverage=True)

    source_index = defaultdict(list)
    for path in root.rglob('*'):
        name = source_name(path)
        if path.is_file() and name and path.suffix in SOURCE_EXTENSIONS:
            source_index[(name, digest(path))].append(str(path.relative_to(root)))
    for archive in root.rglob('*.tar.gz'):
        with tarfile.open(archive) as bundle:
            for member in bundle.getmembers():
                name = source_name(member.name)
                if member.isfile() and name and Path(name).suffix in SOURCE_EXTENSIONS:
                    value = sha256(bundle.extractfile(member).read()).hexdigest()
                    source_index[(name, value)].append(f'{archive.relative_to(root)}::{member.name}')

    def sources(hashes, bare=False):
        for name, value in hashes.items():
            if bare and '/' not in name:
                name = 'npu/ffn/' + name
            assert (name, value) in source_index, ('unresolved source version', name, value)
            audit['source_versions'][name + '@' + value] = source_index[(name, value)]

    artifact_index = defaultdict(list)
    for path in sorted(root.rglob('*.xclbin.json')):
        manifest = load(path)
        binary, instructions = Path(str(path)[:-5]), path.parent / 'insts.bin'
        assert digest(binary) == manifest['xclbin_sha256']
        assert digest(instructions) == manifest['insts_sha256']
        assert manifest['cols'] == 8 and manifest['worker_count'] == 32
        assert manifest['weight_tile_bytes'] == 4352
        assert manifest['weight_layout'] == 'glassescrab_w4a16_k128_n64_colmod8_4352_v1'
        assert manifest['arithmetic'] == manifest['compute_format']
        assert manifest['arithmetic'] in ('bf16', 'bfp16')
        assert manifest['worker_stack_size'] == (4096 if manifest['arithmetic'] == 'bfp16' else 2048)
        sources(manifest['dependency_sha256'], bare=True)
        for key, filename in (('source_sha256', 'w4a16_prefill_upstream.cc'),
                              ('graph_sha256', 'w4a16_upstream.py'),
                              ('weight_layout_sha256', 'upstream_weights.py'),
                              ('schedule_sha256', 'upstream_schedule.py')):
            assert manifest[key] == manifest['dependency_sha256'][filename]
        contract = load(path.parent / 'build_contract.json')
        assert contract['source_sha256'] == manifest['dependency_sha256']
        assert all(manifest[k] == v for k, v in contract['expected_manifest'].items())
        assert contract['target_mlir_aie_commit'] == manifest['target_mlir_aie_commit']
        identity = (manifest['xclbin_sha256'], manifest['insts_sha256'])
        artifact_index[identity].append((manifest, contract))
        audit['artifacts'][str(path.parent.relative_to(root))] = dict(xclbin_sha256=identity[0],
            instructions_sha256=identity[1], shape={k: manifest[k] for k in ('m', 'k', 'n', 'weight_k', 'weight_n')},
            mode=manifest['mode'], arithmetic=manifest['arithmetic'], source_and_contract_verified=True)

    def artifact(value):
        manifest, contract = value['manifest'], value['build_contract']
        identity = (manifest['xclbin_sha256'], manifest['insts_sha256'])
        assert any(manifest == m and contract == c for m, c in artifact_index[identity]), ('unresolved report artifact', identity)
        return manifest

    def gpu_build(metadata):
        sources(metadata['source_sha256'])
        keys = ('source_sha256', 'torch_version', 'hip_version', 'gpu_arch',
                'rocm_path', 'pytorch_rocm_arch', 'packed_layout')
        fingerprint = sha256(json.dumps({k: metadata[k] for k in keys}, sort_keys=True).encode()).hexdigest()
        assert metadata['build_fingerprint'] == fingerprint
        directory = root / 'gpu_build' / fingerprint[:20]
        files = list(directory.glob('heteromega_ffn_gpu_' + fingerprint[:16] + '*.so'))
        assert len(files) == 1, ('GPU extension missing or ambiguous', directory)
        assert (directory / 'build.ninja').is_file()
        audit['gpu_builds'][fingerprint] = dict(extension=str(files[0].relative_to(root)),
            extension_sha256=digest(files[0]), build_ninja_sha256=digest(directory / 'build.ninja'),
            source_fingerprint_verified=True)

    fixture_groups, baseline_hashes, partition_hashes = {}, {}, {}
    totals = Counter()
    all_metrics = []
    for path in sorted((root / 'results').glob('*.json')):
        data = load(path)
        if not isinstance(data, dict) or 'partitions' not in data or 'provenance' not in data or 'config' not in data:
            audit['retained_nonbenchmark_reports'].append(path.name)
            continue
        sources(data['provenance']['source_sha256'])
        if data['status'] not in SUCCESS:
            audit['retained_failed_reports'][path.name] = dict(status=data['status'], error=data.get('error'),
                partitions=len(data['partitions']), completions=sum(sum(p.get('completed_npu_dispatches_by_stage', {}).values())
                    for p in data['partitions']))
            continue
        cfg = data['config']
        m, h, inter, seed = (cfg[k] for k in ('m', 'hidden', 'intermediate', 'seed'))
        fixture_key = (m, h, inter, seed)
        arithmetic, policy = cfg['npu_arithmetic'], cfg['accuracy_policy']
        assert arithmetic in ('bf16', 'bfp16') and policy in ('strict', 'report')
        if arithmetic == 'bf16':
            assert policy == 'strict', 'native BF16 control must remain strict'
        assert data['copy_output_bits'] is False
        assert data['npu_options'] == dict(arithmetic=arithmetic, segment_pipeline_depth=2,
            swiglu_reuse=2, down_reuse=4, swiglu_activation_fifo_depth=2,
            down_activation_fifo_depth=1, vector_zero=True, mmul_m_reuse=1,
            output_layout='down_a', swiglu_input_layout='row_major')
        originals = data['original_weight_buffers']
        assert originals == data['original_weight_buffers_after'] and data['original_weight_buffers_unchanged']
        assert set(originals) == {'gate', 'up', 'down'}
        for stage, expected_shape in (('gate', (h, inter)), ('up', (h, inter)), ('down', (inter, h))):
            value = originals[stage]
            assert (value['k'], value['n']) == expected_shape and value['readonly']
            assert value['bytes'] == (value['k'] // 128) * (value['n'] // 64) * 4352
            valid_hash(value['sha256'])
            assert data['gpu_baseline_packed_weight_sha256'][stage] == value['sha256']
        assert len(data['input_sha256']) == 3
        for value in data['input_sha256']:
            valid_hash(value)
        zero_hash = sha256(np.zeros((m, h), dtype=np.float32).tobytes()).hexdigest()
        assert data['input_sha256'][2] == zero_hash
        assert data['input_sha256'][0] != data['input_sha256'][1]
        fixture = dict(weights=originals, input_sha256=data['input_sha256'])
        if fixture_key in fixture_groups:
            assert fixture_groups[fixture_key]['fixture'] == fixture, ('changed fullshape fixtures', path.name)
        else:
            fixture_groups[fixture_key] = dict(fixture=fixture, reports=[])
        fixture_groups[fixture_key]['reports'].append(path.name)
        gpu_build(data['gpu_baseline'])
        assert data['gpu_baseline']['backend'] == 'heteromosaic_original_gpu_packed'
        for value in data['correctness'].values():
            audit_metrics(value, 'strict')
        all_metrics.extend(data['correctness'].values())
        assert len(data['correctness']) == 4
        result = dict(status=data['status'], shape=dict(m=m, hidden=h, intermediate=inter),
            seed=seed, arithmetic=arithmetic, accuracy_policy=policy, partitions=[], report_sha256=digest(path))

        assert [p['npu_channels'] for p in data['partitions']] == list(dict.fromkeys(int(x) for x in cfg['npu_channels'].split(',')))
        for part in data['partitions']:
            p = part['npu_channels']
            assert part['status'] in SUCCESS and part['gpu_channels'] == inter - p
            assert 0 < p < inter and p % 128 == 0 and part['npu_channel_start'] == 0
            close(part['npu_fraction'], p / inter)
            assert part['accuracy_policy'] == policy
            assert part['original_weight_buffers_unchanged'] and part['weight_buffers_after'] == originals
            gpu_build(part['gpu'])
            assert part['gpu']['source_sha256'] == data['gpu_baseline']['source_sha256']
            assert part['gpu']['backend'] == 'heteromosaic_original_gpu_packed'
            assert part['gpu']['channels'] == inter - p
            npu = part['npu']
            assert npu['arithmetic'] == npu['npu_arithmetic'] == npu['compute_format'] == arithmetic
            assert npu['weight_repacking'] is False and npu['full_weight_buffers']
            assert npu['full_intermediate'] == inter and npu['channel_start'] == 0 and npu['channels'] == p
            assert npu['fixed_weight_bytes'] == sum(x['bytes'] for x in originals.values())
            assert npu['fixed_weight_uploads'] == 3 and npu['launches_per_run'] == 2
            assert npu['worker_count'] == 32 and npu['columns_requested'] == 8
            assert npu['host_output_readback'] == 'borrowed_until_consumed'
            for stage in ('swiglu', 'down'):
                saved = artifact(data['artifacts'][str(p)][stage])
                assert saved == artifact(npu['artifacts'][stage])
                swiglu = stage == 'swiglu'
                expected = dict(m=m, k=h if swiglu else p, n=p if swiglu else h,
                    weight_k=h if swiglu else inter, weight_n=inter if swiglu else h,
                    k_start=0, n_start=0, arithmetic=arithmetic, segment_pipeline_depth=2,
                    vector_zero=True, mmul_m_reuse=1,
                    activation_fifo_depth=2 if swiglu else 1,
                    input_layout='row_major' if swiglu else 'compact',
                    output_layout='down_a' if swiglu else 'compact')
                assert all(saved[k] == v for k, v in expected.items()), ('artifact shape/options', stage, p)
                # Effective M reuse may shrink for the smoke's smaller M.
                assert saved['m_reuse'] in ((1, 2) if swiglu else (1, 2, 4))
            validations, warmups, samples = (part[k] for k in ('validation_runs', 'warmup_samples', 'samples'))
            assert [(r['run'], r['input_index'], r['mode']) for r in validations] == [
                (run, idx, mode) for run, idx in enumerate((0, 1, 2, 0)) for mode in ('serial', 'concurrent')]
            assert len(warmups) == 3 * cfg['warmup'] and len(samples) == 3 * cfg['iterations']
            all_timed = warmups + samples
            for iteration in range(-cfg['warmup'], cfg['iterations']):
                records = [r for r in all_timed if r['iteration'] == iteration]
                assert len(records) == 3 and {r['mode'] for r in records} == {'baseline', 'serial', 'concurrent'}
                assert [r['order_index'] for r in records] == [0, 1, 2]
                assert all(r['input_index'] == iteration % 2 for r in records)
            assert len(part['correctness']) == 32 + 9 * (cfg['warmup'] + cfg['iterations'])
            for name, metric in part['correctness'].items():
                expected_policy = 'strict' if name.endswith('_gpu_partial') or name.endswith('_baseline') and '_gpu_baseline' not in name else policy
                audit_metrics(metric, expected_policy)
            candidate_count = 0
            metric_count = 0
            for rec in validations + all_timed:
                mode, idx = rec['mode'], rec['input_index']
                assert math.isfinite(rec['wall_us']) and rec['wall_us'] > 0
                valid_hash(rec['output_sha256'])
                key = (fixture_key, idx) if mode == 'baseline' else (fixture_key, arithmetic, p, idx)
                index = baseline_hashes if mode == 'baseline' else partition_hashes
                if key in index:
                    assert index[key] == rec['output_sha256'], ('repeat/mode/hash disagreement', path.name, key)
                else:
                    index[key] = rec['output_sha256']
                if idx == 2:
                    assert rec['output_sha256'] == zero_hash
                label = (f"validation_{rec['run']}_{mode}" if 'run' in rec else f"iteration_{rec['iteration']}_{mode}")
                if mode == 'baseline':
                    assert rec['accuracy']['output'] == part['correctness'][label]
                    assert set(rec['accuracy']) == {'output'}
                    audit_metrics(rec['accuracy']['output'], 'strict')
                    assert not rec['diagnostics']
                else:
                    candidate_count += 1
                    assert set(rec['accuracy']) == {'output', 'baseline', 'gpu', 'npu'}
                    for kind, metric in rec['accuracy'].items():
                        suffix = {'output': '_partition_reference', 'baseline': '_gpu_baseline', 'gpu': '_gpu_partial', 'npu': '_npu_partial'}[kind]
                        assert metric == part['correctness'][label + suffix]
                        audit_metrics(metric, 'strict' if kind == 'gpu' else policy)
                    diag = rec['diagnostics']
                    inner = diag['npu']
                    assert inner['completed_dispatches_total'] == 2 * candidate_count
                    assert inner['weight_upload_counts'] == dict(gate=1, up=1, down=1)
                    for elapsed in [diag['input_gpu_to_host_us'], diag['output_stage_and_boundary_wait_us'],
                                    inner['branch_host_wall_us'], *inner['stages'].values(), *inner['dispatch_wait_us'].values()]:
                        assert math.isfinite(elapsed) and elapsed >= 0
                    assert inner['branch_host_wall_us'] <= rec['wall_us']
                metric_count += len(rec['accuracy'])
            for idx in (0, 1):
                assert (fixture_key, arithmetic, p, idx) in partition_hashes
            assert partition_hashes[(fixture_key, arithmetic, p, 0)] != partition_hashes[(fixture_key, arithmetic, p, 1)]
            # Baseline may have one measured input with iterations=1/warmup=0;
            # only assert changed-input hash when both are actually recorded.
            if all((fixture_key, idx) in baseline_hashes for idx in (0, 1)):
                assert baseline_hashes[(fixture_key, 0)] != baseline_hashes[(fixture_key, 1)]
            expected_calls = 8 + 2 * (cfg['warmup'] + cfg['iterations'])
            assert candidate_count == expected_calls == part['completed_candidate_calls'] == part['expected_npu_dispatches_per_stage']
            assert part['completed_npu_dispatches_by_stage'] == dict(swiglu=expected_calls, down=expected_calls)
            assert part['input_write_counts_by_stage'] == dict(swiglu=[expected_calls, 1, 1], down=[expected_calls, 1])
            assert part['fixed_weight_upload_counts'] == dict(gate=1, up=1, down=1)
            all_metrics.extend(part['correctness'].values())
            expected_accuracy = summary_metrics(part['correctness'].values())
            assert part['accuracy'] == expected_accuracy and metric_count == len(part['correctness'])
            assert part['status'] == ('passed' if expected_accuracy['passed'] else 'completed_with_accuracy_deviations')
            stats = {}
            for mode in ('baseline', 'serial', 'concurrent'):
                stats[mode] = statistics([r['wall_us'] for r in samples if r['mode'] == mode])
                for key, value in stats[mode].items():
                    close(part['stats'][mode][key], value)
            gpu_ratio = stats['baseline']['median_us'] / stats['concurrent']['median_us']
            serial_ratio = stats['serial']['median_us'] / stats['concurrent']['median_us']
            for mode, ratio in (('gpu_baseline', gpu_ratio), ('serial_partition', serial_ratio)):
                close(part['latency_ratio_vs_' + mode], ratio)
                if expected_accuracy['passed']:
                    close(part['speedup_vs_' + mode], ratio)
                else:
                    assert part['speedup_vs_' + mode] is None
            worst = {label: max(v['relative_l2_error'] or 0 for r in validations + all_timed if r['mode'] != 'baseline'
                               for key, v in r['accuracy'].items() if key == label)
                     for label in ('output', 'baseline', 'gpu', 'npu')}
            result['partitions'].append(dict(npu_channels=p, status=part['status'], stats=stats,
                accuracy=expected_accuracy, max_relative_l2=worst, completed_npu_dispatches=2 * expected_calls,
                latency_ratio_vs_gpu_baseline=gpu_ratio, latency_ratio_vs_serial_partition=serial_ratio,
                reduction_vs_gpu_percent=100 * (1 - 1 / gpu_ratio), zero_repeat_changed_and_mode_hashes_verified=True))
            totals['partitions'] += 1
            totals['npu_completions'] += 2 * expected_calls
            totals['timed_invocations'] += len(samples)
            totals['candidate_validation_calls'] += len(validations)
            totals['warmup_invocations'] += len(warmups)
            totals['original_tolerance_checks'] += metric_count
        expected_top = summary_metrics([*data['correctness'].values(),
            *(v for p in data['partitions'] for v in p['correctness'].values())])
        assert data['accuracy'] == expected_top
        assert data['status'] == ('passed' if expected_top['passed'] else 'completed_with_accuracy_deviations')
        audit['reports'][path.name] = result
        totals['successful_reports'] += 1
        totals['original_tolerance_checks'] += len(data['correctness'])
    assert audit['reports'], 'no completed partition reports found'
    audit['fixture_groups'] = {'/'.join(map(str, key)): value for key, value in fixture_groups.items()}
    audit['totals'] = dict(totals)
    audit['numerical_summary'] = dict(check_count=len(all_metrics),
        original_tolerance_failures=sum(not x['passed'] for x in all_metrics),
        structural_failure_count=sum(len(x['structural_failures']) for x in all_metrics),
        max_relative_l2=max(x['relative_l2_error'] or 0 for x in all_metrics),
        max_absolute_error=max(x['max_abs_error'] for x in all_metrics))
    audit['status'] = 'passed'
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archive', type=Path, help='Optional immutable outer tarball identity to retain in the audit.')
    args = parser.parse_args()
    output = run(args.evidence_root)
    if args.archive:
        output['outer_archive'] = dict(filename=args.archive.name, bytes=args.archive.stat().st_size, sha256=digest(args.archive))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(status=output['status'], totals=output['totals'],
                         verified_files=output['checksums']['verified_files']), indent=2))


if __name__ == '__main__':
    main()
