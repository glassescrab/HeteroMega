#!/usr/bin/env python3
"""Audit the GPU-suffix autotune and torch-BF16 negative results."""
import argparse, hashlib, json, pathlib

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def require(c, m):
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

    log=(root/'autotune.log').read_text()
    require(log.count('selected=generic')==2, 'autotune did not select generic for both shapes')
    require('generic=7.9' in log and 'generic=3.9' in log, 'autotune generic timings missing')
    a=json.loads((root/'autotune_p6400.json').read_text())
    require(a['status']=='completed_with_accuracy_deviations' and
            a['gpu']['gemm_autotune']==1, 'autotune report state differs')
    checks.append('autotune selected generic for gate/up and down')

    t=json.loads((root/'torch_bf16_p6400.json').read_text())
    require(t['config']['gpu_variant']=='torch_bf16' and
            t['gpu']['backend']=='torch_bf16_dequantized_gpu_ffn' and
            t['status']=='completed_with_accuracy_deviations', 'torch report state differs')
    torch_serial=t['stats']['serial']['median_us']
    torch_concurrent=t['stats']['concurrent']['median_us']
    ref=json.loads((root/'teammate_p6400_reference.json').read_text())
    ref_serial=ref['stats']['serial']['median_us']; ref_concurrent=ref['stats']['concurrent']['median_us']
    require(torch_serial < ref_serial, 'torch BF16 was not faster serialized')
    require(torch_concurrent > ref_concurrent, 'torch BF16 unexpectedly won concurrent')
    checks.append('torch BF16 faster serialized but slower concurrent')
    require(abs(ref_concurrent-13866.815)<1e-6, 'teammate P6400 reference changed')

    source=(repo/'experiments/ffn_partition/teammate_gpu.py').read_text()
    require('HETEROMEGA_GPU_AUTOTUNE", "0"' in source, 'autotune is no longer opt-in')
    runner=(repo/'experiments/ffn_partition/run_merged_partition.py').read_text()
    require("default='teammate'" in runner, 'teammate GPU is no longer the default')
    checks.append('production defaults unchanged')

    result=dict(passed=True, checks=checks,
        autotune=dict(gate_up_generic_ms=7.90882, gate_up_selected='generic',
                      down_generic_ms=3.98001, down_selected='generic',
                      complete_ms=a['stats']['concurrent']['median_us']),
        torch_bf16=dict(serial_ms=torch_serial, concurrent_ms=torch_concurrent,
                        teammate_serial_ms=ref_serial, teammate_concurrent_ms=ref_concurrent),
        scope='isolated synthetic FFN; report-policy deviations; not model accuracy')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
