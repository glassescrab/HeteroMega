"""Run fixed-workload baselines and diagnostic traces; no model downloads."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('variant', choices=['gpu_native', 'gpu_matched', 'hetero_serial', 'hetero_pipeline', 'hetero_down_config'])
p.add_argument('--trace', choices=['none', 'host', 'sync'], default='none')
p.add_argument('--repeats', type=int, default=5)
p.add_argument('--tag', default='baseline')
p.add_argument('--torch-profile', action='store_true')
a = p.parse_args()
root = Path('/notebooks/HeteroMosaic-baseline')
outdir = Path('/notebooks/heteromega-profile-2026-10-14')
outdir.mkdir(exist_ok=True)
name = f'{a.variant}-{a.tag}-{a.trace}'
sys.path.insert(0, str(root / 'py/unified_llm_w4a16'))
import torch
from llama3_8b_w4a16_model import LLaMA3W4A16Model

c = json.loads((root / 'py/unified_llm_w4a16/configs/configs_strixP_llama3_8b.json5').read_text())
c.update(heterogeneity='gpu' if a.variant.startswith('gpu') else 'hetero',
         prompt_len=1024, usePreSavedWeights=False, warmup=False, debug_verbosity=0,
         trace_output_path='' if a.trace == 'none' else str(outdir / (name + '.stages.jsonl')),
         trace_run_tag=name, trace_sync_stages=a.trace == 'sync', stage_bubbles=[])
if a.variant == 'gpu_matched':
    c['gpu_chunking']['gpu_chunk_size'] = [512]
    c['gpu_chunking']['gpu_chunking_inflight'] = 1
if a.variant == 'hetero_pipeline':
    # Keep precisely the serial group's partitions; change only scheduling.
    group = next(g for g in c['kernels_gemm_chunked'] if g['prompt_len'] == 1024)
    group['hetero_inflight'] = 2
    c['kernels_gemm_chunked'] = [group]
if a.variant == 'hetero_down_config':
    for g in c.get('kernels_gemv', []):
        if g.get('layer') == 'down':
            g['cpuN'] = 0
config = outdir / (name + '.config.json')
config.write_text(json.dumps(c, indent=2))
start = time.perf_counter()
m = LLaMA3W4A16Model(model_path='/notebooks/heteromosaic-model',
                     tokenizer_path='/notebooks/heteromosaic-model', max_seq_len=1536,
                     device='cuda', config_path=str(config))
setup_seconds = time.perf_counter() - start
text = ('This experiment measures language model inference on heterogeneous processors. ' * 200) + ' Explain the purpose of this experiment.'
ids = m.tokenizer(text, return_tensors='pt')['input_ids'][:, :1024].contiguous().to('cuda')
assert ids.shape == (1, 1024)
sha = hashlib.sha256(ids.cpu().numpy().tobytes()).hexdigest()
assert sha == '2c11d2476f8b0d68744bec04b88ae434fa2c7f2e1f15a66f6db8785ec5e481c7'
expected = [4221, 1646, 45478, 389, 98882, 37686, 13, 1115]
libc = ctypes.CDLL(None)
records = []

for i in range(a.repeats + 1):
    log = outdir / f'{name}-iteration-{i}.log'
    sys.stdout.flush(); sys.stderr.flush(); libc.fflush(None)
    saveout, saveerr = os.dup(1), os.dup(2)
    with log.open('w') as f:
        os.dup2(f.fileno(), 1); os.dup2(f.fileno(), 2)
        t0ns = time.monotonic_ns()
        try:
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            with torch.no_grad():
                result = m.generate(ids, max_new_tokens=8, temperature=0.0)
            torch.cuda.synchronize()
            wall = time.perf_counter() - t0
        finally:
            libc.fflush(None)
            os.dup2(saveout, 1); os.dup2(saveerr, 2)
            os.close(saveout); os.close(saveerr)
    t1ns = time.monotonic_ns()
    raw = log.read_text()
    prefill = re.findall(r'Prefill time: ([0-9.e+-]+) seconds', raw)
    decode = re.findall(r'Total Generation Time: ([0-9.e+-]+) seconds', raw)
    gen = result[0, 1024:].cpu().tolist()
    row = dict(iteration=i, warmup=i == 0, wall_seconds=wall,
               prefill_seconds=float(prefill[-1]), decode_loop_seconds=float(decode[-1]),
               decode_steps=max(0, len(gen) - 1), generated_ids=gen,
               matches_previous_gpu=gen == expected, start_ns=t0ns, end_ns=t1ns,
               fallback_warnings=raw.count('exceeds total N'),
               command_errors=raw.count('Failed to submit') + raw.count('Failed to wait'))
    records.append(row)
    print('ITERATION', name, json.dumps(row), flush=True)
    (outdir / (name + '.results.json')).write_text(json.dumps(dict(
        variant=a.variant, trace=a.trace, tag=a.tag, input_sha256=sha,
        setup_seconds=setup_seconds, context_capacity=1536, records=records), indent=2))

if a.torch_profile:
    # Optional diagnostic, separate from normal latency repetitions.
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU,
                                          torch.profiler.ProfilerActivity.CUDA],
                                record_shapes=True) as prof:
        with torch.no_grad():
            m.generate(ids, max_new_tokens=8, temperature=0.0)
        torch.cuda.synchronize()
    prof.export_chrome_trace(str(outdir / (name + '.torch.json')))
    (outdir / (name + '.torch-table.txt')).write_text(prof.key_averages().table(
        sort_by='self_cuda_time_total', row_limit=40))

print('PROFILE COMPLETE', name, flush=True)

