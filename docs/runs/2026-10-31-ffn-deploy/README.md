# C++ FFN deployment validation, October31

**Measured:** full C++/HIP/XRT executor and model builds succeed on AUP. All
required deployment jobs complete under explicit report policy. The deployed
implementation was tested uncommitted on `codex/ffn-cpp-deploy-20261031`, based
on e6ca183c; publication now includes the required sources on main. Original compute kernels are unchanged. See
[the deployment runbook](../../ffn-deployment.md) for reproduction.

Cloud root: `/notebooks/heteromega-deploy.eT0uOJ/HeteroMega-ffn-deploy`.
Environment: Ryzen AI HX370/Radeon890M, gfx1150, kernel6.17.0-42, ROCm7.2,
Torch2.11.0+rocm7.2, NumPy2.5.4, existing pinned IRON environment. Built-in
browser access worked in this new chat. The user approved the source upload
after automatic approval review initially rejected it. No credentials or model
weights were placed in the source/evidence bundles. Shared host driver/kernel,
baseline checkouts and Python environments were preserved. No commit/push.

## Measured results

| Job | Merged FFN completions | Native NPU calls | Result |
| --- | ---: | ---: | --- |
| Isolated C++ smoke, two layers/two streams | 30 | 0 | Accepted with numerical deviations |
| Real weights, GPU attention, 512 tokens/inflight1 | 64 | 0 | Completed under report policy |
| Real weights, GPU attention, 1024 tokens/inflight2 | 128 | 0 | Completed under report policy |
| Real weights, native attention, 1024 tokens/inflight1 | 128 | 640 | Completed under report policy |
| Real weights, native attention, 1024 tokens/inflight2 | 128 | 640 | Completed under report policy |

Smoke covers serial/concurrent branches, alternating/zero/repeated inputs,
caller-output guards, malformed inputs and counted completions. Strict GPU
controls and execution/integrity checks pass. Of90 numerical checks,24 remain
outside original tolerance. Worst relative L2: combined .0148590, GPU .00365177,
NPU .0215046; worst absolute errors .078125/.015625/.0703125 respectively.
Report mode retains all original error metrics and failed verdicts.

All four model jobs have finite logits, bit-exact cold/warm candidate repeats,
and zero new merged completions for decode/M256 fallback. Candidate versus
original logits **fail the fixed numerical tolerance**:

| Attention / workload | Relative L2 | Maximum absolute error |
| --- | ---: | ---: |
| GPU / 512 tokens | .0454436 | .46875 |
| GPU / 1024 tokens, inflight2 | .0375734 | .46875 |
| Native / 1024 tokens, inflight1 | .0861131 | 1.28125 |
| Native / 1024 tokens, inflight2 | .0861131 | 1.28125 |

Native coexistence is supported by counted execution, not a config flag. Each
job has three successful contexts,768 successful submissions/timeline waits,
zero submission/timeline failures, and640 native calls (768 total minus128
merged). The640 unsupported legacy waits use the documented fallback. Imports
report291 parameters plus15/35 buffers with zero failures; the inflight2 log
confirms two pipeline workers. The historical native down-GEMV5120>4096 fallback
is unchanged. These results validate the tested deployment path; they do not
establish pretrained accuracy, performance improvement or general runtime
coexistence across other workloads.

Five packaging tests pass on Linux, including the real-symlink regression, and
the portable C++ contract CTest passes. Optional exact Python-host parity was
not run: pyxrt is absent from the runtime import path and NumPy2.5.4 is outside
the recorded compatible readback setup. No packages were changed for that check.

## Fixes and retained failures

- Pybind11 enabled GCC slim LTO while HIP linked with LLVM. The initial build
  returned success but its module lacked `PyInit_heteromega_ffn_deploy`.
  `NO_EXTRAS` disables that automatic LTO; symbol inspection and import pass.
- The initial model module loaded system HIP5 and ROCm7.2 and aborted before
  FFN execution. Adding `CMAKE_MODULE_LINKER_FLAGS` relinked against HIP7.2;
  corrected model runs complete. The runbook now includes the missing flag.
- The first native-mode job silently fell back to GPU because the loader used
  its original-author default root. Its report said completed but the counter
  showed only128 merged submissions and zero native calls. Preserve
  `model-hetero-invalid-root.*` as **invalid coexistence evidence**. The model
  smoke now anchors `HETEROMOSAIC_ROOT` and requires `root/hw_bins/npu2`; the
  corrected jobs have verified native execution.

## Evidence and next step

- [Checked summary](deployment-results/cloud-summary.json),
  [environment](deployment-results/environment.json),
  [source/binary provenance](deployment-results/source-provenance.json).
- Raw job JSONs, logs, model config copies, portable-test logs, native ioctl
  counter, initial failures and exact tested source snapshots are in
  `deployment-results/`. `artifact/` retains the actual compiled XCLBIN/PDI,
  instructions, manifest and compiler log. Historical saved metadata below is
  separate from these new binaries.
- [Downloaded archive](cloud-evidence.tar.gz) SHA256:
  `72600d36a3d4fab9f1e0f9486d59eea85ac9f8d7b43ff9aae7f3ec42893edf1d`.
  This matches cloud output. All nine retained source files match the local
  worktree after CRLF/LF normalization.
- Raw logs/counters are retained here; UI screenshots remain local. Single
  cold/warm timings are retained
  as diagnostics only. Next work is optional exact host parity in a compatible
  isolated environment and paired end-to-end timing with fixed weights,
  schedules and attention interference. No speedup is inferred here.

## Earlier portable local checks

The following records predate the cloud run and are not hardware results.

- Native C++17 parser test compiled with Zig0.13, -Wall -Wextra -Werror; exit0.
  Valid shape/BO sizing/fallback/overflow checks pass;40 invalid contracts reject.
- Same compiled parser accepts saved M512/H4096/I14336/P6400 artifact metadata.
  saved-artifact-metadata/final.xclbin.json comes from the existing author
  October28 b0_p6400.json. No binaries were used in that earlier metadata-only check; its result alone
  makes no hash/execution claim. Actual cloud binaries are in artifact/ above.
- Four new Python packaging tests pass, including binary tampering, wrong graph
  and unaligned instruction rejection. Tests passed outside the Windows sandbox
  after its TemporaryDirectory ACL restrictions blocked fixture creation.
- Python compileall and Git whitespace checks pass.
- cloud-access.json records the earlier access failure before any deployment
  upload; the later cloud run above supersedes that blocker.

Tools were isolated in the outer workspace .tools; no system driver/kernel or
model environment changes. No commit/push. Generated binaries live under the
ignored build directory. None of these checks establish arithmetic correctness
or performance of the deployed kernel.
