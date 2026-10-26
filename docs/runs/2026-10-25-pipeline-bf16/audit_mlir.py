#!/usr/bin/env python3
"""Audit emitted, pre-lowering MLIR for serial/pipelined upstream FFN graphs.

Usage: python /tmp/audit_upstream_pipeline_mlir.py SERIAL.mlir PIPELINED.mlir
This audits explicit logical task BDs and declared shim channels; device
allocation and completion still require compiler/runtime evidence.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re


def normalize(text):
    return ' '.join(text.split())


def parse(path, expected_depth):
    text = Path(path).read_text()
    assert text.count('aie.runtime_sequence(') == 1, 'expected one runtime sequence'
    prefix, runtime = text.split('aie.runtime_sequence(', 1)
    tiles = {name: int(col) for name, col in re.findall(
        r'(%[\w]+) = aie.logical_tile<ShimNOCTile>\((\d+), 0\)', prefix)}
    channels = {}
    for line in prefix.splitlines():
        match = re.search(r'aie.objectfifo @(direct_[awy]_host_\d+)\((%[\w]+), \{([^}]+)\},', line)
        if not match:
            continue
        fifo, producer, consumers = match.groups()
        if producer in tiles:
            channel = int(re.search(r'prod_dma_channel = (\d+)', line).group(1))
            channels[fifo] = (tiles[producer], 'MM2S', channel)
        else:
            shims = [item.strip() for item in consumers.split(',') if item.strip() in tiles]
            assert len(shims) == 1, (fifo, shims)
            channel = int(re.search(r'cons_dma_channels = array<i32: (\d+)>', line).group(1))
            channels[fifo] = (tiles[shims[0]], 'S2MM', channel)
    assert channels, 'no declared direct shim channels found'
    output_fifos = {fifo for fifo, (_, direction, _) in channels.items() if direction == 'S2MM'}
    configure = re.compile(r'(?ms)^\s*(%[\w]+) = aiex\.dma_configure_task_for @(\w+) \{\n(.*?)^\s*\}([^\n]*)$')
    events, tasks, ordinals = [], {}, Counter()
    for match in configure.finditer(runtime):
        task, fifo, body, attrs = match.groups()
        assert fifo in channels, fifo
        assert body.count('aie.dma_bd(') == 1, 'expected one BD per transfer'
        assert task not in tasks, task
        issue = 'issue_token = true' in attrs
        assert issue == (fifo in output_fifos), (task, fifo, attrs)
        tasks[task] = dict(fifo=fifo, ordinal=ordinals[fifo], body=normalize(body), attrs=normalize(attrs))
        ordinals[fifo] += 1
        events.append((match.start(), 'configure', task))
    for match in re.finditer(r'aiex\.dma_(start|await|free)_task\((%[\w]+)\)', runtime):
        events.append((match.start(), match.group(1), match.group(2)))
    assert len(set(ordinals.values())) == 1, f'channel segment-count mismatch: {ordinals}'
    assert len(events) == len(tasks) * 3 + sum(t['fifo'] in output_fifos for t in tasks.values())
    live, started, awaited, freed = set(), set(), set(), set()
    per_channel, per_shim = Counter(), Counter()
    maxima_channel, maxima_shim = Counter(), Counter()
    group_awaited = defaultdict(set)
    next_await = Counter()
    first_await_seen, starts_before_first_await = False, 0
    start_order, await_order, free_order = [], [], []
    for _, action, task in sorted(events):
        item = tasks[task]
        fifo, ordinal = item['fifo'], item['ordinal']
        channel = channels[fifo]
        key = (fifo, ordinal)
        if action == 'configure':
            assert task not in live and task not in freed
            live.add(task)
            per_channel[channel] += 1
            per_shim[channel[0]] += 1
            maxima_channel[channel] = max(maxima_channel[channel], per_channel[channel])
            maxima_shim[channel[0]] = max(maxima_shim[channel[0]], per_shim[channel[0]])
        elif action == 'start':
            assert task in live and task not in started
            started.add(task)
            start_order.append(key)
            starts_before_first_await += not first_await_seen
        elif action == 'await':
            first_await_seen = True
            assert task in started and task in live and task not in awaited
            assert fifo in output_fifos
            assert ordinal == next_await[fifo], 'completion tokens awaited out of FIFO order'
            next_await[fifo] += 1
            awaited.add(task)
            group_awaited[ordinal].add(fifo)
            await_order.append(key)
        else:
            assert action == 'free'
            assert task in live and task in started and task not in freed
            assert group_awaited[ordinal] == output_fifos, 'task freed before all segment outputs awaited'
            live.remove(task)
            freed.add(task)
            per_channel[channel] -= 1
            per_shim[channel[0]] -= 1
            free_order.append(key)
    assert not live and len(freed) == len(tasks)
    assert max(maxima_channel.values()) <= expected_depth
    assert max(maxima_shim.values()) <= 3 * expected_depth
    return dict(prefix=prefix, configs=[(t['fifo'], t['ordinal'], t['body'], t['attrs']) for t in tasks.values()],
        start_order=start_order, await_order=await_order, free_order=free_order,
        summary=dict(path=str(path), sha256=sha256(text.encode()).hexdigest(), logical_task_BDs=len(tasks),
            segments_per_channel=next(iter(ordinals.values())), starts_before_first_await=starts_before_first_await,
            maximum_live_BDs_per_shim={str(k): v for k, v in sorted(maxima_shim.items())},
            maximum_live_transfers_per_channel={str(k): v for k, v in sorted(maxima_channel.items())},
            all_output_awaits_precede_group_frees=True, all_tasks_started_and_freed_once=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('serial')
    parser.add_argument('pipeline')
    args = parser.parse_args()
    serial, pipeline = parse(args.serial, 1), parse(args.pipeline, 2)
    checks = dict(prefix_bytes_identical=serial['prefix'] == pipeline['prefix'],
                  prefix_tokens_identical=normalize(serial['prefix']) == normalize(pipeline['prefix']),
                  dma_configs_identical=serial['configs'] == pipeline['configs'],
                  start_order_identical=serial['start_order'] == pipeline['start_order'],
                  await_order_identical=serial['await_order'] == pipeline['await_order'],
                  free_order_identical=serial['free_order'] == pipeline['free_order'],
                  starts_before_first_await_doubled=pipeline['summary']['starts_before_first_await'] ==
                      2 * serial['summary']['starts_before_first_await'])
    assert all(v for k, v in checks.items() if k != 'prefix_bytes_identical'), checks
    print(json.dumps(dict(status='passed', checks=checks, serial=serial['summary'], pipeline=pipeline['summary'],
        scope='Emitted pre-lowering MLIR logical task audit; not device-cycle or physical BD-allocation evidence'), indent=2))

if __name__ == '__main__':
    main()
