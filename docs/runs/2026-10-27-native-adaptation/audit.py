#!/usr/bin/env python3
"""Audit native-adaptation evidence without executing GPU/NPU work.

Checks exported-byte closure, source versions, loaded binaries, counters and
recorded numerical decisions. Each fresh comparison uses its exact archived
validator and Python dependencies in a temporary subprocess. An integrity pass
does not promote failed experiments or establish model accuracy.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import tarfile
import tempfile


NATIVE_SHA = '6fa53d1cb6fd24e87a639b0d2f5a7d007dd0eaac78fed45bca2af4a66b121b8b'
PIN = '61714a3147f34857aa5dfef21a28e762777a2df0'
SUCCESS = {'passed', 'completed_with_accuracy_deviations'}
MARKERS = ('experiments/ffn_partition/', 'npu/ffn/', 'kernels/gpu/', 'src/', 'include/')


def load(path):
    return json.loads(Path(path).read_text())


def digest(path):
    value = sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inside(root, name):
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), f'path escapes evidence: {name}')
    return path


def source_name(name):
    name = str(name).replace('\\', '/')
    return next((name[name.index(marker):] for marker in MARKERS if marker in name), None)


def metric(value):
    for key, expected in (('rtol', .03), ('atol', .05), ('l2_limit', .02)):
        require(value.get(key) == expected, f'changed tolerance {key}')
    passed = False
    if value.get('finite') is True:
        maximum, reference = value['max_abs_error'], value['reference_max_abs']
        require(all(isinstance(x, (int, float)) and math.isfinite(x) and x >= 0
                    for x in (maximum, reference, value['rms_error'])), 'invalid finite metric')
        require(math.isclose(value['max_error_limit'], .05 + .03 * reference, rel_tol=1e-12),
                'maximum error threshold changed')
        if reference == 0:
            passed = maximum == 0
            require(value['relative_l2_error'] == (0 if passed else None), 'zero reference L2 differs')
        else:
            l2 = value['relative_l2_error']
            require(isinstance(l2, (int, float)) and math.isfinite(l2) and l2 >= 0, 'invalid L2')
            passed = l2 <= .02 and maximum <= .05 + .03 * reference
    structural = not value.get('structural_failures', [])
    policy = value.get('accuracy_policy', 'strict')
    require(policy in ('strict', 'report'), 'unknown accuracy policy')
    accepted = structural and (passed or policy == 'report')
    if 'accepted' in value:
        require(value['accepted'] == accepted, 'metric acceptance was relabeled')
    numerical = passed
    if 'numerical_passed' in value:
        require(value['numerical_passed'] == numerical and value['structural_passed'] == structural,
                'native structural/numerical verdict differs')
        passed = numerical and structural
    require(value['passed'] == passed and value['correctness'] == ('passed' if passed else 'failed'),
            'original tolerance verdict was relabeled')
    return dict(numerical_passed=numerical, structural_passed=structural, accepted=accepted)


def metrics_summary(values):
    verdicts = [metric(v) for v in values.values()]
    worst = {}
    for key in ('relative_l2_error', 'max_abs_error', 'rms_error', 'normalized_max_error'):
        available = [(v[key], label) for label, v in values.items() if v.get(key) is not None]
        if available:
            number, label = max(available)
            worst[key] = dict(value=number, check=label)
    return dict(checks=len(verdicts), numerical_failures=sum(not v['numerical_passed'] for v in verdicts),
                structural_failures=sum(not v['structural_passed'] for v in verdicts),
                rejected_checks=sum(not v['accepted'] for v in verdicts), worst=worst)


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def percentile(values, quantile):
    values = sorted(values)
    index = (len(values) - 1) * quantile
    lo, hi = math.floor(index), math.ceil(index)
    return values[lo] + (values[hi] - values[lo]) * (index - lo)


def candidate_records(report):
    """General sweep/smoke checks, including diagnostic-only and failed runs."""
    config = report['config']
    parts, dispatches = [], 0
    all_metrics = dict(report.get('correctness', {}))
    for part in report.get('partitions', []):
        p = part['npu_channels']
        completed = part.get('status') in SUCCESS
        named = part.get('correctness', {})
        all_metrics.update({f'P{p}/{key}': value for key, value in named.items()})
        records = sum((part.get(phase, []) for phase in
                       ('validation_runs', 'warmup_samples', 'samples')), [])
        calls, seen, reconstructed = 0, {}, {}
        suffix = dict(output='partition_reference', baseline='gpu_baseline', gpu='gpu_partial', npu='npu_partial')
        for record in records:
            mode, idx = record['mode'], record['input_index']
            require(math.isfinite(record['wall_us']) and record['wall_us'] > 0, 'invalid wall timing')
            checked = record.get('accuracy', {})
            label = (f"validation_{record['run']}_{mode}" if 'run' in record else
                     f"iteration_{record['iteration']}_{mode}")
            for kind, item in checked.items():
                verdict = metric(item)
                if completed:
                    require(verdict['accepted'], 'completed candidate contains rejected check')
                reconstructed[label if mode == 'baseline' else label + '_' + suffix[kind]] = item
            if completed:
                require(set(checked) == ({'output'} if mode == 'baseline' else set(suffix)),
                        'missing per-invocation numerical checks')
                key = ('baseline' if mode == 'baseline' else 'candidate', idx)
                output = record['output_sha256']
                require(key not in seen or seen[key] == output, 'repeat or serial/concurrent output changed')
                seen[key] = output
                if idx == 2:
                    require(output == sha256(bytes(config['m'] * config['hidden'] * 4)).hexdigest(),
                            'zero-input output hash differs')
            if mode != 'baseline':
                calls += 1
                diag = record.get('diagnostics', {}).get('npu', {})
                require(diag.get('completed_dispatches_total') == 2 * calls,
                        'per-call completion sequence differs')
                require(diag.get('weight_upload_counts') == dict(gate=1, up=1, down=1),
                        'weights uploaded again inside measurements')
                if config.get('shared_intermediate'):
                    require(diag.get('shared_input_completed_consumptions') == calls and
                            diag.get('down_input_host_write_count') == 0, 'shared intermediate counter differs')
                if config.get('dmabuf_gpu_output'):
                    require(diag.get('gpu_output_dmabuf') is True and
                            diag.get('gpu_output_sync_count') == calls and
                            diag.get('final_output_bo_reads') == 0 and
                            diag.get('final_output_h2d_copies') == 0, 'DMA-BUF output counter differs')
        counts = part.get('completed_npu_dispatches_by_stage', {})
        recorded_dispatches = sum(counts.values()) if counts else 2 * calls
        dispatches += recorded_dispatches
        stats = {}
        if completed:
            require(reconstructed == named, 'sample/named metric tables differ')
            expected = 8 + 2 * (config['warmup'] + config['iterations'])
            require(calls == expected == part['completed_candidate_calls'] ==
                    part['expected_npu_dispatches_per_stage'], 'candidate call count differs')
            require(counts == dict(swiglu=calls, down=calls), 'stage completion totals differ')
            require(part['fixed_weight_upload_counts'] == dict(gate=1, up=1, down=1), 'weight upload count differs')
            require(part['input_write_counts_by_stage'] == dict(swiglu=[calls, 1, 1],
                    down=[0 if config.get('shared_intermediate') else calls, 1]), 'input write count differs')
            require(part.get('weight_buffers_after') == report['original_weight_buffers'] and
                    part.get('original_weight_buffers_unchanged') is True, 'weight buffers changed')
            require(seen[('candidate', 0)] != seen[('candidate', 1)], 'changed input produced stale output')
            expected_probes = [(i, idx, mode) for i, idx in enumerate((0, 1, 2, 0))
                               for mode in ('serial', 'concurrent')]
            require([(s['run'], s['input_index'], s['mode']) for s in part['validation_runs']] == expected_probes,
                    'changed/zero/repeat probe coverage differs')
            for phase, indexes in (('warmup_samples', range(-config['warmup'], 0)),
                                   ('samples', range(config['iterations']))):
                samples = part[phase]
                require(len(samples) == 3 * len(indexes), 'missing measurements')
                for mode in ('baseline', 'serial', 'concurrent'):
                    require(sorted(s['iteration'] for s in samples if s['mode'] == mode) == list(indexes),
                            'missing/duplicate measurement iteration')
            for mode in ('baseline', 'serial', 'concurrent'):
                times = [s['wall_us'] for s in part['samples'] if s['mode'] == mode]
                actual = dict(count=len(times), median_us=statistics.median(times),
                              p10_us=percentile(times, .1), p90_us=percentile(times, .9),
                              min_us=min(times), max_us=max(times))
                recorded = part.get('stats', {}).get(mode, {})
                require(recorded.keys() == actual.keys() and all(
                    math.isclose(recorded[k], v, rel_tol=1e-12, abs_tol=1e-9) for k, v in actual.items()),
                    'timing summary differs from raw samples')
                stats[mode] = actual
        parts.append(dict(npu_channels=p, status=part.get('status'), completed_dispatches=recorded_dispatches,
                          counter_validation='complete' if completed else 'recorded_prefix_only', stats=stats))
    if report.get('status') in SUCCESS:
        require(report.get('original_weight_buffers_unchanged') is True and
                report.get('original_weight_buffers_after') == report['original_weight_buffers'],
                'full original weight buffers changed')
        accuracy = report['accuracy']
        verdicts = [metric(v) for v in all_metrics.values()]
        require(accuracy['check_count'] == len(verdicts) and accuracy['outside_tolerance_count'] ==
                sum(not v['numerical_passed'] for v in verdicts), 'accuracy count differs')
        require(all(v['accepted'] for v in verdicts), 'completed report contains rejected metrics')
        passed = all(v['numerical_passed'] for v in verdicts)
        require(accuracy['passed'] == passed and report['status'] ==
                ('passed' if passed else 'completed_with_accuracy_deviations'), 'report status was relabeled')
    return dict(parts=parts, completed_npu_dispatches=dispatches, accuracy=metrics_summary(all_metrics),
                ordinary_headline_eligible=report.get('ordinary_headline_eligible', True),
                measurement_mode=report.get('measurement_mode', 'ordinary_latency'))


VALIDATOR_SCRIPT = r'''
import hashlib,json,pathlib,sys
from types import SimpleNamespace
root,manifest_path,expected_path=map(pathlib.Path,sys.argv[1:])
sys.path.insert(0,str(root))
from experiments.ffn_partition import compare_upstream_native as driver
expected=json.loads(expected_path.read_text())
imports={}
for module in list(sys.modules.values()):
    name=getattr(module,'__file__',None)
    if not name: continue
    path=pathlib.Path(name).resolve()
    if not path.is_relative_to(root):
        if getattr(module,'__name__','').startswith('experiments.ffn_partition'):
            raise ValueError('validator imported a non-archived project module: '+str(path))
        continue
    relative=str(path.relative_to(root))
    if relative.endswith('__init__.py'): continue
    if not relative.endswith('.py'): continue
    value=hashlib.sha256(path.read_bytes()).hexdigest()
    if expected.get(relative)!=value: raise ValueError('unverified validator import: '+relative)
    imports[relative]=value
manifest=json.loads(manifest_path.read_text()); args=SimpleNamespace(**manifest['config']); jobs=[]
for job in manifest['jobs']:
    if job['status'] not in ('passed','completed_with_accuracy_deviations'): continue
    path=manifest_path.parent/job['report_path']; report=json.loads(path.read_text())
    validate=driver.validate_native if job['variant']=='native' else driver.validate_candidate
    actual=validate(report,job,args); actual['report_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual!=job['evidence']: raise ValueError('stored validator evidence differs: '+job['id'])
    jobs.append(dict(id=job['id'],evidence=actual))
summary=driver.summarize(manifest,manifest_path.parent)
if summary!=json.loads((manifest_path.parent/'comparison_summary.json').read_text()):
    raise ValueError('comparison summary differs')
print(json.dumps(dict(validated_jobs=jobs,summary=summary,verified_imports=imports)))
'''


def run(root):
    root = root.resolve()
    result = dict(status='running', integrity_errors=[], reports={}, comparisons={}, artifacts={},
                  limitations=[
                      'No hardware execution or independent rebuild is performed.',
                      'Recorded errors and their tolerance decisions are audited; full output arrays are not available for recomputing numerical errors.',
                      'Failed experiments remain failures. Accepted report-mode deviations do not establish model accuracy.',
                      'System runtime/header hashes without exported bytes are explicitly recorded-only.',
                      'Ordinary FFN timing is distinct from synchronized diagnostics and whole-model prefill.',
                  ])

    def attempt(label, operation):
        try:
            return operation()
        except Exception as error:
            result['integrity_errors'].append(dict(check=label, error=str(error)))
            return None

    hashes = {}

    def checksums():
        table = load(root / 'SHA256SUMS.json')
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()
                  and p != root / 'SHA256SUMS.json'}
        require(set(table) == actual, f'root checksum coverage differs: {sorted(set(table) ^ actual)[:20]}')
        for name, value in table.items():
            require(digest(inside(root, name)) == value, f'checksum differs: {name}')
            hashes[name] = value
        for path in root.rglob('SHA256SUMS.json'):
            if path == root / 'SHA256SUMS.json':
                continue
            for name, value in load(path).items():
                require(digest(inside(path.parent, name)) == value, f'nested checksum differs: {path}/{name}')
        return dict(verified_files=len(table), root_manifest_sha256=digest(root / 'SHA256SUMS.json'))
    result['checksums'] = attempt('all exported checksums', checksums)
    require(result['checksums'] is not None, 'cannot validate sources after export checksum failure')
    sources, binaries, archive_manifests = {}, defaultdict(list), []
    for relative, value in hashes.items():
        path = root / relative
        binaries[value].append(relative)
        name = source_name(relative)
        if name and path.suffix in ('.py', '.cc', '.cpp', '.cu', '.h', '.hpp'):
            sources.setdefault((name, value), (path.read_bytes(), []))[1].append(relative)
    for path in sorted(root.rglob('*.tar.gz')):
        def source_archive(path=path):
            count = 0
            with tarfile.open(path) as archive:
                for member in archive:
                    if not member.isfile():
                        continue
                    name = source_name(member.name)
                    if name and Path(name).suffix in ('.py', '.cc', '.cpp', '.cu', '.h', '.hpp'):
                        content = archive.extractfile(member).read()
                        value = sha256(content).hexdigest()
                        sources.setdefault((name, value), (content, []))[1].append(
                            f'{path.relative_to(root)}::{member.name}')
                        count += 1
                    if 'source' in Path(member.name).name and member.name.endswith('.json'):
                        archive_manifests.append((f'{path.relative_to(root)}::{member.name}',
                                                  json.load(archive.extractfile(member))))
            return count
        result.setdefault('source_archives', {})[str(path.relative_to(root))] = attempt(str(path), source_archive)

    def verify_sources(table):
        for original, value in table.items():
            name = source_name(original)
            require(name and (name, value) in sources, f'unresolved source version: {original} {value}')
        return len(table)

    def baseline():
        base = root / 'baseline'
        provenance = load(base / 'BUILD_PROVENANCE.json')
        build = load(base / 'build-evidence/build-result.json')
        require(provenance['original_revision'] == PIN, 'baseline revision differs')
        require(digest(base / 'native.so') == build['library_sha256'] == NATIVE_SHA,
                'faithful native library changed')
        for name, value in provenance['source_sha256'].items():
            require(digest(inside(base / 'sources', name)) == value, f'baseline source differs: {name}')
        for name, value in provenance['patch_sha256'].items():
            require(digest(inside(base, name)) == value, f'baseline patch differs: {name}')
        require(digest(base / 'build-evidence/payload_manifest.json') == provenance['payload_manifest_sha256'],
                'baseline payload manifest differs')
        return dict(native_library_sha256=NATIVE_SHA, original_revision=PIN,
                    patched_source_count=len(provenance['source_sha256']),
                    note='Pinned library identity preserved; previous baseline audit contains independent patch replay.')
    result['baseline'] = attempt('preserved faithful native baseline', baseline)

    for name, value in archive_manifests:
        table = value.get('files', value.get('sources', value.get('source_sha256', value)))
        if isinstance(table, dict) and any(source_name(k) for k in table):
            table = {k: v for k, v in table.items() if source_name(k)}
            result.setdefault('source_manifests', {})[name] = attempt(name, lambda t=table: verify_sources(t))
    for path in root.glob('*/*.json'):
        if 'source' not in path.name and 'provenance' not in path.name:
            continue
        value = load(path)
        table = value.get('files', value.get('sources', value.get('source_sha256', value)))
        if isinstance(table, dict):
            table = {k: v for k, v in table.items() if source_name(k)}
        if isinstance(table, dict) and table:
            result.setdefault('source_manifests', {})[str(path.relative_to(root))] = attempt(str(path), lambda t=table: verify_sources(t))

    artifacts = {}
    for path in sorted(root.rglob('*.xclbin.json')):
        def artifact(path=path):
            manifest = load(path)
            require(digest(Path(str(path)[:-5])) == manifest['xclbin_sha256'] and
                    digest(path.parent / 'insts.bin') == manifest['insts_sha256'], 'NPU binary/instructions differ')
            verify_sources({'npu/ffn/' + name: value for name, value in manifest['dependency_sha256'].items()})
            contract = load(path.parent / 'build_contract.json')
            require(contract['source_sha256'] == manifest['dependency_sha256'] and all(
                manifest.get(k) == v for k, v in contract['expected_manifest'].items()), 'build contract differs')
            key = (manifest['xclbin_sha256'], manifest['insts_sha256'])
            artifacts.setdefault(key, []).append((manifest, contract))
            return dict(xclbin_sha256=key[0], insts_sha256=key[1],
                        flags={k: manifest.get(k) for k in ('arithmetic', 'bfp16_native_layout', 'split_m32_a',
                            'preconvert_b', 'preconvert_a', 'm_reuse', 'activation_m_reuse',
                            'activation_fifo_depth', 'output_fifo_depth', 'input_layout', 'output_layout')})
        result['artifacts'][str(path.relative_to(root))] = attempt(str(path), artifact)

    def runtime(report, path):
        source_checks, binary_checks, external = 0, 0, []
        for value in walk(report):
            if isinstance(value.get('source_sha256'), dict):
                table = value['source_sha256']
                if table and not all(source_name(k) for k in table):
                    table = {'npu/ffn/' + k: v for k, v in table.items()}
                source_checks += verify_sources(table)
            for key in ('binding_library_sha256', 'binary_sha256', 'native_library_sha256'):
                if value.get(key):
                    require(value[key] in binaries, f'loaded binary not exported: {key} {value[key]}')
                    if key == 'native_library_sha256':
                        require(value[key] == NATIVE_SHA, 'native implementation changed')
                    binary_checks += 1
            for key in ('runtime_dependency_sha256', 'xrt_header_sha256', 'pybind_header_sha256'):
                for original, expected in value.get(key, {}).items():
                    if expected not in binaries:
                        external.append(dict(path=original, sha256=expected, status='recorded_only'))
            for key in ('pyxrt_sha256', 'xrt_library_sha256'):
                if value.get(key) and value[key] not in binaries:
                    external.append(dict(path=key, sha256=value[key], status='recorded_only'))
        for part in report.get('partitions', []):
            npu = part.get('npu', {})
            if npu:
                require(npu.get('weight_repacking') is False and npu.get('full_weight_buffers') is True,
                        'original full packed-weight contract changed')
            for stage, item in part.get('npu', {}).get('artifacts', {}).items():
                manifest, contract = item['manifest'], item['build_contract']
                key = (manifest['xclbin_sha256'], manifest['insts_sha256'])
                require((manifest, contract) in artifacts.get(key, []), f'loaded {stage} artifact not archived exactly')
                for flag in ('bfp16_native_layout', 'split_m32_a', 'preconvert_b', 'preconvert_a'):
                    require(bool(report['config'].get(flag, False)) == bool(manifest.get(flag, False)),
                            f'requested {flag} differs from loaded manifest')
                require(manifest['weight_tile_bytes'] == 4352 and manifest['cols'] == 8 and
                        manifest['worker_count'] == 32, 'weight ABI or eight-column geometry changed')
        for item in report.get('native_artifacts', []):
            if item.get('sha256'):
                require(item['sha256'] in binaries, 'native PDI/instruction bytes missing')
        if report.get('native_config_sha256'):
            config = path.parent / Path(report['native_config_path']).name
            require(digest(config) == report['native_config_sha256'] and load(config) == report['native_config'],
                    'native runtime configuration differs')
        return dict(source_entries_verified=source_checks, loaded_binary_entries_verified=binary_checks,
                    external_dependencies_recorded_only=external)

    totals = Counter()
    report_paths = sorted(path for path in root.rglob('*.json') if 'results' in path.parts)
    for path in report_paths:
        report = load(path)
        if not isinstance(report, dict) or 'config' not in report or 'provenance' not in report:
            continue
        name = str(path.relative_to(root))
        entry = dict(status=report.get('status'), error=report.get('error'), report_sha256=digest(path))
        result['reports'][name] = entry
        entry['runtime_provenance'] = attempt(name + ' runtime', lambda r=report, p=path: runtime(r, p))
        if 'partitions' in report:
            entry['kind'] = 'candidate'
            records = attempt(name + ' recorded calls/metrics', lambda r=report: candidate_records(r))
            entry['records'] = records
            count = records['completed_npu_dispatches'] if records else 0
        else:
            entry['kind'] = 'native'
            count = report.get('completed_npu_dispatches', 0)
            values = dict(report.get('correctness', {}))
            for phase in ('warmup_samples', 'samples'):
                values.update({f'{phase}/{i}': record['accuracy'] for i, record in
                               enumerate(report.get(phase, [])) if 'accuracy' in record})
            entry['accuracy'] = attempt(name + ' metrics', lambda v=values: metrics_summary(v))
            entry['completed_npu_dispatches'] = count
            entry['expected_npu_dispatches'] = report.get('expected_npu_dispatches')
        totals['completed_npu_dispatches'] += count
        totals[entry['kind'] + '_reports'] += 1
        totals['status_' + str(report.get('status'))] += 1

    for path in sorted(root.rglob('comparison_manifest.json')):
        def comparison(path=path):
            manifest = load(path)
            verify_sources(manifest['source_sha256'])
            table = {source_name(k): v for k, v in manifest['source_sha256'].items()}
            for job in manifest['jobs']:
                report_path = inside(path.parent, job['report_path'])
                if job.get('saved_report_sha256'):
                    require(digest(report_path) == job['saved_report_sha256'], 'saved comparison report changed')
                for boundary in ('before', 'after'):
                    summary = job.get('power_' + boundary + '_summary')
                    if summary is None:
                        require(job['status'] not in SUCCESS, 'accepted job lacks power snapshot')
                        continue
                    snapshot = inside(path.parent, job['power_' + boundary])
                    require(digest(snapshot) == summary['sha256'], 'power snapshot hash differs')
                    modes = [platform['status']['power_mode'] for device in load(snapshot).get('devices', [])
                             if device.get('device_id') == manifest['config']['power_device']
                             for platform in device.get('platforms', [])
                             if isinstance(platform.get('status', {}).get('power_mode'), str)]
                    require(modes == [summary['mode']], 'power snapshot mode differs')
            with tempfile.TemporaryDirectory(prefix='native-adaptation-validator-') as temporary:
                destination = Path(temporary)
                for name, value in table.items():
                    if not name.endswith('.py'):
                        continue
                    target = inside(destination, name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(sources[(name, value)][0])
                expected = destination / 'expected.json'
                expected.write_text(json.dumps(table))
                process = subprocess.run([sys.executable, '-I', '-c', VALIDATOR_SCRIPT, str(destination),
                    str(path), str(expected)], cwd=destination, capture_output=True, text=True, timeout=60)
                require(process.returncode == 0, 'exact archived validator failed: ' + process.stderr[-5000:])
                validated = json.loads(process.stdout)
            return dict(status=manifest['status'],
                        validator_sha256=table['experiments/ffn_partition/compare_upstream_native.py'],
                        **validated)
        result['comparisons'][str(path.relative_to(root))] = attempt(str(path) + ' exact comparison', comparison)
    result['totals'] = dict(totals)
    result['status'] = 'integrity_failed' if result['integrity_errors'] else 'integrity_passed'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('audit.json'))
    args = parser.parse_args()
    try:
        result = run(args.evidence_dir)
    except Exception as error:
        result = dict(status='integrity_failed', integrity_errors=[dict(check='audit setup', error=str(error))])
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: result.get(key) for key in ('status', 'checksums', 'totals', 'integrity_errors')}))
    return result['status'] != 'integrity_passed'


if __name__ == '__main__':
    raise SystemExit(main())
