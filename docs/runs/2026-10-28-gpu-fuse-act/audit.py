#!/usr/bin/env python3
"""Audit the rejected fused gate/up activation epilogue."""
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

    f=json.loads((root/'fused_p6400.json').read_text())
    g=json.loads((root/'generic_p6400_reference.json').read_text())
    d=json.loads((root/'debug_epilogue.json').read_text())
    require(f['config']['npu_channels']==6400 and f['gpu']['fuse_activation']==1 and
            f['gpu']['prefill_gemm'].endswith('FUSE_ACT=1'), 'fused report config differs')
    require(f['status']=='completed_with_accuracy_deviations' and
            f['accuracy']['accepted'] is True, 'fused accuracy state differs')
    require(d['exact'] is True and d['mismatch_count']==0 and d['max_abs']==0.0,
            'fused epilogue is not bit-exact')
    checks.append('fused epilogue is bit-exact to silu_mul')
    fw=f['stats']['concurrent']['median_us']; gw=g['stats']['concurrent']['median_us']
    fs=f['stats']['serial']['median_us']; gs=g['stats']['serial']['median_us']
    require(fw>gw and fs>gs, 'fused epilogue unexpectedly beat the generic path')
    require(abs(gw-13866.815)<1e-6, 'generic P6400 reference changed')
    checks.append('fused epilogue is slower concurrent and serialized')

    tm=(repo/'experiments/ffn_partition/teammate_gpu.py').read_text()
    require('HETEROMEGA_GPU_FUSE_ACT", "0"' in tm, 'fusion is no longer opt-in')
    gf=(repo/'kernels/gpu/src/gpu_ffn.cpp').read_text()
    require('HETEROMEGA_GPU_FUSE_ACT 0' in gf, 'gpu_ffn fusion default changed')
    checks.append('fusion is opt-in and generic default remains')

    result=dict(passed=True, checks=checks,
        generic_ms=dict(concurrent=gw, serial=gs),
        fused_ms=dict(concurrent=fw, serial=fs),
        debug=dict(exact=d['exact'], mismatch_count=d['mismatch_count']),
        scope='isolated synthetic FFN; fused GPU epilogue experiment; not model accuracy')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
