"""Export isolated optimization overlays, exact sources, binaries and raw results.

Run in the notebook after all measurements have completed. Does not collect
notebook configuration, credentials, model weights, or arbitrary home files.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import os
import shutil
import tarfile

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--notebooks-root', type=Path, default=Path('/notebooks'))
parser.add_argument('--cache-root', type=Path,
                    default=Path.home() / '.cache/heteromega')
parser.add_argument('--direct-output-root', type=Path)
parser.add_argument('--pybind-package-root', type=Path)
parser.add_argument('--dmabuf-build-root', type=Path,
                    default=os.environ.get('HETEROMEGA_DMABUF_BUILD_ROOT'))
args = parser.parse_args()
out = args.output
if out.exists():
    raise SystemExit('Refusing to overwrite evidence directory')
out.mkdir(parents=True)
notebooks = args.notebooks_root
collection = []


def digest(path):
    result = sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


# Only the explicitly listed overlays, compilation caches and header package
# below are traversed. Never scan the notebook home or a Python environment.
# Compiled instructions/PDI/XCLBIN files remain eligible; model checkpoints do
# not. These ignores also apply if an excluded file is placed in a cache.
ignored = shutil.ignore_patterns(
    '__pycache__', '.git', '.pytest_cache', '.ipynb_checkpoints',
    '.env', '.env.*', '*credentials*', '*.safetensors', '*.gguf',
    '*.pt', '*.pth', 'pytorch_model*', 'model_weights', 'model-weights',
)

def cp(src, dst):
    src, dst = Path(src), out / dst
    record = dict(source=str(src), destination=str(dst.relative_to(out)))
    if not src.exists():
        collection.append(dict(record, status='missing_optional'))
        return
    if dst.exists():
        raise RuntimeError(f'Duplicate evidence destination: {dst}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, ignore=ignored)
    else:
        shutil.copy2(src, dst)
    collection.append(dict(record, status='copied'))

for label, root in (
    ('shared', notebooks / 'HeteroMega-shared-ffn-20261027'),
    ('reuse4', notebooks / 'HeteroMega-reuse4-20261027'),
    ('native8', notebooks / 'HeteroMega-native8-20261027'),
    ('prefetch', notebooks / 'HeteroMega-prefetch-20261027'),
    ('direct-output', args.direct_output_root or
     notebooks / 'HeteroMega-direct-output-20261027'),
):
    for name in ('results', 'artifacts'):
        cp(root / name, Path(label) / name)
    for name in ('experiments/ffn_partition', 'npu/ffn', 'src/hipkernels',
                 'include/hipkernels', 'kernels/gpu'):
        for path in (root / name).rglob('*'):
            if path.is_file() and path.suffix in ('.py', '.cc', '.cpp', '.hpp', '.h', '.cu'):
                cp(path, Path(label) / 'sources' / path.relative_to(root))
    manifests = set()
    for pattern in ('*source*.json', '*manifest*.json', '*provenance*.json',
                    '*SHA256*.json', '*sha256*.json'):
        manifests.update(root.glob(pattern))
    for path in sorted(manifests):
        cp(path, Path(label) / path.name)
for pattern in ('heteromega-shared-*.tar.gz', 'heteromega-reuse4-*.tar.gz',
                'heteromega-native8-*.tar.gz', 'heteromega-diagnostics-*.tar.gz',
                'heteromega-prefetch-*.tar.gz', 'heteromega-direct-output-*.tar.gz',
                'heteromega-dmabuf-*.tar.gz',
                'native8-kernel-inspect.tar.gz', 'native8-aie-api.tar.gz',
                'native8-combined-compiler.tar.gz',
                'native8-register-a-experiment.tar.gz', 'installed-kernel-compiler.tar.gz',
                'xrt-sharing-api.tar.gz', 'preconvert-build-failure.tar.gz',
                'native-heteromosaic-baseline-20261027.tar.gz',
                'heteromega-native-comparison-20261027.tar.gz',
                'native-report-policy-20261027.tar.gz'):
    for path in sorted(notebooks.glob(pattern)):
        cp(path, Path('uploads') / path.name)
# Bounded compile-only control/candidate experiment. Its outputs establish
# compiler behavior, not NPU execution or a measured latency improvement.
cp(notebooks / 'native8-register-a-experiment', 'compiler-experiments/register-a')
for name, env in (
    ('ffn_gpu', 'HETEROMEGA_GPU_BUILD_ROOT'),
    ('ffn_teammate_gpu', 'HETEROMEGA_TEAMMATE_GPU_BUILD_ROOT'),
    ('native_ffn', 'HETEROMEGA_NATIVE_BUILD_ROOT'),
    ('shared_gpu', 'HETEROMEGA_SHARED_GPU_BUILD_ROOT'),
):
    cp(Path(os.environ.get(env, args.cache_root / name)), Path('builds') / name)
# Both the standalone XRT bridge and the Torch/HIP allocation extension use
# this cache, in fingerprint and hip-fingerprint subdirectories respectively.
cp(args.dmabuf_build_root or args.cache_root / 'dmabuf', 'builds/dmabuf')

# This is the isolated pip --target package, not the inference virtualenv.
# Preserve pybind's headers, package/CMake files and installation metadata so
# the XRT bridge's exact pybind registry can be reconstructed independently.
pybind_root = args.pybind_package_root or notebooks / 'heteromega-pybind213-build'
cp(pybind_root / 'pybind11', 'dependencies/pybind213/pybind11')
for path in sorted(pybind_root.glob('pybind11-*.dist-info')):
    cp(path, Path('dependencies/pybind213') / path.name)
if not list(pybind_root.glob('pybind11-*.dist-info')):
    collection.append(dict(source=str(pybind_root / 'pybind11-*.dist-info'),
                           destination='dependencies/pybind213', status='missing_optional'))
for relative in ('results/pybind213-install.log', 'pybind213-install.log'):
    cp(notebooks / 'HeteroMega-prefetch-20261027' / relative,
       Path('dependencies/pybind213/install-logs') / relative)
# An explicitly selected include tree can differ from the known pip target.
# Copy only its pybind11 subtree, never its parent site-packages directory.
if os.environ.get('HETEROMEGA_XRT_PYBIND_INCLUDE'):
    include = Path(os.environ['HETEROMEGA_XRT_PYBIND_INCLUDE'])
    cp(include / 'pybind11', 'dependencies/selected-pybind-include/pybind11')

base = notebooks / 'HeteroMosaic-baseline-20261027'
cp(base / 'BUILD_PROVENANCE.json', 'baseline/BUILD_PROVENANCE.json')
cp(base / 'build-evidence', 'baseline/build-evidence')
cp(base / 'build/py/unified_llm_w4a16/unified_llm_w4a16_hetero_libtorch.so', 'baseline/native.so')
if (base / 'BUILD_PROVENANCE.json').is_file():
    for name in json.loads((base / 'BUILD_PROVENANCE.json').read_text())['source_sha256']:
        source = (base / name).resolve()
        if not source.is_relative_to(base.resolve()):
            raise RuntimeError(f'Baseline source path escapes isolated tree: {name}')
        cp(source, Path('baseline/sources') / name)
cp(base / 'libraries/xdna-driver-05-19-25', 'baseline/libraries/xdna-driver-05-19-25')
cp(__file__, 'export_evidence.py')
(out / 'collection_manifest.json').write_text(json.dumps(dict(
    schema_version=1,
    scope='Isolated native-adaptation overlays and explicit compilation dependencies',
    entries=collection,
    exclusions='No notebook configuration, arbitrary home files, inference environments or model checkpoints',
), indent=2) + '\n')
files = {str(p.relative_to(out)): digest(p)
         for p in sorted(out.rglob('*')) if p.is_file()}
(out / 'SHA256SUMS.json').write_text(json.dumps(files, indent=2) + '\n')
archive = out.with_suffix('.tar.gz')
with tarfile.open(archive, 'w:gz') as tar:
    for path in sorted(out.iterdir()):
        tar.add(path, arcname=path.name)
print(json.dumps(dict(archive=str(archive), bytes=archive.stat().st_size,
                     sha256=digest(archive), files=len(files),
                     missing_optional=sum(x['status'] == 'missing_optional'
                                          for x in collection))))
