#!/usr/bin/env python3
"""Audit the rejected role-specialized split-Z experiments."""
import argparse, hashlib, json, pathlib

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(c,m):
    if not c: raise AssertionError(m)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--evidence-dir', type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent)
    ap.add_argument('--output', type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parent/'audit.json')
    args=ap.parse_args(); root=args.evidence_dir; repo=root.parents[2]
    sources=json.loads((root/'source_manifest.json').read_text())
    for rel,d in sources['files'].items(): require(sha(repo/rel)==d, f'source changed: {rel}')
    for rel,d in sources['evidence'].items(): require(sha(root/rel)==d, f'evidence changed: {rel}')
    checks=[f"{len(sources['files'])} source and {len(sources['evidence'])} evidence hashes"]
    ref=json.loads((root/'merged_p6400_reference.json').read_text())
    ref_wall=ref['stats']['concurrent']['median_us']
    require(abs(ref_wall-13866.815)<1e-6, 'merged P6400 reference changed')
    rows={}
    for name in ('torch_bf16_p8192.json','packed_p8192.json'):
        d=json.loads((root/name).read_text())
        require(d['config']['npu_channels']==8192, f'{name} P differs')
        require(d['status']=='passed' and d['accuracy']['passed'] is True and
                d['accuracy']['outside_tolerance_count']==0, f'{name} accuracy state differs')
        wall=d['stats']['concurrent']['median_us']
        require(wall > ref_wall, f'{name} unexpectedly beat the merged reference')
        c=[s for s in d['samples'] if s['mode']=='concurrent']
        rows[name]=dict(wall_ms=wall, serial_ms=d['stats']['serial']['median_us'],
            baseline_ms=d['stats']['baseline']['median_us'],
            npu_branch_ms=sum(s['diagnostics']['npu_branch_us'] for s in c)/len(c),
            output_stage_ms=sum(s['diagnostics']['output_stage_and_boundary_wait_us'] for s in c)/len(c),
            backend=d['gpu']['backend'])
    checks.append('both split variants are slower than P6400 and pass tolerance')
    result=dict(passed=True, checks=checks, merged_p6400_ms=ref_wall,
        split=rows, scope='isolated synthetic FFN; split-Z rejected on latency')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
