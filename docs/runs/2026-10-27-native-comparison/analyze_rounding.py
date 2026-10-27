#!/usr/bin/env python3
"""Offline hypotheses for the constant-weight native projection diagnostic.

Reconstructs the seeded BF16 input and verifies its recorded SHA before comparing
simple reduction/rounding models with saved first-column values. These models
are not descriptions of the compiled kernel, and fit is not proof of causality.
No device execution or timing is performed. Only NumPy is required.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np


def array_hash(value):
    return sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def round_bf16(value, mode="nearest"):
    value = np.asarray(value, dtype=np.float32)
    bits = value.view(np.uint32)
    if mode == "nearest":
        bits = bits + np.uint32(0x7FFF) + ((bits >> 16) & 1)
    elif mode != "truncate":
        raise ValueError("unknown rounding mode")
    return (bits & np.uint32(0xFFFF0000)).view(np.float32)


def reconstruct_input(case, seed):
    if case == "constant_signed":
        half = round_bf16(np.random.default_rng(seed + 1).normal(
            size=(256, 4096)).astype(np.float32))
    elif case == "constant_exact":
        half = np.full((256, 4096), 1 / 16, np.float32)
    else:
        raise ValueError("this helper only models the two constant-weight cases")
    return np.concatenate((half, half))


def candidate_models(x):
    """FP32 grouped sums, with sequential group accumulation explicitly modeled."""
    product = x * np.float32(1 / 16)
    oracle = round_bf16(x.sum(axis=1, dtype=np.float64).astype(np.float32) / 16)
    yield "fp64_sum_then_fp32_then_bf16_nearest_oracle", oracle, {
        "family": "reference", "group_k": None, "rounding": "nearest"}
    control = round_bf16(product.sum(axis=1, dtype=np.float32))
    yield "fp32_sum_then_bf16_nearest_control", control, {
        "family": "FP32 NumPy sum control", "group_k": 4096, "rounding": "nearest"}
    for width in (8, 16, 32, 64, 128):
        # NumPy's FP32 group-summation order is a model detail, not a claim about
        # the machine's MAC tree. Each product is exact for the dyadic W=1/16.
        groups = product.reshape(len(x), -1, width).sum(axis=2, dtype=np.float32)
        for mode in ("nearest", "truncate"):
            accumulator = np.zeros(len(x), np.float32)
            for group in groups.T:
                accumulator = round_bf16(accumulator + group, mode)
            yield f"fp32_groups_bf16_acc_k{width}_{mode}", accumulator, {
                "family": "FP32 group sum then sequential BF16 accumulator",
                "group_k": width, "rounding": mode, "output_rounding": mode}
            accumulator = np.zeros(len(x), np.float32)
            for group in groups.T:
                accumulator += round_bf16(group, mode)
            # Stored output remains nearest-even in this family so only the
            # hypothesized group rounding differs between the two candidates.
            yield f"bf16_groups_fp32_acc_k{width}_{mode}", round_bf16(accumulator), {
                "family": "BF16 group sum then sequential FP32 accumulator",
                "group_k": width, "rounding": mode, "output_rounding": "nearest"}


def metrics(actual, expected):
    actual, expected = np.asarray(actual, np.float64), np.asarray(expected, np.float64)
    if actual.shape != expected.shape or not np.all(np.isfinite(actual)) or not np.all(np.isfinite(expected)):
        raise ValueError("saved vectors must be shape-matched and finite")
    difference = actual - expected
    denominator = np.linalg.norm(expected)
    return dict(max_abs_error=float(np.max(np.abs(difference))),
                relative_l2_error=float(np.linalg.norm(difference) / denominator) if denominator else None,
                mean_error=float(np.mean(difference)), rmse=float(np.sqrt(np.mean(difference ** 2))),
                exact_equal_rows=int(np.count_nonzero(actual == expected)), rows=len(actual))


def analyze(report, case_name):
    cases = [entry for entry in report["cases"] if entry["name"] == case_name]
    if len(cases) != 1:
        raise ValueError("report must contain exactly one selected case")
    entry = cases[0]
    x = reconstruct_input(case_name, int(report["config"]["seed"]))
    if array_hash(x) != entry["input_sha256"]:
        raise ValueError("reconstructed input does not match the saved input SHA256")
    models = list(candidate_models(x))
    oracle = models[0][1]
    result = dict(schema_version=1,
        interpretation="Offline arithmetic hypotheses only; no compiled-kernel, cycle, or causal attribution. No correctness thresholds are changed.",
        case=case_name, input_sha256=array_hash(x), reconstructed_input_matches=True,
        shape=list(x.shape), weight="all (q=9 - zero=8) * scale=1/16",
        model_details="FP32 NumPy sums within contiguous K groups; sequential accumulation across groups in increasing K order. Truncation drops low 16 FP32 bits. Group-rounded/FP32-accumulated models store output with BF16 nearest-even. No BFP shared-exponent or compiler MAC-tree model is asserted.",
        original_case_status=entry["status"], candidates=[], observations=[])
    for name, values, config in models:
        result["candidates"].append(dict(name=name, **config,
            vs_cpu_reference=metrics(values[256:], oracle[256:]),
            npu_rows_first_column=values[256:].tolist()))
    for record in entry["runs"]:
        for stage, values in record.get("constant_projection_values", {}).items():
            expected = np.asarray(values["expected_first_column"], np.float32)
            if not np.array_equal(expected, oracle):
                raise ValueError("saved CPU first-column oracle does not match reconstruction")
            actual = np.asarray(values["actual_first_column"], np.float32)
            if actual.shape != oracle.shape:
                raise ValueError("saved actual first-column shape does not match reconstruction")
            minimum, maximum = np.asarray(values["actual_row_min"]), np.asarray(values["actual_row_max"])
            if minimum.shape != oracle.shape or maximum.shape != oracle.shape:
                raise ValueError("saved row range shape does not match reconstruction")
            observation = dict(mode=record["mode"], repetition=record["repetition"], stage=stage,
                all_columns_identical_per_row=values["all_columns_identical_per_row"],
                row_range_matches_saved_flag=bool(np.all(minimum == maximum)) == values["all_columns_identical_per_row"],
                recorded_nonfinite_values=values["nonfinite_values"],
                first_column_in_recorded_row_range=bool(np.all(actual >= minimum) and np.all(actual <= maximum)),
                gpu_rows_vs_cpu=metrics(actual[:256], oracle[:256]),
                npu_rows_vs_cpu=metrics(actual[256:], oracle[256:]),
                duplicate_input_halves_output_difference=metrics(actual[256:], actual[:256]),
                models_vs_observed_npu_rows=[])
            for name, predicted, _ in models:
                observation["models_vs_observed_npu_rows"].append(dict(name=name,
                    **metrics(predicted[256:], actual[256:])))
            observation["models_vs_observed_npu_rows"].sort(key=lambda value: value["rmse"])
            result["observations"].append(observation)
    if not result["observations"]:
        raise ValueError("report has no v2 constant_projection_values evidence")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--case", choices=("constant_signed", "constant_exact"), default="constant_signed")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    result = analyze(json.loads(raw), args.case)
    result["provenance"] = dict(report_path=str(args.report.resolve()), report_sha256=sha256(raw).hexdigest(),
        script_path=str(Path(__file__).resolve()), script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        numpy_version=np.__version__)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    for item in result["observations"]:
        if item["mode"] == "native":
            best = item["models_vs_observed_npu_rows"][0]
            print(json.dumps(dict(mode=item["mode"], repetition=item["repetition"], stage=item["stage"],
                observed_vs_cpu=item["npu_rows_vs_cpu"], lowest_rmse_hypothesis=best)))


if __name__ == "__main__":
    main()
