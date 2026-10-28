"""Role-specialized split-Z FFN: NPU gate/up prefix, GPU suffix + full down.

The NPU computes gate/up+SiLU for channels [0,P). The GPU computes gate/up for
[P,I), assembles Z with the NPU prefix, and runs the full down projection.
Timing includes the NPU gate/up, GPU gate/up suffix, Z copies and GPU full down.
"""
import argparse
import json
from pathlib import Path
import random
import time

import numpy as np

from .contract import (OutputIntegrity, accuracy_summary, benchmark_stats, bf16,
    random_weights, reference_full, split_weights, silu_multiply)
from .gpu_backend import GPUBranch
from .merged_npu import MergedGateUpNpuFFN
from .run import TimedFFN, check, comparison_metrics, cpu_values, provenance, save
from .run_upstream_partition import prepare_original_weights, array_hash
from .torch_gpu import TorchBF16SplitDownBranch, PackedSplitDownBranch


class TimedSplitZ:
    def __init__(self, gpu, npu, m, hidden, p1, device):
        import torch
        self.torch, self.gpu, self.npu = torch, gpu, npu
        self.m, self.hidden, self.p1 = m, hidden, p1
        self.compute = torch.cuda.Stream(device=device)
        self.transfer = torch.cuda.Stream(device=device)
        self.reduce = torch.cuda.Stream(device=device)
        self.gpu_gu_done = torch.cuda.Event()
        self.copy_done = torch.cuda.Event()
        self.host_x = torch.empty((m, hidden), dtype=torch.bfloat16, pin_memory=True)
        self.host_x_bits = self.host_x.view(torch.uint16).numpy()
        self.host_z = torch.empty((m, p1), dtype=torch.bfloat16, pin_memory=True)
        self.host_z_bits = self.host_z.view(torch.uint16).numpy()
        self.z_npu_gpu = torch.empty((m, p1), dtype=torch.bfloat16, device=device)
        torch.cuda.synchronize(device)

    def run(self, x, serial=False):
        self.torch.cuda.synchronize(x.device)
        diagnostics = {}
        start = time.perf_counter_ns()
        z_suffix = self.gpu.enqueue_gate_up(x, self.compute)
        self.gpu_gu_done.record(self.compute)
        if serial:
            self.compute.synchronize()
        before = time.perf_counter_ns()
        with self.torch.cuda.stream(self.transfer):
            self.host_x.copy_(x, non_blocking=True)
        self.transfer.synchronize()
        diagnostics['input_gpu_to_host_us'] = (time.perf_counter_ns() - before) / 1000
        z_npu = self.npu.run(self.host_x_bits)
        diagnostics['npu_branch_us'] = self.npu.last_diagnostics['branch_host_wall_us']
        before = time.perf_counter_ns()
        np.copyto(self.host_z_bits, z_npu)
        with self.torch.cuda.stream(self.transfer):
            self.z_npu_gpu.copy_(self.host_z, non_blocking=True)
            self.copy_done.record(self.transfer)
        with self.torch.cuda.stream(self.reduce):
            self.reduce.wait_event(self.gpu_gu_done)
            self.gpu.z_full[:, self.p1:].copy_(z_suffix)
            self.reduce.wait_event(self.copy_done)
            self.gpu.z_full[:, :self.p1].copy_(self.z_npu_gpu)
            self.gpu.enqueue_down(self.gpu.z_full, self.reduce)
        self.reduce.synchronize()
        diagnostics['output_stage_and_boundary_wait_us'] = (time.perf_counter_ns() - before) / 1000
        elapsed = (time.perf_counter_ns() - start) / 1000
        diagnostics['npu'] = self.npu.last_diagnostics
        diagnostics['gpu_diagnostics'] = dict(z_suffix_shape=list(z_suffix.shape),
            z_full_shape=list(self.gpu.z_full.shape), p1=self.p1)
        return self.gpu.output, elapsed, diagnostics


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--m', type=int, default=512)
    ap.add_argument('--hidden', type=int, default=4096)
    ap.add_argument('--intermediate', type=int, default=14336)
    ap.add_argument('--npu-channels', type=int, default=8192)
    ap.add_argument('--seed', type=int, default=12832)
    ap.add_argument('--warmup', type=int, default=2)
    ap.add_argument('--iterations', type=int, default=5)
    ap.add_argument('--artifact-root', type=Path, default=Path('artifacts'))
    ap.add_argument('--iron-python')
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--accuracy-policy', choices=('strict', 'report'), default='report')
    ap.add_argument('--gpu-kind', choices=('torch_bf16', 'packed'), default='packed')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    report = dict(schema_version=1, status='preparing',
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        scope='role-specialized split-Z FFN microbenchmark; experimental, not model prefill',
        provenance=provenance(), correctness={}, samples=[], warmup_samples=[], validation_runs=[])
    weights = random_weights(args.hidden, args.intermediate, args.seed)
    original = prepare_original_weights(weights)
    report['original_weight_buffers'] = {name: dict(k=w.k, n=w.n, sha256=array_hash(w.data))
        for name, w in zip(('gate','up','down'), original)}
    import torch
    suffix = split_weights(weights, args.npu_channels)['gpu']
    if args.gpu_kind == 'packed':
        gpu = PackedSplitDownBranch(original, args.hidden, args.intermediate,
                                    args.npu_channels, args.m)
    else:
        gpu = TorchBF16SplitDownBranch(suffix.gate, suffix.up, weights.down,
            args.m, args.npu_channels, args.hidden)
    npu = MergedGateUpNpuFFN(args.m, args.hidden, args.npu_channels, *original,
        args.artifact_root, python_executable=args.iron_python, build=not args.no_build)
    baseline_gpu = GPUBranch(weights.gate, weights.up, weights.down, args.m, verbose_build=False)
    baseline = TimedFFN(baseline_gpu, None, args.m, args.hidden, baseline_gpu.device)
    candidate = TimedSplitZ(gpu, npu, args.m, args.hidden, args.npu_channels, baseline_gpu.device)
    report.update(gpu=gpu.metadata, npu=npu.metadata, baseline_gpu=baseline_gpu.metadata)
    rng = np.random.default_rng(args.seed + 1)
    inputs = [bf16(rng.normal(size=(args.m, args.hidden)).astype(np.float32)) for _ in range(2)]
    inputs.append(np.zeros_like(inputs[0]))
    gpu_inputs = [torch.from_numpy(x).to(device=baseline_gpu.device, dtype=torch.bfloat16) for x in inputs]
    torch.cuda.synchronize(baseline_gpu.device)
    refs = [reference_full(x, weights) if i != 2 else np.zeros_like(x) for i, x in enumerate(inputs)]
    npu_branch = split_weights(weights, args.npu_channels)['npu']
    z_refs = []
    for x in inputs:
        gate = bf16(x @ npu_branch.gate.dequantize(True).T)
        up = bf16(x @ npu_branch.up.dequantize(True).T)
        z_refs.append(silu_multiply(gate, up, bf16_io=True))
    all_checks = {}
    integrity = {name: OutputIntegrity() for name in ('output', 'npu', 'gpu')}
    for run_index, index in enumerate((0, 1, 2, 0)):
        for mode in ('serial', 'concurrent'):
            output, elapsed, diagnostics = candidate.run(gpu_inputs[index], serial=mode == 'serial')
            actual = cpu_values(output)
            record = dict(run=run_index, input_index=index, mode=mode, wall_us=elapsed,
                          output_sha256=array_hash(actual), diagnostics=diagnostics)
            report['validation_runs'].append(record)
            record['output_check'] = check(actual, refs[index], f'validation_{run_index}_{mode}',
                all_checks, args.accuracy_policy, integrity['output'], index)
            zbits = np.asarray(npu.last_output).view(np.uint16)
            zfloat = (zbits.astype(np.uint32) << 16).view(np.float32).reshape(args.m, args.npu_channels)
            record['npu_z_check'] = check(zfloat, z_refs[index], f'validation_{run_index}_{mode}_z',
                all_checks, args.accuracy_policy, integrity['npu'], index)
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
