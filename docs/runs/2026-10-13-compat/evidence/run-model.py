import sys,json,time,hashlib
from pathlib import Path
import torch
root=Path('/notebooks/HeteroMosaic-baseline')
sys.path.insert(0,str(root/'py/unified_llm_w4a16'))
from llama3_8b_w4a16_model import LLaMA3W4A16Model
mode=sys.argv[1]
config=Path('/notebooks/heteromega-compat-2026-10-13')/(mode+'-model-config.json')
c=json.loads((root/'py/unified_llm_w4a16/configs/configs_strixP_llama3_8b.json5').read_text())
c.update(heterogeneity=mode,prompt_len=1024,usePreSavedWeights=False,warmup=False,debug_verbosity=1)
config.write_text(json.dumps(c,indent=2))
m=LLaMA3W4A16Model(model_path='/notebooks/heteromosaic-model',tokenizer_path='/notebooks/heteromosaic-model',max_seq_len=1536,device='cuda',config_path=str(config))
text=('This experiment measures language model inference on heterogeneous processors. '*200)+' Explain the purpose of this experiment.'
ids=m.tokenizer(text,return_tensors='pt')['input_ids'][:,:1024].contiguous().to('cuda')
assert ids.shape==(1,1024)
record={'mode':mode,'input_ids':ids.cpu().tolist(),'context_capacity':1536,'max_new_tokens':8,'temperature':0.0}
record['input_sha256']=hashlib.sha256(ids.cpu().numpy().tobytes()).hexdigest()
print('INPUT',record['input_sha256'],ids.shape,flush=True)
torch.cuda.synchronize(); t=time.perf_counter()
with torch.no_grad():out=m.generate(ids,max_new_tokens=8,temperature=0.0)
torch.cuda.synchronize(); record['generation_wall_seconds']=time.perf_counter()-t
record['output_ids']=out.cpu().tolist(); record['generated_ids']=out[0,1024:].cpu().tolist()
record['generated_text']=m.tokenizer.decode(record['generated_ids'],skip_special_tokens=False)
Path('/notebooks/heteromega-compat-2026-10-13',mode+'-model-result.json').write_text(json.dumps(record,indent=2))
print('MODEL GENERATION COMPLETE',json.dumps({k:v for k,v in record.items() if k not in ['input_ids','output_ids']}),flush=True)
