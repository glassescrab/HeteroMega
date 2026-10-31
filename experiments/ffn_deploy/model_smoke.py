"""Real-weight model-hook check, using cached local weights/tokenizer only.

Run the isolated C++ smoke first. This checks completion counts, finite logits,
decode/unsupported-shape fallback and records numerical differences. It does
not establish pretrained accuracy or an end-to-end speedup.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--model-dir', type=Path, required=True)
    ap.add_argument('--build-dir', type=Path, default=Path('build'))
    ap.add_argument('--prompt-tokens', type=int, choices=(512, 1024), default=512)
    ap.add_argument('--inflight', type=int, choices=(1, 2), default=1)
    ap.add_argument('--base-mode', choices=('gpu', 'hetero'), default='gpu')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if not args.model_dir.is_dir():
        ap.error('--model-dir must already exist; this check does not download weights')
    root = Path(__file__).resolve().parents[2]
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    os.environ.pop('HETEROMEGA_FFN_CONFIG', None)
    os.environ.pop('HETEROMEGA_GPU_FFN', None)
    sys.path.insert(0, str((args.build_dir / 'py/unified_llm_w4a16').resolve()))
    # Import first: frontend otherwise prepends root/build ahead of a custom build directory.
    import torch
    import unified_llm_w4a16_hetero_libtorch as backend
    sys.path.insert(0, str(root / 'py/unified_llm_w4a16'))
    from llama3_8b_w4a16_model import LLaMA3W4A16Model
    from experiments.ffn_partition.contract import error_metrics

    settings = json.loads(args.config.read_text())
    directory = args.config.resolve().parent / settings['artifact_dir']
    manifest = json.loads((directory / 'final.xclbin.json').read_text())
    if (manifest['m'], manifest['hidden'], manifest['weight_n']) != (512, 4096, 14336):
        ap.error('this model check requires the M512/H4096/I14336 artifact')
    config = json.loads((root / 'py/unified_llm_w4a16/configs/configs_strixP_llama3_8b.json5').read_text())
    config.update(heterogeneity=args.base_mode, warmup=False, dummy_weights=False, prompt_len=args.prompt_tokens,
                  usePreSavedWeights=False, usePackedWeights=True, padPackedWeights=False,
                  cpu_decode=False, debug_verbosity=1, chunking=True, chunking_scheduled=False)
    config['gpu_chunking'] = dict(gpu_chunk_size=512, gpu_chunking_inflight=args.inflight)
    if args.base_mode == 'hetero':
        if args.prompt_tokens != 1024:
            ap.error('start native-NPU coexistence checks with the documented 1024-token chunk schedule')
        if not (root / 'hw_bins/npu2').is_dir():
            ap.error('native coexistence requires matching original artifacts under root/hw_bins/npu2')
        # The native loader otherwise defaults to the original author's checkout.
        os.environ['HETEROMOSAIC_ROOT'] = str(root)
        for group in config['kernels_gemm_chunked']:
            if group.get('prompt_len') == args.prompt_tokens:
                group['hetero_inflight'] = args.inflight
    args.output.parent.mkdir(parents=True, exist_ok=True)
    model_config = args.output.with_suffix('.model-config.json')
    model_config.write_text(json.dumps(config, indent=2) + '\n')
    report = dict(status='starting', scope=__doc__, prompt_tokens=args.prompt_tokens, inflight=args.inflight,
                  base_mode=args.base_mode, backend_file=backend.__file__, artifact_manifest=manifest)
    try:
        model = LLaMA3W4A16Model(model_path=str(args.model_dir.resolve()),
            tokenizer_path=str(args.model_dir.resolve()), device='cuda', max_seq_len=args.prompt_tokens + 128,
            config_path=str(model_config.resolve()))
        text = ('This experiment measures language model inference on heterogeneous processors. ' * 200)
        ids = model.tokenizer(text, return_tensors='pt')['input_ids'][:, :args.prompt_tokens].contiguous().to('cuda')
        if ids.shape != (1, args.prompt_tokens):
            raise RuntimeError('prompt did not reach requested length')
        report['input_sha256'] = hashlib.sha256(ids.cpu().numpy().tobytes()).hexdigest()

        def prefill():
            torch.cuda.synchronize()
            start = time.perf_counter()
            with torch.no_grad():
                out = model.model.forward(ids, 0)
            torch.cuda.synchronize()
            if not bool(torch.isfinite(out).all().item()):
                raise RuntimeError('nonfinite model logits')
            return out.detach().float().cpu().numpy(), time.perf_counter() - start

        native, report['original_prefill_seconds'] = prefill()
        os.environ['HETEROMEGA_FFN_CONFIG'] = str(args.config.resolve())
        before = model.model.merged_ffn_completed_dispatches()
        candidate, report['candidate_cold_prefill_seconds'] = prefill()
        expected = 32 * (args.prompt_tokens // 512)
        after = model.model.merged_ffn_completed_dispatches()
        if after - before != expected:
            raise RuntimeError(f'model hook completed {after-before} FFNs; expected {expected}')
        report['last_logits_error'] = error_metrics(candidate, native)
        warm, report['candidate_warm_prefill_seconds'] = prefill()
        report['candidate_repeat_error'] = error_metrics(warm, candidate)
        report['candidate_repeat_bit_exact'] = bool((warm == candidate).all())
        if not report['candidate_repeat_error']['passed']:
            raise RuntimeError('repeated candidate prefill is outside control tolerance')
        if model.model.merged_ffn_completed_dispatches() != after + expected:
            raise RuntimeError('warm prefill completion count mismatch')
        before = model.model.merged_ffn_completed_dispatches()
        with torch.no_grad():
            decode = model.model.forward(ids[:, -1:].contiguous(), args.prompt_tokens)
            fallback = model.model.forward(ids[:, :256].contiguous(), 0)
        torch.cuda.synchronize()
        if not bool(torch.isfinite(decode).all().item() and torch.isfinite(fallback).all().item()):
            raise RuntimeError('nonfinite fallback/decode logits')
        if model.model.merged_ffn_completed_dispatches() != before:
            raise RuntimeError('decode or unsupported M256 dispatched merged FFN work')
        report.update(status='completed_with_report_policy', completed_dispatches=before,
                      expected_dispatches=2 * expected, decode_fallback=True, unsupported_shape_fallback=True)
    except Exception as exc:
        report.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        print(json.dumps({k: report[k] for k in ('status', 'error', 'completed_dispatches') if k in report}, indent=2))


if __name__ == '__main__':
    main()
