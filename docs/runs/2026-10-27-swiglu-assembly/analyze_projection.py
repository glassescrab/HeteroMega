#!/usr/bin/env python3
import hashlib,importlib.util,json,re
from pathlib import Path
spec=importlib.util.spec_from_file_location('audit',str(Path(__file__).resolve().parents[1] / '2026-10-25-kernel-optimizations/audit_stack_v1.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
root=Path('/tmp/kernel-opt-bf16-evidence-20261025/prebuilt/selected/swiglu')
dis=Path('/tmp/compiler_final/selected/swiglu')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
for p in sorted(dis.glob('*.dis')):
 col,row=map(int,re.search(r'core_(\d+)_(\d+)\.elf\.dis$',p.name).groups())
 elf=root/'final.prj'/f'elfs_main_core_{col}_{row}'/f'elfs_main_core_{col}_{row}.elf'
 syms=a.symbols(elf)
 for name,f in a.functions(p).items():
  if not name.startswith('w4a16_prefill_reuse_accumulate'):continue
  starts=re.findall(r'movxm\s+ls, #(0x[0-9a-f]+)',f['body']);ends=re.findall(r'movxm\s+le, #(0x[0-9a-f]+)',f['body']);assert len(starts)==len(ends)==2
  loops=[]
  for kind,lo,hi,trip in zip(('dequant','mmul'),starts,ends,(14,15)):
   lo_i,hi_i=int(lo,16),int(hi,16)
   records=[r for r in f['records'] if lo_i<=int(r['address'],16)<=hi_i]
   for x,y in zip(records,records[1:]):
    encoded=bytes.fromhex(x['instruction'].split('\t')[0].split(':',1)[1].strip())
    assert int(x['address'],16)+len(encoded)==int(y['address'],16)
   before=[r for r in f['records'] if int(r['address'],16)<lo_i]
   after=[r for r in f['records'] if int(r['address'],16)>hi_i]
   count=lambda arr,pattern:sum(len(re.findall(pattern,r['instruction'])) for r in arr)
   loops.append({'kind':kind,'inclusive_start':lo,'inclusive_end':hi,'first_line':records[0]['line'],'last_line':records[-1]['line'],
    'decoded_bundles_per_hardware_iteration':len(records),'hardware_loop_iterations':trip,
    'vmac_f_per_iteration':count(records,r'\bvmac\.f\b'),'vmul_f_per_iteration':count(records,r'\bvmul\.f\b'),
    'stack_vector_loads_per_iteration':count(records,r'\bvld[ab]\s+\w+, \[sp,'),'stack_vector_stores_per_iteration':count(records,r'\bvst\s+\w+, \[sp,'),
    'vmac_f_before_loop':count(before,r'\bvmac\.f\b'),'vmac_f_after_loop':count(after,r'\bvmac\.f\b'),
    'loop_setup_evidence':[r for r in before if re.search(r'\blc,|\bls,|\ble,',r['instruction'])][-3:]})
  mac=loops[1];assert (mac['vmac_f_before_loop'],mac['vmac_f_per_iteration'],mac['vmac_f_after_loop'])==(19,32,13)
  assert mac['decoded_bundles_per_hardware_iteration']==36
  results.append({'projection':'gate' if col==0 else 'up','half':'low' if name.endswith('_low') else 'high','function':name,
    'function_start':hex(syms[name]['address']),'function_end_exclusive':hex(syms[name]['address']+syms[name]['size']),
    'function_size_bytes':syms[name]['size'],'static_visible_bundle_count_in_entire_function':len(f['records']),
    'disassembly':str(p),'disassembly_sha256':sha(p),'elf':str(elf),'elf_sha256':sha(elf),'hardware_loops':loops})
manifest=root/'final.xclbin.json'
report={
 'classification':'compiled-artifact-confirmed plus source-derived dynamic operation counts',
 'scope':'First selected SwiGLU launch only, M512/H4096/P2560, both gate/up projections; excludes the second down-projection launch.',
 'manifest':str(manifest),'manifest_sha256':sha(manifest),'instruction_match_evidence':'/tmp/final_kernel_audit.json verifies each visible disassembly instruction against matching ELF bytes.',
 'halves':results,
 'per_k128_n32_call':{
  'm_reuse':2,'m_rows':32,'output_register_blocks':8,'k8_groups':16,'api_mac_per_k8_per_block':4,
  'native_4x8x8_api_mac_scalar_products':256,'vmac_f_per_api_mac':8,
  'vmac_f_per_register_block':'19 + 15 * 32 + 13 = 512','vmac_f_per_call':4096,
  'source_scratch_bf16_write_bytes':8192,'source_scratch_bf16_read_bytes':32768,
  'source_activation_read_bytes':16384,'source_fp32_partial_read_bytes':4096,'source_fp32_partial_write_bytes':4096,
  'source_quantized_weight_read_bytes':2048,'source_scale_read_bytes':64,'source_zero_metadata_read_bytes':64,
  'dequantized_bf16_weights':4096,'vector_dequant_groups_of_64_weights':64,
  'mmul_steady_loop_bundles_per_block':540,'mmul_steady_loop_bundles_per_call':4320,
  'note':'The 4320 steady-loop bundles exclude software-pipeline prologues, epilogues, outer-loop control, dequantization and function overhead. Source access counts describe logical local accesses, not measured DRAM traffic.'},
 'entire_first_launch':{
  'workers':32,'half_calls_per_worker':2560,'half_calls_total':81920,
  'vmac_f_per_worker':10485760,'vmac_f_total':335544320,
  'scalar_bf16_multiply_accumulate_products':10737418240,
  'source_scratch_write_mib':640,'source_scratch_read_mib':2560,
  'source_activation_read_mib':1280,'source_fp32_partial_read_plus_write_mib':640,
  'half_call_derivation':'2 projections * (512 / 32 M-row groups) * (2560 / 32 output-channel halves) * (4096 / 128 K groups) = 81920',
  'first_launch_includes':'Both matrix projections, FIFO/DMA/lock handling, gate transfer and up-worker SiLU/multiply; only projection instruction work is counted here.'},
 'interpretation':[
  'Native BF16 arithmetic expansion is a strong plausible compute cost: each API 4x8x8 MAC lowers to eight vmac.f, giving 10.49 million vmac.f instructions per worker for the two first-launch projections.',
  'The MMUL steady loop contains 32 vmac.f instructions in 36 decoded bundles and no accumulator stack spills. Increasing logical accumulator reuse is not needed to remove spilling in this selected implementation.',
  'Each low/high helper finishes dequantizing its whole K128/N32 half to an 8 KiB BF16 scratch tile before starting MMUL. Four output register blocks per M16 lane and reuse2 reread that scratch four times.',
  'The original packed W4 layout is consumed directly. Dequantization consists of packed loads, unpack/bit construction, subtraction, scale multiplication and BF16 conversion/stores; there are no software scalar integer-to-float calls.',
  'Dequantization, MMUL, local scratch traffic, FP32 partial loads/stores and graph synchronization all add work. Static instructions alone cannot establish their measured latency shares or whether the worker is compute-bound, memory-stalled or waiting for data.'
 ],
 'limits':['No clock frequency or hardware cycle trace was recorded in this audit.','Decoded bundle counts are not measured cycles: issue rules, pipeline overlap, memory latency, bank conflicts and DMA/lock stalls are not timed.','These are per-worker and aggregate-work counts; aggregate instructions across32 parallel workers must not be treated as serial elapsed work.','Global shared-memory bandwidth saturation is not established by the local scratch access counts.'],
 'reproduce_script':str(Path(__file__).resolve()),'reproduce_script_sha256':sha(Path(__file__))}
output=Path('/tmp/swiglu_projection_assembly.json');output.write_text(json.dumps(report,indent=2)+'\n')
print(output,sha(output))
for r in results:print(r['projection'],r['half'],[(x['kind'],x['decoded_bundles_per_hardware_iteration'],x['hardware_loop_iterations']) for x in r['hardware_loops']])
