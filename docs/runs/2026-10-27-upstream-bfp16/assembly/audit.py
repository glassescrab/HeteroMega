#!/usr/bin/env python3
"""Read archived AIE ELF/disassembly/MLIR; never build or run on hardware."""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbols(path):
    result = {}
    output = subprocess.check_output(['llvm-readelf', '--symbols', str(path)], text=True)
    for line in output.splitlines():
        m = re.match(r'\s*\d+:\s+([0-9a-fA-F]+)\s+(\d+)\s+\w+\s+\w+\s+\w+\s+\S+\s+(\S+)', line)
        if m:
            result[m[3]] = {'address': int(m[1], 16), 'size': int(m[2])}
    return result


def sections(binary):
    assert binary[:6] == b'\x7fELF\x01\x01'
    offset = struct.unpack_from('<I', binary, 32)[0]
    stride, count, names_index = struct.unpack_from('<HHH', binary, 46)
    headers = [struct.unpack_from('<IIIIIIIIII', binary, offset + i * stride)
               for i in range(count)]
    names_header = headers[names_index]
    names = binary[names_header[4]:names_header[4] + names_header[5]]
    return {names[h[0]:].split(b'\0', 1)[0].decode():
            {'address': h[3], 'offset': h[4], 'size': h[5]} for h in headers}


def functions(path):
    text = path.read_text()
    starts = [m for m in re.finditer(r'(?m)^([0-9a-f]+) <([^>]+)>:\n', text)
              if not m[2].startswith('.')]
    result = {}
    for i, match in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        body = text[match.end():end]
        start_line = text[:match.end()].count('\n') + 1
        records, frames = [], []
        for j, line in enumerate(body.splitlines()):
            ins = re.match(r'\s*([0-9a-f]+):', line)
            if not ins:
                continue
            record = {'address': hex(int(ins[1], 16)), 'line': start_line + j,
                      'instruction': line.strip()}
            records.append(record)
            for frame in re.finditer(r'paddxm\s+\[sp\], #(0x[0-9a-f]+|\d+)', line):
                frames.append({'bytes': int(frame[1], 0), **record})
        assert len(frames) <= 1
        result[match[2]] = {'address': int(match[1], 16), 'body': body,
                           'records': records, 'frame': frames[0] if frames else {'bytes': 0}}
    return result


def count(records, pattern):
    return sum(len(re.findall(pattern, r['instruction'])) for r in records)


def core_buffers(mlir):
    result = {}
    for number, line in enumerate(mlir.read_text().splitlines(), 1):
        m = re.search(r'aie.buffer\(%tile_(\d+)_(\d+)\).*address = (\d+).*sym_name = "([^"]+)".*memref<([0-9x]+)x(bf16|f32|ui8|i8)>', line)
        if not m:
            continue
        tile = (int(m[1]), int(m[2]))
        elements = 1
        for extent in m[5].split('x'):
            elements *= int(extent)
        size = elements * {'bf16': 2, 'f32': 4, 'ui8': 1, 'i8': 1}[m[6]]
        result.setdefault(tile, []).append({'symbol': m[4], 'start': int(m[3]),
            'end': int(m[3]) + size, 'bytes': size, 'mlir_line': number})
    return result


def audit_elf(path, buffers, reservation, root):
    syms = symbols(path)
    stack = syms['_sp_start_value_DM_stack']['address']
    binary = path.read_bytes()
    sect = sections(binary)
    regions = [{'symbol': 'reserved_stack', 'start': 0, 'end': reservation}, *buffers]
    for buffer in buffers:
        assert syms[buffer['symbol']]['address'] == stack + buffer['start']
    for name in ('.data', '.bss', '.rodata'):
        if name in sect and sect[name]['size']:
            start = sect[name]['address'] - stack
            regions.append({'symbol': name, 'start': start, 'end': start + sect[name]['size']})
    regions.sort(key=lambda r: r['start'])
    for left, right in zip(regions, regions[1:]):
        assert left['end'] <= right['start'], (path, left, right)
    assert regions[0]['start'] == 0 and regions[-1]['end'] <= 65536
    assert sect['.text']['size'] <= 131072
    return {'elf': str(path.relative_to(root)), 'elf_sha256': sha(path),
            'stack_start': hex(stack), 'reserved_stack_bytes': reservation,
            'local_memory_high_water_bytes': regions[-1]['end'],
            'program_bytes': sect['.text']['size'], 'regions': regions}, syms, sect


def audit_disassembly(path, elf, manifest, root):
    fs = functions(path)
    by_address = {f['address']: name for name, f in fs.items()}
    binary = elf.read_bytes()
    text = sections(binary)['.text']
    edges = {name: set() for name in fs}
    checked = 0
    for name, function in fs.items():
        assert not re.search(r'\bjl\s+[pr]\d', function['body'])
        for record in function['records']:
            encoded = bytes.fromhex(record['instruction'].split('\t')[0].split(':', 1)[1].strip())
            offset = text['offset'] + int(record['address'], 16) - text['address']
            assert binary[offset:offset + len(encoded)] == encoded
            checked += 1
            for call in re.finditer(r'\bjl\s+#(0x[0-9a-f]+)', record['instruction']):
                edges[name].add(by_address[int(call[1], 16)])
    def maximum_chain(name, seen=()):
        assert name not in seen
        children = [maximum_chain(child, seen + (name,)) for child in sorted(edges[name])]
        peak, chain = max(children, key=lambda item: item[0]) if children else (0, [])
        return peak + fs[name]['frame']['bytes'], [name] + chain
    peak, chain = maximum_chain('_main_init')
    assert peak <= manifest['worker_stack_size']
    halves = []
    bfp = manifest['arithmetic'] == 'bfp16'
    for name, function in fs.items():
        if not name.startswith('w4a16_prefill_reuse_accumulate_'):
            continue
        starts = re.findall(r'movxm\s+ls, #(0x[0-9a-f]+)', function['body'])
        ends = re.findall(r'movxm\s+le, #(0x[0-9a-f]+)', function['body'])
        assert len(starts) == len(ends) == 2
        loops = []
        for kind, lower, upper, iterations in zip(('dequant', 'mmul'), starts, ends, (14, 15)):
            low, high = int(lower, 16), int(upper, 16)
            records = [r for r in function['records'] if low <= int(r['address'], 16) <= high]
            for previous, following in zip(records, records[1:]):
                encoded = bytes.fromhex(previous['instruction'].split('\t')[0].split(':', 1)[1].strip())
                assert int(previous['address'], 16) + len(encoded) == int(following['address'], 16)
            before = [r for r in function['records'] if int(r['address'], 16) < low]
            after = [r for r in function['records'] if int(r['address'], 16) > high]
            loop = {'kind': kind, 'inclusive_start': lower, 'inclusive_end': upper,
                'first_line': records[0]['line'], 'last_line': records[-1]['line'],
                'hardware_iterations': iterations, 'decoded_bundles': len(records),
                'vmac_f': count(records, r'\bvmac\.f\b'),
                'bfp16_operand_conversions': count(records, r'\bvconv\.bfp16ebs8\.fp32\b'),
                'vmul_f': count(records, r'\bvmul\.f\b'),
                'stack_vector_loads': count(records, r'\bvld[ab](?:\.\w+)*\s+\w+, \[sp,'),
                'stack_vector_stores': count(records, r'\bvst(?:\.\w+)*\s+\w+, \[sp,'),
                'vmac_f_in_prologue': count(before, r'\bvmac\.f\b'),
                'vmac_f_in_epilogue': count(after, r'\bvmac\.f\b'),
                'instructions': records}
            assert loop['stack_vector_loads'] == loop['stack_vector_stores'] == 0
            if kind == 'mmul':
                expected = (0, 4, 4, 20) if bfp else (19, 32, 13, 36)
                assert (loop['vmac_f_in_prologue'], loop['vmac_f'], loop['vmac_f_in_epilogue'], len(records)) == expected
            else:
                assert (len(records), loop['vmac_f'], loop['vmul_f']) == (13, 0, 1)
            loops.append(loop)
        blocks = (2 if bfp else 4) * manifest['m_reuse']
        mac = loops[1]
        mac_per_block = mac['vmac_f_in_prologue'] + 15 * mac['vmac_f'] + mac['vmac_f_in_epilogue']
        halves.append({'function': name, 'start': hex(function['address']),
            'frame_bytes': function['frame']['bytes'], 'loops': loops,
            'output_register_blocks_per_call': blocks,
            'matrix_mac_instructions_per_call': mac_per_block * blocks,
            'steady_mmul_bundles_per_call': 15 * mac['decoded_bundles'] * blocks,
            'steady_bundle_scope': 'Hardware-loop body only; excludes first-iteration preparation, prologue, epilogue, outer-loop control, dequantization and graph waits.'})
    return {'disassembly': str(path.relative_to(root)), 'sha256': sha(path),
        'visible_instructions_matched_to_elf': checked,
        'maximum_direct_call_chain': chain, 'maximum_nested_stack_bytes': peak,
        'stack_headroom_bytes': manifest['worker_stack_size'] - peak,
        'frames': {name: f['frame'] for name, f in fs.items()}, 'projection_halves': halves,
        'delay_slot_note': '_main_init adjusts SP in the jl main delay slots; its 64-byte frame is included.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('audit.json'))
    args = parser.parse_args()
    root = args.evidence_root
    source_path = root / 'sources/npu/ffn/w4a16_prefill_upstream.cc'
    source = source_path.read_text()
    dequant = source[source.index('template <unsigned Half>'):source.index('#if AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16', source.index('template <unsigned Half>'))]
    assert 'AIE_API_EMULATE_BFLOAT16_MMUL_WITH_BFP16' not in dequant
    stages = []
    for arithmetic in ('bf16', 'bfp16'):
        for stage in ('swiglu', 'down'):
            directory = root / 'prebuilt' / arithmetic / stage
            manifest_path = directory / 'final.xclbin.json'
            manifest = json.loads(manifest_path.read_text())
            assert manifest['source_sha256'] == sha(source_path)
            assert manifest['weight_tile_bytes'] == 4352 and manifest['worker_count'] == 32
            assert manifest['mmul_m_reuse'] == 1 and manifest['vector_zero'] is True
            mlir = directory / 'final.prj/input_with_addresses.mlir'
            stacks = re.findall(r'stack_size = (\d+) : i32', mlir.read_text())
            assert len(stacks) == 32 and set(map(int, stacks)) == {manifest['worker_stack_size']}
            buffers = core_buffers(mlir)
            all_elf = []
            for elf in sorted((directory / 'final.prj').glob('elfs_main_core_*/*.elf')):
                col, row = map(int, re.search(r'core_(\d+)_(\d+)\.elf$', elf.name).groups())
                check, _, _ = audit_elf(elf, buffers[(col, row)], manifest['worker_stack_size'], root)
                all_elf.append(check)
            assert len(all_elf) == 32
            representatives = []
            for disassembly in sorted((root / 'disassembly' / arithmetic / stage).glob('*.dis')):
                elf_name = disassembly.name.removesuffix('.dis')
                elf = directory / 'final.prj' / elf_name.removesuffix('.elf') / elf_name
                representatives.append(audit_disassembly(disassembly, elf, manifest, root))
            assert len(representatives) == 2
            stages.append({'arithmetic': arithmetic, 'stage': stage, 'manifest': manifest,
                'manifest_path': str(manifest_path.relative_to(root)), 'manifest_sha256': sha(manifest_path),
                'address_assigned_mlir': str(mlir.relative_to(root)), 'mlir_sha256': sha(mlir),
                'all_core_resource_audits': all_elf, 'representative_assembly': representatives})
    invariants = ('m', 'k', 'n', 'weight_k', 'weight_n', 'k_start', 'n_start', 'weight_layout',
                  'weight_tile_bytes', 'm_reuse', 'mmul_m_reuse', 'vector_zero', 'input_layout',
                  'output_layout', 'worker_count', 'segment_pipeline_depth', 'activation_fifo_depth')
    for stage in ('swiglu', 'down'):
        pair = [s['manifest'] for s in stages if s['stage'] == stage]
        assert all(pair[0][key] == pair[1][key] for key in invariants)
    timings = []
    for order in ('abba', 'baab'):
        path = root / 'results' / f'arithmetic_{order}.json'
        report = json.loads(path.read_text())
        assert report['weight_repacking'] is False
        baseline = report['summary']['1']['dispatch_wait']['swiglu']
        candidate = report['summary']['2']['dispatch_wait']['swiglu']
        timings.append({'order': order, 'report': str(path.relative_to(root)), 'sha256': sha(path),
            'samples_per_arithmetic': baseline['count'], 'native_median_us': baseline['median_us'],
            'bfp16_median_us': candidate['median_us'],
            'latency_reduction_percent': 100 * (1 - candidate['median_us'] / baseline['median_us']),
            'scope': report['dispatch_wait_note']})
    result = {'version': 1, 'classification': 'Compiled-artifact-confirmed counts; separately labeled host measurements.',
        'source': str(source_path.relative_to(root)), 'source_sha256': sha(source_path),
        'shared_dequant_routine_sha256': hashlib.sha256(dequant.encode()).hexdigest(),
        'shared_dequant_has_no_arithmetic_conditional': True, 'unchanged_profile_contract_fields': invariants,
        'elf_count': 128, 'representative_disassembly_count': 8, 'all_resource_checks_pass': True,
        'first_swiglu_launch_measurements': timings, 'stages': stages,
        'limits': ['All 128 ELF memory regions/program sizes are checked; exact loop/frame disassembly covers two representative workers per stage/profile.',
                   'Bundles and matrix-instruction counts are not measured cycles; no frequency or stall attribution is inferred.',
                   'The 4,320 versus 1,200 reuse2 steady-MMUL bundles exclude prologues/epilogues and all other work.',
                   'BFP16 converts BF16 operands inside the core, with different numerical behavior; original packed W4 buffers and dequantization are shared.',
                   'The first SwiGLU launch also includes DMA, locks, gate transfer, SiLU and multiplication; its host launch+wait measurement is not an isolated matrix-kernel timer.'],
        'reproduce_script_sha256': sha(Path(__file__))}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'sha256': sha(args.output), 'elf_count': 128,
                      'representative_count': 8, 'first_launch_measurements': timings}, indent=2))


if __name__ == '__main__':
    main()
