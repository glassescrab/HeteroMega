from pathlib import Path
import hashlib, json, shutil, subprocess, sys, tarfile
root=Path.cwd(); out=root/'evidence'
out.mkdir(exist_ok=True)
for arithmetic in ('bf16','bfp16'):
    report=json.loads((root/'results'/f'{arithmetic}_model.json').read_text())
    assert report['status']=='passed'
    for stage, artifact in report['cases'][0]['artifacts'].items():
        src=Path(artifact['xclbin']).parent
        dst=out/'prebuilt'/arithmetic/stage
        shutil.copytree(src,dst,dirs_exist_ok=True)
        dis=out/'disassembly'/arithmetic/stage
        dis.mkdir(parents=True,exist_ok=True)
        for col in (0,1):
            path=dst/'final.prj'/f'elfs_main_core_{col}_2'/f'elfs_main_core_{col}_2.elf'
            assert path.is_file(),path
            with (dis/(path.name+'.dis')).open('w') as f:
                subprocess.run(['/home/mliraie/mlir-aie/ironenv/lib/python3.12/site-packages/llvm-aie/bin/llvm-objdump','-d',str(path)],stdout=f,check=True)
shutil.copytree(root/'results',out/'results',dirs_exist_ok=True)
for directory in ('npu/ffn','experiments/ffn_partition'):
    dst=out/'sources'/directory;dst.mkdir(parents=True,exist_ok=True)
    for p in (root/directory).iterdir():
        if p.suffix in ('.py','.cc','.h'):shutil.copy2(p,dst/p.name)
(out/'environment.json').write_text(json.dumps({'python':sys.version,'uname':subprocess.check_output(['uname','-a'],text=True),'toolchain_commit':'7e00b57955e108fe9d8e9419f5828a0c7e650858'},indent=2)+'\n')
hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='SHA256SUMS.json'}
(out/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
archive=Path('/notebooks/upstream-bfp16-evidence-20261027.tar.gz')
with tarfile.open(archive,'w:gz') as t:t.add(out,arcname='upstream-bfp16-evidence-20261027')
print(archive,archive.stat().st_size, len(hashes))
