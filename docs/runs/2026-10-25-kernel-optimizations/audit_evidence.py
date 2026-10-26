#!/usr/bin/env python3
"""Read-only consistency/source/binary audit of a native BF16 evidence archive.

Usage: python audit_upstream_optimization_evidence.py EVIDENCE_DIRECTORY \
  --output /tmp/optimization_integrity_audit.json [--selected-dir prebuilt/selected] \
  [--selected-profile PROFILE.json] [--previous-report OLD_MODEL_REPORT.json] [--archive-directory DOWNLOADS_DIRECTORY]

Failed bring-up reports remain separate from passing evidence. Source versions
may resolve to retained upload tarballs rather than the final source snapshot.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import tarfile
import numpy as np


def load(path): return json.loads(Path(path).read_text())
def digest(path): return sha256(Path(path).read_bytes()).hexdigest()
def source_relative(name):
    name = str(name).replace('\\', '/')
    for marker in ('npu/ffn/', 'experiments/ffn_partition/'):
        if marker in name:
            return name[name.index(marker):]
    return None

def finite_number(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def audit_final_selection(args, evidence, report):
    """Additional checks for the final optimization archive and selected pair."""
    selected_items = report['selected_artifacts'].values()
    selected = {'swiglu' if item['manifest']['mode'] == 'swiglu' else 'down':
                item['manifest'] for item in selected_items}
    if selected:
        confirmations = {}
        for path in sorted((evidence / 'results').glob('confirm_selected_*.json')):
            data = load(path)
            assert all(data['artifacts']['2'][stage]['manifest'] == selected[stage]
                       for stage in selected)
            candidates = [block for block in data['blocks'] if block['profile_index'] == 2]
            assert len(candidates) == 2 * data['config']['rounds']
            for block in candidates:
                assert all(block['runner_metadata']['artifacts'][stage]['manifest'] == selected[stage]
                           for stage in selected)
            prior_matches = report['benchmarks'][path.name]['controls_matching_external_prior_oracle']
            if args.previous_report:
                assert prior_matches == 2
            confirmations[path.name] = dict(selected_pair_exact_match=True,
                matching_candidate_blocks=len(candidates),
                controls_matching_external_prior_oracle=prior_matches)
        report['selected_final_confirmation_identity'] = confirmations

        fullshape = evidence / 'results' / 'v3_safe_model.json'
        if fullshape.exists():
            data = load(fullshape)
            assert data['status'] == 'passed' and len(data['cases']) == 1
            case = data['cases'][0]
            assert all(case['artifacts'][stage]['manifest'] == selected[stage] for stage in selected)
            prior = {}
            for previous_path in args.previous_report:
                for old_case in load(previous_path)['cases']:
                    for run in old_case['runs']:
                        key = (tuple(sorted(old_case['original_weight_sha256'].items())), run['input_sha256'])
                        prior[key] = (run['output_sha256'], run['reference_sha256'])
            runs = []
            for run in case['runs']:
                key = (tuple(sorted(case['original_weight_sha256'].items())), run['input_sha256'])
                if args.previous_report:
                    assert prior[key] == (run['output_sha256'], run['reference_sha256'])
                runs.append(dict(input=run['input'], input_sha256=run['input_sha256'],
                    output_sha256=run['output_sha256'], reference_sha256=run['reference_sha256'],
                    prior_pipeline_exact=True if args.previous_report else None))
            report['selected_fullshape_prior_pipeline_equivalence'] = dict(status='passed',
                report=fullshape.name, original_weight_sha256=case['original_weight_sha256'], runs=runs)

    if args.archive_directory:
        archives = {}
        names = ('kernel-opt-bf16-evidence-20261025.tar.gz',
                 'kernel-opt-v1-compiler-evidence.tar.gz', 'kernel-opt-final-disassembly.tar.gz')
        for name in names:
            path = args.archive_directory / name
            archives[name] = dict(bytes=path.stat().st_size, sha256=digest(path))
        assert archives[names[0]] == dict(bytes=11020877,
            sha256='76ca2dccbbe9bda1b97535e750ae0ac400eee1b76d5af10042c1d8e8a539668d')
        report['archive_identities'] = archives
        with tarfile.open(args.archive_directory / names[-1]) as archive:
            files = {member.name: dict(bytes=member.size,
                sha256=sha256(archive.extractfile(member).read()).hexdigest())
                for member in archive.getmembers() if member.isfile()}
        assert len(files) == 12 and all(name.endswith('.elf.dis') for name in files)
        report['final_disassembly_supplement'] = dict(archive=names[-1], files=files,
            limitation='Text disassembly identity recorded; this audit does not regenerate disassembly from ELF.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('--repo', type=Path, default=Path('/home/adam/Documents/ChatGPT/HeteroMega'))
    parser.add_argument('--output', type=Path, default=Path('/tmp/optimization_integrity_audit.json'))
    parser.add_argument('--selected-dir', type=Path)
    parser.add_argument('--selected-profile', type=Path)
    parser.add_argument('--previous-report', type=Path, action='append', default=[])
    parser.add_argument('--archive-directory', type=Path, help='Optional directory holding the three immutable downloaded evidence archives.')
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    report = dict(status='running', evidence=str(evidence), final_sources={}, source_versions={},
        binaries={}, correctness={}, benchmarks={}, retained_failures={}, selected_artifacts={},
        completion_totals={}, external_oracles=[], final_source_test_only_differences={}, limitations=[
            'Saved-record and byte-identity checks do not repeat hardware execution.',
            'NPU-branch timing does not establish GPU+NPU or whole-model speedup.',
            'Missing historical binaries are listed separately; selected artifacts must be present.'])
    source_index = defaultdict(list)
    for path in evidence.rglob('*'):
        if path.is_file() and path.suffix in ('.py', '.cc', '.h', '.cpp'):
            relative = source_relative(path.relative_to(evidence))
            if relative:
                source_index[(relative, digest(path))].append(str(path.relative_to(evidence)))
    for archive in sorted(evidence.glob('uploads/*.tar.gz')):
        with tarfile.open(archive) as bundle:
            for member in bundle.getmembers():
                relative = source_relative(member.name)
                if relative and member.isfile() and Path(relative).suffix in ('.py', '.cc', '.h', '.cpp'):
                    value = sha256(bundle.extractfile(member).read()).hexdigest()
                    source_index[(relative, value)].append(f'{archive.relative_to(evidence)}::{member.name}')

    def sources(hashes, bare=False):
        current = True
        for name, value in hashes.items():
            relative = 'npu/ffn/' + name if bare and '/' not in name else name
            assert (relative, value) in source_index, ('unresolved recorded source', relative, value)
            local = args.repo / relative
            matches = local.exists() and digest(local) == value
            current &= matches
            report['source_versions'][relative + '@' + value] = dict(
                sha256=value, archived_at=source_index[(relative, value)], current_local_match=matches)
        return current

    final_sources = evidence / 'sources'
    if final_sources.exists():
        for path in final_sources.rglob('*'):
            if path.is_file():
                relative = path.relative_to(final_sources)
                local = args.repo / relative
                matches = local.is_file() and digest(path) == digest(local)
                if not matches:
                    assert relative.name.startswith('test_') and local.is_file(), ('final/local runtime source mismatch', relative)
                    report['final_source_test_only_differences'][str(relative)] = dict(archived_sha256=digest(path), local_sha256=digest(local))
                report['final_sources'][str(relative)] = digest(path)

    binary_index = {}
    for manifest_path in sorted(evidence.rglob('*.xclbin.json')):
        manifest = load(manifest_path)
        directory = manifest_path.parent
        binary = Path(str(manifest_path)[:-5])
        instructions = directory / 'insts.bin'
        assert binary.is_file() and instructions.is_file(), ('incomplete archived binary pair', directory)
        assert digest(binary) == manifest['xclbin_sha256']
        assert digest(instructions) == manifest['insts_sha256']
        assert manifest['arithmetic'] == manifest['compute_format'] == 'bf16'
        assert manifest['cols'] == 8 and manifest['worker_count'] == 32
        assert manifest['weight_tile_bytes'] == 4352
        current = sources(manifest['dependency_sha256'], bare=True)
        contract_path = directory / 'build_contract.json'
        if contract_path.exists():
            contract = load(contract_path)
            assert contract['source_sha256'] == manifest['dependency_sha256']
            assert all(manifest[key] == value for key, value in contract['expected_manifest'].items())
            assert contract['target_mlir_aie_commit'] == manifest['target_mlir_aie_commit']
        identity = (manifest['xclbin_sha256'], manifest['insts_sha256'])
        binary_index.setdefault(identity, []).append((directory, manifest))
        elfs = sorted(directory.rglob('*.elf'))
        relative = str(directory.relative_to(evidence))
        report['binaries'][relative] = dict(manifest=manifest, current_sources=current,
            build_contract_verified=contract_path.exists(), elf_count=len(elfs),
            elf_sha256={str(p.relative_to(directory)): digest(p) for p in elfs})

    missing_historical = set()
    def artifact_sources(artifact):
        manifest = artifact.get('manifest')
        if not manifest:
            return
        sources(manifest['dependency_sha256'], bare=True)
        identity = (manifest['xclbin_sha256'], manifest['insts_sha256'])
        if identity in binary_index:
            assert any(manifest == saved for _, saved in binary_index[identity]), 'report/archive manifest mismatch'
        else:
            missing_historical.add(identity)

    results_dir = evidence / 'results'
    datasets = []
    for path in sorted(results_dir.glob('*.json')):
        data = load(path)
        if isinstance(data, dict) and 'source_sha256' in data and ('cases' in data or 'blocks' in data):
            datasets.append((path, data))
    assert datasets, 'no hardware/benchmark reports found'
    oracle_outputs = {}
    external_oracle_outputs = {}
    strict_max_l2 = strict_max_abs = 0.0
    completions = Counter()

    def weight_key(weights): return tuple(sorted(weights.items()))
    def add_oracle(data, external=False):
        for case in data.get('cases', []):
            if case.get('status') != 'passed' or case.get('config', {}).get('mode') != 'ffn':
                continue
            weights = weight_key(case['original_weight_sha256'])
            for run in case['runs']:
                key = (weights, run['input_sha256'])
                previous = oracle_outputs.get(key)
                assert previous is None or previous == run['output_sha256'], 'strict FFN controls disagree'
                oracle_outputs[key] = run['output_sha256']
                if external:
                    external_oracle_outputs[key] = run['output_sha256']
    for previous in args.previous_report:
        data = load(previous)
        assert data['status'] == 'passed'
        add_oracle(data, external=True)
        report['external_oracles'].append(dict(path=str(previous), sha256=digest(previous)))

    for path, data in datasets:
        sources(data['source_sha256'])
        if 'cases' not in data:
            continue
        passed = data['status'] == 'passed'
        count = sum(run.get('completed_npu_dispatches', 0) for case in data['cases'] for run in case.get('runs', []))
        assert count == data['completed_npu_dispatches'], ('correctness completion count', path)
        for case in data['cases']:
            for artifact in case.get('artifacts', {}).values(): artifact_sources(artifact)
        if passed:
            assert data['arithmetic'] == 'bf16' and data['weight_repacking'] is False
            assert data['tolerances'] == dict(rtol=0.03, atol=0.05, relative_l2_limit=0.02)
            for case in data['cases']:
                assert case['status'] == 'passed' and all(case['checks'].values())
                assert len(case['runs']) == 4
                by_input = {run['input']: run for run in case['runs']}
                assert by_input['signed_a']['output_sha256'] == by_input['repeat_a']['output_sha256']
                assert by_input['signed_a']['output_sha256'] != by_input['signed_b']['output_sha256']
                for run in case['runs']:
                    assert run['status'] == 'completed'
                    errors = run['errors']
                    assert errors['correctness'] == 'passed' and errors['finite']
                    assert errors['relative_l2_error'] <= 0.02
                    strict_max_l2 = max(strict_max_l2, errors['relative_l2_error'])
                    strict_max_abs = max(strict_max_abs, errors['max_abs_error'])
                if case['config']['mode'] == 'ffn':
                    assert case['runner_completed_dispatches'] == dict(swiglu=4, down=4)
            add_oracle(data)
            report['correctness'][path.name] = dict(status='passed', cases=len(data['cases']),
                completed_npu_dispatches=count, config=data['config'])
            completions['passing_correctness'] += count
        else:
            report['retained_failures'][path.name] = dict(kind='correctness', status=data['status'],
                completed_npu_dispatches=count, error=data.get('error'), config=data.get('config'))
            completions['failed_correctness'] += count

    all_control_outputs = {}
    for path, data in datasets:
        if 'blocks' not in data:
            continue
        for artifacts in data.get('artifacts', {}).values():
            for artifact in artifacts.values(): artifact_sources(artifact)
        reference = data.get('reference_block', {})
        blocks = [reference] + data['blocks']
        count = sum(sum(b.get('completed_dispatches', {}).values()) for b in blocks)
        assert count == data['completed_npu_dispatches'], ('benchmark completion count', path)
        if data['status'] != 'passed':
            report['retained_failures'][path.name] = dict(kind='benchmark', status=data['status'],
                completed_npu_dispatches=count, error=data.get('error'), config=data.get('config'))
            completions['failed_benchmarks'] += count
            continue
        assert all(data['checks'].values())
        assert reference.get('excluded_from_summary') and reference not in data['blocks']
        assert len(reference['warmup']) == len(reference['runs']) == 2
        field = 'profile_index' if 'profile_index' in data['blocks'][0] else 'segment_pipeline_depth'
        expected_order = [1 if x == 'A' else 2 for x in data['config']['order']] * data['config']['rounds']
        assert [b[field] for b in data['blocks']] == expected_order
        assert reference[field] == 1
        expected_count = 8 + 8 * data['config']['rounds'] * (data['config']['warmup'] + data['config']['iterations'])
        assert count == expected_count
        controls = {r['input']: r['output_sha256'] for r in reference['runs']}
        assert set(controls) == set(data['input_sha256'])
        oracle_matches = 0
        external_oracle_matches = 0
        for label, expected_hash in controls.items():
            key = (weight_key(data['original_weight_sha256']), data['input_sha256'][label])
            assert key not in all_control_outputs or all_control_outputs[key] == expected_hash
            all_control_outputs[key] = expected_hash
            if key in oracle_outputs:
                assert oracle_outputs[key] == expected_hash
                oracle_matches += 1
            if key in external_oracle_outputs:
                assert external_oracle_outputs[key] == expected_hash
                external_oracle_matches += 1
        for block in blocks:
            assert block['status'] == 'passed' and all(block['checks'].values())
            assert block['child_process_returncode'] == 0
            calls = len(block['warmup']) + len(block['runs'])
            assert block['completed_dispatches'] == dict(swiglu=calls, down=calls)
            assert block['fixed_weight_upload_counts'] == dict(gate=1, up=1, down=1)
            metadata = block['runner_metadata']
            if 'profile' in block:
                for name, value in block['profile'].items():
                    if name == 'copy_output_bits':
                        assert metadata['host_output_readback'] == ('owned_copy' if value else 'borrowed_until_consumed')
                    else:
                        assert metadata['kernel_options'][name] == value
                assert metadata['segment_pipeline_depth'] == 2
                assert block['profile'] == data['profile_definitions'][str(block[field])]
            for artifact in metadata['artifacts'].values(): artifact_sources(artifact)
            for ordinal, run in enumerate(block['warmup'] + block['runs']):
                assert run['finite'] and run['output_sha256'] == controls[run['input']]
                diag = run['diagnostics']
                assert diag['completed_dispatches_total'] == 2 * (ordinal + 1)
                assert diag['weight_upload_counts'] == dict(gate=1, up=1, down=1)
            for run in block['runs']:
                errors = run.get('errors_vs_profile_a_control', run.get('errors_vs_serial_control'))
                assert errors['correctness'] == 'passed' and errors['finite']
                assert errors['max_abs_error'] == errors['relative_l2_error'] == 0
                assert finite_number(run['wall_us']) and run['wall_us'] > 0
                assert run['wall_us'] >= run['diagnostics']['branch_host_wall_us']
        summary = {}
        for index in (1, 2):
            runs = [run for block in data['blocks'] if block[field] == index for run in block['runs']]
            raw = np.asarray([run['wall_us'] for run in runs], dtype=np.float64)
            recomputed = dict(count=len(raw), median_us=float(np.median(raw)), mean_us=float(np.mean(raw)),
                min_us=float(np.min(raw)), max_us=float(np.max(raw)),
                p10_us=float(np.percentile(raw, 10)), p90_us=float(np.percentile(raw, 90)))
            assert all(math.isclose(recomputed[k], data['summary'][str(index)]['wall'][k], rel_tol=1e-12, abs_tol=1e-6) for k in recomputed)
            waits = {}
            for label in ('swiglu', 'down'):
                waits[label] = float(np.median([r['diagnostics']['dispatch_wait_us'][label] for r in runs]))
                assert waits[label] == data['summary'][str(index)]['dispatch_wait'][label]['median_us']
            summary[str(index)] = dict(wall=recomputed, median_host_dispatch_wait_us=waits)
        baseline, candidate = summary['1']['wall']['median_us'], summary['2']['wall']['median_us']
        reduction = 100 * (baseline - candidate) / baseline
        assert abs(reduction - data['summary']['candidate_latency_reduction_percent']) < 1e-10
        report['benchmarks'][path.name] = dict(status='passed', completed_npu_dispatches=count,
            config=data['config'], profiles=data.get('profile_definitions'), results=summary,
            reduction_percent=reduction, controls_matching_strict_oracle=oracle_matches,
            controls_matching_external_prior_oracle=external_oracle_matches,
            all_outputs_match_exactly=True, reference_excluded_from_summary=True)
        completions['passing_benchmarks'] += count

    if args.selected_dir:
        selected_root = args.selected_dir if args.selected_dir.is_absolute() else evidence / args.selected_dir
        selected = [(path, item) for path, item in report['binaries'].items()
                    if (evidence / path).is_relative_to(selected_root)]
        assert len(selected) == 2, ('expected selected SwiGLU/down artifact pair', selected_root)
        profile = load(args.selected_profile) if args.selected_profile else None
        if profile is None and (evidence / 'results' / 'confirm_selected_abba.json').exists():
            profile = load(evidence / 'results' / 'confirm_selected_abba.json')['profile_definitions']['2']
        report['selected_profile'] = profile
        for path, item in selected:
            manifest = item['manifest']
            assert item['current_sources'] and item['build_contract_verified']
            assert manifest['segment_pipeline_depth'] == 2
            if profile:
                swiglu = manifest['mode'] == 'swiglu'
                expected = dict(vector_zero=profile['vector_zero'], mmul_m_reuse=profile['mmul_m_reuse'],
                    m_reuse=profile['swiglu_reuse' if swiglu else 'down_reuse'],
                    input_layout=profile['swiglu_input_layout'] if swiglu else 'compact',
                    output_layout=profile['output_layout'] if swiglu else 'compact',
                    activation_fifo_depth=profile['swiglu_activation_fifo_depth' if swiglu else 'down_activation_fifo_depth'],
                    worker_stack_size=4096 if profile['mmul_m_reuse'] == 2 else 2048)
                assert all(manifest[k] == value for k, value in expected.items()), ('selected profile mismatch', path)
            report['selected_artifacts'][path] = item
    report.update(status='passed', completion_totals=dict(completions),
        passing_npu_completions=completions['passing_correctness'] + completions['passing_benchmarks'],
        retained_failed_run_completions=completions['failed_correctness'] + completions['failed_benchmarks'],
        max_passing_relative_l2=strict_max_l2, max_passing_absolute_error=strict_max_abs,
        referenced_historical_binary_pairs_not_archived=[list(v) for v in sorted(missing_historical)])
    audit_final_selection(args, evidence, report)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status','completion_totals','passing_npu_completions',
        'retained_failed_run_completions','max_passing_relative_l2','max_passing_absolute_error')}, indent=2))
    print(args.output)


if __name__ == '__main__':
    main()
