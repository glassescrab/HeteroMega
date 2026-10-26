#!/usr/bin/env python3
"""Audit saved AIE compiler artifacts, without compiling or using a device."""
import hashlib, json, re, struct, subprocess
from pathlib import Path

ROOT=Path('/tmp/kernel-opt-bf16-evidence-20261025/prebuilt')
DIS=Path('/tmp/compiler_final')
OUT=Path('/tmp/final_kernel_audit.json')
PAIR='_ZN12_GLOBAL__N_127accumulate_dequantized_pairEPK8bfloat16S2_Pf'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def symbols(path):
    result={}
    for line in subprocess.check_output(['llvm-readelf','--symbols',str(path)],text=True).splitlines():
        m=re.match(r'\s*\d+:\s+([0-9a-fA-F]+)\s+(\d+)\s+\w+\s+\w+\s+\w+\s+\S+\s+(\S+)',line)
        if m:result[m[3]]={'address':int(m[1],16),'size':int(m[2])}
    return result

def parse_functions(path):
    text=path.read_text()
    starts=[m for m in re.finditer(r'(?m)^([0-9a-f]+) <([^>]+)>:\n',text) if not m[2].startswith('.')]
    funcs={}
    for i,m in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else len(text)
        body=text[m.end():end];start_line=text[:m.end()].count('\n')+1;records=[]
        for j,line in enumerate(body.splitlines()):
            ins=re.match(r'\s*([0-9a-f]+):',line)
            if ins:records.append({'address':hex(int(ins[1],16)),'line':start_line+j,'instruction':line.strip()})
        adjustments=[]
        for record in records:
            for p in re.finditer(r'paddxm\s+\[sp\], #(0x[0-9a-f]+|\d+)',record['instruction']):
                adjustments.append({'bytes':int(p[1],0),**record})
        assert len(adjustments)<=1,(path,m[2],adjustments)
        funcs[m[2]]={'address':int(m[1],16),'frame':adjustments[0] if adjustments else {'bytes':0},'records':records,'body':body}
    return funcs

def hardware_loops(func):
    starts=re.findall(r'movxm\s+ls, #(0x[0-9a-f]+)',func['body'])
    ends=re.findall(r'movxm\s+le, #(0x[0-9a-f]+)',func['body'])
    assert len(starts)==len(ends)
    result=[]
    for begin,end in zip(starts,ends):
        records=[r for r in func['records'] if int(begin,16)<=int(r['address'],16)<=int(end,16)]
        body='\n'.join(r['instruction'] for r in records)
        mac=len(re.findall(r'\bvmac\.f\b',body))
        if not mac:continue
        result.append({'inclusive_start':begin,'inclusive_end':end,'first_disassembly_line':records[0]['line'],'last_disassembly_line':records[-1]['line'],
            'static_vmac_f':mac,'static_stack_vector_loads':len(re.findall(r'\bvld[ab]\s+\w+, \[sp,',body)),
            'static_stack_vector_stores':len(re.findall(r'\bvst\s+\w+, \[sp,',body)),
            'stack_instruction_examples':[r for r in records if re.search(r'\bv(?:ld[ab]|st)\s+\w+, \[sp,',r['instruction'])][:4]})
    return result

def audit_rep(stage,disasm,manifest):
    col,row=map(int,re.search(r'core_(\d+)_(\d+)\.elf\.dis$',disasm.name).groups())
    elf=stage/'final.prj'/f'elfs_main_core_{col}_{row}'/f'elfs_main_core_{col}_{row}.elf'
    syms=symbols(elf);funcs=parse_functions(disasm);by_address={f['address']:name for name,f in funcs.items()}
    edges=[];adjacency={name:set() for name in funcs}
    for name,func in funcs.items():
        for rec in func['records']:
            for match in re.finditer(r'\bjl\s+#(0x[0-9a-f]+)',rec['instruction']):
                address=int(match[1],16);assert address in by_address,(elf,address)
                callee=by_address[address];adjacency[name].add(callee)
                if not any(e['caller']==name and e['callee']==callee for e in edges):
                    edges.append({'caller':name,'callee':callee,'first_call':rec})
        assert not re.search(r'\bjl\s+[pr]\d',func['body']),(elf,name,'indirect call')
    def chain(name,seen=()):
        assert name not in seen,(name,seen)
        children=[chain(c,seen+(name,)) for c in sorted(adjacency[name])]
        descendant=max(children,key=lambda x:x[0]) if children else (0,[])
        return funcs[name]['frame']['bytes']+descendant[0],[name]+descendant[1]
    binary=elf.read_bytes()
    assert binary[:6]==b'\x7fELF\x01\x01'
    shoff=struct.unpack_from('<I',binary,32)[0]
    shentsize,shnum,shstrndx=struct.unpack_from('<HHH',binary,46)
    headers=[struct.unpack_from('<IIIIIIIIII',binary,shoff+i*shentsize) for i in range(shnum)]
    names_header=headers[shstrndx]
    strings=binary[names_header[4]:names_header[4]+names_header[5]]
    text_header=next(h for h in headers if strings[h[0]:].split(b'\0',1)[0]==b'.text')
    checked_instructions=0
    for func in funcs.values():
        for rec in func['records']:
            encoded=bytes.fromhex(rec['instruction'].split('\t')[0].split(':',1)[1].strip())
            offset=text_header[4]+int(rec['address'],16)-text_header[3]
            assert binary[offset:offset+len(encoded)]==encoded,(elf,rec)
            checked_instructions+=1
    peak,names=chain('_main_init')
    matrix_names=['_main_init','main','w4a16_prefill_reuse_accumulate_low']+([PAIR] if PAIR in funcs else [])
    matrix_bytes=sum(funcs[n]['frame']['bytes'] for n in matrix_names)
    stack_start=syms['_sp_start_value_DM_stack']['address'];reservation=manifest['worker_stack_size'];peak_sp=stack_start+peak
    mlir=stage/'final.prj'/'input_with_addresses.mlir';buffers=[]
    for num,line in enumerate(mlir.read_text().splitlines(),1):
        if f'aie.buffer(%tile_{col}_{row})' not in line or 'direct_a_broadcast_' not in line:continue
        m=re.search(r'address = (\d+).*sym_name = "([^"]+)".*memref<(\d+)xbf16>',line)
        if m:buffers.append({'symbol':m[2],'tile_offset':int(m[1]),'size_bytes':2*int(m[3]),'mlir_line':num,'mlir_instruction':line.strip(),'elf_address':hex(syms[m[2]]['address'])})
    first_a=min(buffers,key=lambda b:b['tile_offset'])
    assert int(first_a['elf_address'],16)==stack_start+reservation
    mmul={name:hardware_loops(funcs[name]) for name in funcs if name.startswith('w4a16_prefill_reuse_accumulate_') or name==PAIR}
    matrix_loop_count=sum(len(v) for v in mmul.values());assert matrix_loop_count==(1 if PAIR in funcs else 2)
    for loops in mmul.values():
        for loop in loops:
            assert (loop['static_vmac_f'],loop['static_stack_vector_loads'],loop['static_stack_vector_stores'])==((64,128,128) if PAIR in funcs else (32,0,0))
    saves=[]
    if PAIR in funcs:
        matrix_sp=stack_start+matrix_bytes
        for rec in funcs[PAIR]['records']:
            m=re.search(r'(?<!v)\bst\s+(\w+), \[sp, #(-?(?:0x[0-9a-f]+|\d+))\]',rec['instruction'])
            if m:
                address=matrix_sp+int(m[2],0)
                saves.append({**rec,'register':m[1],'absolute_store_address':hex(address),'width_bytes':4,'outside_reserved_stack':not stack_start<=address<address+4<=stack_start+reservation})
        assert len(saves)==4 and not any(r['outside_reserved_stack'] for r in saves)
    assert peak<=reservation
    return {'core':[col,row],'elf':str(elf),'elf_sha256':sha(elf),'disassembly':str(disasm),'disassembly_sha256':sha(disasm),'visible_disassembly_instructions_matched_to_elf':checked_instructions,
        'stack_start':hex(stack_start),'reserved_stack_bytes':reservation,'reserved_stack_end_exclusive':hex(stack_start+reservation),
        'first_a_buffer':first_a,'max_direct_call_chain':names,'max_direct_call_chain_bytes':peak,'max_sp':hex(peak_sp),'stack_headroom_bytes':reservation-peak,
        'matrix_projection_call_chain':matrix_names,'matrix_projection_stack_bytes':matrix_bytes,
        'function_frames':{name:{'symbol_address':hex(f['address']),'frame':f['frame']} for name,f in funcs.items()},'direct_call_edges':edges,
        'mmul_k8_hardware_loops':mmul,'paired_helper_scalar_saves':saves,
        'main_init_delay_slot_evidence':funcs['_main_init']['records'][:7],
        'stack_overlaps_first_activation_buffer':peak_sp>int(first_a['elf_address'],16)}

stages=[]
for contract in sorted(ROOT.glob('*/*/build_contract.json')):
    stage=contract.parent;config=json.loads(contract.read_text());m=config['expected_manifest']
    variant,kind=stage.relative_to(ROOT).parts
    mlir=stage/'final.prj'/'input_with_addresses.mlir';s=mlir.read_text()
    stack_entries=[int(v) for v in re.findall(r'stack_size = (\d+) : i32',s)]
    assert len(stack_entries)==32 and set(stack_entries)=={m['worker_stack_size']}
    reps=[audit_rep(stage,p,m) for p in sorted((DIS/variant/kind).glob('*.dis'))];assert len(reps)==2
    all_elf=[]
    for p in sorted(stage.glob('final.prj/elfs_main_core_*/*.elf')):
        syms=symbols(p);start=syms['_sp_start_value_DM_stack']['address']
        c,r=map(int,re.search(r'core_(\d+)_(\d+)\.elf$',p.name).groups())
        a=[(name,sym) for name,sym in syms.items() if name.startswith('direct_a_broadcast_') and name.endswith('_cons_buff_0') and sym['address']>=start]
        first=min(a,key=lambda item:item[1]['address']);assert first[1]['address']-start==m['worker_stack_size']
        all_elf.append({'core':[c,r],'elf':str(p),'elf_sha256':sha(p),'stack_start':hex(start),'first_a_symbol':first[0],'first_a_address':hex(first[1]['address']),'first_a_offset_from_stack':first[1]['address']-start})
    assert len(all_elf)==32
    stages.append({'variant':variant,'stage':kind,'build_contract':str(contract),'build_contract_sha256':sha(contract),
        'manifest':m,'address_assigned_mlir':str(mlir),'address_assigned_mlir_sha256':sha(mlir),
        'all_32_mlir_stack_reservations_match_manifest':True,'all_core_elf_stack_activation_address_checks':all_elf,'representative_disassembly_audits':reps})

summary=[]
for variant in ('baseline','selected','paired'):
    groups=[s for s in stages if s['variant']==variant];reps=[r for g in groups for r in g['representative_disassembly_audits']]
    loops=[loop for r in reps for values in r['mmul_k8_hardware_loops'].values() for loop in values]
    summary.append({'variant':variant,'reserved_stack_bytes':groups[0]['manifest']['worker_stack_size'],
        'matrix_projection_stack_bytes':sorted({r['matrix_projection_stack_bytes'] for r in reps}),
        'max_any_observed_call_chain_bytes':max(r['max_direct_call_chain_bytes'] for r in reps),
        'minimum_observed_stack_headroom_bytes':min(r['stack_headroom_bytes'] for r in reps),
        'mmul_k8_stack_vector_loads':sorted({l['static_stack_vector_loads'] for l in loops}),
        'mmul_k8_stack_vector_stores':sorted({l['static_stack_vector_stores'] for l in loops}),
        'mmul_k8_vmac_f_instructions':sorted({l['static_vmac_f'] for l in loops})})
result={'audit_version':1,'classification':'compiled-artifact-confirmed','generated_by':str(Path(__file__)),'script_sha256':sha(Path(__file__)),
    'scope':'Final M512/H4096/I14336/P2560 native BF16 baseline, selected optimizations and repaired paired-MMUL ablation. No device execution performed by this audit.',
    'summary':summary,'all_audited_call_chains_fit_reserved_stack':True,'elf_address_checks':sum(len(g['all_core_elf_stack_activation_address_checks']) for g in stages),
    'representative_disassemblies':sum(len(g['representative_disassembly_audits']) for g in stages),
    'findings':[
        'Selected four-accumulator MMUL has no stack vector loads/stores in either low/high K8 inner loop. Projection nesting uses 256 B; the separate SiLU call on up workers determines the 704 B maximum, below 2 KiB.',
        'Baseline projection nesting uses 320 B because scalar zero metadata requires a 128 B wrapper frame; its four-accumulator K8 loops also have zero stack vector spills.',
        'Repaired paired ablation reserves 4 KiB. Nesting is 64 B init + 128 B generated main + 128 B scalar-zero wrapper + 1856 B paired helper = 2176 B; first A is at stack + 4096, so the prior overlap is removed.',
        'The paired K8 loop still performs 128 stack vector loads and 128 stores around 64 vmac.f instructions. This confirms substantial accumulator spilling, without attributing a cycle percentage or translating static counts into latency.',
        'The earlier failed combination used vector-zero wrappers with 64 B frames and a 2 KiB reservation (2112 B nested use); the final paired control uses scalar-zero wrappers with 128 B frames and a 4 KiB reservation (2176 B nested use). Do not equate these candidate configurations.'
    ],
    'method':['Read ELF symbols with llvm-readelf; parse actual saved AIE disassembly from non-local function boundaries.','Follow direct jl calls and sum fixed positive paddxm stack increments, including _main_init call delay-slot prologue.','Compare with actual assigned firstA symbols and all 32 per-stage MLIR stack reservations.','Count SP-relative vector accesses only within hardware-loop ls/le ranges containing projection vmac.f. Selected/baseline loop bodies retain accumulators in registers; paired explicit stack accesses are retained with addresses.'],
    'limitations':['Exact instruction/frame audit covers cores (0,2) and (1,2) of each graph; all 192 ELF files are checked for stack/firstA placement.','Direct-call static stack safety is not a substitute for runtime correctness checks or a proof of every memory access.','Loop instruction counts are not cycle measurements; bundles and software-pipeline prologues/epilogues differ.','This report makes no GPU+NPU, model-latency, accuracy or timing claim.'],
    'stages':stages}
OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'summary':summary,'elf_address_checks':result['elf_address_checks'],'representative_disassemblies':result['representative_disassemblies'],'output':str(OUT),'sha256':sha(OUT)},indent=2))
