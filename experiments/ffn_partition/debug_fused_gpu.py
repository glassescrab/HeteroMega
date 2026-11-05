"""Diagnose the packed gate/up fused-activation epilogue against silu_mul."""
import argparse
import json

import numpy as np

from .contract import random_weights, split_weights
from .run_upstream_partition import prepare_original_weights


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--m', type=int, default=512)
    ap.add_argument('--hidden', type=int, default=4096)
    ap.add_argument('--intermediate', type=int, default=14336)
    ap.add_argument('--npu-channels', type=int, default=6400)
    ap.add_argument('--seed', type=int, default=12832)
    ap.add_argument('--output', type=__import__('pathlib').Path, required=True)
    args = ap.parse_args()
    import torch
    from .teammate_gpu import TeammateGPUBranch
    weights = random_weights(args.hidden, args.intermediate, args.seed)
    original = prepare_original_weights(weights)
    branch = TeammateGPUBranch.from_upstream(*(w.data for w in original),
        args.hidden, args.intermediate, args.npu_channels, args.intermediate,
        args.m)
    channels = branch.channels
    stream = torch.cuda.current_stream(branch.device)
    rng = np.random.default_rng(args.seed + 7)
    x = torch.from_numpy(rng.normal(size=(args.m, args.hidden)).astype(np.float32)).to(
        branch.device, dtype=torch.bfloat16)
    packed = branch.weights[0]
    # Non-fused control: gate/up GEMM then the existing silu_mul.
    branch._module.linear(branch.gate_up_output, x, packed, args.hidden, 2 * channels,
        args.hidden, 2 * channels, int(stream.cuda_stream), False)
    branch._module.silu_mul(branch.gate_up_output, branch.activation, 1, int(stream.cuda_stream))
    torch.cuda.synchronize(branch.device)
    reference = branch.activation.clone()
    # Fused epilogue.
    fused = torch.empty_like(branch.activation)
    branch._module.linear(fused, x, packed, args.hidden, 2 * channels,
        args.hidden, 2 * channels, int(stream.cuda_stream), True)
    torch.cuda.synchronize(branch.device)
    diff = (fused.float() - reference.float()).abs()
    result = dict(channels=channels, m=args.m,
        reference_zero=bool((reference == 0).all()), fused_zero=bool((fused == 0).all()),
        exact=bool(torch.equal(fused, reference)),
        max_abs=float(diff.max()), mean_abs=float(diff.mean()),
        reference_abs_mean=float(reference.float().abs().mean()),
        fused_abs_mean=float(fused.float().abs().mean()),
        mismatch_count=int((diff != 0).sum()),
        first_mismatches=[[int(i), int(j), float(fused[i, j].float()), float(reference[i, j].float())]
            for i, j in zip(*torch.nonzero(diff != 0)[:5].T.tolist())] if not torch.equal(fused, reference) else [])
    print(json.dumps(result, indent=2))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    branch._module = None
    torch.cuda.empty_cache()


if __name__ == '__main__':
    main()
