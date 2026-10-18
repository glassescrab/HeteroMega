"""Summarize saved raw measurements, keeping diagnostic and baseline runs apart."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics as st
import zipfile

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
a = p.parse_args()
root = a.directory

def summary(values):
    v = list(values)
    return dict(n=len(v), median=st.median(v), mean=st.mean(v), min=min(v), max=max(v),
                stdev=st.stdev(v) if len(v) > 1 else 0)

result = dict(measurements={}, stages={}, npu_phases={}, ioctls={}, gpu_kernels={})
for file in sorted(root.glob('*.results.json')):
    d = json.loads(file.read_text())
    r = [x for x in d['records'] if not x['warmup']]
    if not r:
        continue
    key = file.name.removesuffix('.results.json')
    result['measurements'][key] = dict(
        variant=d['variant'], trace=d['trace'], tag=d['tag'],
        setup_seconds=d['setup_seconds'],
        wall_ms=summary(x['wall_seconds'] * 1000 for x in r),
        prefill_ms=summary(x['prefill_seconds'] * 1000 for x in r),
        decode_ms=summary(x['decode_loop_seconds'] * 1000 for x in r),
        decode_ms_per_step=summary(x['decode_loop_seconds'] * 1000 / x['decode_steps'] for x in r),
        all_tokens_match=all(x['matches_previous_gpu'] for x in d['records']),
        fallback_warnings=[x['fallback_warnings'] for x in r],
        command_errors=[x['command_errors'] for x in r])
    trace = root / (key + '.stages.jsonl')
    if trace.exists():
        rows = [json.loads(line) for line in trace.read_text().splitlines()]
        run_ids = list(dict.fromkeys(x['run_id'] for x in rows))
        # One trace run per generate invocation; iteration zero is warmup.
        mapping = {run: i for i, run in enumerate(run_ids)}
        perrun = defaultdict(lambda: defaultdict(float))
        counts = defaultdict(lambda: defaultdict(int))
        for row in rows:
            run = mapping[row['run_id']]
            if run == 0 or run >= len(d['records']):
                continue
            phase = 'prefill' if row['seq_len'] > 1 else 'decode'
            label = phase + '/' + row['stage']
            perrun[label][run] += (row['end_ts_us'] - row['start_ts_us']) / 1000
            counts[label][run] += 1
        result['stages'][key] = {label: dict(ms=summary(t.values()), counts=dict(counts[label]))
                                       for label, t in perrun.items()}

for file in sorted(root.glob('*.npu.csv')):
    key = file.name.removesuffix('.npu.csv')
    rfile = root / (key + '.results.json')
    if not rfile.exists():
        continue
    d = json.loads(rfile.read_text())
    records = [r for r in d['records'] if not r['warmup']]
    rows = []
    for line in file.read_text().splitlines():
        v = list(map(int, line.split(',')))
        if len(v) == 8:
            rows.append(v)
    phase_rows = defaultdict(list)
    # Actual context instruction indices distinguish this fixed model's prefill/decode calls.
    # Inst 0..8 are prefill; Inst 9 is gate GEMV; down GEMV (10) falls back by config.
    for v in rows:
        for i, record in enumerate(records):
            if record['start_ns'] <= v[0] <= record['end_ns']:
                phase = 'prefill' if v[7] < 9 else 'decode'
                phase_rows[phase].append((i, v))
                break
    totals = {}
    names = ['command_build', 'input_ready_poll', 'mutex_queue', 'submit', 'completion_wait']
    for phase, selected in phase_rows.items():
        phases = {}
        for j, name in enumerate(names):
            phases[name] = dict(per_call_us=summary((v[j + 1] - v[j]) / 1000 for _, v in selected))
            per_iteration = defaultdict(float)
            for i, v in selected:
                per_iteration[i] += (v[j + 1] - v[j]) / 1e6
            phases[name]['sum_ms_per_iteration'] = summary(per_iteration.values())
        instructions = {}
        for idx in sorted(set(v[7] for _, v in selected)):
            values = [v for _, v in selected if v[7] == idx]
            instructions[str(idx)] = dict(calls=len(values), **{
                name: summary((v[j + 1] - v[j]) / 1000 for v in values)
                for j, name in enumerate(names)})
        totals[phase] = dict(calls=len(selected), phases=phases,
                            instruction_indices=sorted(set(v[7] for _, v in selected)),
                            by_instruction=instructions)
    result['npu_phases'][key] = totals

for file in sorted(root.glob('*.ioctl.csv')):
    groups = defaultdict(list)
    with file.open() as f:
        for row in csv.DictReader(f):
            groups[row['operation']].append(row)
    result['ioctls'][file.stem] = {op: dict(
        count=len(rows), failures=sum(int(x['ret']) < 0 for x in rows),
        duration_us=summary((int(x['end_ns']) - int(x['start_ns'])) / 1000 for x in rows))
        for op, rows in groups.items()}

traces = [(file.name, file.read_text()) for file in sorted(root.glob('*.torch.json'))]
archive = root / 'gpu-kernel-traces.zip'
if archive.exists():
    with zipfile.ZipFile(archive) as z:
        traces.extend((name, z.read(name).decode()) for name in z.namelist()
                      if name.endswith('.torch.json'))
for filename, contents in traces:
    doc = json.loads(contents)
    groups = defaultdict(list)
    seen = set()
    duplicates = 0
    for row in doc.get('traceEvents', []):
        if row.get('cat') == 'kernel' and row.get('ph') == 'X':
            ident = (row.get('pid'), row.get('tid'), row.get('ts'), row.get('dur'), row.get('name'))
            duplicates += ident in seen
            seen.add(ident)
            groups[row['name']].append(row.get('dur', 0) / 1000)
    result['gpu_kernels'][filename] = dict(
        total_ms=sum(sum(v) for v in groups.values()),
        exact_duplicate_kernel_events=duplicates,
        kernels=sorted([dict(name=k, calls=len(v), sum_ms=sum(v), median_ms=st.median(v))
                        for k, v in groups.items()], key=lambda x: -x['sum_ms']))

(root / 'analysis.json').write_text(json.dumps(result, indent=2))
with (root / 'baseline-summary.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['configuration', 'prefill_median_ms', 'prefill_min_ms', 'prefill_max_ms',
                'decode_loop_median_ms', 'decode_ms_per_step', 'generation_wall_median_ms', 'all_tokens_match'])
    for key, d in result['measurements'].items():
        if d['tag'] == 'baseline':
            w.writerow([d['variant'], d['prefill_ms']['median'], d['prefill_ms']['min'],
                        d['prefill_ms']['max'], d['decode_ms']['median'],
                        d['decode_ms_per_step']['median'], d['wall_ms']['median'], d['all_tokens_match']])
for name, d in result['measurements'].items():
    print(name, 'prefill_ms', round(d['prefill_ms']['median'], 2),
          'decode_ms', round(d['decode_ms']['median'], 2),
          'wall_ms', round(d['wall_ms']['median'], 2), 'tokens', d['all_tokens_match'])
