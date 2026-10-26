#!/usr/bin/env python3
"""Read saved AIE disassembly and ELF symbols; no build/device execution."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path

PAIR = '_ZN12_GLOBAL__N_127accumulate_dequantized_pairEPK8bfloat16S2_Pf'
LOW = 'w4a16_prefill_reuse_accumulate_low'
HIGH = 'w4a16_prefill_reuse_accumulate_high'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def symbols(p):
    text = subprocess.check_output(['llvm-readelf', '--symbols', str(p)], text=True)
    result = {}
    for line in text.splitlines():
        match = re.match(r'\s*\d+:\s+([0-9a-fA-F]+)\s+(\d+)\s+\w+\s+\w+\s+\w+\s+\S+\s+(\S+)', line)
        if match:
            result[match[3]] = {'address': int(match[1], 16), 'size': int(match[2])}
    return result

def functions(p):
    source = p.read_text()
    starts = [m for m in re.finditer(r'(?m)^([0-9a-f]+) <([^>]+)>:\n', source)
              if not m[2].startswith('.')]
    out = {}
    for i, match in enumerate(starts):
        end = starts[i+1].start() if i+1 < len(starts) else len(source)
        body = source[match.end():end]
        records = []
        start_line = source[:match.end()].count('\n') + 1
        for j, line in enumerate(body.splitlines()):
            ins = re.match(r'\s*([0-9a-f]+):', line)
            if ins:
                records.append({'address': hex(int(ins[1],16)), 'line': start_line+j, 'instruction': line.strip()})
        frames = []
        for rec in records:
            for frame in re.finditer(r'paddxm\s+\[sp\], #(0x[0-9a-f]+|\d+)', rec['instruction']):
                frames.append({'bytes': int(frame[1],0), **rec})
        # The selected functions have one fixed positive stack adjustment.
        assert len(frames) <= 1, (p, match[2], frames)
        out[match[2]] = {'address': hex(int(match[1],16)), 'frame': frames[0] if frames else {'bytes':0}, 'records': records, 'body': body}
    return out

def count_inner(helper):
    body=helper['body']
    ls=re.search(r'movxm\s+ls, #(0x[0-9a-f]+)',body)
    le=re.search(r'movxm\s+le, #(0x[0-9a-f]+)',body)
    if not ls or not le:
        return None
    lower,upper=int(ls[1],16),int(le[1],16)
    loop='\n'.join(r['instruction'] for r in helper['records'] if lower<=int(r['address'],16)<=upper)
    return {'inclusive_start':hex(lower), 'inclusive_end':hex(upper),
            'static_stack_vector_loads':len(re.findall(r'\bvld[ab]\s+\w+, \[sp,',loop)),
            'static_stack_vector_stores':len(re.findall(r'\bvst\s+\w+, \[sp,',loop)),
            'static_vmac_f':len(re.findall(r'\bvmac\.f\b',loop)),
            'note':'Instruction counts in one K8 inner-loop body, not cycle attribution. Physical vector transfer byte width is not inferred here.'}

def audit_core(stage,disasm):
    col,row=map(int,re.search(r'core_(\d+)_(\d+)\.disasm$',disasm.name).groups())
    elf=stage/'final.prj'/f'elfs_main_core_{col}_{row}'/f'elfs_main_core_{col}_{row}.elf'
    syms=symbols(elf); fs=functions(disasm)
    manifest=json.loads((stage/'build_contract.json').read_text())['expected_manifest']
    mlir=stage/'final.prj'/'input_with_addresses.mlir'
    mlir_lines=mlir.read_text().splitlines()
    candidates=[]
    for lineno,line in enumerate(mlir_lines,1):
        if f'aie.buffer(%tile_{col}_{row})' in line and 'direct_a_broadcast_' in line:
            m=re.search(r'address = (\d+).*sym_name = "([^"]+)".*memref<(\d+)xbf16>',line)
            if m:
                candidates.append({'symbol':m[2],'tile_offset':int(m[1]),'size_bytes':2*int(m[3]),'mlir_line':lineno,'mlir':line.strip()})
    first_a=min(candidates,key=lambda x:x['tile_offset'])
    first_a['elf_address']=hex(syms[first_a['symbol']]['address'])
    stack_start=syms['_sp_start_value_DM_stack']['address']
    chain_names=['_main_init','main',LOW,PAIR]
    chain=[]; current_sp=stack_start
    for name in chain_names:
        f=fs[name]; current_sp+=f['frame']['bytes']
        chain.append({'function':name,'symbol_address':f['address'],'frame':f['frame'],'sp_after_frame':hex(current_sp)})
    assert fs[LOW]['frame']['bytes']==fs[HIGH]['frame']['bytes']
    calls=[]
    for caller,callee in zip(chain_names,chain_names[1:]):
        target=fs[callee]['address']
        matching=[r for r in fs[caller]['records'] if re.search(r'\bjl\s+#'+re.escape(target)+r'\b',r['instruction'])]
        assert matching,(disasm,caller,callee,target)
        calls.append({'caller':caller,'callee':callee,'count':len(matching),'first':matching[0]})
    boundary=stack_start+manifest['worker_stack_size']; stores=[]
    for rec in fs[PAIR]['records']:
        m=re.search(r'(?<!v)\bst\s+(\w+), \[sp, #(-?(?:0x[0-9a-f]+|\d+))\]',rec['instruction'])
        if m:
            offset=int(m[2],0); address=current_sp+offset
            stores.append({**rec,'register':m[1],'address_from_sp':hex(address),'width_bytes':4,
                           'overlaps_first_a':address<syms[first_a['symbol']]['address']+first_a['size_bytes'] and address+4>syms[first_a['symbol']]['address'],
                           'outside_reserved_stack':address<stack_start or address+4>boundary})
    return {'disassembly':str(disasm.relative_to(stage.parent.parent)),'disassembly_sha256':digest(disasm),
            'elf':str(elf.relative_to(stage.parent.parent)),'elf_sha256':digest(elf),'core':[col,row],
            'stack_start':hex(stack_start),'reserved_stack_bytes':manifest['worker_stack_size'],'reserved_stack_end_exclusive':hex(boundary),
            'first_a_buffer':first_a,'call_chain':chain,'call_edges':calls,'high_wrapper_frame_bytes':fs[HIGH]['frame']['bytes'],
            'peak_chain_bytes':current_sp-stack_start,'excess_over_reservation_bytes':max(0,current_sp-boundary),
            'paired_helper_scalar_stores':stores,'paired_inner_loop':count_inner(fs[PAIR]),
            'main_init_instructions':fs['_main_init']['records'][:7],
            'delay_slot_accounting':'The SP increment and saved LR/P7 stores following _main_init jl main are call-delay-slot instructions executed before main; the startup jl _main_init similarly has movxm sp in its delay slots.'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); stages=[]
    for contract in sorted(args.root.glob('*/*/build_contract.json')):
        stage=contract.parent; manifest=json.loads(contract.read_text())['expected_manifest']
        if manifest.get('mmul_m_reuse')!=2: continue
        reps=[audit_core(stage,p) for p in sorted(stage.glob('core_*.disasm'))]
        all_elf=[]
        for elf in sorted(stage.glob('final.prj/elfs_main_core_*/*.elf')):
            syms=symbols(elf); stack=syms['_sp_start_value_DM_stack']['address']
            col,row=map(int,re.search(r'elfs_main_core_(\d+)_(\d+)\.elf$',elf.name).groups())
            a_symbols=[(name,sym) for name,sym in syms.items() if name.startswith('direct_a_broadcast_') and name.endswith('_cons_buff_0') and sym['address']>=stack]
            first=min(a_symbols,key=lambda pair:pair[1]['address'])
            all_elf.append({'core':[col,row],'elf_sha256':digest(elf),'stack_start':hex(stack),'first_a_symbol':first[0], 'first_a_address':hex(first[1]['address']), 'first_a_offset_from_stack':first[1]['address']-stack})
        stages.append({'stage':str(stage.relative_to(args.root)),'build_contract_sha256':digest(contract),'manifest':manifest,
                       'representative_disassembly_audits':reps,'all_core_elf_address_checks':all_elf})
    result={'audit_version':1,'classification':'compiled-artifact-confirmed','scope':'Paired eight-accumulator native BF16 candidate; local read-only analysis of saved compiler output.',
            'method':'Parse non-local disassembly function boundaries; read actual positive paddxm stack adjustments; follow direct jl calls; combine with ELF _sp_start_value_DM_stack and A-buffer symbols and address-assigned MLIR. Local labels do not end function bodies.',
            'limitations':['Representative cores (0,2) and (1,2) per stage have disassembly; all archived core ELF stack/A addresses are checked.','Does not count device cycles or certify absence of any unrelated memory fault.','The .stack_sizes section omits worker frames and is not sufficient for nested stack safety.'],
            'stages':stages}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    for stage in stages:
        print(stage['stage'], 'ELFs',len(stage['all_core_elf_address_checks']), [(r['core'],r['peak_chain_bytes'],r['excess_over_reservation_bytes'],r['paired_inner_loop']) for r in stage['representative_disassembly_audits']])

if __name__=='__main__':main()
