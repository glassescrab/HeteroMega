#!/usr/bin/env python3
"""Reproduce bounded static counts from archived AIE objects/disassembly.

Bundle counts describe disassembly lines in exact loop ranges, not cycles.
No timing is consumed here. ELF32 executable section sizes come from bytes.
"""
import hashlib
import json
import re
import struct
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOW = 'w4a16_prefill_reuse_accumulate_low'
HIGH = 'w4a16_prefill_reuse_accumulate_high'
DQ = 'w4a16_prefill_dequantize_pair'
M0 = 'w4a16_prefill_accumulate_pair_m0'
M1 = 'w4a16_prefill_accumulate_pair_m1'


def elf_text(path):
    data = path.read_bytes()
    assert data[:6] == b'\x7fELF\x01\x01', 'expected little-endian ELF32'
    header = struct.unpack_from('<16sHHIIIIIHHHHHH', data)
    offset, size, count, strings = header[6], header[11], header[12], header[13]
    sections = [struct.unpack_from('<IIIIIIIIII', data, offset + i * size)
                for i in range(count)]
    names = data[sections[strings][4]:sections[strings][4] + sections[strings][5]]
    result = {}
    for section in sections:
        name = names[section[0]:].split(b'\0', 1)[0].decode()
        if section[2] & 4:  # SHF_EXECINSTR
            result[name] = section[5]
    return result


def parse_dis(path):
    result = {}
    function = None
    for line in path.read_text().splitlines():
        match = re.match(r'Disassembly of section \.text\.(.*):', line)
        if match:
            function = match[1]
            result[function] = []
            continue
        match = re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(.*)', line)
        if match and function:
            ops = [op.strip() for op in match[3].split(';') if op.strip()]
            result[function].append({'address': int(match[1], 16),
                                     'bytes': len(match[2].split()), 'ops': ops})
    return result


def range_audit(function, start, end):
    records = [r for r in function if start <= r['address'] < end]
    assert sum(r['bytes'] for r in records) == end - start, 'loop range has omitted bytes'
    op_counts = Counter(op.split()[0] for r in records for op in r['ops'])
    stack = [f"0x{r['address']:x}: {op}" for r in records for op in r['ops']
             if '[sp' in op]
    return {'start_inclusive': hex(start), 'end_exclusive': hex(end),
            'encoded_bytes': end - start, 'encoded_bundles': len(records),
            'opcode_counts': dict(sorted(op_counts.items())), 'stack_accesses': stack}


def function_audit(records, code_bytes):
    ops = [(r['address'], op) for r in records for op in r['ops']]
    frames = [int(m[1], 16) for _, op in ops
              if (m := re.search(r'paddxm\s+\[sp\], #0x([0-9a-f]+)', op))]
    stack = [{'address': hex(address), 'instruction': op}
             for address, op in ops if '[sp' in op and op.split()[0] != 'paddxm']
    vector_stack = [entry for entry in stack
                    if entry['instruction'].split()[0].startswith(('vld', 'vst'))]
    return {'code_bytes': code_bytes, 'storage_equivalent_32bit_words': code_bytes // 4,
            'frame_bytes': max(frames, default=0),
            'static_vector_stack_transfers': len(vector_stack),
            'stack_operations': stack,
            'calls': [{'address': hex(a), 'instruction': op} for a, op in ops
                      if op.split()[0] in ('jl', 'jal', 'call')]}


def main():
    variants = {}
    parsed = {}
    for name in ('native8_r4', 'split_m32_preconvert_b'):
        obj, dis = HERE / (name + '.o'), HERE / (name + '.dis')
        sections = elf_text(obj)
        functions = parse_dis(dis)
        parsed[name] = functions
        variants[name] = {
            'object_sha256': hashlib.sha256(obj.read_bytes()).hexdigest(),
            'disassembly_sha256': hashlib.sha256(dis.read_bytes()).hexdigest(),
            'executable_sections_bytes': sections,
            'all_executable_bytes_in_object': sum(sections.values()),
            'functions': {f: function_audit(records, sections['.text.' + f])
                          for f, records in functions.items()},
        }
    base, candidate = parsed['native8_r4'], parsed['split_m32_preconvert_b']
    loops = {
        'native8_low_k8': range_audit(base[LOW], 0x320, 0x3c0),
        'native8_high_k8': range_audit(base[HIGH], 0x320, 0x3c0),
        'candidate_dequant_low_k8': range_audit(candidate[DQ], 0x130, 0x1b0),
        'candidate_dequant_high_k8': range_audit(candidate[DQ], 0x2c0, 0x340),
        'candidate_m0_low_k8': range_audit(candidate[M0], 0x180, 0x1f0),
        'candidate_m0_high_k8': range_audit(candidate[M0], 0x350, 0x3c0),
        'candidate_m1_low_k8': range_audit(candidate[M1], 0x190, 0x200),
        'candidate_m1_high_k8': range_audit(candidate[M1], 0x360, 0x3d0),
    }
    assert loops['native8_low_k8']['opcode_counts']['vconv.bfp16ebs8.fp32'] == 4
    assert loops['candidate_m0_low_k8']['opcode_counts']['vconv.bfp16ebs8.fp32'] == 2
    for name, loop in loops.items():
        assert not loop['stack_accesses']
        if 'dequant' not in name:
            assert loop['opcode_counts']['vmac.f'] == 4
    active = {
        'native8_r4': [LOW, HIGH, 'w4a16_prefill_reuse_init', 'w4a16_prefill_reuse_finish'],
        'split_m32_preconvert_b': [DQ, M0, M1, 'w4a16_prefill_reuse_init', 'w4a16_prefill_reuse_finish'],
    }
    for variant, exports in active.items():
        variants[variant]['projection_export_subset'] = exports
        variants[variant]['projection_export_subset_bytes'] = sum(
            variants[variant]['functions'][f]['code_bytes'] for f in exports)
    result = {
        'scope': 'Static kernel object audit, not linked-core program size or measured device cycles.',
        'artifacts': variants, 'loops': loops,
        'derived_per_m64_k128_n64': {
            'matrix_register_blocks': 16,
            'explanation': '4 M16 lanes * 2 N32 halves * 2 N16 register groups. Each K loop executes15 steady iterations plus peeled work for the16th K8.',
            'matrix_mac_instructions_both': 16 * (15 * 4 + 4),
            'baseline_bfp_conversions': {'a': 512, 'b': 512, 'total': 1024},
            'candidate_bfp_conversions': {'a': 512, 'b_in_dequant': 128, 'total': 640},
            'conversion_count_reduction_fraction': .375,
            'baseline_steady_mmul_bundles': 16 * 15 * loops['native8_low_k8']['encoded_bundles'],
            'candidate_steady_mmul_bundles': 16 * 15 * loops['candidate_m0_low_k8']['encoded_bundles'],
            'candidate_extra_vector_stack_bytes': 16 * (8 + 8) * 64,
            'candidate_stack_traffic_explanation': '8 stores +8 loads of64-byte vector quarters before each register-group K loop; no steady-loop spills. This is local stack traffic, not measured DRAM traffic.',
            'baseline_b_scratch_payload_bytes': {'writes': 16384, 'reads': 65536},
            'candidate_b_scratch_payload_bytes': {'writes': 9216, 'reads': 36864},
            'payload_note': 'Logical data payload. FIFO refill/flush transactions and padding may differ.',
        },
        'limits': [
            'Encoded bundle counts are not cycles; compressed instruction size, issue constraints, stalls and overlap prevent conversion to latency.',
            'Steady-loop totals exclude preparation, prologue/epilogue, C loads/stores, graph FIFO waits and host/device transfers.',
            'Both candidate stages have identical object SHA256; the audit applies to SwiGLU and down R4 projection bodies.',
            'Candidate leaf frame576B is below the graph4096B allocation; complete stack safety also requires linked main/call-chain evidence, which this object-only audit does not establish.',
            'Whole object includes unused legacy exports; projection subset is not the full linked-core text. No program-memory capacity claim is made.',
        ],
    }
    (HERE / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'loops': {k: v['encoded_bundles'] for k, v in loops.items()},
                      'projection_subset_bytes': {k: v['projection_export_subset_bytes'] for k, v in variants.items()}}, indent=2))


if __name__ == '__main__':
    main()
