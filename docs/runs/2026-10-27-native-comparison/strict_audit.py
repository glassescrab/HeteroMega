#!/usr/bin/env python3
"""Audit exported native/direct-buffer comparison bytes and recorded outcomes.

python audit.py --evidence-dir /tmp/native-comparison-evidence-20261027 --output audit.json

An integrity pass does not mean native accuracy passed. Failed measurements are
retained and summarized. No hardware work or numerical array recomputation runs.
"""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from types import SimpleNamespace


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from experiments.ffn_partition import compare_upstream_native as driver

PIN = "61714a3147f34857aa5dfef21a28e762777a2df0"
DRIVER_PIN = "0e6d303b2cc2b3fe1cf10aba0acbf57a422588fb"
BASELINE_PAYLOAD_SHA256 = "91cdced5e5b3998cd35ead83b775c1823b5b067158ff2692341634eebcbf3fbb"
SUCCESS = {"passed", "completed_with_accuracy_deviations"}
MARKERS = ("experiments/ffn_partition/", "npu/ffn/", "src/", "include/")


def load(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inside(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"path escapes evidence: {relative}")
    return path


def source_name(path):
    name = str(path).replace("\\", "/")
    return next((name[name.index(marker):] for marker in MARKERS if marker in name), None)


def metric_verdict(value):
    """Recalculate decisions, including native numerical/structural separation."""
    for key, expected in (("rtol", .03), ("atol", .05), ("l2_limit", .02)):
        require(value.get(key) == expected, f"changed tolerance: {key}")
    numerical = False
    if value.get("finite") is True:
        maximum, reference = value["max_abs_error"], value["reference_max_abs"]
        require(all(isinstance(x, (int, float)) and math.isfinite(x) and x >= 0
                    for x in (maximum, reference, value["rms_error"])), "invalid finite error magnitude")
        require(math.isclose(value["max_error_limit"], .05 + .03 * reference, rel_tol=1e-12),
                "changed maximum-error bound")
        if reference == 0:
            numerical = maximum == 0
            require(value["relative_l2_error"] == (0 if numerical else None), "zero reference L2 mismatch")
        else:
            l2 = value["relative_l2_error"]
            require(isinstance(l2, (int, float)) and math.isfinite(l2) and l2 >= 0, "invalid relative L2")
            numerical = l2 <= .02 and maximum <= .05 + .03 * reference
    failures = value.get("structural_failures", [])
    policy = value.get("accuracy_policy", "strict")
    require(policy in ("strict", "report"), "unknown numerical policy")
    accepted = not failures and (numerical or policy == "report")
    if "accepted" in value:
        require(value["accepted"] == accepted, "accepted verdict disagrees with recorded metrics")
    if "numerical_passed" in value:
        require(value["numerical_passed"] == numerical and value["structural_passed"] == (not failures),
                "native numerical/structural verdict mismatch")
        passed = numerical and not failures
    else:
        passed = numerical
    require(value["passed"] == passed and value["correctness"] == ("passed" if passed else "failed"),
            "original tolerance verdict was relabeled")
    return dict(numerical_passed=numerical, structural_passed=not failures, accepted=accepted)


def numerical_summary(metrics):
    verdicts = {label: metric_verdict(value) for label, value in metrics.items()}
    worst = {}
    for key in ("relative_l2_error", "max_abs_error", "normalized_max_error", "rms_error"):
        values = [(item[key], label) for label, item in metrics.items() if item.get(key) is not None]
        if values:
            value, label = max(values)
            worst[key] = dict(value=value, check=label)
    return dict(recorded_check_count=len(metrics), numerical_failure_count=sum(not v["numerical_passed"] for v in verdicts.values()),
                structural_failure_count=sum(not v["structural_passed"] for v in verdicts.values()),
                rejected_check_count=sum(not v["accepted"] for v in verdicts.values()), worst=worst,
                failed_checks={label: dict(**verdicts[label], relative_l2_error=value.get("relative_l2_error"),
                    max_abs_error=value.get("max_abs_error"), structural_failures=value.get("structural_failures", []))
                    for label, value in metrics.items() if not verdicts[label]["accepted"]})


def diagnostic_records(report):
    """Cross-check untimed diagnostic records without accepting failed cases."""
    expected_runs = 2 * report["config"]["repetitions"]
    recorded_dispatches, cases = 0, []
    for case in report["cases"]:
        records = case.get("runs", [])
        seen = {}
        for index, record in enumerate(records):
            mode = ("baseline", "native")[index % 2]
            require(record["mode"] == mode and record["repetition"] == index // 2,
                    "diagnostic run order/repetition changed")
            count = 0 if mode == "baseline" else 2
            require(record["completed_npu_dispatches"] == count, "diagnostic per-run completion mismatch")
            recorded_dispatches += count
            for stage, value in record["output_sha256"].items():
                label = f"run{record['repetition']}_{mode}_{stage}_all"
                require(case["correctness"][label]["actual_sha256"] == value,
                        "diagnostic output record differs from checked output")
                key = (mode, stage)
                require(key not in seen or seen[key] == value, "diagnostic repeated output changed")
                seen[key] = value
        after = case.get("buffer_hashes_after")
        unchanged = None
        if after is not None:
            unchanged = (after["device_packed_sha256"] == case["packed_sha256"] == after["host_packed_sha256"]
                and after["device_input_sha256"] == case["input_sha256"] == after["host_input_sha256"])
            require(unchanged == case["buffers_unchanged"], "diagnostic buffer verdict differs from hashes")
        complete = len(records) == expected_runs and after is not None
        if complete:
            expected_labels = {
                f"run{run}_{mode}_{stage}_{owner}"
                for run in range(report["config"]["repetitions"])
                for mode in ("baseline", "native") for stage in ("gate", "up")
                for owner in ("all", "gpu_rows", "npu_rows")}
            expected_labels.update(f"run{run}_{comparison}_{stage}"
                for run in range(report["config"]["repetitions"])
                for comparison in ("native_vs_gpu", "native_npu_vs_gpu_rows") for stage in ("gate", "up"))
            require(set(case["correctness"]) == expected_labels, "diagnostic projection/owner coverage changed")
            passed = unchanged and all(value["passed"] for value in case["correctness"].values())
            require(case["status"] == ("passed" if passed else "failed"), "diagnostic case status was relabeled")
        cases.append(dict(name=case["name"], complete_records=complete, recorded_runs=len(records),
                          buffers_unchanged=unchanged, repeat_output_hashes_stable=True))
    complete = (len(cases) == len(dict.fromkeys(report["config"]["cases"].split(",")))
                and all(case["complete_records"] for case in cases))
    if complete:
        require(recorded_dispatches == report["completed_npu_dispatches"] == report["expected_npu_dispatches"],
                "diagnostic total completion mismatch")
        expected_status = "passed" if all(case["status"] == "passed" for case in report["cases"]) else "failed"
        require(report["status"] == expected_status, "diagnostic report status was relabeled")
    return dict(complete_records=complete, recorded_completed_dispatches=recorded_dispatches, cases=cases)


def run(evidence):
    root = evidence.resolve()
    audit = dict(status="running", evidence_dir=str(root), integrity_errors=[], reports={}, comparisons={},
        limitations=["This audit validates exported bytes and recorded evidence; it does not execute GPU/NPU work.",
            "Complete FFN output matrices are absent; constant-projection diagnostics retain row vectors. Error magnitudes are retained; tolerance and policy decisions are recalculated.",
            "A source/binary hash and build log establish a recorded provenance chain, not an independent rebuild.",
            "Integrity success is separate from native numerical success; failed reports never authorize a speedup.",
            "Ordinary complete FFN timing and synchronized/untimed diagnostics remain separate; no whole-model claim."])

    def attempt(label, operation):
        try:
            return operation()
        except Exception as error:
            audit["integrity_errors"].append(dict(check=label, error=str(error)))
            return None

    def checksums():
        tables = {}
        manifests = sorted(root.rglob("SHA256SUMS.json"))
        require(root / "SHA256SUMS.json" in manifests, "root SHA256SUMS.json missing")
        for path in manifests:
            table = load(path)
            require(isinstance(table, dict) and table, f"invalid checksum table: {path}")
            for name, expected in table.items():
                file = inside(path.parent, name)
                require(file.is_file() and digest(file) == expected, f"checksum mismatch/missing file: {name}")
            if path.parent == root:
                actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p != path}
                require(set(table) == actual, f"checksum coverage differs: {sorted(set(table) ^ actual)}")
            tables[str(path.relative_to(root))] = dict(sha256=digest(path), verified_files=len(table))
        return tables
    audit["checksums"] = attempt("export checksums", checksums)

    source_index = defaultdict(list)
    binary_index = defaultdict(list)
    for path in root.rglob("*"):
        if path.is_file():
            name = source_name(path)
            if name:
                source_index[(name, digest(path))].append(str(path.relative_to(root)))
            if path.suffix == ".so":
                binary_index[digest(path)].append(str(path.relative_to(root)))
    for path in root.glob("*.tar.gz"):
        try:
            with tarfile.open(path) as archive:
                for member in archive:
                    name = source_name(member.name)
                    if member.isfile() and name:
                        value = sha256(archive.extractfile(member).read()).hexdigest()
                        source_index[(name, value)].append(f"{path.name}::{member.name}")
        except Exception as error:
            audit["integrity_errors"].append(dict(check=f"source archive {path.name}", error=str(error)))

    def verify_sources(table):
        resolved = {}
        for original, value in table.items():
            name = source_name(original)
            require(name and (name, value) in source_index, f"unresolved source version: {original} {value}")
            resolved[original] = source_index[(name, value)]
        return resolved

    provenance = load(root / "baseline/BUILD_PROVENANCE.json")
    build_result = load(root / "baseline/build-evidence/build-result.json")

    def baseline():
        base = root / "baseline"
        require(provenance["original_revision"] == PIN and provenance["xdna_uapi_revision"] == DRIVER_PIN,
                "baseline or XDNA revision differs from the pinned reproduction")
        for name, expected in provenance["source_sha256"].items():
            require(digest(inside(base / "sources", name)) == expected, f"patched baseline source mismatch: {name}")
        for name, expected in provenance["patch_sha256"].items():
            require(digest(inside(base, name)) == expected, f"recorded baseline patch mismatch: {name}")
        require(digest(base / "native.so") == build_result["library_sha256"], "native.so differs from build result")
        require((base / "native.so").stat().st_size == build_result["library_bytes"], "native.so size differs")
        payload_manifest = load(base / "build-evidence/payload_manifest.json")
        require(digest(base / "build-evidence/payload_manifest.json") == provenance["payload_manifest_sha256"],
                "payload manifest differs from build provenance")
        archive_path = root / "native-heteromosaic-baseline-20261027.tar.gz"
        require(archive_path.is_file(), "original pinned baseline payload missing")
        require(digest(archive_path) == BASELINE_PAYLOAD_SHA256, "original pinned baseline payload changed")
        with tempfile.TemporaryDirectory(prefix="native-comparison-audit-") as temporary, tarfile.open(archive_path) as archive:
            original = Path(temporary)
            archive_files = {m.name.split("/", 1)[1]: m for m in archive if m.isfile() and "/" in m.name}
            for name, expected in payload_manifest["source_sha256"].items():
                value = archive.extractfile(archive_files["source/" + name]).read()
                require(sha256(value).hexdigest() == expected, f"pinned original payload hash mismatch: {name}")
                target = inside(original, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(value)
            # Replay the two exact archived compatibility patches on the pinned
            # snapshot. The sole build-patch relocation is its include pathname.
            runtime = archive.extractfile(archive_files["patches/runtime-compat.patch"]).read()
            cloud = archive.extractfile(archive_files["patches/cloud-build.patch"]).read()
            for name, value in (("runtime-compat.patch", runtime), ("cloud-build.patch", cloud)):
                require(sha256(value).hexdigest() == payload_manifest["patch_sha256"][name], f"saved patch changed: {name}")
                require((base / "build-evidence/patches" / name).read_bytes() == value, f"build used a different saved patch: {name}")
            relocated = cloud.decode().replace("/notebooks/heteromega-baseline-logs/torch211-hip-compat.hpp",
                build_result["native_root"] + "/build-evidence/patches/torch211-hip-compat.hpp")
            require((base / "build-evidence/cloud-build-relocated.patch").read_text() == relocated,
                    "cloud build patch changed beyond the isolated include path")
            for value in (relocated.encode(), runtime):
                subprocess.run(["git", "apply", "--check", "-"], input=value, cwd=original, check=True, capture_output=True)
                subprocess.run(["git", "apply", "-"], input=value, cwd=original, check=True, capture_output=True)
            for name, expected in provenance["source_sha256"].items():
                require(digest(original / name) == expected, f"baseline differs from pinned source + approved patches: {name}")
        for entry in payload_manifest["xdna_uapi_files"]:
            actual = base / "libraries/xdna-driver-05-19-25" / entry["path"]
            require(digest(actual) == entry["sha256"], "pinned XDNA header mismatch")
        compat = base / "build-evidence/patches/torch211-hip-compat.hpp"
        require(digest(compat) == payload_manifest["patch_sha256"][compat.name], "Torch compatibility header changed")
        return dict(original_revision=PIN, snapshot_git_head=provenance["snapshot_git_head"],
            original_payload_files_verified=len(payload_manifest["source_sha256"]),
            patched_source_files_verified=len(provenance["source_sha256"]), compatibility_patch_replay_verified=True,
            native_library_sha256=build_result["library_sha256"], native_library_bytes=build_result["library_bytes"],
            build_status=build_result["status"], xdna_uapi_revision=DRIVER_PIN)
    audit["baseline"] = attempt("baseline provenance and patch replay", baseline)

    if (root / "source_provenance.json").exists():
        snapshot = load(root / "source_provenance.json")
        audit["harness_snapshot"] = attempt("harness source snapshot", lambda: dict(
            base_head=snapshot.get("base_head"),
            resolved_files=len(verify_sources(snapshot.get("sources", snapshot.get("source_sha256", {}))))))

    candidate_artifacts = {}
    for path in sorted((root / "artifacts").rglob("*.xclbin.json")):
        def artifact(path=path):
            manifest = load(path)
            binary, instructions = Path(str(path)[:-5]), path.parent / "insts.bin"
            require(digest(binary) == manifest["xclbin_sha256"] and digest(instructions) == manifest["insts_sha256"],
                    "candidate binary/instructions differ from manifest")
            verify_sources({"npu/ffn/" + name: value for name, value in manifest["dependency_sha256"].items()})
            contract = load(path.parent / "build_contract.json")
            require(contract["source_sha256"] == manifest["dependency_sha256"] and
                    all(manifest[key] == value for key, value in contract["expected_manifest"].items()),
                    "candidate manifest/build contract mismatch")
            candidate_artifacts[(manifest["xclbin_sha256"], manifest["insts_sha256"])] = (manifest, contract)
            return dict(manifest_sha256=digest(path), xclbin_sha256=manifest["xclbin_sha256"],
                        instructions_sha256=manifest["insts_sha256"], dependency_count=len(manifest["dependency_sha256"]))
        audit.setdefault("candidate_artifacts", {})[str(path.relative_to(root))] = attempt(str(path.relative_to(root)), artifact)

    def runtime_provenance(report, path):
        found = dict(source_files=len(verify_sources(report.get("provenance", {}).get("source_sha256", {}))))
        native = report.get("native_build")
        if native:
            require(native["native_library_sha256"] == build_result["library_sha256"], "loaded native.so differs from rebuilt binary")
            require(native["binding_library_sha256"] in binary_index, "loaded native binding .so missing")
            require(native["binding_sha256"] == next(value for name, value in report["provenance"]["source_sha256"].items()
                if name.endswith("native_heteromosaic_bindings.cpp")), "native binding source hash mismatch")
            header = root / "baseline/libraries/xdna-driver-05-19-25/src/include/uapi/drm_local/amdxdna_accel.h"
            require(native["driver_header_sha256"] == digest(header), "native runtime driver header differs")
            require(report["provenance"]["native_git_head"] == provenance["snapshot_git_head"], "native source snapshot differs")
            found["binding_binaries"] = binary_index[native["binding_library_sha256"]]
        for artifact in report.get("native_artifacts", []):
            if not artifact.get("sha256"):
                continue
            suffix = artifact["path"].split("hw_bins/", 1)[1]
            require(digest(root / "baseline/sources/hw_bins" / suffix) == artifact["sha256"], "native PDI/instruction mismatch")
        if report.get("native_config_sha256"):
            config_path = path.parent / Path(report["native_config_path"]).name
            require(digest(config_path) == report["native_config_sha256"], "native runtime config hash mismatch")
            require(load(config_path) == report["native_config"], "native runtime config content differs")
        for part in report.get("partitions", []):
            for label, item in part.get("npu", {}).get("artifacts", {}).items():
                manifest, contract = item["manifest"], item["build_contract"]
                key = (manifest["xclbin_sha256"], manifest["insts_sha256"])
                require(candidate_artifacts.get(key) == (manifest, contract), f"runtime candidate {label} artifact not exported exactly")
        return found

    total = Counter()
    fixture_groups = defaultdict(list)
    for path in sorted((root / "results").rglob("*.json")):
        report = load(path)
        if not isinstance(report, dict) or "config" not in report or "provenance" not in report:
            continue
        name = str(path.relative_to(root))
        entry = dict(status=report.get("status"), error=report.get("error"), report_sha256=digest(path),
                     scope=report.get("scope"), timed_invocations=len(report.get("samples", [])))
        audit["reports"][name] = entry
        entry["runtime_provenance"] = attempt(f"{name} runtime provenance", lambda r=report, p=path: runtime_provenance(r, p))
        metrics = dict(report.get("correctness", {}))
        if "partitions" in report:
            entry["kind"] = "direct_candidate"
            for part in report["partitions"]:
                metrics.update({f"P{part['npu_channels']}/{key}": value for key, value in part.get("correctness", {}).items()})
            entry["completed_npu_dispatches"] = sum(sum(part.get("completed_npu_dispatches_by_stage", {}).values()) for part in report["partitions"])
            entry["timed_invocations"] = sum(len(part.get("samples", [])) for part in report["partitions"])
        else:
            entry["kind"] = "native_projection_diagnostic" if "cases" in report else "native_ffn"
            entry["completed_npu_dispatches"] = report.get("completed_npu_dispatches", 0)
            entry["expected_npu_dispatches"] = report.get("expected_npu_dispatches", 0)
            entry["completion_count_matches_expected"] = entry["completed_npu_dispatches"] == entry["expected_npu_dispatches"]
            for case in report.get("cases", []):
                metrics.update({f"{case['name']}/{key}": value for key, value in case.get("correctness", {}).items()})
            entry["cases"] = [{"name": case["name"], "status": case.get("status"),
                "buffers_unchanged": case.get("buffers_unchanged"),
                "accuracy": attempt(f"{name}/{case['name']} metrics", lambda c=case: numerical_summary(c.get("correctness", {})))}
                for case in report.get("cases", [])]
            if "cases" in report:
                entry["record_validation"] = attempt(f"{name} diagnostic records", lambda r=report: diagnostic_records(r))
            for phase in ("warmup_samples", "samples"):
                metrics.update({f"{phase}/{i}": item["accuracy"] for i, item in enumerate(report.get(phase, [])) if "accuracy" in item})
        entry["accuracy"] = attempt(f"{name} numerical verdicts", lambda m=metrics: numerical_summary(m))
        if entry["kind"] in ("native_ffn", "direct_candidate"):
            variant = "native" if entry["kind"] == "native_ffn" else "upstream"
            # A rejected native numerical result still has a valid fixture.
            # Include it here independently of the success-only comparison.
            if report.get("input_sha256") and (report.get("native_packed_weight_sha256") or
                                               report.get("original_weight_buffers")):
                fixture = attempt(f"{name} fixture identity including failures",
                                  lambda r=report, v=variant: driver.fixture_identity(r, v))
                entry["fixture"] = fixture
                if fixture is not None:
                    fixture_groups[json.dumps(fixture, sort_keys=True)].append(dict(
                        report=name, kind=entry["kind"], status=entry["status"]))
                if variant == "native" and fixture is not None:
                    def buffer_records(report=report, fixture=fixture):
                        records = {}
                        for phase in ("before", "after"):
                            item = report.get("buffer_integrity_" + phase)
                            if item is None:
                                records[phase] = dict(recorded=False)
                                continue
                            expected = dict(
                                host_weights_match_initial=item.get("host_packed_weight_sha256") == fixture["full_packed_weight_sha256"],
                                device_weights_match_initial=item.get("device_packed_weight_sha256") == fixture["full_packed_weight_sha256"],
                                host_inputs_match_initial=item.get("host_input_sha256") == fixture["input_sha256"],
                                device_inputs_match_initial=item.get("device_input_sha256") == fixture["input_sha256"])
                            require(item.get("checks") == expected and item.get("passed") == all(expected.values()),
                                    f"native {phase} buffer verdict differs from actual recorded hashes")
                            records[phase] = dict(recorded=True, passed=item["passed"], checks=expected)
                        return records
                    entry["buffer_integrity"] = attempt(f"{name} before/after buffers", buffer_records)
        total[entry["kind"] + "_reports"] += 1
        total["completed_npu_dispatches"] += entry["completed_npu_dispatches"]
        total["failed_reports"] += report.get("status") == "failed"
        # Current success validators remain strict; failures are evidence, not
        # an audit error merely because their numerical gate rejected the run.
        if report.get("status") in SUCCESS and entry["kind"] in ("native_ffn", "direct_candidate"):
            args = SimpleNamespace(**report["config"])
            job = dict(iterations=args.iterations, mode="ordinary" if getattr(args, "mode", "latency") == "latency" else "diagnostic",
                       npu_channels=int(args.npu_channels) if entry["kind"] == "direct_candidate" else None)
            validate = driver.validate_candidate if entry["kind"] == "direct_candidate" else driver.validate_native
            entry["validator"] = attempt(f"{name} success validator", lambda r=report, j=job, a=args, v=validate: v(r, j, a))

    for path in sorted((root / "results").rglob("comparison_manifest.json")):
        def comparison(path=path):
            manifest = load(path)
            verify_sources(manifest["source_sha256"])
            args = SimpleNamespace(**manifest["config"])
            jobs = []
            for job in manifest["jobs"]:
                report_path = inside(path.parent, job["report_path"])
                if job.get("saved_report_sha256"):
                    require(digest(report_path) == job["saved_report_sha256"], "comparison saved report changed")
                if job["status"] in SUCCESS:
                    raw = load(report_path)
                    validate = driver.validate_native if job["variant"] == "native" else driver.validate_candidate
                    actual = validate(raw, job, args)
                    actual["report_sha256"] = digest(report_path)
                    require(actual == job["evidence"], "stored job evidence differs from current validator")
                jobs.append(dict(id=job["id"], status=job["status"], error=job.get("error"), returncode=job.get("returncode")))
            recalculated = driver.summarize(manifest, path.parent)
            require(recalculated == load(path.parent / "comparison_summary.json"), "comparison summary differs from raw reports")
            if recalculated["native_failed"]:
                require(not recalculated["comparisons"], "failed native baseline allowed a speedup comparison")
            return dict(status=manifest["status"], jobs=jobs, summary_verified=True,
                native_failed=recalculated["native_failed"], admitted_comparisons=recalculated["comparisons"],
                full_packed_weights_and_inputs_match=recalculated["full_packed_weights_and_inputs_match"],
                comparison_allowed=bool(recalculated["comparisons"]))
        audit["comparisons"][str(path.relative_to(root))] = attempt(f"{path.relative_to(root)} comparison validation", comparison)
    audit["totals"] = dict(total)
    audit["full_ffn_fixture_groups_including_failed_native"] = [dict(fixture=json.loads(identity), reports=reports)
        for identity, reports in fixture_groups.items()]
    compared_kinds = {item["kind"] for reports in fixture_groups.values() for item in reports}
    audit["cross_backend_full_ffn_fixture_match_including_failed_native"] = (
        len(fixture_groups) == 1 if compared_kinds == {"native_ffn", "direct_candidate"} else None)
    audit["fixture_match_does_not_change_native_acceptance"] = True
    audit["native_failed_reports"] = [name for name, entry in audit["reports"].items()
                                      if entry["kind"].startswith("native") and entry["status"] == "failed"]
    audit["validator_source_sha256"] = digest(Path(driver.__file__))
    audit["status"] = "integrity_failed" if audit["integrity_errors"] else "integrity_passed"
    return audit


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, default=Path("/tmp/native-comparison-evidence-20261027"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("audit.json"))
    args = parser.parse_args(argv)
    try:
        result = run(args.evidence_dir)
    except Exception as error:
        result = dict(status="integrity_failed", evidence_dir=str(args.evidence_dir),
                      integrity_errors=[dict(check="audit setup", error=str(error))])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: result.get(key) for key in ("status", "totals", "native_failed_reports", "integrity_errors")}))
    return 0 if result["status"] == "integrity_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
