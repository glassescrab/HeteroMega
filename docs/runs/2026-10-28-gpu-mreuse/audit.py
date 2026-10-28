#!/usr/bin/env python3
"""Audit the rejected GPU M-reuse 2 kernel experiment."""
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

    m=json.loads((root/'mreuse2_p6400.json').read_text())
    g=json.loads((root/'generic_p6400_reference.json').read_text())
    require(m['config']['npu_channels']==6400 and m['gpu']['gemm_mreuse']==2 and
            m['gpu']['prefill_gemm'].endswith('MREUSE=2'), 'M-reuse report config differs')
    require(m['status']=='completed_with_accuracy_deviations' and
            m['accuracy']['accepted'] is True, 'M-reuse accuracy state differs')
    require(g['config']['npu_channels']==6400, 'generic reference P differs')
    mw=m['stats']['concurrent']['median_us']; gw=g['stats']['concurrent']['median_us']
    ms=m['stats']['serial']['median_us']; gs=g['stats']['serial']['median_us']
    require(mw>gw and ms>gs, 'M-reuse unexpectedly beat the generic kernel')
    require(abs(gw-13866.815)<1e-6, 'generic P6400 reference changed')
    checks.append('M-reuse 2 is slower concurrent and serialized')

    src=(repo/'src/hipkernels/w4a16_gemm_packed.cu').read_text()
    require('w4a16_gemm_rocwmma_packed_mt' in src and 'HETEROMEGA_GPU_MREUSE == 2' in src,
            'M-reuse kernel source missing')
    tm=(repo/'experiments/ffn_partition/teammate_gpu.py').read_text()
    require('HETEROMEGA_GPU_MREUSE", "1"' in tm, 'M-reuse is no longer opt-in')
    checks.append('M-reuse is opt-in and generic default remains')

    result=dict(passed=True, checks=checks,
        generic_ms=dict(concurrent=gw, serial=gs),
        mreuse2_ms=dict(concurrent=mw, serial=ms),
        controls_ms=dict(generic=g['stats']['baseline']['median_us'],
                         mreuse2=m['stats']['baseline']['median_us']),
        scope='isolated synthetic FFN; packed GPU kernel experiment; not model accuracy')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
