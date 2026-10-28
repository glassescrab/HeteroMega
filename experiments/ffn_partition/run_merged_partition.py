"""Measure the experimental merged-NPU FFN against matched GPU controls."""
import argparse
import json
from pathlib import Path
import random
import time

import numpy as np

from .contract import (OutputIntegrity, accuracy_summary, benchmark_stats, bf16,
    random_weights, reference_partitioned, split_weights)
from .gpu_backend import GPUBranch
from .run import TimedFFN, check, comparison_metrics, cpu_values, provenance, save
from .run_upstream_partition import prepare_original_weights, weight_metadata, array_hash
from .merged_npu import MergedUpstreamNpuFFN


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--m', type=int, default=512)
    ap.add_argument('--hidden', type=int, default=4096)
    ap.add_argument('--intermediate', type=int, default=14336)
    ap.add_argument('--npu-channels', type=int, default=4352)
    ap.add_argument('--seed', type=int, default=12832)
    ap.add_argument('--warmup', type=int, default=2)
    ap.add_argument('--iterations', type=int, default=10)
    ap.add_argument('--artifact-root', type=Path, default=Path('artifacts'))
    ap.add_argument('--iron-python')
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--gpu-variant', choices=('original', 'teammate'), default='teammate')
    ap.add_argument('--accuracy-policy', choices=('strict', 'report'), default='report')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    report = dict(schema_version=1, status='preparing',
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        scope='merged-NPU complete FFN microbenchmark; experimental, not model prefill',
        provenance=provenance(), correctness={}, samples=[], warmup_samples=[],
        validation_runs=[])
    weights = random_weights(args.hidden, args.intermediate, args.seed)
    original = prepare_original_weights(weights)
    report['original_weight_buffers'] = weight_metadata(original)
    import torch
    suffix = split_weights(weights, args.npu_channels)['gpu']
    if args.gpu_variant == 'teammate':
        from .teammate_gpu import TeammateGPUBranch
        gpu = TeammateGPUBranch.from_upstream(*(w.data for w in original),
            args.hidden, args.intermediate, args.npu_channels, args.intermediate,
            args.m, verbose_build=False)
    else:
        gpu = GPUBranch(suffix.gate, suffix.up, suffix.down, args.m, verbose_build=False)
    device = gpu.device
    baseline_gpu = GPUBranch(weights.gate, weights.up, weights.down, args.m, verbose_build=False)
    baseline = TimedFFN(baseline_gpu, None, args.m, args.hidden, device)
    npu = MergedUpstreamNpuFFN(args.m, args.hidden, args.npu_channels, *original,
        args.artifact_root, python_executable=args.iron_python, build=not args.no_build)
    candidate = TimedFFN(gpu, npu, args.m, args.hidden, device)
    report['gpu'] = gpu.metadata
    report['npu'] = npu.metadata
    report['baseline_gpu'] = baseline_gpu.metadata
    rng = np.random.default_rng(args.seed + 1)
    inputs = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32)) for _ in range(2)]
    inputs.append(np.zeros_like(inputs[0]))
    gpu_inputs = [torch.from_numpy(x).to(device=device, dtype=torch.bfloat16) for x in inputs]
    torch.cuda.synchronize(device)
    refs, partials = [], []
    for x in inputs:
        ref, part = reference_partitioned(x, weights, args.npu_channels)
        refs.append(ref); partials.append(part)
    report['input_sha256'] = [array_hash(x) for x in inputs]
    all_checks = {}
    integrity = {name: OutputIntegrity() for name in ('output', 'gpu', 'npu')}
    for run_index, index in enumerate((0, 1, 2, 0)):
        for mode in ('serial', 'concurrent'):
            output, elapsed, diagnostics = candidate.run(gpu_inputs[index], serial=mode == 'serial')
            actual = cpu_values(output)
            record = dict(run=run_index, input_index=index, mode=mode, wall_us=elapsed,
                          output_sha256=array_hash(actual), diagnostics=diagnostics)
            report['validation_runs'].append(record)
            record['output_check'] = check(actual, refs[index], f'validation_{run_index}_{mode}',
                all_checks, args.accuracy_policy, integrity['output'], index)
            npu_bits = np.asarray(npu.last_output).view(np.uint16)
            npu_actual = (npu_bits.astype(np.uint32) << 16).view(np.float32).reshape(args.m, args.hidden)
            record['npu_check'] = check(npu_actual, partials[index]['npu'],
                f'validation_{run_index}_{mode}_npu', all_checks, args.accuracy_policy, integrity['npu'], index)
            record['gpu_check'] = check(cpu_values(gpu.output), partials[index]['gpu'],
                f'validation_{run_index}_{mode}_gpu', all_checks, 'strict', integrity['gpu'], index)
    modes = ['baseline', 'serial', 'concurrent']
    rng = random.Random(args.seed + args.npu_channels)
    for iteration in range(-args.warmup, args.iterations):
        index = iteration % 2
        rng.shuffle(modes)
        for ordinal, mode in enumerate(modes):
            runner = baseline if mode == 'baseline' else candidate
            output, elapsed, diagnostics = runner.run(gpu_inputs[index], serial=mode == 'serial')
            actual = cpu_values(output)
            record = dict(iteration=iteration, order_index=ordinal, input_index=index,
                          mode=mode, wall_us=elapsed, output_sha256=array_hash(actual),
                          diagnostics=diagnostics)
            report['samples' if iteration >= 0 else 'warmup_samples'].append(record)
            if mode == 'baseline':
                record['accuracy'] = check(actual, refs[index], f'iteration_{iteration}_baseline',
                    all_checks, 'strict', None, index)
            else:
                record['accuracy'] = check(actual, refs[index], f'iteration_{iteration}_{mode}',
                    all_checks, args.accuracy_policy, integrity['output'], index)
        print(f'P={args.npu_channels}: completed round {iteration + 1}/{args.iterations}', flush=True)
    report['stats'] = {mode: benchmark_stats([r['wall_us'] for r in report['samples']
        if r['mode'] == mode]) for mode in modes}
    report['accuracy'] = accuracy_summary(list(all_checks.values()))
    report.update(comparison_metrics(report['stats'], report['accuracy']['passed']))
    report['status'] = 'passed' if report['accuracy']['passed'] else 'completed_with_accuracy_deviations'
    save(report, args.output)
    print(json.dumps({key: report[key] for key in ('stats', 'status', 'latency_ratio_vs_gpu_baseline')}, indent=2))


if __name__ == '__main__':
    main()
