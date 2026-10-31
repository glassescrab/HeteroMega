"""CPU evidence/CLI checks for the opt-in output-only DMA-BUF experiment."""

import contextlib
import copy
import io
import unittest

from . import compare_upstream_native as compare
from . import run_upstream_partition as bench
from .test_native8_integration import optimized_report


def dmabuf_report():
    args, job, report = optimized_report()
    args.dmabuf_gpu_output = True
    part = report["partitions"][0]
    report["config"]["dmabuf_gpu_output"] = True
    registry = dict(registered_types_shared=True, glibcxx_cxx11_abi=1, gxx_abi_version=1018,
                    pybind_internals_id="__pybind11_internals_v5_gcc_libstdcpp_cxxabi1018__")
    builds = {}
    for label, source in (("xrt_bridge", "xrt_dmabuf_bindings.cpp"),
                          ("hip_allocation", "hip_dmabuf_bindings.cpp")):
        builds[label] = dict(build_fingerprint="a" * 64, binding_library_sha256="b" * 64,
            source_sha256={"experiments/ffn_partition/dmabuf_output.py": "c" * 64,
                           "experiments/ffn_partition/" + source: "d" * 64})
    builds["xrt_bridge"].update(registry=registry, expected_pybind_internals_id=registry["pybind_internals_id"],
        pyxrt_sha256="e" * 64, xrt_library_sha256="f" * 64,
        xrt_header_sha256={"xrt_bo.h": "a" * 64}, pybind_header_sha256={"common.h": "b" * 64})
    builds["hip_allocation"]["runtime_dependency_sha256"] = {f"/runtime/{i}": "a" * 64 for i in range(4)}
    contract = dict(shape=[512, 4096], dtype="BF16", python_buffer_type="pyxrt.bo", output_argument=5,
        copy_fallback=False, fd_closed_after_import=True, kernel_group_id=0x10000, kernel_bank_id=0,
        allocation=dict(nbytes=4194304, export_offset=0, export_fd_closed=True, gpu_pointer=4096,
            allocation="hipMalloc standalone allocation", export="hsa_amd_portable_export_dmabuf"),
        imported_bo=dict(nbytes=4194304, bank_id=0, flags_name="normal", flags=0, address=8192),
        registry=registry, build=builds)
    part["npu"].update(gpu_output_dmabuf=True, gpu_output_dmabuf_contract=contract,
                       host_output_readback="gpu_owned_dmabuf")
    part["runtime"] = dict(gpu_output_dmabuf=True, output=contract)
    for record in part["validation_runs"] + part["warmup_samples"] + part["samples"]:
        if record["mode"] == "baseline":
            continue
        diag = record["diagnostics"]
        calls = diag["npu"]["completed_dispatches_total"] // 2
        diag.update(gpu_output_dmabuf=True, final_output_h2d_copies=0)
        diag["npu"].update(gpu_output_dmabuf=True, gpu_output_sync_count=calls,
                           final_output_bo_reads=0, final_output_h2d_copies=0)
    part["gpu_output_sync_count"] = part["completed_candidate_calls"]
    return args, job, report


class DmaBufIntegrationTests(unittest.TestCase):
    def test_cli_changes_candidate_output_only_and_rejects_conflicting_mappings(self):
        args = compare.parse_args(["--native-root", "/native", "--artifact-root", "/artifact",
            "--no-build-candidate", "--output-dir", "/output", "--npu-channels", "4096",
            "--dmabuf-gpu-output"])
        for job in compare.build_jobs(args):
            if job["variant"] == "native":
                self.assertNotIn("--dmabuf-gpu-output", job["command"])
            else:
                child, channels = bench.parse_args(job["command"][3:])
                self.assertTrue(child.dmabuf_gpu_output)
                self.assertFalse(child.mapped_npu_output)
                self.assertFalse(child.shared_gpu_output)
                self.assertEqual(channels, [4096])
                self.assertEqual(bench.kernel_options(child), compare.candidate_options(args))
                self.assertEqual(child.down_output_layout, "row_major")
        ordinary, _ = bench.parse_args(["--no-build"])
        self.assertFalse(ordinary.dmabuf_gpu_output)
        for flag in ("--mapped-npu-output", "--shared-gpu-output"):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                bench.parse_args(["--no-build", "--dmabuf-gpu-output", flag])

    def test_complete_evidence_preserves_all_existing_numerical_and_structural_gates(self):
        args, job, report = dmabuf_report()
        result = compare.validate_candidate(report, job, args)
        self.assertEqual(result["status"], "passed")
        mutations = (
            lambda r: r["config"].update(dmabuf_gpu_output=False),
            lambda r: r["partitions"][0]["runtime"].update(output={}),
            lambda r: r["partitions"][0]["npu"]["gpu_output_dmabuf_contract"]["allocation"].update(export_offset=4096),
            lambda r: r["partitions"][0]["npu"]["gpu_output_dmabuf_contract"]["allocation"].update(export_fd_closed=False),
            lambda r: r["partitions"][0]["npu"]["gpu_output_dmabuf_contract"]["imported_bo"].update(bank_id=1),
            lambda r: r["partitions"][0]["npu"]["gpu_output_dmabuf_contract"]["registry"].update(registered_types_shared=False),
            lambda r: r["partitions"][0]["npu"]["gpu_output_dmabuf_contract"]["build"]["hip_allocation"].update(binding_library_sha256="bad"),
            lambda r: r["partitions"][0]["validation_runs"][0]["diagnostics"]["npu"].update(final_output_bo_reads=1),
            lambda r: r["partitions"][0]["validation_runs"][0]["diagnostics"]["npu"].update(gpu_output_sync_count=0),
            lambda r: r["partitions"][0].update(gpu_output_sync_count=0),
            lambda r: r["partitions"][0]["input_write_counts_by_stage"].update(swiglu=[0, 1, 1]),
            lambda r: r["partitions"][0]["validation_runs"][4].update(output_sha256="1" * 64),
        )
        for index, mutate in enumerate(mutations):
            broken = copy.deepcopy(report)
            mutate(broken)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                compare.validate_candidate(broken, job, args)

    def test_larger_backing_requires_exact_logical_subbuffer_evidence(self):
        args, job, report = dmabuf_report()
        contract = report["partitions"][0]["npu"]["gpu_output_dmabuf_contract"]
        contract.update(import_extent_policy="zero_offset_logical_subbuffer", sub_buffer_used=True,
            sub_buffer_offset=0, imported_backing_bo=dict(contract["imported_bo"], nbytes=8388608))
        contract["allocation"]["backing_nbytes"] = 8388608
        compare.validate_candidate(report, job, args)
        for mutate in (
            lambda c: c.pop("import_extent_policy"),
            lambda c: c.update(sub_buffer_offset=4096),
            lambda c: c.update(sub_buffer_used=False),
            lambda c: c["allocation"].update(backing_nbytes=2097152),
            lambda c: c["imported_backing_bo"].update(address=12288),
            lambda c: c["imported_bo"].update(nbytes=8388608),
        ):
            broken = copy.deepcopy(report)
            mutate(broken["partitions"][0]["npu"]["gpu_output_dmabuf_contract"])
            with self.assertRaises(ValueError):
                compare.validate_candidate(broken, job, args)


if __name__ == "__main__":
    unittest.main()
