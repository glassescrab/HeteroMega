#!/usr/bin/env bash
# Bounded source snapshot build; no kernel, firmware, driver or system-package changes.
set -Eeuo pipefail
umask 022
PAYLOAD_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BASELINE_ROOT="${HETEROMEGA_NATIVE_BASELINE_ROOT:-/notebooks/HeteroMosaic-baseline-20261027}"
RUNTIME_PYTHON="${HETEROMEGA_NATIVE_PYTHON:-/notebooks/heteromega-ffn-venv/bin/python}"
ROCM_INSTALL=/opt/rocm-7.2.0
BASE_REVISION=61714a3147f34857aa5dfef21a28e762777a2df0
DRIVER_REVISION=0e6d303b2cc2b3fe1cf10aba0acbf57a422588fb
export BASELINE_ROOT RUNTIME_PYTHON ROCM_INSTALL BASE_REVISION DRIVER_REVISION PAYLOAD_ROOT
[[ -x "$RUNTIME_PYTHON" ]] || { echo "Missing configured ROCm Python: $RUNTIME_PYTHON" >&2; exit 2; }
(cd "$PAYLOAD_ROOT" && sha256sum --check SHA256SUMS)
if [[ -e "$BASELINE_ROOT" ]]; then
    echo "Refusing to overwrite existing baseline: $BASELINE_ROOT. Use a fresh HETEROMEGA_NATIVE_BASELINE_ROOT for a retry." >&2
    exit 2
fi
mkdir -p "$BASELINE_ROOT/build-evidence"
exec > >(tee "$BASELINE_ROOT/build-evidence/bootstrap.log") 2>&1
trap 'build_rc=$?; printf "{\"exit_code\":%d}\n" "$build_rc" > "$BASELINE_ROOT/build-evidence/bootstrap-status.json"' EXIT
cp -a "$PAYLOAD_ROOT/source/." "$BASELINE_ROOT/"
cp -a "$PAYLOAD_ROOT/dependencies" "$BASELINE_ROOT/libraries"
cp -a "$PAYLOAD_ROOT/patches" "$BASELINE_ROOT/build-evidence/patches"
cp "$PAYLOAD_ROOT/payload_manifest.json" "$BASELINE_ROOT/build-evidence/"
cp "$PAYLOAD_ROOT/SHA256SUMS" "$BASELINE_ROOT/build-evidence/payload-SHA256SUMS"
cp "$PAYLOAD_ROOT/bootstrap.sh" "$BASELINE_ROOT/build-evidence/bootstrap.sh"
cd "$BASELINE_ROOT"
# This is a bounded source snapshot, not a fabricated checkout of BASE_REVISION.
git init --initial-branch=baseline-source-snapshot .
printf '/build/\n/build-evidence/\n/libraries/\n/BUILD_PROVENANCE.json\n' >> .git/info/exclude
git add CMakeLists.txt include src hw_bins LICENSE THIRD_PARTY_NOTICES.md
GIT_AUTHOR_DATE='2000-01-01T00:00:00+0000' GIT_COMMITTER_DATE='2000-01-01T00:00:00+0000' 
export GIT_AUTHOR_DATE GIT_COMMITTER_DATE
git -c user.name='HeteroMega baseline snapshot' -c user.email='baseline-snapshot@invalid' \
    commit -m "Bounded source snapshot of $BASE_REVISION (not original history)"
unset GIT_AUTHOR_DATE GIT_COMMITTER_DATE
export HOME_LIBS="$BASELINE_ROOT/libraries"
export HETEROMOSAIC_ROOT="$BASELINE_ROOT"
export HETEROMEGA_ROCM_PATH="$ROCM_INSTALL"
export ROCM_PATH="$ROCM_INSTALL"
export ROCM_HOME="$ROCM_INSTALL"
export PYTORCH_ROCM_ARCH=gfx1150
export PATH="$(dirname "$RUNTIME_PYTHON"):$ROCM_INSTALL/bin:$PATH"
export LD_LIBRARY_PATH="$ROCM_INSTALL/lib:/opt/xilinx/xrt/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MAX_JOBS=2
unset HSA_OVERRIDE_GFX_VERSION PYTHONPATH LD_PRELOAD
# Read-only probes precede the sole conditional Python package installation.
"$RUNTIME_PYTHON" - <<'PY'
import importlib.util,json,os,pathlib,platform,shutil,subprocess,sys,sysconfig
import torch,numpy
root=pathlib.Path(os.environ['BASELINE_ROOT']);rocm=pathlib.Path(os.environ['ROCM_INSTALL'])
commands={name:shutil.which(name) for name in ('cmake','g++','make','ninja','git','sha256sum','ldd','nm','readelf')}
required=[rocm/'lib/llvm/bin/clang++',rocm/'include/hip/hip_runtime.h',rocm/'include/rocwmma/rocwmma.hpp',rocm/'lib/libhsa-runtime64.so',rocm/'lib/libamdhip64.so',pathlib.Path('/usr/include/libdrm/drm.h'),pathlib.Path(sysconfig.get_path('include'))/'Python.h',root/'libraries/xdna-driver-05-19-25/src/include/uapi/drm_local/amdxdna_accel.h']
info=dict(python=sys.version,python_executable=sys.executable,torch=str(torch.__version__),torch_hip=torch.version.hip,numpy=numpy.__version__,platform=platform.platform(),commands=commands,files={str(p):p.exists() for p in required},pybind11_present=importlib.util.find_spec('pybind11') is not None,torch_cxx11_abi=bool(torch._C._GLIBCXX_USE_CXX11_ABI),environment={k:os.environ.get(k) for k in ('HOME_LIBS','HETEROMOSAIC_ROOT','ROCM_PATH','PYTORCH_ROCM_ARCH','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS')})
(root/'build-evidence/dependency-probe.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info,indent=2))
missing=[str(p) for p in required if not p.exists()]+[name for name,p in commands.items() if not p]
if not torch.version.hip:missing.append('ROCm Torch')
if missing:raise SystemExit('Missing prerequisites (no system installation attempted): '+', '.join(missing))
subprocess.run(['g++','-print-file-name=libgomp.so'],check=True)
PY
if ! "$RUNTIME_PYTHON" -c 'import pybind11' >/dev/null 2>&1; then
    "$RUNTIME_PYTHON" -m pip install --disable-pip-version-check --no-deps pybind11==3.1.0 \
        2>&1 | tee build-evidence/install-pybind11.log
fi
"$RUNTIME_PYTHON" -m pip freeze > build-evidence/packages.txt
# Keep both saved patches intact in evidence. Only the old force-include pathname
# is relocated into this isolated build; the compatibility header is byte-identical.
"$RUNTIME_PYTHON" - <<'PY'
import os,pathlib
root=pathlib.Path(os.environ['BASELINE_ROOT']);old='/notebooks/heteromega-baseline-logs/torch211-hip-compat.hpp'
source=(root/'build-evidence/patches/cloud-build.patch').read_text()
assert source.count(old)==1
new=str(root/'build-evidence/patches/torch211-hip-compat.hpp')
(root/'build-evidence/cloud-build-relocated.patch').write_text(source.replace(old,new))
PY
git apply --check build-evidence/cloud-build-relocated.patch
git apply --check build-evidence/patches/runtime-compat.patch
git apply build-evidence/cloud-build-relocated.patch
git apply build-evidence/patches/runtime-compat.patch
git diff --binary > build-evidence/applied-source.patch
git status --short > build-evidence/source-status.txt
git rev-parse HEAD > build-evidence/source-snapshot-commit.txt
"$RUNTIME_PYTHON" - <<'PY'
import hashlib,json,os,pathlib,subprocess
root=pathlib.Path(os.environ['BASELINE_ROOT']);payload=pathlib.Path(os.environ['PAYLOAD_ROOT'])
files=[p for rel in ('src','include','hw_bins') for p in (root/rel).rglob('*') if p.is_file()]+[root/'CMakeLists.txt']
provenance=dict(original_repository='https://github.com/glassescrab/HeteroMega',original_revision=os.environ['BASE_REVISION'],snapshot_git_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),snapshot_note='New local commit records only the bounded pinned file selection; it is not the original git commit. Compatibility patches remain uncommitted.',xdna_uapi_revision=os.environ['DRIVER_REVISION'],payload_manifest_sha256=hashlib.sha256((payload/'payload_manifest.json').read_bytes()).hexdigest(),source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},patch_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'build-evidence').rglob('*.patch'))})
(root/'BUILD_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')
PY
PYBIND_CMAKE_DIR="$("$RUNTIME_PYTHON" -m pybind11 --cmakedir)"
cmake_args=(-S "$BASELINE_ROOT" -B "$BASELINE_ROOT/build"
    "-DPython_EXECUTABLE=$RUNTIME_PYTHON"
    -DCMAKE_HIP_ARCHITECTURES=gfx1150
    "-DCMAKE_HIP_COMPILER=$ROCM_INSTALL/lib/llvm/bin/clang++"
    "-Dpybind11_DIR=$PYBIND_CMAKE_DIR"
    "-DCMAKE_PREFIX_PATH=$ROCM_INSTALL"
    "-DCMAKE_CXX_FLAGS=-isystem $ROCM_INSTALL/include"
    "-DCMAKE_HIP_FLAGS=-isystem $ROCM_INSTALL/include --hip-path=$ROCM_INSTALL --rocm-path=$ROCM_INSTALL"
    "-DCMAKE_EXE_LINKER_FLAGS=-L$ROCM_INSTALL/lib -Wl,-rpath,$ROCM_INSTALL/lib"
    "-DCMAKE_SHARED_LINKER_FLAGS=-L$ROCM_INSTALL/lib -Wl,-rpath,$ROCM_INSTALL/lib"
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON)
printf '%q ' cmake "${cmake_args[@]}" > build-evidence/configure-command.txt
printf '\n' >> build-evidence/configure-command.txt
cmake "${cmake_args[@]}" 2>&1 | tee build-evidence/configure.log
cmake --build "$BASELINE_ROOT/build" -j2 --target unified_llm_w4a16_hetero_libtorch \
    2>&1 | tee build-evidence/build.log
NATIVE_LIBRARY="$BASELINE_ROOT/build/py/unified_llm_w4a16/unified_llm_w4a16_hetero_libtorch.so"
export NATIVE_LIBRARY
[[ -f "$NATIVE_LIBRARY" ]]
ldd "$NATIVE_LIBRARY" > build-evidence/library-ldd.txt
readelf -d "$NATIVE_LIBRARY" > build-evidence/library-dynamic.txt
nm -D -C "$NATIVE_LIBRARY" > build-evidence/library-symbols.txt
"$RUNTIME_PYTHON" - <<'PY'
import hashlib,json,os,pathlib
root=pathlib.Path(os.environ['BASELINE_ROOT']);lib=pathlib.Path(os.environ['NATIVE_LIBRARY'])
text=(root/'build-evidence/library-ldd.txt').read_text()
if 'not found' in text:raise SystemExit('Unresolved shared-library dependency; see library-ldd.txt')
symbols=(root/'build-evidence/library-symbols.txt').read_text()
for required in ('hetero_matmul_out_gemm_packed_M','hipkernels::w4a16_gemm_fused_packed','initialize_xdna_driver','wait_for_npu_command'):
 if required not in symbols:raise SystemExit('Missing exported native adapter symbol '+required)
result=dict(status='built_not_executed',library=str(lib),library_bytes=lib.stat().st_size,library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),native_root=str(root),driver_include=str(root/'libraries/xdna-driver-05-19-25/src/include/uapi/drm_local'))
(root/'build-evidence/build-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
PY
# Compilation and dependency/symbol validation are complete. No GPU/NPU inference
# is run here; launch the independently validated native FFN harness separately.
