"""Untimed native HeteroMosaic gate/up diagnostics using controlled W4 fixtures.

The existing binding still executes its original complete FFN. Only captured
gate/up outputs are diagnosed; no performance or full-FFN accuracy is claimed.
Run once per fresh process: imported allocations stay alive until process exit.
"""

import argparse
import json
import os
from pathlib import Path
import traceback

import numpy as np

from .contract import FFNWeights, OutputIntegrity, W4A16, bf16, random_weights
from .gpu_backend import pack_heteromosaic_weights
from .native_heteromosaic import (ARTIFACT_STEM, FW_DIR, ROOT, array_hash,
    checked_metrics, file_hash, load_native_extension, native_config, save,
    source_provenance)


CASES = ("constant_signed", "constant_exact", "onehot_qzeros", "onehot_scales", "canonical_random")


def representative_k_indices(hidden=4096):
    if hidden % 128:
        raise ValueError("K must be divisible by 128")
    return (np.arange(hidden // 128)[:, None] * 128 +
            np.array([0, 1, 7, 8, 63, 64, 126, 127])[None, :]).reshape(-1)


def make_weight(hidden, intermediate, *, seed, kind):
    """Canonical [N,K] storage, never raw NPU-format edits."""
    rng = np.random.default_rng(seed)
    groups = hidden // 128
    if kind == "qzeros":
        # Uniform bytes independently encode two random unsigned nibbles.
        packed = rng.integers(0, 256, (intermediate, hidden // 2), dtype=np.uint8)
        zeros = rng.integers(0, 16, (intermediate, groups), dtype=np.uint8)
    else:
        packed = np.full((intermediate, hidden // 2), 0x99, np.uint8)
        zeros = np.full((intermediate, groups), 8, np.uint8)
    scales = np.full((intermediate, groups), 1 / 16, np.float32)
    if kind == "scales":
        powers = ((np.arange(intermediate)[:, None] + np.arange(groups)[None, :]) % 4) - 1
        scales = np.ldexp(scales, powers).astype(np.float32)
    return W4A16(packed, scales, zeros, 128)


def make_fixture(name, seed=12832, hidden=4096, intermediate=14336):
    if name not in CASES:
        raise ValueError("unknown diagnostic fixture")
    rng = np.random.default_rng(seed + 1)
    if name == "canonical_random":
        weights = random_weights(hidden, intermediate, seed)
    else:
        kind = "qzeros" if name == "onehot_qzeros" else "scales" if name == "onehot_scales" else "constant"
        gate = make_weight(hidden, intermediate, seed=seed + 2, kind=kind)
        up = make_weight(hidden, intermediate, seed=seed + 3, kind=kind)
        # Zero down weights keep the unmodified full binding numerically quiet;
        # this helper validates projections only and never times this workload.
        down = W4A16(np.zeros((hidden, intermediate // 2), np.uint8),
                     np.full((hidden, intermediate // 128), 1 / 16, np.float32),
                     np.zeros((hidden, intermediate // 128), np.uint8), 128)
        weights = FFNWeights(gate, up, down)
    indices = representative_k_indices(hidden)
    half_m = len(indices)
    if name.startswith("onehot"):
        half = np.zeros((half_m, hidden), np.float32)
        half[np.arange(half_m), indices] = 1
    elif name == "constant_exact":
        half = np.full((half_m, hidden), 1 / 16, np.float32)
    else:
        half = bf16(rng.normal(size=(half_m, hidden)).astype(np.float32))
    x = np.concatenate((half, half), axis=0)
    return weights, x, indices


def projection_reference(name, x, weight, indices):
    """Canonical-coordinate oracle; basis probes avoid any K reduction."""
    if name.startswith("onehot"):
        source = weight.packed[:, indices // 2]
        q = (source >> (4 * (indices % 2))[None, :]) & 15
        values = bf16((q.astype(np.float32) - weight.zeros[:, indices // 128]) *
                      bf16(weight.scales[:, indices // 128]))
        half = values.T
        return np.concatenate((half, half), axis=0)
    if name.startswith("constant"):
        summed = bf16(x.sum(axis=1, dtype=np.float64).astype(np.float32) / 16)
        return np.broadcast_to(summed[:, None], (x.shape[0], weight.shape[0])).copy()
    return bf16(x @ weight.dequantize(True).T)


def fixture_hashes(weights, x):
    return dict(input_sha256=array_hash(x), canonical={
        name: {field + "_sha256": array_hash(getattr(weight, field))
               for field in ("packed", "scales", "zeros")}
        for name, weight in zip(("gate", "up", "down"), (weights.gate, weights.up, weights.down))})


def constant_projection_values(actual, expected):
    """Small raw-value evidence for constant-W reduction diagnostics."""
    actual, expected = np.asarray(actual), np.asarray(expected)
    if actual.ndim != 2 or actual.shape != expected.shape or not actual.size:
        raise ValueError("constant projection evidence requires matching nonempty matrices")

    def serializable(values):
        return [float(value) if np.isfinite(value) else None for value in values]

    minimum, maximum = np.min(actual, axis=1), np.max(actual, axis=1)
    return dict(actual_first_column=serializable(actual[:, 0]),
                expected_first_column=serializable(expected[:, 0]),
                actual_row_min=serializable(minimum), actual_row_max=serializable(maximum),
                all_columns_identical_per_row=bool(np.all(minimum == maximum)),
                nonfinite_values=int(np.count_nonzero(~np.isfinite(actual))),
                shape=list(actual.shape))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-root", type=Path, default=ROOT)
    parser.add_argument("--native-library", type=Path, default=os.environ.get("HETEROMOSAIC_NATIVE_LIBRARY"))
    parser.add_argument("--driver-include", type=Path)
    parser.add_argument("--seed", type=int, default=12832)
    parser.add_argument("--cases", default="constant_signed,constant_exact,onehot_qzeros")
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--output", type=Path, default=Path("experiments/ffn_partition/results/native_projection_diagnostic.json"))
    parser.add_argument("--verbose-build", action="store_true")
    args = parser.parse_args(argv)
    cases = list(dict.fromkeys(args.cases.split(",")))
    if not cases or any(name not in CASES for name in cases):
        parser.error("cases must be comma-separated names from " + ",".join(CASES))
    if args.repetitions < 2:
        parser.error("at least two repetitions are required for exact repeat checks")
    args.native_root = args.native_root.resolve()
    if args.native_library is None:
        args.native_library = args.native_root / "build/py/unified_llm_w4a16/unified_llm_w4a16_hetero_libtorch.so"
    report = dict(schema_version=1, status="preparing", scope="untimed captured native gate/up projection diagnostics",
        excluded_claims=["FFN correctness", "performance", "model accuracy"],
        config={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        provenance=source_provenance(args.native_root), cases=[], completed_npu_dispatches=0,
        expected_npu_dispatches=0, numerical_policy="unchanged strict rtol=.03 atol=.05 relative-L2<=.02",
        projection_checks="captured gate/up before pointwise overwrite; all 14336 columns, full 512 rows and GPU [0,256)/NPU [256,512) owners; native versus GPU and identical-input row halves; exact_equal is reported separately from unchanged numerical acceptance",
        native_config=native_config())
    report["provenance"]["source_sha256"][str(Path(__file__).resolve())] = file_hash(__file__)
    module = None
    keepalive = []
    config_path = args.output.with_suffix(".native_config.json").resolve()
    save(report["native_config"], config_path)
    report.update(native_config_path=str(config_path), native_config_sha256=file_hash(config_path))
    integrity = {(mode, stage, owner): OutputIntegrity() for mode in ("baseline", "native")
                 for stage in ("gate", "up") for owner in ("all", "gpu_rows", "npu_rows")}
    try:
        paths = [args.native_root / FW_DIR / f"{prefix}_{ARTIFACT_STEM}.{extension}"
                 for prefix, extension in (("final", "pdi"), ("insts", "txt"))]
        report["native_artifacts"] = [{"path": str(path), "sha256": file_hash(path)} for path in paths]
        os.environ["HETEROMOSAIC_ROOT"] = str(args.native_root)
        module, report["native_build"] = load_native_extension(args)
        import torch
        torch.cuda.set_device(0)
        report["selected_native_configs"] = module.initialize(str(config_path), 256)
        gate = torch.empty((512, 14336), device="cuda", dtype=torch.bfloat16)
        up, output = torch.empty_like(gate), torch.empty((512, 4096), device="cuda", dtype=torch.bfloat16)
        keepalive.extend((gate, up, output))
        for value in (gate, up):
            module.import_tensor(value)
        for name in cases:
            entry = dict(name=name, status="running", correctness={}, runs=[])
            report["cases"].append(entry)
            weights, x, indices = make_fixture(name, args.seed)
            entry.update(fixture_hashes(weights, x))
            entry["onehot_k_coordinates"] = indices.tolist() if name.startswith("onehot") else None
            packed = [pack_heteromosaic_weights(w) for w in (weights.gate, weights.up, weights.down)]
            entry["packed_sha256"] = [array_hash(w) for w in packed]
            device_weights = [torch.from_numpy(w).to("cuda") for w in packed]
            device_x = torch.from_numpy(x).to(device="cuda", dtype=torch.bfloat16)
            keepalive.extend([device_x, *device_weights])
            torch.cuda.synchronize()
            entry["imported_handles"] = [int(module.import_tensor(t)) for t in (device_x, *device_weights[:2])]
            references = {stage: projection_reference(name, x, weight, indices)
                          for stage, weight in (("gate", weights.gate), ("up", weights.up))}
            entry["reference_sha256"] = {stage: array_hash(value) for stage, value in references.items()}
            if name == "constant_exact":
                entry["exact_expected_value"] = 4096 / 256
            save(report, args.output)
            for repetition in range(args.repetitions):
                actuals = {}
                for mode in ("baseline", "native"):
                    if mode == "native":
                        report["expected_npu_dispatches"] += 2
                    torch.cuda.synchronize()
                    result = module.run(device_x, gate, up, output, device_weights, mode == "native", False, True)
                    # Deliberately discard every timing field from this diagnostic.
                    count = int(result["completed_npu_dispatches"])
                    report["completed_npu_dispatches"] = int(module.completed_npu_dispatches())
                    if count != (2 if mode == "native" else 0):
                        raise RuntimeError("native diagnostic did not complete its two NPU projections")
                    actuals[mode] = {stage: result[stage].float().cpu().numpy() for stage in ("gate", "up")}
                    record = dict(repetition=repetition, mode=mode, completed_npu_dispatches=count,
                        output_sha256={stage: array_hash(value) for stage, value in actuals[mode].items()})
                    if name.startswith("constant"):
                        record["constant_projection_values"] = {
                            stage: constant_projection_values(value, references[stage])
                            for stage, value in actuals[mode].items()}
                    entry["runs"].append(record)
                    for stage, actual in actuals[mode].items():
                        for owner, rows in (("all", slice(None)), ("gpu_rows", slice(0, 256)), ("npu_rows", slice(256, None))):
                            label = f"run{repetition}_{mode}_{stage}_{owner}"
                            entry["correctness"][label] = checked_metrics(actual[rows], references[stage][rows],
                                integrity[(mode, stage, owner)], name)
                            entry["correctness"][label]["exact_equal"] = bool(np.array_equal(actual[rows], references[stage][rows]))
                for stage in ("gate", "up"):
                    entry["correctness"][f"run{repetition}_native_vs_gpu_{stage}"] = checked_metrics(
                        actuals["native"][stage], actuals["baseline"][stage])
                    entry["correctness"][f"run{repetition}_native_npu_vs_gpu_rows_{stage}"] = checked_metrics(
                        actuals["native"][stage][256:], actuals["native"][stage][:256])
                save(report, args.output)
            after = dict(device_packed_sha256=[array_hash(w.detach().cpu().numpy()) for w in device_weights],
                         device_input_sha256=array_hash(device_x.detach().float().cpu().numpy()),
                         host_packed_sha256=[array_hash(w) for w in packed], host_input_sha256=array_hash(x))
            entry["buffer_hashes_after"] = after
            entry["buffers_unchanged"] = (after["device_packed_sha256"] == entry["packed_sha256"] == after["host_packed_sha256"]
                and after["device_input_sha256"] == entry["input_sha256"] == after["host_input_sha256"])
            entry["status"] = "passed" if entry["buffers_unchanged"] and all(m["passed"] for m in entry["correctness"].values()) else "failed"
            print(json.dumps(dict(case=name, status=entry["status"],
                worst_relative_l2=max((m.get("relative_l2_error") or 0) for m in entry["correctness"].values()))), flush=True)
            save(report, args.output)
        if report["completed_npu_dispatches"] != report["expected_npu_dispatches"]:
            raise RuntimeError("native diagnostic total completion mismatch")
        report["status"] = "passed" if all(entry["status"] == "passed" for entry in report["cases"]) else "failed"
        save(report, args.output)
        if report["status"] != "passed":
            raise RuntimeError("native projection diagnostics contain strict numerical or structural failures; see each case")
        return report
    except Exception as error:
        if module is not None:
            report["completed_npu_dispatches"] = int(module.completed_npu_dispatches())
        report.update(status="failed", error=str(error), traceback=traceback.format_exc())
        if report["cases"] and report["cases"][-1]["status"] == "running":
            report["cases"][-1].update(status="failed", error=str(error))
        save(report, args.output)
        raise


if __name__ == "__main__":
    main()
