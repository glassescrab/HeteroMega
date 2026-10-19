"""Reproduce the independent saved-report SwiGLU correctness audit.

Run from any working directory with NumPy available::

    python experiments/ffn_partition/results/swiglu_fusion/verify_exact.py

This regenerates exact_verification.json beside the saved evidence. It checks
recorded metrics, hashes, launch counters, fixed tolerances, input/weight seeds,
current source/build contracts, power snapshots and the earlier source archive.
It does not launch hardware or modify measurement reports. Device output arrays
and compiled binaries are absent, so their recorded hashes cannot be recomputed.
The report records this auditor's own source hash for reproducibility.
"""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json, math, re, sys, tarfile
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from experiments.ffn_partition.contract import random_weights,bf16
from experiments.ffn_partition.npu_backend import _artifact_specs,_build_contract
from prefill_reference import bf16_bits
D=ROOT/'experiments/ffn_partition/results/swiglu_fusion'
H=lambda b:sha256(b).hexdigest()
AH=lambda x:H(np.ascontiguousarray(x).tobytes())
fail=[]
def require(ok,where):
 if not ok: fail.append(where)
def sha_valid(x):return isinstance(x,str) and re.fullmatch('[0-9a-f]{64}',x) is not None
report_out=[]
for name,before,after,expected_cases in [('exact_smoke.json','power_before_smoke.json','power_after_smoke.json',[(128,128,128)]),('exact_m512.json','power_before_exact_retry.json','power_after_exact_retry.json',[(512,4096,384),(512,4096,896)])]:
 r=json.loads((D/name).read_text()); checks=r['checks']; label=name
 require(r['status']=='passed',label+'/status')
 require([(c['m'],c['hidden'],c['channels']) for c in r['cases']]==expected_cases,label+'/case_shapes')
 require(len(checks)==60*len(expected_cases),label+'/check_count')
 require(all(c.get('passed') is True for c in checks.values()),label+'/all_checks_passed')
 source_checks={p:H((ROOT/p).read_bytes())==h for p,h in r['source_sha256'].items()}
 for p,ok in source_checks.items(): require(ok,label+'/source/'+p)
 case_out=[]; total_completions=0; exact_count=0; maxerr={'z':{'relative_l2_error':0.,'max_abs_error':0.},'ffn':{'relative_l2_error':0.,'max_abs_error':0.}}
 for case in r['cases']:
  m,h,p=(case[k] for k in ('m','hidden','channels')); prefix=f'{name}/p{p}'
  weights=random_weights(h,p,r['config']['seed'])
  weights_match=case['weights_sha256']=={proj:{component:AH(getattr(getattr(weights,proj),component)) for component in ('packed','scales','zeros')} for proj in ('gate','up','down')}
  require(weights_match,prefix+'/regenerated_weights')
  rng=np.random.default_rng(r['config']['input_seed'])
  a,b=[bf16(rng.normal(size=(m,h)).astype(np.float32)) for _ in range(2)]
  inputs={'random_a':a,'random_b':b,'zero':np.zeros_like(a),'repeat_a':a.copy()}
  inputs_match=case['inputs_sha256']=={k:AH(bf16_bits(v)) for k,v in inputs.items()}
  require(inputs_match,prefix+'/regenerated_inputs')
  expected_names=set(); variants={}; artifact_sources=set()
  for vn,fused in [('gate_up_then_silu',False),('onchip_swiglu',True)]:
   v=case['variants'][vn]; md=v['metadata']; base=f'p{p}/{vn}'; stages={'swiglu','down'} if fused else {'gate_up','silu_mul','down'}; projections=stages-{'silu_mul'}; launches=len(stages)
   expected_names|={base+'/'+x for x in ('launches_per_run','completed_dispatches','one_fixed_weight_upload','branch_contract')}
   require(v['completed_dispatches']=={s:4 for s in stages},prefix+'/'+vn+'/counter_per_runner')
   require(v['weight_upload_counts']=={s:1 for s in projections},prefix+'/'+vn+'/weight_uploads')
   require(md['fuse_swiglu'] is fused and md['fuse_gate_up'] is True and md['launches_per_run']==launches and md['fixed_weight_uploads']==2 and md['cpu_activation_fallback'] is False,prefix+'/'+vn+'/metadata')
   require(md['columns_requested']==8 and md['npu_design']=='array8',prefix+'/'+vn+'/array8')
   require(md['host_bo_io_bytes_per_run_estimate']==4*m*h+(4 if fused else 12)*m*p,prefix+'/'+vn+'/payload_estimate')
   require(checks[base+'/launches_per_run']['actual']==[{s:1 for s in stages}]*4,prefix+'/'+vn+'/launch_deltas')
   require(checks[base+'/completed_dispatches']['actual']==v['completed_dispatches'],prefix+'/'+vn+'/counter_crosscheck')
   require(checks[base+'/one_fixed_weight_upload']['actual']==[{s:1 for s in projections}]*5,prefix+'/'+vn+'/uploads_every_run')
   require(len(v['diagnostics'])==4,prefix+'/'+vn+'/diagnostic_count')
   for i,diag in enumerate(v['diagnostics']):
    require(set(diag['dispatch_wait_us'])==stages and diag['completed_dispatches_total']==launches*(i+1),prefix+'/'+vn+f'/diagnostic_counter{i}')
    require(diag['weight_upload_counts']=={s:1 for s in projections},prefix+'/'+vn+f'/diagnostic_weights{i}')
    for stage in stages:
     require(0<=diag['dispatch_wait_us'][stage]<=diag['stages'][stage+'_with_host_io_us'],prefix+'/'+vn+f'/nested_interval{i}/{stage}')
   specs=_artifact_specs(m,h,p,D/'not_loaded',columns=8,design='array8',fuse_gate_up=not fused,fuse_swiglu=fused)
   require(set(specs)==set(md['artifacts']),prefix+'/'+vn+'/artifact_set')
   artifacts=[]
   for stage,artifact in md['artifacts'].items():
    spec=specs[stage]; contract=artifact['build_contract']; manifest=artifact['manifest']
    require(contract==_build_contract(spec),prefix+'/'+vn+'/'+stage+'/current_build_contract')
    for k,value in contract['expected_manifest'].items(): require(manifest.get(k)==value,prefix+'/'+vn+'/'+stage+'/manifest/'+k)
    for path,digest in contract['source_sha256'].items():
     artifact_sources.add(path);require(H((ROOT/path).read_bytes())==digest,prefix+'/'+vn+'/'+stage+'/source/'+path)
    require(manifest.get('target_mlir_aie_commit')==contract['target_mlir_aie_commit'],prefix+'/'+vn+'/'+stage+'/compiler_commit')
    require(sha_valid(manifest.get('xclbin_sha256')) and sha_valid(manifest.get('insts_sha256')),prefix+'/'+vn+'/'+stage+'/recorded_binary_hash_format')
    artifacts.append({'stage':stage,'source_and_build_contract_match':(contract==_build_contract(spec) and all(H((ROOT/path).read_bytes())==digest for path,digest in contract['source_sha256'].items())),'xclbin_sha256':manifest['xclbin_sha256'],'insts_sha256':manifest['insts_sha256']})
   for input_name in inputs:
    for stage,shape in [('z',[m*p]),('ffn',[m,h])]:
     for suffix in ('buffer_contract','vs_cpu'): expected_names.add(base+'/'+input_name+'/'+stage+'_'+suffix)
     buf=checks[base+'/'+input_name+'/'+stage+'_buffer_contract'];err=checks[base+'/'+input_name+'/'+stage+'_vs_cpu']
     require(buf['dtype']==buf['expected_dtype']=='uint16' and buf['shape']==buf['expected_shape']==shape,prefix+'/'+vn+'/'+input_name+'/'+stage+'/buffer')
     require((err['rtol'],err['atol'],err['l2_limit'])==(.03,.05,.02),prefix+'/'+vn+'/'+input_name+'/'+stage+'/fixed_limits')
     require(err['finite'] is True and err['correctness']=='passed',prefix+'/'+vn+'/'+input_name+'/'+stage+'/finite')
     limit=.05+.03*err['reference_max_abs']
     require(math.isclose(err['max_error_limit'],limit,rel_tol=1e-14,abs_tol=1e-14),prefix+'/'+vn+'/'+input_name+'/'+stage+'/max_bound_formula')
     require(0<=err['relative_l2_error']<=.02 and 0<=err['max_abs_error']<=limit,prefix+'/'+vn+'/'+input_name+'/'+stage+'/within_bounds')
     if input_name=='zero':
      expected_names.add(base+'/zero/'+stage+'_zero')
      require(err['reference_max_abs']==err['max_abs_error']==err['relative_l2_error']==0,prefix+'/'+vn+'/zero/'+stage)
     for field in ('relative_l2_error','max_abs_error'):maxerr[stage][field]=max(maxerr[stage][field],err[field])
   for stage in ('z','ffn'):
    expected_names|={base+'/'+stage+'_repeat',base+'/'+stage+'_changed_input'}
    hashes=v['output_sha256'];require(hashes['random_a'][stage]==hashes['repeat_a'][stage] and hashes['random_b'][stage]!=hashes['random_a'][stage],prefix+'/'+vn+'/'+stage+'/reuse_hashes')
    same=checks[base+'/'+stage+'_repeat']
    require(same['actual_sha256']==same['expected_sha256']==hashes['random_a'][stage] and same['mismatched_elements']==0 and same['dtype']==same['expected_dtype']=='uint16',prefix+'/'+vn+'/'+stage+'/repeat_exact')
   total_completions+=sum(v['completed_dispatches'].values())
   variants[vn]={'launches_per_invocation':launches,'completed_dispatches':sum(v['completed_dispatches'].values()),'weight_uploads':v['weight_upload_counts'],'artifact_contracts':artifacts}
  for inp in inputs:
   for stage,shape in [('z',[m*p]),('ffn',[m,h])]:
    key=f'p{p}/{inp}/{stage}_onchip_vs_gate_up_then_silu';expected_names.add(key);check=checks[key]
    baseline=case['variants']['gate_up_then_silu']['output_sha256'][inp][stage];candidate=case['variants']['onchip_swiglu']['output_sha256'][inp][stage]
    require(check['mismatched_elements']==0 and check['dtype']==check['expected_dtype']=='uint16' and check['shape']==check['expected_shape']==shape,prefix+'/'+key+'/bit_contract')
    require(check['actual_sha256']==check['expected_sha256']==baseline==candidate and sha_valid(baseline),prefix+'/'+key+'/matching_hashes');exact_count+=1
  require({key for key in checks if key.startswith(f'p{p}/')}==expected_names,prefix+'/exact_check_coverage')
  case_out.append({'m':m,'hidden':h,'channels':p,'checks':len(expected_names),'input_and_weight_hashes_regenerated':bool(inputs_match and weights_match),'cross_variant_bit_comparisons':8,'variants':variants,'artifact_source_files_verified':sorted(artifact_sources)})
 powers=[]
 for power_file in (before,after):
  data=json.loads((D/power_file).read_text());devs=data['devices']
  selected=[(dev['device_id'],pl) for dev in devs for pl in dev['platforms']]
  require(len(selected)==1,label+'/'+power_file+'/single_device')
  dev,pl=selected[0]
  require(pl['status']['power_mode']=='default' and pl['static_region']['total_columns']=='8',label+'/'+power_file+'/power_array8')
  powers.append({'file':power_file,'sha256':H((D/power_file).read_bytes()),'device_id':dev,'mode':pl['status']['power_mode'],'timestamp_utc':parsedate_to_datetime(data['schema_version']['creation_date']).isoformat(),'electrical_measurement_available':not bool(pl.get('electrical',{}).get('error_msg'))})
 start=datetime.fromisoformat(r['timestamp_utc'])
 require(datetime.fromisoformat(powers[0]['timestamp_utc'])<=start<=datetime.fromisoformat(powers[1]['timestamp_utc']),label+'/power_snapshot_start_order')
 require(powers[0]['device_id']==powers[1]['device_id'],label+'/same_power_device')
 report_out.append({'file':name,'sha256':H((D/name).read_bytes()),'recorded_status':r['status'],'checks':len(checks),'recorded_all_passed':all(c.get('passed') is True for c in checks.values()),'source_hashes_match_current_tree':source_checks,'cross_variant_exact_bit_comparisons':exact_count,'completed_npu_dispatches':total_completions,'max_cpu_errors':maxerr,'cases':case_out,'power_boundary_snapshots':powers})
interrupted=json.loads((D/'exact_m512_interrupted.json').read_text())
require(interrupted['status']=='preparing' and not interrupted['checks'] and not interrupted['cases'],'interrupted_report_not_success')
archive_manifest=json.loads((D/'baseline_source_manifest.json').read_text())
require(H((D/'baseline_sources.tar.gz').read_bytes())==archive_manifest['archive_sha256'],'baseline_archive_hash')
with tarfile.open(D/'baseline_sources.tar.gz') as tar:
 files={member.name.lstrip('./'):H(tar.extractfile(member).read()) for member in tar.getmembers() if member.isfile()}
 require(files==archive_manifest['source_sha256'],'baseline_archive_file_hashes')
output={'status':'passed' if not fail else 'failed','verification_kind':'independent offline audit of saved hardware reports','verified_at_utc':datetime.now(timezone.utc).isoformat(),'auditor_script':'verify_exact.py','script_sha256':H(Path(__file__).read_bytes()),'verification_numpy':np.__version__,'total_completed_report_checks':sum(r['checks'] for r in report_out),'cross_variant_exact_bit_comparisons':sum(r['cross_variant_exact_bit_comparisons'] for r in report_out),'completed_npu_dispatches':sum(r['completed_npu_dispatches'] for r in report_out),'reports':report_out,'excluded_incomplete_report':{'file':'exact_m512_interrupted.json','sha256':H((D/'exact_m512_interrupted.json').read_bytes()),'status':interrupted['status'],'checks':0,'reason':'interrupted before case completion; excluded from successful check/launch totals'},'baseline_source_archive':{'archive_sha256':archive_manifest['archive_sha256'],'files_verified':len(files),'matches_manifest':files==archive_manifest['source_sha256']},'limitations':['Native output arrays and compiled binaries are not in this downloaded evidence set: exact-bit and numerical findings are cross-checked against saved metrics/hashes, not recomputed from device output bytes.','Inputs and canonical weights were independently regenerated from recorded seeds and matched saved hashes.','Artifact source/build contracts were recomputed against current source; binary hash strings were checked for format and recording, not independently rehashed from absent binaries.','Both before/after snapshots report default mode. They are not continuous power or clock monitoring; performance mode is not established.','Electrical telemetry reports unsupported operation; no measured watts or energy is available.','These are NPU-only correctness runs, not timing, whole-model accuracy, or end-to-end prefill measurements.'],'failures':fail}
(D/'exact_verification.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:output[k] for k in ('status','total_completed_report_checks','cross_variant_exact_bit_comparisons','completed_npu_dispatches','failures')},indent=2))
for r in report_out:print(r['file'],r['max_cpu_errors'])
