"""HeteroMosaic NPU GEMMs built from our MLIR-AIE W4A16 projection with the deployed merged-FFN arithmetic.

    python3 experiments/npu_align/hm_bins.py build --iron-python IRON_PY [--out hw_bins_ours]
    python3 experiments/npu_align/hm_bins.py config IN.json OUT.json [--prefix hw_bins_ours]

build: compiles npu/ffn/w4a16_upstream.py --mode projection (row-major A/Y, full 4352-byte-tile weights, args a, w, y)
for the gate/up and down shapes the CP2 configs place on the NPU, with the merged profile's flags, and copies PDI +
instructions under HeteroMosaic's file names (OUT/npu2/<family>/<dtype dir>/final_<M>x<K>x<N>_64x128x64_8c_bf16_int4AWQ_bf16.pdi, insts_....txt).
config: copies a HeteroMosaic config with the gate/up/down GEMM fw_path pointed at OUT (relative to HETEROMOSAIC_ROOT).
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
GRAPH = ROOT / 'npu/ffn/w4a16_upstream.py'
STEM = '64x128x64_8c_bf16_int4AWQ_bf16'
# (family dir, dtype dir, K, N, npuM values): gate/up, down. Down keeps HeteroMosaic's _K directory name.
SHAPES = [('8192x4096x14336', 'bf16_int4AWQ_bf16_M', 4096, 14336, (256, 512, 1024, 1280, 1536, 1792, 2048)),
          ('8192x14336x4096', 'bf16_int4AWQ_bf16_K', 14336, 4096, (256, 512, 1536))]
# Merged profile (experiments/ffn_deploy/prepare.py), mode projection instead of merged.
FLAGS = ['-co', '8', '--max-reuse', '4', '--arithmetic', 'bfp16', '--segment-pipeline-depth', '2',
         '--activation-fifo-depth', '2', '--output-fifo-depth', '1', '--mmul-m-reuse', '1', '--vector-zero',
         '--bfp16-native-layout', '--split-m32-a', '--preconvert-b',
         '--input-layout', 'row_major', '--output-layout', 'row_major']


def build(args):
    out = args.out.resolve()
    for family, dtype_dir, k, n, ms in SHAPES:
        for m in ms:
            work = out / 'build' / f'{m}x{k}x{n}'
            work.mkdir(parents=True, exist_ok=True)
            command = [str(args.iron_python), str(GRAPH), '--mode', 'projection', '-M', str(m), '-K', str(k), '-N', str(n),
                       '--weight-k', str(k), '--weight-n', str(n), *FLAGS, '--xclbin-path', str(work / 'final.xclbin'),
                       '--insts-path', str(work / 'insts.bin'), '--pdi-path', str(work / 'final.pdi')]
            start = time.perf_counter()
            with (work / 'compile.log').open('w') as log:
                subprocess.run(command, cwd=GRAPH.parent, stdout=log, stderr=subprocess.STDOUT, check=True)
            seconds = time.perf_counter() - start
            target = out / 'npu2' / family / dtype_dir
            target.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / 'final.pdi', target / f'final_{m}x{k}x{n}_{STEM}.pdi')
            shutil.copyfile(work / 'insts.bin', target / f'insts_{m}x{k}x{n}_{STEM}.txt')
            print(f'COMPILED {m}x{k}x{n} seconds={seconds:.1f} pdi_bytes={(work / "final.pdi").stat().st_size} '
                  f'insts_bytes={(work / "insts.bin").stat().st_size}', flush=True)


def config(args):
    cfg = json.loads(args.input.read_text())
    groups = [g['kernels'] for g in cfg.get('kernels_gemm_chunked', [])] + [cfg.get('kernels_gemm', [])]
    count = 0
    for kernels in groups:
        for kernel in kernels:
            path = kernel.get('fw_path', '')
            if kernel.get('layer') in ('gate', 'up', 'down') and any(
                    path.rstrip('/') == f'hw_bins/npu2/{family}/{dtype_dir}' for family, dtype_dir, *_ in SHAPES):
                kernel['fw_path'] = args.prefix + path[len('hw_bins'):]
                count += 1
    args.output.write_text(json.dumps(cfg, indent=2) + '\n')
    print(f'{args.output}: {count} gate/up/down GEMM entries -> {args.prefix}/')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--iron-python', type=Path, required=True)
    b.add_argument('--out', type=Path, default=ROOT / 'hw_bins_ours')
    c = sub.add_parser('config')
    c.add_argument('input', type=Path)
    c.add_argument('output', type=Path)
    c.add_argument('--prefix', default='hw_bins_ours')
    args = ap.parse_args()
    build(args) if args.cmd == 'build' else config(args)


if __name__ == '__main__':
    main()
