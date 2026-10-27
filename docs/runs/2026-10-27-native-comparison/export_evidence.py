from pathlib import Path
from hashlib import sha256
import json,shutil,tarfile
root=Path('/notebooks/HeteroMega-native-comparison-20261027')
base=Path('/notebooks/HeteroMosaic-baseline-20261027')
out=Path('/notebooks/native-faithful-comparison-evidence-20261027')
if out.exists(): raise SystemExit('Refusing to overwrite evidence directory')
out.mkdir()
def cp(src,dst):
 src=Path(src);dst=out/dst
 if not src.exists(): return
 dst.parent.mkdir(parents=True,exist_ok=True)
 if src.is_dir():shutil.copytree(src,dst)
 else:shutil.copy2(src,dst)
cp(root/'results','results')
cp(root/'source_provenance.json','source_provenance.json')
cp(root/'report_policy_source_provenance.json','report_policy_source_provenance.json')
for d in ('experiments/ffn_partition','npu/ffn','src/hipkernels','include/hipkernels'):
 for p in (root/d).glob('*'):
  if p.is_file() and p.suffix in ('.py','.cc','.cpp','.hpp','.h','.cu'):cp(p,Path('sources')/p.relative_to(root))
cp(base/'BUILD_PROVENANCE.json','baseline/BUILD_PROVENANCE.json')
cp(base/'build-evidence','baseline/build-evidence')
for p in json.loads((base/'BUILD_PROVENANCE.json').read_text())['source_sha256']:
 cp(base/p,Path('baseline/sources')/p)
cp(base/'libraries','baseline/libraries')
cp(base/'build/CMakeCache.txt','baseline/cmake/CMakeCache.txt')
cp(base/'build/compile_commands.json','baseline/cmake/compile_commands.json')
for name in ('flags.make','link.txt'):
 for p in (base/'build').rglob(name):cp(p,Path('baseline/cmake')/p.relative_to(base/'build'))
cp(base/'build/py/unified_llm_w4a16/unified_llm_w4a16_hetero_libtorch.so','baseline/native.so')
cp(Path.home()/'.cache/heteromega/native_ffn','native_binding_build')
cp(Path.home()/'.cache/heteromega/ffn_gpu','gpu_build')
for archive in ('native-heteromosaic-baseline-20261027.tar.gz','heteromega-native-comparison-20261027.tar.gz','native-diagnostic-20261027.tar.gz','native-diagnostic-v2-20261027.tar.gz','native-report-policy-20261027.tar.gz'):
 cp('/notebooks/'+archive,archive)
for name in ('native-baseline-bootstrap-20261027.log','native-ffn-pybind-install-20261027.log'):
 cp('/notebooks/'+name,Path('setup')/name)
cp(__file__,'export_evidence.py')
# Candidate artifacts are already archived in prior evidence; copy the four used
# cached directories so this comparison remains independently inspectable.
cache=Path('/notebooks/HeteroMega-upstream-partition-20261027/artifacts')
if cache.exists():
 for p in cache.glob('upstream_*'):
  if any(x in p.name for x in ('_n2560_','_n2816_','_k2560_','_k2816_')):cp(p,Path('artifacts')/p.name)
files={str(p.relative_to(out)):sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
(out/'SHA256SUMS.json').write_text(json.dumps(files,indent=2)+'\n')
archive=out.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(out.iterdir()):t.add(p,arcname=p.name)
print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha256(archive.read_bytes()).hexdigest(),files=len(files))))
