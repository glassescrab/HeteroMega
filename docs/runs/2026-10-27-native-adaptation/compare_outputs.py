#!/usr/bin/env python3
"""Compare recorded native8 full-FFN output hashes; never compare timings.

Partial GPU/NPU arrays were not archived: their error metrics are compared,
but this does not independently prove bitwise partial-array identity.
"""
import argparse
import hashlib
import json
from pathlib import Path


def audit(paths, channels):
    errors = []
    reports = []
    expected_fixture = None
    expected_gpu = None
    expected_outputs = {}
    expected_metrics = {}
    expected_baseline_source = None
    total_records = total_metrics = numeric_failures = 0
    for path in paths:
        data = json.loads(path.read_text())
        matches = [p for p in data['partitions'] if p['npu_channels'] == channels]
        if len(matches) != 1:
            errors.append(f'{path}: expected one P{channels} partition')
            continue
        part = matches[0]
        label = str(path)
        def check(condition, message):
            if not condition:
                errors.append(f'{label}: {message}')
        check(data.get('original_weight_buffers_unchanged') is True,
              'source weight buffers changed or integrity field missing')
        check(part.get('original_weight_buffers_unchanged') is True,
              'partition source weight buffers changed or integrity field missing')
        fixture = {
            'config': {k: data['config'][k] for k in
                       ('m', 'hidden', 'intermediate', 'seed', 'gpu_variant')},
            'inputs': data['input_sha256'],
            'weights': data['original_weight_buffers'],
            'baseline_weights': data['gpu_baseline_packed_weight_sha256'],
            'channels': channels, 'channel_start': part['npu_channel_start'],
        }
        gpu_keys = ('backend', 'source_sha256', 'build_fingerprint', 'activation',
                    'source_packed_sha256', 'prepared_packed_sha256', 'channels',
                    'source_channel_begin', 'source_channel_end', 'gemm_autotune')
        gpu = {k: part['gpu'][k] for k in gpu_keys}
        if expected_fixture is None:
            expected_fixture = fixture
            expected_gpu = gpu
            expected_baseline_source = data['gpu_baseline']['source_sha256']
        check(fixture == expected_fixture, 'fixtures/geometry differ from first report')
        check(gpu == expected_gpu, 'GPU source/config/packed buffers differ from first report')
        check(data['gpu_baseline']['source_sha256'] == expected_baseline_source,
              'GPU baseline sources differ from first report')
        for stage, count in part['completed_npu_dispatches_by_stage'].items():
            check(count == part['expected_npu_dispatches_per_stage'],
                  f'{stage}: completed count differs from expected')
            check(count == part['completed_candidate_calls'],
                  f'{stage}: completed count differs from candidate calls')
        current = {'path': label,
                   'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                   'measurement_mode': data.get('measurement_mode', 'ordinary'),
                   'ordinary_headline_eligible': data.get('ordinary_headline_eligible', True),
                   'gpu_binary_sha256': part['gpu'].get('binary_sha256'),
                   'status': part['status'],
                   'kernel_flags': {k: part['npu'].get(k, False) for k in
                                    ('bfp16_native_layout', 'split_m32_a', 'preconvert_b', 'preconvert_a')},
                   'completed_npu_dispatches_by_stage': part['completed_npu_dispatches_by_stage'],
                   'collections': {}, 'numerical_failed_metrics': 0}
        validation_inputs = set()
        for collection in ('validation_runs', 'warmup_samples', 'samples'):
            records = part[collection]
            current['collections'][collection] = len(records)
            for index, record in enumerate(records):
                total_records += 1
                kind = 'baseline' if record['mode'] == 'baseline' else 'candidate'
                key = (kind, record['input_index'])
                observed = record['output_sha256']
                check(len(observed) == 64, f'{collection}[{index}]: malformed output hash')
                if key not in expected_outputs:
                    expected_outputs[key] = observed
                    expected_metrics[key] = record['accuracy']
                check(observed == expected_outputs[key],
                      f'{collection}[{index}]: full output differs for {key}')
                check(record['accuracy'] == expected_metrics[key],
                      f'{collection}[{index}]: recorded partial/full error metrics differ for {key}')
                if collection == 'validation_runs':
                    validation_inputs.add(record['input_index'])
                for name, metric in record['accuracy'].items():
                    total_metrics += 1
                    check(metric['finite'] is True and metric['accepted'] is True,
                          f'{collection}[{index}]/{name}: nonfinite or not accepted')
                    check(metric.get('structural_failures') == [],
                          f'{collection}[{index}]/{name}: structural failure')
                    check((metric['rtol'], metric['atol'], metric['l2_limit']) == (.03, .05, .02),
                          f'{collection}[{index}]/{name}: original tolerances changed')
                    if kind == 'baseline' or name == 'gpu':
                        check(metric['accuracy_policy'] == 'strict' and metric['passed'] is True,
                              f'{collection}[{index}]/{name}: GPU strict control failed')
                    if not metric['passed']:
                        numeric_failures += 1
                        current['numerical_failed_metrics'] += 1
        check(validation_inputs == {0, 1, 2}, 'missing random/changed/zero validation input')
        reports.append(current)
    if expected_fixture:
        config = expected_fixture['config']
        zero = hashlib.sha256(bytes(config['m'] * config['hidden'] * 4)).hexdigest()
        if expected_outputs.get(('candidate', 2)) != zero:
            errors.append('zero-input output does not equal the all-zero FP32 output hash')
        if expected_outputs.get(('candidate', 0)) == expected_outputs.get(('candidate', 1)):
            errors.append('different random inputs produced identical outputs')
    return {'passed': not errors, 'errors': errors,
            'scope': 'Recorded full-FFN output hashes and error metrics only; no timing comparison.',
            'limitations': ['Partial GPU/NPU arrays are not archived; identical error metrics do not independently prove partial bitwise identity.',
                           'GPU binary hashes can differ across rebuilds; matching source closure, build fingerprint, fixture hashes and outputs are required here.',
                           'Diagnostic records are included only for output parity and cannot establish ordinary latency.'],
            'fixture': expected_fixture, 'gpu_contract': expected_gpu,
            'records_checked': total_records, 'metrics_checked': total_metrics,
            'numerical_failed_metrics_retained': numeric_failures,
            'output_hashes': {f'{k[0]}_input{k[1]}': v for k, v in expected_outputs.items()},
            'reports': reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', type=Path, nargs='+')
    parser.add_argument('--channels', type=int, default=3584)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.reports, args.channels)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('passed', 'errors', 'records_checked', 'metrics_checked', 'numerical_failed_metrics_retained')}, indent=2))
    raise SystemExit(0 if result['passed'] else 1)

if __name__ == '__main__':
    main()
