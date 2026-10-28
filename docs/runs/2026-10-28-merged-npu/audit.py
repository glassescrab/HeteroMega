#!/usr/bin/env python3
"""Audit the merged-NPU P6400 comparison and sweep evidence."""
import argparse, hashlib, json, pathlib

def sha(path): return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def require(cond, msg):
    if not cond: raise AssertionError(msg)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--evidence-dir', type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent)
    ap.add_argument('--output', type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent/'audit.json')
    args=ap.parse_args(); root=args.evidence_dir
    sources=json.loads((root/'source_manifest.json').read_text())
    repo=root.parents[2]
    checks=[]
    for rel,digest in sources['files'].items():
        require(sha(repo/rel)==digest, f'source changed: {rel}')
    for rel,digest in sources['evidence'].items():
        require(sha(root/rel)==digest, f'evidence changed: {rel}')
    checks.append(f"{len(sources['files'])} source and {len(sources['evidence'])} evidence hashes")

    jobs={name: json.loads((root/name).read_text()) for name in
          ('b0_native.json','b0_p6400.json','b1_p6400.json','b1_native.json')}
    fixtures=set()
    for name, report in jobs.items():
        cfg=report['config']
        require(report['status']=='completed_with_accuracy_deviations', f'{name} status')
        require(report['accuracy']['accepted'] is True and
                report['accuracy']['accuracy_status']=='reported_deviations', f'{name} accuracy policy')
        if 'npu_channels' in cfg:
            require(cfg['npu_channels']==6400 and cfg['gpu_variant']=='teammate' and
                    cfg['warmup']==5 and cfg['iterations']==100, f'{name} config')
            require(report['npu']['merged_kernel'] is True and
                    report['npu']['launches_per_run']==1, f'{name} merged metadata')
            require(report['stats']['concurrent']['count']==100, f'{name} samples')
            weights=tuple(report['original_weight_buffers'][k]['sha256'] for k in ('gate','up','down'))
            inputs=tuple(report['input_sha256'])
        else:
            require(cfg['npu_rows']==256 and cfg['iterations']==100, f'{name} native config')
            weights=tuple(report['native_packed_weight_sha256'])
            inputs=tuple(report['input_sha256'])
        require(len(weights)==3 and len(inputs)==3, f'{name} fixture')
        fixtures.add((weights,inputs))
    require(len(fixtures)==1, 'fixtures differ across merged/native jobs')
    checks.append('job config/accepted deviations/fixtures')

    def med(name):
        r=jobs[name]
        return r['stats']['concurrent']['median_us'] if 'npu_channels' in r['config'] else r['stats']['native']['median_us']
    def ctrl(name):
        r=jobs[name]
        return r['stats']['baseline']['median_us']
    pairs=[('b0_native.json','b0_p6400.json'),('b1_native.json','b1_p6400.json')]
    ratios=[]
    for native,merged in pairs:
        n,m=med(native),med(merged)
        require(m<n, f'{merged} did not beat {native}')
        ratios.append(n/m)
    require(ratios[0]>1.08 and ratios[1]>1.08, 'merged win below 8% in a block')
    controls=[ctrl('b0_native.json')/ctrl('b0_p6400.json'),
              ctrl('b1_native.json')/ctrl('b1_p6400.json')]
    require(all(0.98<value<1.02 for value in controls), 'GPU controls drifted')
    checks.append('two reversed confirmation blocks favor merged by >8% with matched controls')

    exact=json.loads((root/'p4352_exact_compare.json').read_text())
    require(exact['records'] and all(r['merged_vs_two_launch_exact'] is True and
            r['merged_vs_two_launch_relative_l2']==0.0 for r in exact['records']),
            'merged output is not bit-exact to two-launch at P4352')
    checks.append('P4352 merged output bit-exact to two-launch')

    sweep={p: json.loads((root/f'p{p}_partition.json').read_text())['stats']['concurrent']['median_us']
           for p in (4352,6144,6400,6656)}
    require(min(sweep,key=sweep.get)==6400, f'P6400 is not the sweep minimum: {sweep}')
    require(abs(sweep[6400]-13866.815)<1e-6, 'P6400 sweep median changed')
    checks.append('P sweep minimum at P6400')

    result=dict(passed=True, checks=checks,
        medians=dict(native_b0=med('b0_native.json'), merged_b0=med('b0_p6400.json'),
                     merged_b1=med('b1_p6400.json'), native_b1=med('b1_native.json')),
        ratios=dict(block0=ratios[0], block1=ratios[1]),
        controls=dict(block0=controls[0], block1=controls[1]),
        sweep_ms=sweep,
        scope='synthetic complete prefill FFN; report-policy numerical deviations; not model accuracy')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
