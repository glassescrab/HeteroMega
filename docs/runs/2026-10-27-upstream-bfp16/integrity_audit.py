#!/usr/bin/env python3
"""Read-only independent audit of saved direct-weight BF16/BFP16 evidence.

No hardware execution. Recomputes hashes, report accounting and statistics;
checks recorded output hashes, not absent raw numerical output arrays.
"""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import re
import shlex
from pathlib import Path
import sys
import numpy as np

EVIDENCE = Path('/tmp/upstream-bfp16-evidence-20261027')
REPO = Path('/home/adam/Documents/ChatGPT/HeteroMega')
PACKAGE = REPO.with_name('HeteroMega-kernels') / 'npu/ffn'
OUT = Path('/tmp/upstream_bfp16_integrity_audit.json')
failures = []
notes = []
hash_cache = {}

def check(value, label):
    if not value:
        failures.append(label)
    return bool(value)

def digest(path):
    path = Path(path)
    if path not in hash_cache:
        hash_cache[path] = sha256(path.read_bytes()).hexdigest()
    return hash_cache[path]

def read(path):
    return json.loads(Path(path).read_text())

def near(a, b):
    return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-10)

def stats(values):
    a = np.asarray(values, dtype=np.float64)
    return dict(count=len(a), median_us=float(np.median(a)), mean_us=float(np.mean(a)),
                min_us=float(a.min()), max_us=float(a.max()),
                p10_us=float(np.percentile(a, 10)), p90_us=float(np.percentile(a, 90)))

def check_stats(expected, recorded, label):
    check(set(expected) == set(recorded), label + ': stat keys')
    for key, value in expected.items():
        check(near(value, recorded[key]), label + ':' + key)

def all_true(values):
    return bool(values) and all(value is True for value in values.values())

def all_artifacts(obj):
    if isinstance(obj, dict):
        if {'manifest', 'build_contract', 'xclbin', 'insts'} <= set(obj):
            yield obj
        for value in obj.values():
            yield from all_artifacts(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from all_artifacts(value)

def failed_statuses(obj, path=''):
    if isinstance(obj, dict):
        if obj.get('status') == 'failed':
            yield path
        for key, value in obj.items():
            yield from failed_statuses(value, path + '/' + key)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from failed_statuses(value, path + '/' + str(index))

checksums = read(EVIDENCE / 'SHA256SUMS.json')
check(len(checksums) == 950, '950 expected payload checksum records')
for relative, expected in checksums.items():
    check(digest(EVIDENCE / relative) == expected, 'evidence hash:' + relative)
actual_files = {str(p.relative_to(EVIDENCE)) for p in EVIDENCE.rglob('*') if p.is_file()}
check(actual_files == set(checksums) | {'SHA256SUMS.json'}, 'checksum covers every evidence file')

source_matches, source_differences = [], []
for source in sorted((EVIDENCE / 'sources').rglob('*')):
    if not source.is_file():
        continue
    relative = source.relative_to(EVIDENCE / 'sources')
    local = REPO / relative
    if local.exists() and digest(source) == digest(local):
        source_matches.append(str(relative))
    else:
        source_differences.append(str(relative))
        check(relative.name.startswith('test_'), 'runtime source differs from snapshot:' + str(relative))

reports = {p.stem: read(p) for p in sorted((EVIDENCE / 'results').glob('*.json'))
           if 'completed_npu_dispatches' in read(p)}
check(set(reports) == {'arithmetic_abba', 'arithmetic_baab', 'bf16_model', 'bfp16_model',
                       'bfp16_offset', 'bfp16_smoke'}, 'six expected hardware reports')
for name, report in reports.items():
    check(report['status'] == 'passed' and 'error' not in report, name + ': final status')
    check(not list(failed_statuses(report)), name + ': no nested failure status')
    for relative, expected in report['source_sha256'].items():
        check(digest(EVIDENCE / 'sources' / relative) == expected, name + ': reported source:' + relative)
        check(digest(REPO / relative) == expected, name + ': local reported source:' + relative)

source_tree = ast.parse((EVIDENCE / 'sources/npu/ffn/w4a16_upstream.py').read_text())
deps = ast.literal_eval(next(n.value for n in source_tree.body if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'DEPENDENCIES' for t in n.targets)))
unique_artifacts = {}
for report in reports.values():
    for artifact in all_artifacts(report):
        key = artifact['xclbin']
        if key in unique_artifacts:
            check(unique_artifacts[key] == artifact, 'repeated artifact identity:' + key)
        unique_artifacts[key] = artifact
for key, artifact in unique_artifacts.items():
    manifest, contract = artifact['manifest'], artifact['build_contract']
    check(set(manifest['dependency_sha256']) == set(deps), key + ': dependency closure')
    for name, expected in manifest['dependency_sha256'].items():
        check(digest(EVIDENCE / 'sources/npu/ffn' / name) == expected, key + ': dependency:' + name)
    for name, expected in contract['expected_manifest'].items():
        check(manifest.get(name) == expected, key + ': build contract:' + name)
    check(contract['source_sha256'] == manifest['dependency_sha256'], key + ': contract dependency hashes')
    arithmetic = manifest['arithmetic']
    check(manifest['kind'] == 'w4a16_upstream_' + arithmetic, key + ': arithmetic kind')
    check(manifest['compute_format'] == arithmetic, key + ': compute format')
    check(manifest['worker_stack_size'] == (4096 if arithmetic == 'bfp16' else 2048), key + ': stack')
    check(manifest['cols'] == 8 and manifest['worker_count'] == 32 and
          manifest['weight_tile_bytes'] == 4352 and manifest['mmul_m_reuse'] == 1, key + ': fixed ABI/topology')

prebuilt = {}
for path in sorted((EVIDENCE / 'prebuilt').glob('*/*/final.xclbin.json')):
    manifest = read(path)
    arithmetic, stage = path.parent.parent.name, path.parent.name
    for filename, field in (('final.xclbin', 'xclbin_sha256'), ('insts.bin', 'insts_sha256')):
        check(digest(path.parent / filename) == manifest[field], f'{arithmetic}/{stage}: {filename} manifest hash')
    artifact = reports[arithmetic + '_model']['cases'][0]['artifacts'][stage]
    check(manifest == artifact['manifest'], f'{arithmetic}/{stage}: exact model manifest')
    check(read(path.parent / 'build_contract.json') == artifact['build_contract'], f'{arithmetic}/{stage}: exact contract')
    mlir = (path.parent / 'final.prj/aie.mlir').read_text()
    check(mlir.count(' = aie.core(') == 32, f'{arithmetic}/{stage}: 32 generated workers')
    check(mlir.count(f'stack_size = {manifest["worker_stack_size"]}') == 32, f'{arithmetic}/{stage}: 32 correct stacks')
    prebuilt[arithmetic + '/' + stage] = dict(xclbin_sha256=manifest['xclbin_sha256'],
        insts_sha256=manifest['insts_sha256'], mlir_sha256=digest(path.parent / 'final.prj/aie.mlir'))
check(len(prebuilt) == 4, 'four full-model prebuilt artifacts')
notes.append('Only the four full-model binaries are exported; smoke/offset artifact manifests and source identity are verified, but those binaries are not independently available in this snapshot.')

correctness = {}
for name, report in reports.items():
    if 'cases' not in report:
        continue
    total = 0
    metrics = []
    for index, case in enumerate(report['cases']):
        label = f'{name}/case{index}'
        check(all_true(case['checks']), label + ': all original and structural checks')
        check(case['numerical_status'] == case['structural_status'] == 'passed', label + ': separate verdicts')
        runs = case['runs']
        check([r['input'] for r in runs] == ['signed_a', 'signed_b', 'zero', 'repeat_a'], label + ': input sequence')
        check(runs[0]['output_sha256'] == runs[3]['output_sha256'], label + ': exact repeat')
        check(runs[0]['input_sha256'] == runs[3]['input_sha256'], label + ': repeat input')
        check(runs[0]['output_sha256'] != runs[1]['output_sha256'], label + ': changed input')
        launches = 2 if case['config']['mode'] == 'ffn' else 1
        for run in runs:
            check(run['status'] == 'completed' and run['completed_npu_dispatches'] == launches, label + ': completed run')
            check(run['errors']['correctness'] == 'passed' and run['errors']['finite'], label + ': original tolerance')
            metrics.append(run['errors'])
            total += run['completed_npu_dispatches']
        if launches == 2:
            check(case['runner_completed_dispatches'] == dict(swiglu=4, down=4), label + ': runner counters')
    check(total == report['completed_npu_dispatches'], name + ': independently summed dispatches')
    correctness[name] = dict(completed_dispatches=total, cases=len(report['cases']),
        max_relative_l2_error=max(x['relative_l2_error'] for x in metrics),
        max_abs_error=max(x['max_abs_error'] for x in metrics),
        all_original_tolerances_passed=True, arithmetic=report['arithmetic'], accuracy_policy=report['accuracy_policy'])

benchmarks = {}
control_hashes = {}
for name in ('arithmetic_abba', 'arithmetic_baab'):
    report = reports[name]
    cfg = report['config']
    refs = report['reference_blocks']
    controls = {b['arithmetic']: {r['input']: r['output_sha256'] for r in b['preflight']} for b in refs}
    control_hashes[name] = controls
    check([b['arithmetic'] for b in refs] == ['bf16', 'bfp16'], name + ': separate references')
    order = ['bf16' if letter == 'A' else 'bfp16' for letter in cfg['order']] * cfg['rounds']
    check([b['arithmetic'] for b in report['blocks']] == order, name + ': actual ABBA/BAAB order')
    count = 0
    for block in refs + report['blocks']:
        arithmetic = block['arithmetic']
        ref = bool(block.get('excluded_from_summary'))
        check(all_true(block['checks']) and all_true(block['preflight_checks']), name + ': block checks')
        check(block['child_process_returncode'] == 0, name + ': child completion')
        check(block['profile'] == {k:v for k,v in report['profile_definitions'][str(block['profile_index'])].items() if k != 'arithmetic'}, name + ': fixed profile')
        check(block['runner_metadata']['arithmetic'] == arithmetic and
              block['runner_metadata']['weight_repacking'] is False, name + ': runner arithmetic/weight ABI')
        check([r['input'] for r in block['preflight']] == ['signed_a','signed_b','zero','repeat_a'], name + ': preflight order')
        check(len(block['warmup']) == (0 if ref else cfg['warmup']), name + ': warmup length')
        check(len(block['runs']) == (0 if ref else cfg['iterations']), name + ': timed length')
        records = block['preflight'] + block['warmup'] + block['runs']
        check(block['completed_dispatches'] == dict(swiglu=len(records), down=len(records)), name + ': per-block counts')
        check(block['fixed_weight_upload_counts'] == dict(gate=1, up=1, down=1), name + ': weight uploads')
        count += 2 * len(records)
        for i, item in enumerate(records, 1):
            check(item['finite'] and item['output_sha256'] == controls[arithmetic][item['input']], name + ': exact same-arithmetic output')
            check(item['diagnostics']['completed_dispatches_total'] == 2*i, name + ': diagnostic dispatch sequence')
            if 'errors_vs_native_control' in item:
                check(item['identical_to_same_arithmetic_control'] is True and
                      item['errors_vs_native_control']['correctness'] == 'passed', name + ': recorded cross-format tolerance')
    check(count == report['completed_npu_dispatches'] == 16 + 8*cfg['rounds']*(4+cfg['warmup']+cfg['iterations']), name + ': dispatch sum/formula')
    timing = {}
    for index, arithmetic in (('1','bf16'),('2','bfp16')):
        runs = [r for b in report['blocks'] if b['arithmetic'] == arithmetic for r in b['runs']]
        recomputed = stats([r['wall_us'] for r in runs])
        check_stats(recomputed, report['summary'][index]['wall'], name + '/' + arithmetic + ': wall')
        for stage in ('swiglu', 'down'):
            check_stats(stats([r['diagnostics']['dispatch_wait_us'][stage] for r in runs]),
                        report['summary'][index]['dispatch_wait'][stage], name + '/' + arithmetic + ':' + stage)
        for stage in runs[0]['diagnostics']['stages']:
            check_stats(stats([r['diagnostics']['stages'][stage] for r in runs]),
                        report['summary'][index]['host_stages'][stage], name + '/' + arithmetic + ':' + stage)
        l2 = max(r['errors_vs_native_control']['relative_l2_error'] for r in runs)
        absolute = max(r['errors_vs_native_control']['max_abs_error'] for r in runs)
        check(near(l2, report['summary'][index]['max_relative_l2_vs_native']), name + ': max L2')
        check(near(absolute, report['summary'][index]['max_absolute_error_vs_native']), name + ': max abs')
        timing[arithmetic] = dict(**recomputed, max_relative_l2_vs_native=l2, max_abs_error_vs_native=absolute)
    native, bfp = timing['bf16']['median_us'], timing['bfp16']['median_us']
    speedup, reduction = native/bfp, 100*(native-bfp)/native
    check(near(speedup, report['summary']['candidate_over_baseline_speedup']), name + ': speedup')
    check(near(reduction, report['summary']['candidate_latency_reduction_percent']), name + ': reduction')
    benchmarks[name] = dict(completed_dispatches=count, order=cfg['order'], statistics=timing,
                           speedup=speedup, latency_reduction_percent=reduction)
check(control_hashes['arithmetic_abba'] == control_hashes['arithmetic_baab'], 'ABBA/BAAB output reproducibility')
for key in ('original_weight_sha256','input_sha256','profile_definitions','artifacts'):
    check(reports['arithmetic_abba'][key] == reports['arithmetic_baab'][key], 'ABBA/BAAB fixed:' + key)
for arithmetic in ('bf16', 'bfp16'):
    case = reports[arithmetic + '_model']['cases'][0]
    check({r['input']: r['output_sha256'] for r in case['runs']} == control_hashes['arithmetic_abba'][arithmetic], arithmetic + ': CPU-check vs timing output identity')

previous_path = REPO / 'docs/runs/2026-10-25-kernel-optimizations/v3_safe_model.json'
previous, current = read(previous_path), reports['bf16_model']
previous_case, current_case = previous['cases'][0], current['cases'][0]
check(previous['status'] == 'passed', 'previous selected native report passed')
check(previous_case['config'] == current_case['config'], 'previous native geometry')
check(previous_case['original_weight_sha256'] == current_case['original_weight_sha256'], 'previous native weights')
previous_runs = {r['input']: (r['input_sha256'],r['output_sha256']) for r in previous_case['runs']}
current_runs = {r['input']: (r['input_sha256'],r['output_sha256']) for r in current_case['runs']}
check(previous_runs == current_runs, 'native output exact vs previous selected native')

total = sum(r['completed_npu_dispatches'] for r in reports.values())
check(total == 1024 and sum(x['completed_dispatches'] for x in correctness.values()) == 48,
      '1024 total completions = 488 + 488 + 48')

package = dict(exists=PACKAGE.exists(), artifacts=[], payload_files=None)
if PACKAGE.exists():
    package['payload_files'] = len([p for p in PACKAGE.rglob('*') if p.is_file() and p.name != 'SHA256SUMS'])
    for path in sorted(PACKAGE.glob('prebuilt/*/final.xclbin.json')):
        manifest = read(path)
        if manifest.get('arithmetic') != 'bfp16':
            continue
        stage = 'swiglu' if manifest['mode'] == 'swiglu' else 'down'
        evidence = EVIDENCE / 'prebuilt/bfp16' / stage
        check(manifest == read(evidence/'final.xclbin.json'), 'package exact BFP16 manifest:' + stage)
        for filename in ('final.xclbin','insts.bin','final.xclbin.json'):
            check(digest(path.parent/filename) == digest(evidence/filename), 'package exact artifact:' + stage+'/'+filename)
        check(digest(path.parent/'aie.mlir') == digest(evidence/'final.prj/aie.mlir'), 'package exact MLIR:' + stage)
        for dependency, expected in manifest['dependency_sha256'].items():
            check(digest(PACKAGE/dependency) == expected, 'package source dependency:' + dependency)
        package['artifacts'].append(stage)
    check(sorted(package['artifacts']) == ['down','swiglu'], 'two BFP16 package stages present')
    readme = (PACKAGE/'README.md').read_text().replace('\\\n', ' ')
    commands = [shlex.split(line) for line in readme.splitlines() if line.startswith('python w4a16_upstream.py')]
    check(len(commands) == 2, 'package two README compile commands')
    field_flags = dict(m='-M', k='-K', n='-N', weight_k='--weight-k', weight_n='--weight-n',
        m_reuse='--max-reuse', activation_fifo_depth='--activation-fifo-depth',
        segment_pipeline_depth='--segment-pipeline-depth', mmul_m_reuse='--mmul-m-reuse',
        arithmetic='--arithmetic', mode='--mode', input_layout='--input-layout', output_layout='--output-layout')
    for command in commands:
        mode = command[command.index('--mode')+1]
        stage = 'swiglu' if mode == 'swiglu' else 'down'
        manifest = read(EVIDENCE/'prebuilt/bfp16'/stage/'final.xclbin.json')
        for field, flag in field_flags.items():
            check(command[command.index(flag)+1] == str(manifest[field]), 'README CLI matches manifest:'+stage+'/'+field)
        check(('--vector-zero' in command) == manifest['vector_zero'], 'README vectorzero:'+stage)
        mlir = (EVIDENCE/'prebuilt/bfp16'/stage/'final.prj/aie.mlir').read_text()
        signature = next(line for line in mlir.splitlines() if 'aie.runtime_sequence(' in line)
        counts = [(int(n), dtype) for n, dtype in re.findall(r'memref<(\d+)x(bf16|ui8)>', signature)]
        expected = ([(2097152,'bf16'),(31195136,'ui8'),(31195136,'ui8'),(1310720,'bf16')]
                    if stage == 'swiglu' else [(1310720,'bf16'),(31195136,'ui8'),(2097152,'bf16')])
        check(counts == expected, 'README runtime element counts:'+stage)
    package['readme_cli_and_runtime_abi_verified'] = True
    checksum = PACKAGE/'SHA256SUMS'
    if checksum.exists():
        records = [line.split(maxsplit=1) for line in checksum.read_text().splitlines() if line]
        for expected, relative in records:
            check(digest(PACKAGE/relative.lstrip('*')) == expected, 'package checksum:'+relative)
        check(len(records) == 21, '21 package checksum entries')
        package['verified_checksums'] = len(records)

notes.append('Numerical error magnitudes are audited from retained reports and original-tolerance verdicts; raw output tensors were not exported, so numerical errors cannot be independently recalculated from arrays.')
result = dict(status='passed' if not failures else 'failed', timestamp_utc=datetime.now(timezone.utc).isoformat(),
    evidence_root=str(EVIDENCE), audit_script=str(Path(__file__)), checksum_count=len(checksums),
    source_matches=len(source_matches), source_differences=source_differences,
    unique_report_artifacts=len(unique_artifacts), prebuilt=prebuilt,
    correctness=correctness, benchmarks=benchmarks, total_completed_npu_dispatches=total,
    previous_native_report=str(previous_path), native_output_exact_vs_previous=previous_runs == current_runs,
    abba_baab_output_reproducibility=control_hashes['arithmetic_abba'] == control_hashes['arithmetic_baab'],
    package=package, failures=failures, limitations=notes)
OUT.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
print(json.dumps(result, indent=2))
sys.exit(bool(failures))
