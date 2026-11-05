"""Derive host critical-path summaries and graph payload estimates from saved runs.

This runs on CPU and performs no new hardware measurements. Payload estimates
describe the current M16/K128/N32 graph, not measured DRAM traffic or bandwidth.
"""

import argparse
from hashlib import sha256
import json
from math import gcd
from pathlib import Path
from statistics import median


HERE = Path(__file__).resolve().parent
DEFAULT_REPORTS = [HERE / "results" / name for name in (
    "ffn_m128_h4096_i14336_hx370.json",
    "ffn_m512_h4096_i14336_hx370.json",
    "ffn_m512_h4096_i14336_c8_hx370.json",
)]


def projection_accounting(manifest, m, k, n):
    """Logical shim/core work for one recorded projection architecture.

    Array8 broadcasts A horizontally and W to four compute rows. Weight DMA
    and per-core dequantization consequently have different replay factors.
    All byte values describe scheduled payloads, not physical DRAM counters.
    """
    expected = dict(m=m, k=k, n=n, tile_m=16, tile_k=128, tile_n=32,
                    weight_tile_bytes=2144)
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("manifest dimensions/tile ABI do not match the recorded projection")
    if m <= 0 or k <= 0 or n <= 0 or m % 16 or k % 128 or n % 32:
        raise ValueError("payload formulas require aligned M16/K128/N32 dimensions")
    mb, kb, nb = m // 16, k // 128, n // 32
    cols = manifest.get("cols")
    if type(cols) is not int or not 1 <= cols <= 8:
        raise ValueError("manifest must specify one to eight projection columns")
    architecture = manifest.get("design", "legacy")
    if architecture == "legacy":
        if (manifest.get("compute_rows", 1) != 1 or manifest.get("m_reuse", 1) != 1
                or manifest.get("worker_count", cols) != cols or nb % cols):
            raise ValueError("legacy accounting requires one worker per column and no M reuse")
        rows, reuse, workers, n_columns, m_groups = 1, 1, cols, cols, 1
        a_factor, w_factor = 1, 1
    elif architecture == "array8":
        rows, reuse, workers = (manifest.get(key) for key in
                                ("compute_rows", "m_reuse", "worker_count"))
        n_columns, m_groups = gcd(8, nb), 8 // gcd(8, nb)
        if (cols != 8 or rows != 4 or workers != 32 or type(reuse) is not int
                or reuse not in (1, 2, 4) or mb % (m_groups * rows * reuse)
                or manifest.get("n_columns") != n_columns
                or manifest.get("m_column_groups") != m_groups):
            raise ValueError("array8 manifest does not describe a valid eight-column/four-row schedule")
        if nb // n_columns > 64:
            raise ValueError("array8 manifest exceeds the local N repeat bound")
        a_factor, w_factor = n_columns, rows * reuse
    else:
        raise ValueError(f"unsupported projection architecture: {architecture!r}")
    tiles = mb * kb * nb
    unique_w = kb * nb * 2144
    return {
        "architecture": architecture, "m": m, "k": k, "n": n,
        "columns": cols, "compute_rows": rows, "worker_count": workers,
        "m_reuse": reuse, "n_columns": n_columns, "m_column_groups": m_groups,
        "mkn_tiles": tiles,
        "unique_packed_weight_bytes": unique_w,
        "a_shim_payload_bytes": 4096 * tiles // a_factor,
        "weight_shim_payload_bytes": 2144 * tiles // w_factor,
        "output_shim_payload_bytes": 2 * m * n,
        "a_core_payload_bytes": 4096 * tiles,
        "weight_core_payload_bytes": 2144 * tiles // reuse,
        "dequantization_calls": tiles // reuse,
        "weight_shim_replays_per_unique_tile": mb // w_factor,
        "dequant_replays_per_unique_tile": mb // reuse,
    }


def analyze(path):
    report = json.loads(path.read_text())
    if report["status"] != "passed":
        raise ValueError(f"{path}: only correctness-passing reports can be analyzed")
    cfg = report["config"]
    m, h, intermediate = (cfg[key] for key in ("m", "hidden", "intermediate"))
    rows = []
    for part in report["partitions"]:
        p = part["npu_channels"]
        if not 0 < p < intermediate:
            raise ValueError("this analysis requires two nonempty device branches")
        stage_info = {stage: projection_accounting(
            part["npu"]["artifacts"][stage]["manifest"], m, k, n)
            for stage, k, n in (("gate_up", h, p), ("down", p, h))}
        # Gate and up share geometry/artifact, but each reads its own weights
        # and contributes its own launches, traffic, and dequantization work.
        projections_info = {"gate": stage_info["gate_up"],
                            "up": stage_info["gate_up"], "down": stage_info["down"]}
        architectures = {value["architecture"] for value in stage_info.values()}
        architecture = next(iter(architectures)) if len(architectures) == 1 else "mixed"
        samples = part["samples"]
        if not all(s["correctness_passed"] for s in samples):
            raise ValueError("failed invocation in report")
        by_mode = {mode: [s for s in samples if s["mode"] == mode]
                   for mode in ("baseline", "serial", "concurrent")}
        times = {mode: median(s["wall_us"] for s in group) / 1000
                 for mode, group in by_mode.items()}
        concurrent = by_mode["concurrent"]
        npu = [s["diagnostics"]["npu"] for s in concurrent]
        projections = [sum(d["dispatch_wait_us"][stage] for stage in ("gate", "up", "down")) for d in npu]
        host_io = [sum(d["stages"][stage + "_with_host_io_us"] - wait
                       for stage, wait in d["dispatch_wait_us"].items()) for d in npu]
        layouts = [sum(d["stages"][stage] for stage in
                       ("input_layout_us", "down_input_layout_us", "output_layout_us")) for d in npu]
        branch_ms = median(d["branch_host_wall_us"] for d in npu) / 1000
        unique_weight_bytes = sum(v["unique_packed_weight_bytes"] for v in projections_info.values())
        graph_a_bytes = sum(v["a_shim_payload_bytes"] for v in projections_info.values())
        graph_w_bytes = sum(v["weight_shim_payload_bytes"] for v in projections_info.values())
        graph_y_bytes = sum(v["output_shim_payload_bytes"] for v in projections_info.values())
        row = {
            "report": path.name, "m": m, "hidden": h, "intermediate": intermediate,
            "npu_channels": p, "columns_max": cfg["columns"],
            "architecture": architecture,
            "projection_workers": {stage: info["worker_count"] for stage, info in stage_info.items()},
            "projection_columns": {stage: info["columns"] for stage, info in stage_info.items()},
            "effective_m_reuse": {stage: info["m_reuse"] for stage, info in stage_info.items()},
            "projection_details": projections_info,
            "samples_per_mode": {mode: len(group) for mode, group in by_mode.items()},
            "median_ms": dict(times, npu_branch=branch_ms,
                projection_dispatch_wait_sum=median(projections) / 1000,
                silu_dispatch_wait=median(d["dispatch_wait_us"]["silu_mul"] for d in npu) / 1000,
                host_bo_io_outside_dispatch=median(host_io) / 1000,
                layouts=median(layouts) / 1000,
                input_gpu_to_host=median(s["diagnostics"]["input_gpu_to_host_us"] for s in concurrent) / 1000,
                output_stage_and_boundary_wait=median(s["diagnostics"]["output_stage_and_boundary_wait_us"] for s in concurrent) / 1000),
            "median_projection_wait_share_of_npu_percent": median(
                100 * wait / d["branch_host_wall_us"] for wait, d in zip(projections, npu)),
            "speedup_vs_gpu": times["baseline"] / times["concurrent"],
            "npu_branch_over_full_gpu_ratio": branch_ms / times["baseline"],
            "npu_branch_effective_projection_gflops": (6 * m * h * p) / (branch_ms * 1e6),
            "proportional_work_model": {
                "npu_fraction": p / intermediate,
                "gpu_time_released_ms": times["baseline"] * p / intermediate,
                "zero_overhead_instant_npu_speedup": 1 / (1 - p / intermediate),
            },
            "calculated_bytes": {
                "unique_packed_projection_weights": unique_weight_bytes,
                "projection_graph_a_payload": graph_a_bytes,
                "projection_graph_weight_payload": graph_w_bytes,
                "projection_graph_output_payload": graph_y_bytes,
                "projection_graph_total_payload": graph_a_bytes + graph_w_bytes + graph_y_bytes,
                "host_bo_read_write_payload": 6 * m * h + 12 * m * p,
                "gpu_host_input_output_payload": 4 * m * h,
            },
            "calculated_core_bytes": {
                "projection_a_payload": sum(v["a_core_payload_bytes"] for v in projections_info.values()),
                "projection_weight_payload": sum(v["weight_core_payload_bytes"] for v in projections_info.values()),
            },
            "projection_dequantization_calls": sum(v["dequantization_calls"] for v in projections_info.values()),
        }
        # Retain this historical field only where its single replay factor is
        # true. In array8, row multicast reduces shim reads without sharing
        # dequantization across cores, and gate/up and down may have different R.
        if architecture == "legacy":
            row["weight_dma_and_dequant_replays"] = m // 16
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="*", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = {
        "kind": "derived_analysis_no_new_hardware_measurements",
        "notes": [
            "Host dispatch/wait includes device DMA and runtime costs; it is not pure compute time.",
            "Stage sums are computed per sample before taking medians; separate medians need not add.",
            "Graph payloads exclude SiLU, instruction traffic, caches and scratch; they are not DRAM counters.",
            "Architecture and effective reuse come from each projection manifest; gate/up and down may use different reuse.",
            "Array8 shim traffic includes horizontal A and vertical W multicast; core traffic and dequantization are reported separately.",
            "Proportional work model assumes linear GPU scaling, instantaneous NPU and zero overhead; it is not a measured speedup or universal bound.",
            "Effective GFLOPS counts three projection FLOPs over the entire host NPU branch.",
        ],
        "source_reports_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in args.reports},
        "rows": [row for p in args.reports for row in analyze(p)],
    }
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
