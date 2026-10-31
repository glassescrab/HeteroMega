"""Package a prebuilt merged graph, or build it explicitly with the IRON Python.

Standard library only. This utility is not imported by model inference.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def package(artifact_dir, output):
    artifact_dir, output = Path(artifact_dir).resolve(), Path(output).resolve()
    manifest = json.loads((artifact_dir / 'final.xclbin.json').read_text())
    if manifest.get('kind') != 'w4a16_upstream_merged' or manifest.get('mode') != 'merged':
        raise ValueError('expected the complete merged FFN artifact')
    for name, field in (('final.xclbin', 'xclbin_sha256'), ('insts.bin', 'insts_sha256')):
        data = (artifact_dir / name).read_bytes()
        if not data or hashlib.sha256(data).hexdigest() != manifest[field]:
            raise ValueError(f'empty or mismatched artifact: {name}')
        if name == 'insts.bin' and (len(data) % 4 or len(data) > 0xffffffff):
            raise ValueError('instruction length must be whole uint32 words and fit uint32 bytes')
    # The C++ loader additionally validates all geometry, layouts and selected graph flags.
    result = dict(artifact_dir=str(artifact_dir), accuracy_policy='report', timeout_ms=10000, device_index=0)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--artifact-dir', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--build', action='store_true', help='explicitly compile; otherwise only verify/package existing files')
    ap.add_argument('--iron-python', type=Path)
    ap.add_argument('--m', type=int, default=512)
    ap.add_argument('--hidden', type=int, default=4096)
    ap.add_argument('--intermediate', type=int, default=14336)
    ap.add_argument('--npu-channels', type=int, default=6400)
    args = ap.parse_args()
    if args.build:
        if not args.iron_python:
            ap.error('--build requires --iron-python; preserve the supplied IRON environment')
        if (args.m <= 0 or args.m % 512 or args.hidden <= 0 or args.hidden % 128 or
                args.intermediate <= 0 or args.intermediate % 128 or args.npu_channels <= 0 or
                args.npu_channels % 256 or args.npu_channels >= args.intermediate or args.npu_channels > 8192):
            ap.error('unsupported selected-graph geometry/partition')
        root = Path(__file__).resolve().parents[2]
        graph = root / 'npu/ffn/w4a16_merged_upstream.py'
        directory = args.artifact_dir.resolve()
        directory.mkdir(parents=True, exist_ok=True)
        # Keep a venv's bin/python symlink: resolving it can select system Python
        # and lose the IRON packages installed in that environment.
        command = [str(args.iron_python.absolute()), str(graph), '--mode', 'merged',
            '-M', str(args.m), '-K', str(args.hidden), '-N', str(args.npu_channels),
            '--weight-k', str(args.hidden), '--weight-n', str(args.intermediate),
            '--weight-k-down', str(args.intermediate), '--weight-n-down', str(args.hidden),
            '-co', '8', '--max-reuse', '4', '--arithmetic', 'bfp16',
            '--segment-pipeline-depth', '2', '--activation-fifo-depth', '2',
            '--z-output-fifo-depth', '1', '--y-output-fifo-depth', '1',
            '--vector-zero', '--bfp16-native-layout', '--split-m32-a', '--preconvert-b',
            '--xclbin-path', str(directory / 'final.xclbin'),
            '--insts-path', str(directory / 'insts.bin'), '--pdi-path', str(directory / 'final.pdi')]
        with (directory / 'compile.log').open('w') as log:
            subprocess.run(command, cwd=graph.parent, stdout=log, stderr=subprocess.STDOUT, check=True)
    print(json.dumps(package(args.artifact_dir, args.output), indent=2))


if __name__ == '__main__':
    main()
