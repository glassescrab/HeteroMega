from pathlib import Path
from huggingface_hub import snapshot_download
rev=Path('/notebooks/heteromega-baseline-logs/model-revision.txt').read_text().strip().split('\\')[0]
print('Pinned model revision:',rev,flush=True)
snapshot_download(repo_id='hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4', revision=rev, local_dir='/notebooks/heteromosaic-model', allow_patterns=['*.json','*.safetensors','*.model'])
print('MODEL DOWNLOAD COMPLETE',flush=True)
