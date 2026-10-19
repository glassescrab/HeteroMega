"""Plot saved FFN partition evidence; this script performs no hardware runs.

Inputs can be ordinary/timeline JSON files, sweep manifests, or directories.
Only passed reports with passing recorded samples are plotted. Repeated runs
are never pooled. Jobs belonging to one sweep manifest form one plotted series;
standalone files remain separate series. SVG/PDF retain editable vector text.

Example (requires matplotlib):
  python -m experiments.ffn_partition.plot_partition_sweep results/new_sweep \
    results/array8_default_m512_p512_hx370.json --m 512 --output figures/sweep

All bars/bands are sample p10--p90 ranges, not confidence intervals. GPU HIP
events and NPU host intervals have different clocks and must not be aligned as
an exact device timeline. Independent medians are not additive.
"""

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import median


GPU_OPERATIONS = ("gate", "up", "silu", "multiply", "down")
PALETTE = ("#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9")
VARIANT_NAMES = {"unfused": "Separate NPU gate/up", "fused": "Fused NPU gate/up",
                 "swiglu": "On-chip NPU SwiGLU"}
VARIANT_STYLES = {"unfused": "-", "fused": "--", "swiglu": "-."}


def statistics(values):
    """Linear-interpolated sample quantiles, matching NumPy's default method."""
    values = sorted(float(x) for x in values)
    if not values or any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError("durations must be a nonempty finite, nonnegative series")

    def quantile(p):
        index = (len(values) - 1) * p
        lower = math.floor(index)
        fraction = index - lower
        return values[lower] * (1 - fraction) + values[math.ceil(index)] * fraction

    return {"count": len(values), "median": median(values), "p10": quantile(.1),
            "p90": quantile(.9), "min": values[0], "max": values[-1]}


def _shape(config):
    shape = tuple(config[name] for name in ("m", "hidden", "intermediate"))
    if any(type(value) is not int or value <= 0 for value in shape):
        raise ValueError("report must record positive integer M/H/I")
    return shape


def _fusion(config):
    fused = config.get("fuse_gate_up", False)
    swiglu = config.get("fuse_swiglu", False)
    if type(fused) is not bool or type(swiglu) is not bool:
        raise ValueError("config.fuse_gate_up and config.fuse_swiglu must be booleans")
    return fused or swiglu


def _variant(row):
    return "swiglu" if row.get("fuse_swiglu", False) else "fused" if row["fused"] else "unfused"


def _validate_swiglu_metadata(metadata):
    if (metadata.get("fuse_swiglu") is not True or metadata.get("fuse_gate_up") is not True
            or metadata.get("launches_per_run") != 2
            or metadata.get("fixed_weight_uploads") != 2
            or metadata.get("cpu_activation_fallback") is not False
            or set(metadata.get("artifacts", {})) != {"swiglu", "down"}):
        raise ValueError("SwiGLU evidence must record the two-launch swiglu/down NPU backend")


def _validate_swiglu_runs(records):
    previous = None
    for npu in records:
        if (set(npu.get("dispatch_wait_us", {})) != {"swiglu", "down"}
                or npu.get("weight_upload_counts") != {"swiglu": 1, "down": 1}):
            raise ValueError("SwiGLU samples must record swiglu/down and one fixed weight upload")
        completed = npu.get("completed_dispatches_total")
        if (type(completed) is not int or completed <= 0 or completed % 2
                or (previous is not None and completed - previous != 2)):
            raise ValueError("SwiGLU completion counters must advance by two per invocation")
        previous = completed
    if previous is None:
        raise ValueError("SwiGLU evidence lacks completed NPU samples")


def _checked_samples(samples):
    if not samples or any(sample.get("correctness_passed") is not True for sample in samples):
        raise ValueError("every plotted sample must have passed correctness")


def _stats_ms(samples, getter):
    return statistics(getter(sample) / 1000 for sample in samples)


def extract_report(report, source, series=None, power=None):
    """Normalize ordinary/timeline evidence without trusting cached summaries."""
    if report.get("status") != "passed":
        raise ValueError("only passed reports are eligible")
    config = report["config"]
    m, hidden, intermediate = _shape(config)
    common = dict(report=str(source), series=series or Path(source).stem,
                  m=m, hidden=hidden, intermediate=intermediate,
                  design=config.get("npu_design", "legacy"), fused=_fusion(config),
                  fuse_swiglu=config.get("fuse_swiglu", False),
                  seed=config.get("seed"), power=power or {"mode": "unrecorded"},
                  device=report.get("provenance", {}).get("gpu_name", "unrecorded"),
                  started_utc=report.get("provenance", {}).get("started_at_utc"))
    ordinary, diagnostic = [], []
    if "partitions" in report:
        for part in report["partitions"]:
            p = part["npu_channels"]
            if type(p) is not int or not 0 <= p <= intermediate:
                raise ValueError("invalid ordinary partition width")
            samples = part["samples"]
            _checked_samples(samples)
            if common["fuse_swiglu"]:
                _validate_swiglu_metadata(part.get("npu", {}))
                _validate_swiglu_runs([s.get("diagnostics", {}).get("npu", {})
                                       for s in samples if s["mode"] in ("concurrent", "serial")])
            by_mode = {mode: [s for s in samples if s["mode"] == mode]
                       for mode in ("baseline", "concurrent", "serial")}
            times = {mode: _stats_ms(group, lambda s: s["wall_us"])
                     for mode, group in by_mode.items() if group}
            if not {"baseline", "concurrent"} <= times.keys():
                raise ValueError("ordinary reports require matched baseline and concurrent modes")
            if times["concurrent"]["median"] <= 0 or times["baseline"]["median"] <= 0:
                raise ValueError("ordinary wall medians must be positive")
            pairs = {}
            for sample in samples:
                pair = pairs.setdefault(sample["iteration"], {})
                if sample["mode"] in pair:
                    raise ValueError("duplicate iteration/mode in an ordinary report")
                pair[sample["mode"]] = sample["wall_us"]
            paired = [v for v in pairs.values() if "baseline" in v and "concurrent" in v]
            if len(paired) != len(by_mode["baseline"]) or len(paired) != len(by_mode["concurrent"]):
                raise ValueError("baseline and concurrent samples must pair by iteration")
            if any(v["concurrent"] <= 0 for v in paired):
                raise ValueError("ordinary concurrent sample must be positive")
            ordinary.append(dict(common, npu_channels=p, npu_percent=100*p/intermediate,
                                 timing_ms=times,
                                 speedup=times["baseline"]["median"]/times["concurrent"]["median"],
                                 paired_speedup=statistics([v["baseline"]/v["concurrent"] for v in paired]),
                                 paired_wins=sum(v["concurrent"] < v["baseline"] for v in paired),
                                 paired_count=len(paired)))
    elif report.get("samples") and "gpu_event_intervals" in report["samples"][0]:
        samples = report["samples"]
        _checked_samples(samples)
        if common["fuse_swiglu"]:
            _validate_swiglu_metadata(report.get("npu_metadata", {}))
            _validate_swiglu_runs([sample["npu"] for sample in samples])
            completed = report.get("completed_npu_dispatches")
            if (report.get("npu_stage_sequence") != ["swiglu", "down"]
                    or type(completed) is not int or completed <= 0 or completed % 2
                    or completed != report.get("expected_npu_dispatches")):
                raise ValueError("SwiGLU diagnostic runner sequence/completion totals disagree")
        p = config["npu_channels"]
        if type(p) is not int or not 0 < p < intermediate:
            raise ValueError("timeline report requires two nonempty branches")
        metrics = {}

        def add(category, name, getter):
            metrics.setdefault(category, {})[name] = _stats_ms(samples, getter)

        for key in samples[0]["gpu_event_intervals"]:
            add("gpu_event", key, lambda s, key=key: s["gpu_event_intervals"][key]["duration_us"])
        for key in samples[0]["gpu_stage_submit_host"]:
            add("gpu_submit", key, lambda s, key=key: s["gpu_stage_submit_host"][key]["duration_us"])
        for key in samples[0]["npu_submit_wait_host"]:
            add("npu_submit", key, lambda s, key=key: s["npu_submit_wait_host"][key]["submit_host_us"])
            add("npu_wait", key, lambda s, key=key: s["npu_submit_wait_host"][key]["wait_host_us"])
        stage_names = tuple(samples[0]["npu"]["dispatch_wait_us"])
        expected = (("swiglu", "down") if common["fuse_swiglu"] else
                    ("gate_up", "silu_mul", "down") if common["fused"] else
                    ("gate", "up", "silu_mul", "down"))
        if any(set(s["npu"]["dispatch_wait_us"]) != set(expected) or
               set(s["npu_submit_wait_host"]) != set(expected) for s in samples):
            raise ValueError("recorded NPU stage names disagree with fusion flags")
        for stage in stage_names:
            add("npu_stage_host_io", stage,
                lambda s, stage=stage: s["npu"]["stages"][stage+"_with_host_io_us"])
            add("npu_bo_outside_dispatch", stage,
                lambda s, stage=stage: s["npu"]["stages"][stage+"_with_host_io_us"] - s["npu"]["dispatch_wait_us"][stage])
        pair = ("gate_up",) if common["fused"] else ("gate", "up")
        # Compare two projections with two projections. The unfused pair is
        # summed within each sample, never by adding independent medians.
        comparable = ((("swiglu", ("swiglu",)), ("down", ("down",))) if common["fuse_swiglu"] else
                      (("gate_up", pair), ("silu_mul", ("silu_mul",)), ("down", ("down",))))
        for name, stages in comparable:
            add("npu_comparable_stage_host_io", name, lambda s, stages=stages: sum(
                s["npu"]["stages"][stage+"_with_host_io_us"] for stage in stages))
            add("npu_comparable_wait", name, lambda s, stages=stages: sum(
                s["npu_submit_wait_host"][stage]["wait_host_us"] for stage in stages))
        # A fused SwiGLU launch is comparable to the entire earlier frontend,
        # including pointwise work. Sum each invocation before aggregation.
        frontend = tuple(stage for stage in expected if stage != "down")
        for name, stages in (("swiglu", frontend), ("down", ("down",))):
            add("npu_frontend_stage_host_io", name, lambda s, stages=stages: sum(
                s["npu"]["stages"][stage+"_with_host_io_us"] for stage in stages))
            add("npu_frontend_wait", name, lambda s, stages=stages: sum(
                s["npu_submit_wait_host"][stage]["wait_host_us"] for stage in stages))
        for key in samples[0]["npu"]["stages"]:
            if key.endswith("_layout_us"):
                add("npu_layout", key.removesuffix("_us"), lambda s, key=key: s["npu"]["stages"][key])
        # Derive component sums per invocation before taking a median. The
        # difference is explicit host I/O/wrapper time outside dispatch, not
        # a measurement of device DMA or physical DRAM bandwidth.
        def bo_io(sample):
            npu = sample["npu"]
            value = sum(npu["stages"][stage+"_with_host_io_us"] - npu["dispatch_wait_us"][stage]
                        for stage in stage_names)
            if value < -1e-6:
                raise ValueError("host stage interval is shorter than nested dispatch intervals")
            return max(0., value)

        add("npu_components", "BO I/O + wrapper outside dispatch", bo_io)
        add("npu_components", "CPU layouts", lambda s: sum(
            value for key, value in s["npu"]["stages"].items() if key.endswith("_layout_us")))
        add("npu_components", "XRT submission calls", lambda s: sum(
            v["submit_host_us"] for v in s["npu_submit_wait_host"].values()))
        add("npu_components", "XRT host waits", lambda s: sum(
            v["wait_host_us"] for v in s["npu_submit_wait_host"].values()))
        add("wall", "instrumented", lambda s: s["instrumented_wall_us"])
        add("wall", "npu_branch", lambda s: s["npu"]["branch_host_wall_us"])
        diagnostic.append(dict(common, npu_channels=p, npu_percent=100*p/intermediate, metrics_ms=metrics))
    else:
        raise ValueError("unsupported report schema")
    return ordinary, diagnostic


def _resolve(parent, name):
    path = Path(name)
    if path.is_absolute():
        return path.resolve()
    candidate = parent / path
    return candidate.resolve() if candidate.exists() else path.resolve()


def _power_snapshot(path):
    data = json.loads(path.read_text())
    modes = [platform["status"]["power_mode"] for device in data.get("devices", [])
             for platform in device.get("platforms", []) if "power_mode" in platform.get("status", {})]
    return sorted(set(modes))


def collect(inputs, m_filter=None, include_legacy=False):
    files = set()
    for source in inputs:
        source = Path(source).resolve()
        if source.is_dir():
            files.update(source.rglob("*.json"))
        elif source.is_file():
            files.add(source)
        else:
            raise ValueError(f"missing input: {source}")
    loaded, failed_loads = {}, []
    for path in sorted(files):
        try:
            loaded[path] = json.loads(path.read_text())
        except (ValueError, UnicodeDecodeError) as error:
            failed_loads.append({"file": str(path), "reason": str(error)})
    bindings, ineligible = {}, {}
    for path, manifest in list(loaded.items()):
        if not isinstance(manifest, dict) or not isinstance(manifest.get("jobs"), list):
            continue
        for job in manifest["jobs"]:
            raw_path = job.get("report_path", job.get("output"))
            if not isinstance(raw_path, str):
                continue
            report_path = _resolve(path.parent, raw_path)
            if job.get("status") != "passed":
                ineligible[report_path] = "sweep job did not pass all workload/power gates"
            expected_sha = job.get("report_sha256", job.get("evidence", {}).get("report_sha256"))
            if expected_sha and report_path.exists() and sha256(report_path.read_bytes()).hexdigest() != expected_sha:
                ineligible[report_path] = "report content disagrees with sweep manifest SHA256"
            power = {"mode": "unrecorded"}
            before, after = job.get("power_before"), job.get("power_after")
            if isinstance(before, str) and isinstance(after, str):
                snapshots = [_resolve(path.parent, name) for name in (before, after)]
                if all(p.exists() for p in snapshots):
                    modes = [_power_snapshot(p) for p in snapshots]
                    if modes[0] != modes[1] or len(modes[0]) != 1:
                        ineligible[report_path] = "power snapshots do not establish one unchanged mode"
                    for name, snapshot in zip(("power_before_summary", "power_after_summary"), snapshots):
                        expected = job.get(name, {}).get("sha256")
                        if expected and sha256(snapshot.read_bytes()).hexdigest() != expected:
                            ineligible[report_path] = "power snapshot content disagrees with sweep manifest SHA256"
                    power = {"mode": modes[0][0] if modes[0] == modes[1] and len(modes[0]) == 1 else "changed_or_unknown",
                             "before": str(snapshots[0]), "after": str(snapshots[1]),
                             "note": "boundary snapshots, not continuous power/clock monitoring"}
                else:
                    ineligible[report_path] = "sweep job power snapshots are missing"
            bindings[report_path] = (path.parent.name, power)
            if report_path.exists() and report_path not in loaded:
                loaded[report_path] = json.loads(report_path.read_text())
    ordinary, diagnostic, sources, ignored = [], [], [], failed_loads
    for path, report in sorted(loaded.items()):
        if path in ineligible:
            ignored.append({"file": str(path), "reason": ineligible[path]})
            continue
        if not isinstance(report, dict) or "config" not in report:
            continue
        if not ("partitions" in report or (report.get("samples") and
                "gpu_event_intervals" in report["samples"][0])):
            continue
        if m_filter is not None and report["config"].get("m") != m_filter:
            continue
        if not include_legacy and report["config"].get("npu_design", "legacy") != "array8":
            continue
        try:
            series, power = bindings.get(path, (path.stem, None))
            rows, stages = extract_report(report, path, series, power)
        except (ValueError, KeyError, TypeError) as error:
            ignored.append({"file": str(path), "reason": str(error)})
            continue
        ordinary.extend(rows)
        diagnostic.extend(stages)
        sources.append({"file": str(path), "sha256": sha256(path.read_bytes()).hexdigest()})
    if not ordinary and not diagnostic:
        raise ValueError("no eligible evidence reports found")
    # Do not silently average separate jobs with the same partition in one
    # manifest. Disambiguate their series labels instead.
    for records in (ordinary, diagnostic):
        seen = {}
        for row in records:
            key = tuple(row[k] for k in ("series", "m", "hidden", "intermediate", "design", "fused", "fuse_swiglu", "npu_channels"))
            seen.setdefault(key, []).append(row)
        for group in seen.values():
            if len(group) > 1:
                for row in group:
                    row["series"] += " / " + Path(row["report"]).stem
    return {"schema_version": 1, "sources": sources, "ordinary": ordinary,
            "diagnostic": diagnostic, "ignored_inputs": ignored,
            "interpretation": {
                "variability": "p10-p90 sample ranges, not confidence intervals",
                "speedup": "matched per-report GPU baseline median / concurrent median",
                "selection": "best sampled median among plotted configurations, not a global optimum",
                "pooling": "independent reports are not pooled",
                "clocks": "GPU HIP event and NPU CPU host clocks are not aligned",
                "stages": "independent stage medians are not additive; diagnostics can perturb scheduling",
                "power": "only recorded before/after snapshots establish the reported mode"}}


def _series_key(row):
    return row["series"], row["design"], _variant(row)


def _groups(rows):
    result = {}
    for row in rows:
        result.setdefault(_series_key(row), []).append(row)
    order = {"unfused": 0, "fused": 1, "swiglu": 2}
    return [(key, sorted(group, key=lambda row: row["npu_channels"]))
            for key, group in sorted(result.items(), key=lambda item: (*item[0][:2], order[item[0][2]]))]


def _label(key, short=False):
    series, design, variant = key
    name = VARIANT_NAMES[variant]
    return name if short else f"{name} · {series}"


def _environment_caption(rows):
    devices = sorted({row["device"] for row in rows})
    modes = sorted({row["power"]["mode"] for row in rows})
    return "GPU: "+", ".join(devices)+"  |  NPU power snapshots: "+", ".join(modes)


def _stage_legend(ax, names, groups, short_labels, *, ncol=2, loc="best", bbox_to_anchor=None):
    if not short_labels:
        ax.legend(loc="best", frameon=True, framealpha=.95, fontsize=7)
        return
    from matplotlib.lines import Line2D
    labels = {"gate_up": "gate + up", "silu_mul": "SiLU × up", "silu": "SiLU",
              "swiglu": "gate/up + SiLU × up",
              "input_d2h": "GPU→host input", "output_h2d": "host→GPU partial",
              "reduction": "GPU reduction"}
    handles = [Line2D([], [], color=PALETTE[i % len(PALETTE)], linewidth=2,
                      label=labels.get(name, name.replace("_", " ")))
               for i, name in enumerate(names)]
    handles += [Line2D([], [], color="#444444", linestyle=VARIANT_STYLES[key[2]],
                       marker=("o", "s", "^", "D")[i % 4], markersize=4,
                       label={"fused": "fused NPU G/U", "unfused": "separate NPU G/U",
                              "swiglu": "on-chip SwiGLU"}[key[2]])
                for i, (key, _) in enumerate(groups)]
    ax.legend(handles=handles, loc=loc, bbox_to_anchor=bbox_to_anchor, ncol=ncol,
              frameon=True, framealpha=.95, edgecolor="#E0E0E0",
              columnspacing=1.0, handlelength=2.0)


def _axes(ax, intermediate, ylabel):
    ax.set_xlabel("NPU intermediate channels P")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#DCE1E6", linewidth=.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    secondary = ax.secondary_xaxis("top", functions=(lambda x: x*100/intermediate,
                                                     lambda x: x*intermediate/100))
    secondary.set_xlabel("NPU share of intermediate channels (%)", fontsize=9)


def _errorline(ax, rows, get_stats, label, color, linestyle="-", marker="o", scale=1.):
    x = [row["npu_channels"] for row in rows]
    stats = [get_stats(row) for row in rows]
    y = [v["median"]*scale for v in stats]
    # Draw quantile bars independently of the point: the ratio of two medians
    # need not lie inside the p10--p90 interval of paired sample ratios.
    ax.errorbar(x, [(v["p10"]+v["p90"])*scale/2 for v in stats],
                yerr=[(v["p90"]-v["p10"])*scale/2 for v in stats],
                fmt="none", color=color, elinewidth=.8, capsize=2.5)
    ax.plot(x, y, label=label, color=color, linestyle=linestyle, marker=marker,
            markersize=4, linewidth=1.5)


def _save(fig, destination, formats):
    outputs = []
    for extension in formats:
        path = destination.with_suffix("."+extension)
        fig.savefig(path, dpi=220, facecolor="white", bbox_inches="tight")
        outputs.append(str(path))
    return outputs


def render(summary, output, formats=("svg", "png", "pdf")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.titlesize": 11, "axes.titleweight": "bold",
                         "svg.fonttype": "none", "pdf.fonttype": 42,
                         "legend.fontsize": 7.5, "axes.labelsize": 9})
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    summary["rendering_provenance"] = {"plotter_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                                       "matplotlib": matplotlib.__version__, "formats": list(formats)}
    outputs, selected = [], []
    shapes = sorted({tuple(row[k] for k in ("m", "hidden", "intermediate"))
                     for row in summary["ordinary"]+summary["diagnostic"]})
    for shape in shapes:
        m, hidden, intermediate = shape
        zoom_note = " · P≤2048 detail" if summary.get("zoomed") else ""
        suffix = f"m{m}_h{hidden}_i{intermediate}"
        matching = lambda row: (row["m"], row["hidden"], row["intermediate"]) == shape
        ordinary = [r for r in summary["ordinary"] if matching(r)]
        diagnostics = [r for r in summary["diagnostic"] if matching(r)]
        if ordinary:
            fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
            for index, (key, rows) in enumerate(_groups(ordinary)):
                color = PALETTE[index % len(PALETTE)]
                name = _label(key)
                _errorline(axes[0], rows, lambda r: r["timing_ms"]["concurrent"], name, color)
                _errorline(axes[0], rows, lambda r: r["timing_ms"]["baseline"],
                           "GPU-only control · "+key[0]+" · "+key[2]+" run",
                           color, "--", "x")
                # Paired ratios quantify sample variability separately from
                # the ratio-of-medians point used in the reported speedup.
                point_stats = lambda r: dict(r["paired_speedup"], median=r["speedup"])
                _errorline(axes[1], rows, point_stats, name, color)
                best = min(rows, key=lambda r: r["timing_ms"]["concurrent"]["median"])
                best_speedup = max(rows, key=lambda r: r["speedup"])
                selected.append({"shape": list(shape), "series": key[0], "fused": key[2] != "unfused",
                                 "fuse_swiglu": key[2] == "swiglu", "variant": key[2],
                                 "npu_channels": best["npu_channels"], "npu_percent": best["npu_percent"],
                                 "median_ms": best["timing_ms"]["concurrent"]["median"],
                                 "speedup": best["speedup"], "report": best["report"],
                                 "criterion": "lowest sampled concurrent median in this series",
                                 "highest_matched_speedup": {"npu_channels": best_speedup["npu_channels"],
                                     "speedup": best_speedup["speedup"], "report": best_speedup["report"],
                                     "criterion": "highest sampled matched-baseline median ratio; distinct from minimum latency"}})
                axes[0].scatter([best["npu_channels"]], [best["timing_ms"]["concurrent"]["median"]],
                                s=90, facecolors="none", edgecolors=color, linewidths=1.3, zorder=5)
                axes[1].scatter([best_speedup["npu_channels"]], [best_speedup["speedup"]],
                                s=90, marker="D", facecolors="none", edgecolors=color, linewidths=1.3, zorder=5)
            _axes(axes[0], intermediate, "Ordinary complete FFN latency (ms)")
            _axes(axes[1], intermediate, "Speedup vs matched GPU-only control (×)")
            axes[1].axhline(1, color="#5D6268", linestyle=":", linewidth=1)
            axes[0].set_title("Ready GPU input → synchronized GPU output", pad=48)
            axes[1].set_title("Paired control at each sampled partition", pad=48)
            for ax in axes:
                ax.legend(loc="best", frameon=False)
            fig.suptitle(f"FFN partition sweep · M={m}, H={hidden}, I={intermediate}"+zoom_note, y=1.08, fontsize=14, weight="bold")
            fig.text(.5, 1.015, _environment_caption(ordinary), ha="center", va="top", fontsize=9, color="#555555")
            fig.text(.01, -.03, "Bars: sample p10–p90, not confidence intervals. Open circle: sampled latency minimum; diamond: sampled speedup maximum.\n"
                     "These choices may differ under baseline drift; neither is a global optimum. Speedup ranges use paired sample ratios; repeats are not pooled.", fontsize=8)
            fig.tight_layout()
            outputs += _save(fig, output/("total_ffn_"+suffix), formats)
            plt.close(fig)
        if diagnostics:
            groups = _groups(diagnostics)
            short_labels = len({key[2] for key, _ in groups}) == len(groups)
            has_swiglu = any(row["fuse_swiglu"] for row in diagnostics)
            stage_category = "npu_frontend_stage_host_io" if has_swiglu else "npu_comparable_stage_host_io"
            wait_category = "npu_frontend_wait" if has_swiglu else "npu_comparable_wait"
            combined_label = "gate/up + SiLU × up combined" if has_swiglu else "gate+up pair combined"
            panels = (("gpu_event", GPU_OPERATIONS, "GPU branch operations · HIP events", "GPU event span (ms)"),
                      (stage_category, None, "NPU host stages · "+combined_label, "Host interval (ms)"),
                      (wait_category, None, "NPU host waits · "+combined_label, "Host interval (ms)"),
                      ("gpu_event", ("input_d2h", "output_h2d", "reduction"), "Transfers and boundary sum · HIP events", "GPU event span (ms)"))
            fig, axes = plt.subplots(2, 2, figsize=(12, 9))
            for ax, (category, names, title, ylabel) in zip(axes.flat, panels):
                all_names = list(names) if names is not None else sorted({name for r in diagnostics for name in r["metrics_ms"][category]})
                for gi, (key, rows) in enumerate(groups):
                    for ni, name in enumerate(all_names):
                        available = [r for r in rows if name in r["metrics_ms"][category]]
                        if not available:
                            continue
                        label = name.replace("_", " ")+" · "+_label(key, short=short_labels)
                        _errorline(ax, available, lambda r, n=name, c=category: r["metrics_ms"][c][n],
                                   label, PALETTE[ni % len(PALETTE)], VARIANT_STYLES[key[2]],
                                   ("o", "s", "^", "D")[gi % 4])
                _axes(ax, intermediate, ylabel)
                ax.set_title(title, pad=48)
                _stage_legend(ax, all_names, groups, short_labels)
            fig.suptitle(f"Instrumented stage diagnostics · M={m}, H={hidden}, I={intermediate}"+zoom_note, y=1.02, fontsize=14, weight="bold")
            fig.text(.5, .985, _environment_caption(diagnostics), ha="center", va="top", fontsize=9, color="#555555")
            fig.text(.01, -.035, "Bars: sample p10–p90. GPU events include scheduling/probe effects; NPU stages are CPU-host spans, not device compute cycles.\n"
                     "Compared frontend stages are summed within each invocation before aggregation; individual stages remain in CSV/JSON.\n"
                     "CPU/GPU clocks are not aligned. Independent medians are not additive. Diagnostics are separate from ordinary FFN timing.", fontsize=8)
            fig.tight_layout(h_pad=5)
            outputs += _save(fig, output/("stages_"+suffix), formats)
            plt.close(fig)
            fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
            for ax, category, title in zip(axes, ("npu_bo_outside_dispatch", "npu_layout"),
                                          ("Host BO I/O and wrapper outside dispatch", "CPU layout conversions")):
                names = sorted({name for row in diagnostics for name in row["metrics_ms"][category]})
                for gi, (key, rows) in enumerate(groups):
                    for ni, name in enumerate(names):
                        available = [r for r in rows if name in r["metrics_ms"][category]]
                        if available:
                            _errorline(ax, available, lambda r, n=name, c=category: r["metrics_ms"][c][n],
                                       name.replace("_", " ")+" · "+_label(key, short=short_labels),
                                       PALETTE[ni % len(PALETTE)], VARIANT_STYLES[key[2]],
                                       ("o", "s", "^", "D")[gi % 4])
                _axes(ax, intermediate, "CPU host interval (ms)")
                ax.set_title(title, pad=48)
                _stage_legend(ax, names, groups, short_labels)
            fig.suptitle(f"NPU host handling · M={m}, H={hidden}, I={intermediate}"+zoom_note, y=1.08, fontsize=14, weight="bold")
            fig.text(.5, 1.015, _environment_caption(diagnostics), ha="center", va="top", fontsize=9, color="#555555")
            fig.text(.01, -.03, "Bars: sample p10–p90. BO intervals are derived per invocation: host stage minus nested dispatch/wait.\n"
                     "They include explicit read/write/sync and wrapper work; they do not measure device DMA or physical DRAM bandwidth.", fontsize=8)
            fig.tight_layout()
            outputs += _save(fig, output/("npu_host_"+suffix), formats)
            plt.close(fig)
            fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
            for ax, category, title in zip(axes, ("gpu_submit", "npu_submit"), ("GPU operation submission calls", "NPU XRT submission calls")):
                names = sorted({name for row in diagnostics for name in row["metrics_ms"][category]})
                for gi, (key, rows) in enumerate(groups):
                    for ni, name in enumerate(names):
                        available = [r for r in rows if name in r["metrics_ms"][category]]
                        if available:
                            _errorline(ax, available, lambda r, n=name, c=category: r["metrics_ms"][c][n],
                                       name.replace("_", " ")+" · "+_label(key, short=short_labels),
                                       PALETTE[ni % len(PALETTE)], VARIANT_STYLES[key[2]],
                                       ("o", "s", "^", "D")[gi % 4], scale=1000.)
                _axes(ax, intermediate, "CPU API-call interval (µs)")
                ax.set_title(title, pad=48)
                if category == "gpu_submit" and short_labels:
                    _stage_legend(ax, names, groups, short_labels, ncol=3,
                                  loc="center right", bbox_to_anchor=(1, .52))
                else:
                    _stage_legend(ax, names, groups, short_labels)
            fig.suptitle(f"Submission diagnostics · M={m}, H={hidden}, I={intermediate}"+zoom_note, y=1.08, fontsize=14, weight="bold")
            fig.text(.5, 1.015, _environment_caption(diagnostics), ha="center", va="top", fontsize=9, color="#555555")
            fig.text(.01, -.03, "Bars: sample p10–p90. Python/C++ API-call intervals include runtime work; these are not driver-only launch overhead.\n"
                     "Instrumented diagnostic; independent medians are not additive. GPU event durations appear in the separate stage figure.", fontsize=8)
            fig.tight_layout()
            outputs += _save(fig, output/("submission_"+suffix), formats)
            plt.close(fig)
    summary["sampled_best"] = selected
    # A wide sweep can hide the useful small-partition region. Keep the full
    # evidence/tables and render a separate view; do not rescale or omit points
    # silently in the primary figures.
    all_rows = summary["ordinary"] + summary["diagnostic"]
    if not summary.get("zoomed") and any(r["npu_channels"] > 2048 for r in all_rows):
        zoom = {"ordinary": [r for r in summary["ordinary"] if r["npu_channels"] <= 2048],
                "diagnostic": [r for r in summary["diagnostic"] if r["npu_channels"] <= 2048], "zoomed": True}
        if len({r["npu_channels"] for r in zoom["ordinary"] + zoom["diagnostic"]}) >= 2:
            outputs += render(zoom, output/"zoom_le2048", formats)
    summary["figures"] = outputs
    return outputs


def write_tables(summary, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/"summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False)+"\n")
    common = ("series", "report", "m", "hidden", "intermediate", "npu_channels", "npu_percent", "design", "fused", "fuse_swiglu")
    with (output/"ordinary.csv").open("w", newline="") as stream:
        fields = [*common, "power_mode", "mode", "count", "median_ms", "p10_ms", "p90_ms", "speedup", "paired_wins", "paired_count"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in summary["ordinary"]:
            for mode, stats in row["timing_ms"].items():
                writer.writerow({**{k: row[k] for k in common}, "power_mode": row["power"]["mode"], "mode": mode,
                                 "count": stats["count"], **{k+"_ms": stats[k] for k in ("median", "p10", "p90")},
                                 **{k: row[k] for k in ("speedup", "paired_wins", "paired_count")}})
    with (output/"diagnostic.csv").open("w", newline="") as stream:
        fields = [*common, "power_mode", "category", "stage", "count", "median_ms", "p10_ms", "p90_ms"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in summary["diagnostic"]:
            for category, stages in row["metrics_ms"].items():
                for name, stats in stages.items():
                    writer.writerow({**{k: row[k] for k in common}, "power_mode": row["power"]["mode"],
                                     "category": category, "stage": name, "count": stats["count"],
                                     **{k+"_ms": stats[k] for k in ("median", "p10", "p90")}})


def repeat_comparison(summary, channels):
    """Select complete independent fused runs, ordered by actual report start.

    Missing candidates and ambiguous duplicates are excluded, not pooled or
    replaced by another run. Only ordinary latency supplies this comparison.
    """
    channels = tuple(channels)
    if len(channels) < 2 or len(set(channels)) != len(channels) or any(type(p) is not int or p <= 0 for p in channels):
        raise ValueError("repeat comparison requires at least two distinct positive channel counts")
    groups, excluded = {}, []
    for row in summary["ordinary"]:
        if row["fused"] and not row.get("fuse_swiglu", False) and row["npu_channels"] in channels:
            key = tuple(row[k] for k in ("m", "hidden", "intermediate", "series", "design"))
            groups.setdefault(key, []).append(row)
    runs = []
    for key, rows in groups.items():
        if len(rows) != len(channels) or {r["npu_channels"] for r in rows} != set(channels):
            excluded.append({"series": key[3], "reason": "run lacks exactly one measurement of every requested candidate"})
            continue
        try:
            times = {row["npu_channels"]: datetime.fromisoformat(row["started_utc"].replace("Z", "+00:00"))
                     for row in rows}
            if any(value.tzinfo is None for value in times.values()):
                raise ValueError("start timestamp lacks a time zone")
            times = {p: value.astimezone(timezone.utc) for p, value in times.items()}
        except (ValueError, TypeError, AttributeError):
            excluded.append({"series": key[3], "reason": "valid actual start timestamps are required for chronological order"})
            continue
        candidates = sorted(rows, key=lambda r: channels.index(r["npu_channels"]))
        minimum = min(row["timing_ms"]["concurrent"]["median"] for row in candidates)
        runs.append({"shape": list(key[:3]), "series": key[3], "design": key[4],
                     "started_utc": min(times.values()).isoformat(),
                     "candidate_order": sorted(channels, key=times.get), "candidates": candidates,
                     "lowest_median_candidates": [row["npu_channels"] for row in candidates
                                                   if row["timing_ms"]["concurrent"]["median"] == minimum]})
    runs.sort(key=lambda run: (run["shape"], run["started_utc"], run["series"]))
    return {"channels": list(channels), "runs": runs, "excluded_runs": excluded,
            "interpretation": "independent ordinary runs; no pooling; sample p10-p90 is not a confidence interval"}


def render_repeats(comparison, output, formats=("svg", "png", "pdf")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "svg.fonttype": "none", "pdf.fonttype": 42})
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for shape in sorted({tuple(run["shape"]) for run in comparison["runs"]}):
        runs = [run for run in comparison["runs"] if tuple(run["shape"]) == shape]
        m, hidden, intermediate = shape
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        channels = comparison["channels"]
        for ci, p in enumerate(channels):
            rows = [next(row for row in run["candidates"] if row["npu_channels"] == p) for run in runs]
            x = [index + .12*(ci-(len(channels)-1)/2) for index in range(len(runs))]
            for ax, mode in zip(axes, ("latency", "speedup")):
                stats = [row["timing_ms"]["concurrent"] if mode == "latency"
                         else dict(row["paired_speedup"], median=row["speedup"]) for row in rows]
                color = PALETTE[ci % len(PALETTE)]
                ax.errorbar(x, [(s["p10"]+s["p90"])/2 for s in stats],
                            yerr=[(s["p90"]-s["p10"])/2 for s in stats], fmt="none",
                            color=color, capsize=3, elinewidth=1)
                ax.plot(x, [s["median"] for s in stats], color=color,
                        marker=("o", "s", "^", "D")[ci % 4], linestyle="-", linewidth=1.4,
                        label=f"P={p} ({100*p/intermediate:.2f}% NPU)")
        tick_labels = []
        for i, run in enumerate(runs):
            counts = sorted({r["timing_ms"]["concurrent"]["count"] for r in run["candidates"]})
            started = datetime.fromisoformat(run["started_utc"])
            order = "→".join(str(p) for p in run["candidate_order"])
            tick_labels.append(f"Run {i+1} · n={'/'.join(map(str, counts))}\n{started:%m-%d %H:%M} UTC\norder {order}")
        for ax in axes:
            ax.set_xticks(range(len(runs)), tick_labels)
            ax.set_xlim(-.5, len(runs)-.5)
            ax.set_xlabel("Independent measurement runs, ordered by actual start", labelpad=10)
            ax.grid(axis="y", color="#DCE1E6", linewidth=.6)
            ax.set_axisbelow(True)
            ax.spines[["top", "right"]].set_visible(False)
            ax.legend(frameon=False, loc="best")
        axes[0].set_ylabel("Ordinary complete FFN latency (ms)")
        axes[0].set_title("Candidate medians and sample variability", weight="bold", pad=15)
        axes[1].set_ylabel("Speedup vs each run's matched GPU baseline (×)")
        axes[1].set_title("Each point retains its own GPU-only control", weight="bold", pad=15)
        axes[1].axhline(1, color="#666666", linestyle=":", linewidth=1)
        fig.suptitle(f"Repeated fused-partition comparison · M={m}, H={hidden}, I={intermediate}",
                     y=1.07, fontsize=14, weight="bold")
        fig.text(.5, 1.005, _environment_caption([row for run in runs for row in run["candidates"]]),
                 ha="center", va="top", fontsize=9, color="#555555")
        fig.text(.01, -.045, "Bars: sample p10–p90, not confidence intervals. Each run remains independent; no pooled winner or global optimum is inferred.\n"
                 "Speedup points use matched median ratios; ranges use paired sample ratios. Only runs containing every requested candidate are shown.", fontsize=8)
        fig.tight_layout()
        files += _save(fig, output/f"repeat_candidates_m{m}_h{hidden}_i{intermediate}", formats)
        plt.close(fig)
    return files


def write_repeat_table(comparison, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/"repeat_comparison.json").write_text(json.dumps(comparison, indent=2, allow_nan=False)+"\n")
    with (output/"repeat_comparison.csv").open("w", newline="") as stream:
        fields = ("m", "hidden", "intermediate", "series", "run_start_utc", "candidate_order", "npu_channels",
                  "samples", "median_ms", "p10_ms", "p90_ms", "gpu_baseline_median_ms", "matched_speedup", "report")
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for run in comparison["runs"]:
            for row in run["candidates"]:
                stats = row["timing_ms"]["concurrent"]
                writer.writerow({**{k: row[k] for k in ("m", "hidden", "intermediate", "series", "npu_channels", "report")},
                                 "run_start_utc": run["started_utc"], "candidate_order": " -> ".join(map(str, run["candidate_order"])),
                                 "samples": stats["count"], **{k+"_ms": stats[k] for k in ("median", "p10", "p90")},
                                 "gpu_baseline_median_ms": row["timing_ms"]["baseline"]["median"], "matched_speedup": row["speedup"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--m", type=int)
    parser.add_argument("--include-legacy", action="store_true")
    parser.add_argument("--formats", nargs="+", choices=("svg", "png", "pdf"), default=["svg", "png", "pdf"])
    parser.add_argument("--tables-only", action="store_true", help="validate/export summaries without importing matplotlib")
    parser.add_argument("--repeat-channels", nargs="+", type=int,
                        help="also compare these fused candidates across complete independent runs")
    parser.add_argument("--repeat-only", action="store_true",
                        help="render only repeat-comparison figures; still export all input tables")
    args = parser.parse_args()
    if args.repeat_only and not args.repeat_channels:
        parser.error("--repeat-only requires --repeat-channels")
    summary = collect(args.inputs, args.m, args.include_legacy)
    if not args.tables_only and not args.repeat_only:
        render(summary, args.output, args.formats)
    if args.repeat_channels:
        comparison = repeat_comparison(summary, args.repeat_channels)
        if not comparison["runs"]:
            parser.error("no complete independent fused runs contain every repeat candidate")
        if not args.tables_only:
            summary.setdefault("figures", []).extend(render_repeats(comparison, args.output, args.formats))
        summary["repeat_comparison"] = comparison
        write_repeat_table(comparison, args.output)
    write_tables(summary, args.output)
    print(json.dumps({"ordinary_rows": len(summary["ordinary"]), "diagnostic_rows": len(summary["diagnostic"]),
                      "ignored": summary["ignored_inputs"], "output": str(args.output),
                      "figures": summary.get("figures", [])}, indent=2))


if __name__ == "__main__":
    main()
