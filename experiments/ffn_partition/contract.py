"""Common numerical and layout contract for the staged prefill FFN experiment.

Weights use the canonical unsigned W4A16 format from ``npu/ffn/reference.py``.
The FFN is bias-free and excludes normalization and residual addition. All three
projections use BF16 inputs/dequantized weights, FP32 accumulation, and BF16
outputs in the strict reference. Experimental BFP16 projection arithmetic is
compared with this same reference without changing its fixed error bounds.
SiLU is rounded before multiplication, which is rounded again. Each
device down-projection partial is rounded before the final BF16 boundary sum.

These NumPy routines are correctness oracles, never benchmark implementations.
"""

from dataclasses import dataclass
from numbers import Integral
from pathlib import Path
import sys

import numpy as np


# Existing NPU scripts use direct sibling imports. Use the same module identity
# when this contract is imported either by the standalone runner or unittest.
_NPU_DIR = str(Path(__file__).resolve().parents[2] / "npu" / "ffn")
if _NPU_DIR not in sys.path:
    sys.path.insert(0, _NPU_DIR)
from reference import W4A16, bf16, pack_int4, silu_multiply  # noqa: E402


ALIGNMENT = 128


def _aligned_dimension(value, name):
    if (isinstance(value, bool) or not isinstance(value, Integral)
            or value < ALIGNMENT or value % ALIGNMENT):
        raise ValueError(f"{name} must be an integer >=128 and divisible by 128")


def validate_shape(m, hidden, intermediate, npu_channels):
    """Validate this experiment's common GPU/NPU tile and group constraints."""
    for value, name in ((m, "M"), (hidden, "hidden"), (intermediate, "intermediate")):
        _aligned_dimension(value, name)
    if (isinstance(npu_channels, bool) or not isinstance(npu_channels, Integral)
            or not 0 <= npu_channels <= intermediate or npu_channels % ALIGNMENT):
        raise ValueError("npu_channels must be a multiple of 128 in [0, intermediate]")


@dataclass(frozen=True)
class FFNWeights:
    """Matching gate/up [I,H] and down [H,I] canonical quantized matrices."""

    gate: W4A16
    up: W4A16
    down: W4A16

    def __post_init__(self):
        if not all(isinstance(weight, W4A16) for weight in (self.gate, self.up, self.down)):
            raise ValueError("gate, up, and down must be canonical W4A16 weights")
        intermediate, hidden = self.gate.shape
        _aligned_dimension(hidden, "hidden")
        _aligned_dimension(intermediate, "intermediate")
        if self.up.shape != (intermediate, hidden) or self.down.shape != (hidden, intermediate):
            raise ValueError("expected gate/up [intermediate, hidden] and down [hidden, intermediate]")
        if any(weight.group_size != ALIGNMENT for weight in (self.gate, self.up, self.down)):
            raise ValueError("all FFN projections require quantization group_size=128")

    @property
    def hidden(self):
        return self.gate.shape[1]

    @property
    def intermediate(self):
        return self.gate.shape[0]


def random_weights(hidden, intermediate, seed=12832):
    """Create reproducible varied q/scale/zero arrays shared by both backends.

    Scale magnitudes are proportional to 1/sqrt(K); the constant accounts for
    unsigned int4's spread so complete FFN activations remain well-conditioned.
    Scales are BF16-rounded once before either backend packs them.
    """
    _aligned_dimension(hidden, "hidden")
    _aligned_dimension(intermediate, "intermediate")
    rng = np.random.default_rng(seed)

    def weight(n, k):
        q = rng.integers(0, 16, (n, k), dtype=np.uint8)
        zeros = rng.integers(0, 16, (n, k // ALIGNMENT), dtype=np.uint8)
        scales = bf16(rng.uniform(0.5, 1.5, zeros.shape).astype(np.float32)
                      / np.sqrt(np.float32(42.5 * k)))
        return W4A16(pack_int4(q), scales, zeros, ALIGNMENT)

    return FFNWeights(weight(intermediate, hidden), weight(intermediate, hidden),
                      weight(hidden, intermediate))


def split_weights(weights, npu_channels):
    """NPU owns the prefix; GPU owns its complement. Empty branches are None.

    Slices retain the original q/scale/zero storage. Down slices use exactly
    the same channel boundaries as both gate and up.
    """
    validate_shape(ALIGNMENT, weights.hidden, weights.intermediate, npu_channels)
    branches = {}
    for name, start, stop in (("npu", 0, npu_channels),
                             ("gpu", npu_channels, weights.intermediate)):
        branches[name] = (None if start == stop else FFNWeights(
            weights.gate.output_slice(start, stop),
            weights.up.output_slice(start, stop),
            weights.down.input_slice(start, stop)))
    return branches


def _input(x, weights):
    x = np.asarray(x, dtype=np.float32)
    if x.ndim != 2 or x.shape[1] != weights.hidden or not np.all(np.isfinite(x)):
        raise ValueError("input must be a finite [M, hidden] matrix matching the weights")
    validate_shape(x.shape[0], weights.hidden, weights.intermediate, 0)
    return bf16(x)


def _reference_branch(x, weights):
    gate = bf16(x @ weights.gate.dequantize(True).T)
    up = bf16(x @ weights.up.dequantize(True).T)
    intermediate = silu_multiply(gate, up, bf16_io=True)
    result = bf16(intermediate @ weights.down.dequantize(True).T)
    if not np.all(np.isfinite(result)):
        raise ValueError("FFN reference overflowed or produced nonfinite output")
    return result


def reference_full(x, weights):
    """Unpartitioned BF16 SwiGLU FFN output as FP32 values representing BF16."""
    return _reference_branch(_input(x, weights), weights)


def reference_partitioned(x, weights, npu_channels):
    """Return (BF16 boundary sum, BF16 per-device down partials).

    This intentionally differs from a reference that keeps down partials FP32
    through the reduction: current NPU projection artifacts output BF16.
    """
    x = _input(x, weights)
    partials = {name: (np.zeros_like(x) if branch is None else _reference_branch(x, branch))
                for name, branch in split_weights(weights, npu_channels).items()}
    output = bf16(partials["npu"] + partials["gpu"])
    if not np.all(np.isfinite(output)):
        raise ValueError("FFN partial reduction produced nonfinite output")
    return output, partials


def packed_output_to_activation(packed, m, channels):
    """Reorder native projection C into down-projection A without conversions.

    C: [Mb,Nb,mm4,nm4,mi4,ni8], where Nb=channels/32.
    A: [Mb,Kb,mm4,km16,mi4,ki8], where Kb=channels/128.
    The input and result contain exact BF16 bits in flat uint16 arrays. The
    permutation is valid for every bit pattern, including signed zero and NaN.
    """
    _aligned_dimension(m, "M")
    _aligned_dimension(channels, "channels")
    packed = np.asarray(packed)
    if packed.dtype != np.dtype(np.uint16) or packed.shape != (m * channels,):
        raise ValueError("packed C must be a flat native uint16 array with M*channels entries")
    # Split four adjacent N32 output tiles into one K128 input tile, then move
    # the four-N-tile axis inside the row-microtile axis.
    source = packed.reshape(m // 16, channels // 128, 4, 4, 4, 4, 8)
    return np.ascontiguousarray(source.transpose(0, 1, 3, 2, 4, 5, 6)).reshape(-1)


def error_metrics(actual, expected, rtol=0.03, atol=0.05, l2_limit=0.02):
    """Fixed L2 and tensor-normalized maximum bounds; zero references are exact.

    The maximum bound is atol + rtol * max(abs(expected)), not an elementwise
    relative-error guarantee. Limits are recorded and never adapted to a run.
    """
    if any(not np.isfinite(value) or value < 0 for value in (rtol, atol, l2_limit)):
        raise ValueError("error limits must be finite and nonnegative")
    actual, expected = np.asarray(actual, np.float32), np.asarray(expected, np.float32)
    if actual.shape != expected.shape or actual.size == 0:
        raise ValueError("actual and expected must have the same nonempty shape")
    if not np.all(np.isfinite(expected)):
        raise ValueError("expected output must be finite")
    finite = bool(np.all(np.isfinite(actual)))
    metrics = {"passed": False, "correctness": "failed", "finite": finite,
               "max_abs_error": None, "relative_l2_error": None,
               "normalized_max_error": None, "rms_error": None,
               "rtol": float(rtol), "atol": float(atol), "l2_limit": float(l2_limit)}
    if not finite:
        return metrics
    delta = actual.astype(np.float64) - expected.astype(np.float64)
    reference_norm = float(np.linalg.norm(expected.astype(np.float64)))
    max_ref = float(np.max(np.abs(expected)))
    max_error = float(np.max(np.abs(delta)))
    relative_l2 = (float(np.linalg.norm(delta)) / reference_norm if reference_norm
                   else (0.0 if max_error == 0 else None))
    normalized_max = max_error / max_ref if max_ref else (0.0 if max_error == 0 else None)
    max_limit = float(atol + rtol * max_ref)
    passed = (max_error == 0 if reference_norm == 0
              else relative_l2 <= l2_limit and max_error <= max_limit)
    metrics.update(passed=bool(passed), correctness="passed" if passed else "failed",
                   max_abs_error=max_error, relative_l2_error=relative_l2,
                   normalized_max_error=normalized_max,
                   rms_error=float(np.sqrt(np.mean(delta * delta))),
                   reference_max_abs=max_ref, max_error_limit=max_limit,
                   elementwise_close_fraction=float(np.mean(np.isclose(actual, expected, rtol=rtol, atol=atol))))
    return metrics


def resolve_accuracy_policy(npu_arithmetic="bf16", accuracy_policy=None):
    """BFP16 may report finite numerical differences; BF16 stays strict by default."""
    if npu_arithmetic not in ("bf16", "bfp16"):
        raise ValueError("npu_arithmetic must be bf16 or bfp16")
    policy = accuracy_policy or ("report" if npu_arithmetic == "bfp16" else "strict")
    if policy not in ("strict", "report"):
        raise ValueError("accuracy_policy must be strict or report")
    return policy


class OutputIntegrity:
    """Detect broken execution independently of approximate arithmetic accuracy.

    Each identity must name one fixed input/weight combination on one branch.
    Snapshots are copied because device/host output storage is reused. Distinct
    references producing identical outputs indicate stale or nonresponsive
    execution; repeated inputs must reproduce the exact finite output.
    These checks are necessary guards, not a proof of numerical correctness.
    """

    def __init__(self):
        self.observations = {}

    def observe(self, actual, expected, input_id):
        actual, expected = np.asarray(actual), np.asarray(expected)
        failures = []
        previous = self.observations.get(input_id)
        if previous is not None and not np.array_equal(actual, previous[0]):
            failures.append("repeated_input_changed_output")
        for identity, (output, reference) in self.observations.items():
            if (identity != input_id and not np.array_equal(expected, reference)
                    and np.array_equal(actual, output)):
                failures.append("distinct_inputs_identical_output")
                break
        if previous is None and np.all(np.isfinite(actual)):
            self.observations[input_id] = (actual.copy(), expected.copy())
        return failures


def accuracy_metrics(actual, expected, policy="strict", integrity=None, input_id=None):
    """Keep numerical pass/fail separate from permission to time an experiment.

    Report mode never changes ``passed`` or the fixed ``error_metrics`` limits.
    It may accept finite, nonzero deviations, while nonfinite/zero/stale and
    repeatability failures remain fatal. GPU callers always use strict mode.
    """
    if policy not in ("strict", "report"):
        raise ValueError("accuracy_policy must be strict or report")
    metrics = error_metrics(actual, expected)
    failures = []
    if not metrics["finite"]:
        failures.append("nonfinite_output")
    elif not np.any(expected) and np.any(actual):
        failures.append("zero_reference_nonzero_output")
    elif np.any(expected) and not np.any(actual):
        failures.append("nonzero_reference_zero_output")
    if integrity is not None:
        failures.extend(integrity.observe(actual, expected, input_id))
    accepted = not failures and (metrics["passed"] or policy == "report")
    metrics.update(accuracy_policy=policy, accepted=bool(accepted),
                   structural_failures=failures,
                   accuracy_status=("structural_failure" if failures else
                                    "within_tolerance" if metrics["passed"] else
                                    "reported_deviation" if accepted else "outside_tolerance"))
    return metrics


def accuracy_summary(metrics):
    """Summarize explicit numerical checks without promoting accepted differences."""
    metrics = list(metrics)
    passed = all(item["passed"] for item in metrics)
    accepted = all(item["accepted"] for item in metrics)
    return {"passed": passed, "accepted": accepted, "check_count": len(metrics),
            "outside_tolerance_count": sum(not item["passed"] for item in metrics),
            "accuracy_status": ("failed" if not accepted else
                                "within_tolerance" if passed else "reported_deviations")}


def benchmark_stats(samples_us):
    """Summarize actual complete-invocation measurements, never inferred times."""
    samples = np.asarray(samples_us, dtype=np.float64)
    if samples.ndim != 1 or samples.size == 0 or not np.all(np.isfinite(samples)) or np.any(samples <= 0):
        raise ValueError("samples must be a nonempty one-dimensional sequence of finite positive times")
    return {"count": int(samples.size), "median_us": float(np.median(samples)),
            "p10_us": float(np.percentile(samples, 10)), "p90_us": float(np.percentile(samples, 90)),
            "min_us": float(np.min(samples)), "max_us": float(np.max(samples))}
