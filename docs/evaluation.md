# Prefill evaluation

> **2026-10-31 update:** Main C now has a cloud-validated C++ model endpoint;
> follow [GPU + NPU FFN testing](ffn-teammate-testing.md). The batch runner below
> still has only its original three methods. It has not been extended to select
> the merged endpoint or record merged completion counts. Clear
> `HETEROMEGA_FFN_CONFIG` before all original-method jobs so inherited state
> cannot activate the candidate in a control. Model smoke timing is diagnostic
> and differs from this runner's synchronized generate(1) measurement boundary.

Reuse `kernels/gpu/tools/run_model_ffn.py` from GPU PR #1: one excluded warmup,
then five measured pairs of synchronized `generate(1)` / `generate(64)` calls.
The primary time includes first-token selection and Python call overhead; it is
**not** the older profiler's C++ forward-only timer. Model loading is excluded.
No GPU/NPU kernels or model execution code are changed by this evaluation work.

The full experiment plan includes pending implementations, not just CLI choices:

| Experiment | Comparison / method | Current integration |
| --- | --- | --- |
| Main A | Original GPU-only (`gpu_original`) | Wired; no new hardware measurements |
| Main B | Original HeteroMosaic GPU+NPU (`heteromosaic`) | Wired; working NPU runtime required |
| Main C | Our persistent FFN GPU+NPU | C++ endpoint and cloud deployment checks complete; batch-runner method/counter wiring pending |
| GPU sanity | Original GPU FFN vs our all-GPU FFN (`gpu_original` vs `gpu_ffn_all`) | Model runner wired; reuse PR #1 FFN tests/benchmarks |
| NPU sanity | Original NPU FFN vs our all-NPU FFN | Pending both equivalent full-FFN endpoints |

Main A/B/C compare complete prefill latency and output agreement on identical
weights/inputs. GPU sanity reuses Main A rather than duplicating that baseline.
Both sanity checks compare identical FFN work: output error against the same
reference and complete FFN latency, then model logits/tokens where integrated.
Token agreement is only a regression check. These controls distinguish device
implementation changes from gains due to GPU/NPU cooperation.

All-GPU/all-NPU here means all FFN channels; attention keeps its existing path.
The original runtime's `npu` setting does not establish a complete NPU-only FFN:
its GPU activation/down work must be accounted for in an equivalent endpoint.
Pending entries are documented plans, not runnable CLI methods or measured results.
Main C will sweep supported channel splits and input lengths after integration.
PR #1's partial-GPU mode omits the NPU output, so this runner clears its override.
Existing kernel tests/microbenchmarks stay in their current tools.

From the repository root (a fresh output directory for each experiment):

```bash
# Mac/CPU: inspect the commands without importing Torch or loading a model.
python3 kernels/gpu/tools/evaluate_prefill.py --out build/eval-preview --prompt-tokens 128 512 1024 --dry-run
python3 -m unittest discover -s kernels/gpu/tools -p test_evaluate_prefill.py -v
# AMD/Linux: use the existing PR #1 build/environment and real AWQ model directory.
python3 kernels/gpu/tools/evaluate_prefill.py --model /path/to/AWQ --out build/eval-gpu --prompt-tokens 128 512 1024
# Add the original heterogeneous baseline only with a working NPU runtime/firmware.
python3 kernels/gpu/tools/evaluate_prefill.py --model /path/to/AWQ --out build/eval-three --methods gpu_original gpu_ffn_all heteromosaic
python3 kernels/gpu/tools/evaluate_prefill.py --out build/eval-gpu --summarize
```

Defaults alternate process order (original/new/new/original), with one model
load and warmup per process; `--rounds`, `--reps`, `--build`, `--config` and
`--new-tokens` are adjustable. Configuration scheduling is preserved. All methods
use the same token prefix, weights, quantization and requested output count.
The bundled reference has 1024 tokens; 2048/4096 require a longer `--ref` with
real input IDs and its corresponding reference output, not repeated/padded IDs.
Shortened prompts have no historical output reference; compare their methods.

Each process saves a log, effective config and result JSON. `summary.csv` groups
by method/length: sample count, median/min/max ms, speedup versus original GPU,
token agreement and GPU FFN activation. A speedup of 1.10 means 1.10x as fast.
Token mismatch, a failed historical reference or an inactive new FFN suppresses
the speedup cell. Token agreement is a regression check, not numerical accuracy.
NPU execution stays `unverified`: enabling `hetero` does not establish successful
NPU completions. Confirm these separately before reporting a heterogeneous gain;
use pinned XDNA headers, not PR #1's GPU-only `SYSTEM_XDNA_HEADER=1` build shortcut.
Keep power/thermal conditions and background load comparable. `--dummy` is only
a timing smoke check. This local change has no new AMD measurements.
