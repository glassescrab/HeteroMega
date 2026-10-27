#!/usr/bin/env python3
"""Derive Down counts and measured stage summaries from retained evidence.

This reads saved reports and the CPU graph planner; it never launches a device.
Local operand-byte counts exclude metadata/instruction fetches and are not
measured physical memory bandwidth. Steady bundles are not cycle counts.
"""
from pathlib import Path
from hashlib import sha256
import json
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'npu/ffn'))
from upstream_schedule import plan_upstream

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

report_root = HERE.parent
audit = json.loads((HERE / 'audit.json').read_text())
stages = {x['arithmetic']: x for x in audit['stages'] if x['stage'] == 'down'}
manifest = stages['bfp16']['manifest']
assert (manifest['m'], manifest['k'], manifest['n'], manifest['m_reuse']) == (512, 2560, 4096, 4)
plan = plan_upstream(manifest['m'], manifest['k'], manifest['n'],
    mode='projection', weight_k=manifest['weight_k'], weight_n=manifest['weight_n'],
    k_start=manifest['k_start'], n_start=manifest['n_start'], columns=8, max_reuse=4)
base = plan.base
assert len(base.workers) == 32 and base.groups_per_column == 2 and plan.segment_count == 8
halves_per_worker = base.groups_per_column * base.kb * sum(len(x.halves) for x in plan.segments[0])
half_calls = halves_per_worker * 32
assert half_calls == 20480
acquisitions_per_worker = base.groups_per_column * plan.segment_count * base.kb
output_objects_per_worker = base.groups_per_column * sum(len(x.halves) for x in plan.segments[0])

def elements(tap):
    return int(np.prod(tap.sizes))

dma = dict(activation=0, packed_weight=0, output=0)
for group in range(base.groups_per_column):
    for segment in range(plan.segment_count):
        dma['activation'] += 2 * sum(elements(plan.activation_tap(lane, group)) for lane in range(base.m_column_groups * 4))
        dma['packed_weight'] += sum(elements(plan.weight_tap(col, segment)) for col in range(8))
        dma['output'] += 2 * sum(elements(plan.output_tap(col, group, segment)) for col in range(8))
assert dma == {'activation':20971520, 'packed_weight':11141120, 'output':4194304}

kernels = {}
for arithmetic, stage in stages.items():
    calls = [h for r in stage['representative_assembly'] for h in r['projection_halves']]
    macs = {h['matrix_mac_instructions_per_call'] for h in calls}
    bundles = {h['steady_mmul_bundles_per_call'] for h in calls}
    assert len(macs) == len(bundles) == 1
    read_b = 32768 if arithmetic == 'bfp16' else 65536
    kernels[arithmetic] = dict(matrix_mac_instructions_per_half_call=macs.pop(),
        steady_mmul_bundles_per_half_call=bundles.pop(),
        local_bytes_per_half_call=dict(scratch_write=8192, scratch_read=read_b,
                                      a_read=32768, fp32_c_read_write=16384),
        local_allocation_bytes=max(x['local_memory_high_water_bytes'] for x in stage['all_core_resource_audits']),
        max_nested_stack_bytes=max(x['maximum_nested_stack_bytes'] for x in stage['representative_assembly']),
        worker_stack_reservation=stage['manifest']['worker_stack_size'])
    kernel = kernels[arithmetic]
    kernel['full_launch_matrix_instructions'] = half_calls * kernel['matrix_mac_instructions_per_half_call']
    kernel['full_launch_logical_local_bytes'] = {k:v*half_calls for k,v in kernel['local_bytes_per_half_call'].items()}
assert kernels['bf16']['matrix_mac_instructions_per_half_call'] == 8192
assert kernels['bfp16']['matrix_mac_instructions_per_half_call'] == 512

timings = []
for order in ('abba','baab'):
    path = report_root / f'arithmetic_{order}.json'
    report = json.loads(path.read_text())
    assert report['status'] == 'passed'
    entries = {}
    for index, arithmetic in ((1,'bf16'),(2,'bfp16')):
        runs = [r for b in report['blocks'] if b['profile_index'] == index for r in b['runs']]
        assert len(runs) == 100
        waits = [r['diagnostics']['dispatch_wait_us']['down'] for r in runs]
        host = [r['diagnostics']['stages']['down_with_host_io_us'] for r in runs]
        unpack = [r['diagnostics']['stages']['output_layout_us'] for r in runs]
        entries[arithmetic] = dict(samples=len(runs), launch_wait_median_us=float(np.median(waits)),
            with_host_io_median_us=float(np.median(host)), output_unpack_median_us=float(np.median(unpack)),
            host_io_minus_wait_median_us=float(np.median(np.asarray(host)-waits)),
            with_host_io_plus_unpack_median_us=float(np.median(np.asarray(host)+unpack)))
        assert entries[arithmetic]['launch_wait_median_us'] == report['summary'][str(index)]['dispatch_wait']['down']['median_us']
    timings.append(dict(order=order, report_sha256=digest(path), arithmetic=entries,
        launch_wait_reduction_percent=100*(1-entries['bfp16']['launch_wait_median_us']/entries['bf16']['launch_wait_median_us'])))

result = dict(classification='Saved measurements and code/compiled-artifact-confirmed derived counts; no new hardware run',
    source_hashes={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),HERE/'audit.json', ROOT/'npu/ffn/upstream_schedule.py',ROOT/'npu/ffn/w4a16_prefill_upstream.cc']},
    shape=dict(m=512,k=2560,n=4096,full_weight_k=14336,full_weight_n=4096),
    schedule=dict(columns=8,workers=32,m_reuse=4,m_waves=2,n64_segments=8,k128_groups=20,
        half_calls_per_worker=halves_per_worker,half_calls_total=half_calls,
        input_weight_acquisition_pairs_per_worker=acquisitions_per_worker,
        output_objects_per_worker=output_objects_per_worker,
        core_fifo_acquires_total=32*(2*acquisitions_per_worker+output_objects_per_worker),
        core_fifo_releases_total=32*(2*acquisitions_per_worker+output_objects_per_worker)),
    logical_shim_dma_bytes=dma,kernels=kernels,timings=timings,
    limits=['Down timing is a stage of paired whole-FFN arithmetic experiments; its Z input differs with upstream SwiGLU arithmetic.',
            'No fixed-Z down-only ablation, device-phase cycles, bank-stall breakdown or physical bandwidth measurement is asserted.',
            'Local byte totals count logical operands excluding metadata, graph init/finish, instruction fetches and spills outside MMUL.',
            'Final unpack is measured separately from down_with_host_io; combined medians are calculated from per-call sums.'])
output = HERE/'down_breakdown.json'
output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(output=str(output),half_calls=half_calls,shim_dma_bytes=dma,timings=timings),indent=2))
