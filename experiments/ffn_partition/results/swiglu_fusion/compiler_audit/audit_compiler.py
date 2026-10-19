"""Reproduce the retained M128/K128/P128 SwiGLU compiler-artifact audit.

Requires only Python and GNU readelf, not MLIR-AIE or NPU hardware. The build
directory is an extracted compiler bundle; this script never changes it.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def readelf(path, option):
    return subprocess.run(["readelf", option, str(path)], check=True,
                          capture_output=True, text=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_directory", type=Path)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    build, out = args.build_directory, args.output
    prj = build / "final.prj"
    lowered_path = prj / "input_with_addresses.mlir"
    lowered = lowered_path.read_text()
    contract = json.loads((build / "build_contract.json").read_text())
    manifest = json.loads((build / "final.xclbin.json").read_text())
    assert (manifest["m"], manifest["k"], manifest["channels"], manifest["m_reuse"]) == (128, 128, 128, 2)
    checks = []

    def require(name, value):
        checks.append({"check": name, "passed": bool(value)})
        assert value, name

    for path, expected in contract["source_sha256"].items():
        require(f"source hash: {path}", sha(args.repository / path) == expected)
    for key, expected in contract["expected_manifest"].items():
        require(f"manifest: {key}", manifest[key] == expected)
    for binary, field in [("final.xclbin", "xclbin_sha256"), ("insts.bin", "insts_sha256")]:
        require(f"binary hash: {binary}", sha(build / binary) == manifest[field])

    core_blocks = {(int(c), int(r)): body for c, r, body in re.findall(
        r"^    %core_\d+_\d+ = aie.core\(%tile_(\d+)_(\d+)\) \{\n(.*?)^    \}",
        lowered, re.M | re.S)}
    dma_blocks = {(int(c), int(r)): body for c, r, body in re.findall(
        r"^    %mem_\d+_\d+ = aie.mem\(%tile_(\d+)_(\d+)\) \{\n(.*?)^    \}",
        lowered, re.M | re.S)}
    require("32 projection cores", set(core_blocks) == {(c, r) for c in range(8) for r in range(2, 6)})
    require("32 compute DMA regions", set(dma_blocks) == set(core_blocks))
    buffers = []
    for match in re.finditer(r"^    %(\w+) = aie.buffer\(%tile_(\d+)_(\d+)\) \{address = (\d+) : i32,.*?memref<(\d+)x(bf16|f32|ui8)>", lowered, re.M):
        name, c, r, address, elements, dtype = match.groups()
        size = int(elements) * {"bf16": 2, "f32": 4, "ui8": 1}[dtype]
        buffers.append(dict(name=name, column=int(c), row=int(r), address=int(address), bytes=size))
    gate_buffers = [b for b in buffers if b["name"].startswith("swiglu_gate_")]
    require("one two-deep gate pool for each of 16 pairs", len(gate_buffers) == 32)
    for b in gate_buffers:
        pair, row, slot = map(int, re.fullmatch(r"swiglu_gate_(\d+)_(\d+)_buff_(\d+)", b["name"]).groups())
        require(f"gate pool on producer: {b['name']}",
                (b["column"], b["row"], b["bytes"]) == (2 * pair, row + 2, 2048) and slot in (0, 1))
    require("no gate buffer used by any DMA descriptor", not re.search(r"aie.dma_bd\(%swiglu_gate_", lowered))
    require("no compute-to-compute stream flow", not re.search(r"aie.flow\(%tile_\d+_\d+, DMA : \d+, %tile_\d+_\d+,", lowered))
    z_shims = re.findall(r"aie.shim_dma_allocation @swiglu_z_host_(\d+)_shim_alloc", lowered)
    require("four compact Z output shim drains", sorted(map(int, z_shims)) == [1, 3, 5, 7])

    core_results, evidence_paths = [], [build / "build_contract.json", build / "final.xclbin.json", build / "compile.log", lowered_path, prj / "aie.mlir"]
    section_outputs = {}
    for (col, row), body in sorted(core_blocks.items()):
        odd = col % 2 == 1
        ident = f"{col}_{row}"
        ld_path = prj / f"ldScripts_main_core_{ident}.ld.script"
        elf_path = prj / f"elfs_main_core_{ident}/elfs_main_core_{ident}.elf"
        evidence_paths.extend([ld_path, elf_path])
        script = ld_path.read_text()
        section_text, symbol_text = readelf(elf_path, "-SW"), readelf(elf_path, "-sW")
        section_outputs[ident] = section_text
        sections = {name: {"address": int(address, 16), "bytes": int(size, 16), "flags": flags}
                    for name, address, size, flags in re.findall(
                        r"\[\s*\d+\]\s+(\.\S+)\s+\S+\s+([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+(\S+)", section_text)}
        own_buffers = sorted([b for b in buffers if (b["column"], b["row"]) == (col, row)], key=lambda b: b["address"])
        intervals = [(0, 2048, "reserved stack")] + [(b["address"], b["address"] + b["bytes"], b["name"]) for b in own_buffers]
        data_sections = {name: s for name, s in sections.items() if "A" in s["flags"] and "X" not in s["flags"]}
        for name, section in data_sections.items():
            require(f"{ident}: allocated data belongs to own tile", 0x70000 <= section["address"] < 0x80000)
            begin = section["address"] - 0x70000
            intervals.append((begin, begin + section["bytes"], name))
        intervals.sort()
        require(f"{ident}: nonoverlapping SRAM buffers/stack/ELF data", all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])))
        require(f"{ident}: static allocations fit 64 KiB", intervals[-1][1] <= 65536)
        require(f"{ident}: expected static SRAM high water", intervals[-1][1] == (45248 if odd else 39104))
        require(f"{ident}: reserved stack is 2048 bytes", re.search(r"\. \+= 0x800; /\* stack \*/", script))
        starts = re.findall(r"aie.dma_start\((S2MM|MM2S), (\d+),", dma_blocks[(col, row)])
        s2mm = [int(ch) for direction, ch in starts if direction == "S2MM"]
        mm2s = [int(ch) for direction, ch in starts if direction == "MM2S"]
        require(f"{ident}: exactly A/W inbound channels", s2mm == [0, 1])
        require(f"{ident}: only up cores drain Z", mm2s == ([0] if odd else []))
        dma_buffers = re.findall(r"aie.dma_bd\(%(\w+)", dma_blocks[(col, row)])
        require(f"{ident}: DMA buffers are A/W and optional Z", all(x.startswith(("swiglu_a_", "swiglu_w_", "swiglu_z_")) for x in dma_buffers))
        stream_starts = list(re.finditer(r"aie.dma_start\((S2MM|MM2S), (\d+),", dma_blocks[(col, row)]))
        for i, match in enumerate(stream_starts):
            end = stream_starts[i+1].start() if i+1 < len(stream_starts) else len(dma_blocks[(col, row)])
            stream_buffers = re.findall(r"aie.dma_bd\(%(\w+)", dma_blocks[(col, row)][match.end():end])
            expected_prefix = "swiglu_z_" if match.group(1) == "MM2S" else ("swiglu_a_" if match.group(2) == "0" else "swiglu_w_")
            require(f"{ident}: {match.group(1)}{match.group(2)} buffer ownership", len(stream_buffers) == 2 and all(x.startswith(expected_prefix) for x in stream_buffers))
        calls = re.findall(r"func.call @(\w+)", body)
        require(f"{ident}: unchanged projection entry points", all(calls.count(x) == 1 for x in ("w4a16_prefill_reuse_init", "w4a16_prefill_reuse_accumulate", "w4a16_prefill_reuse_finish")))
        require(f"{ident}: pointwise on odd cores only", calls.count("silu_mul_bf16") == int(odd))
        require(f"{ident}: linked pointwise on odd cores only", bool(re.search(r"FUNC.*\bsilu_mul_bf16$", symbol_text, re.M)) == odd)
        require(f"{ident}: all projection symbols present", all(re.search(rf"FUNC.*\b{x}$", symbol_text, re.M) for x in ("w4a16_prefill_reuse_init", "w4a16_prefill_reuse_accumulate", "w4a16_prefill_reuse_finish")))
        require(f"{ident}: ELF data is only expected LUT", sum(s["bytes"] for s in data_sections.values()) == (4096 if odd else 0))
        require(f"{ident}: linked code fits 128 KiB program region", sections[".text"]["address"] == 0 and sections[".text"]["bytes"] <= 131072)
        if odd:
            pair, row_index = col // 2, row - 2
            for slot in range(2):
                name = f"swiglu_gate_{pair}_{row_index}_buff_{slot}"
                require(f"{ident}: directly references shared {name}", f"%{name}" in body)
                symbol = re.search(rf"^\s*\d+:\s+([0-9a-f]+)\s+.*\b{name}$", symbol_text, re.M)
                require(f"{ident}: west-memory symbol for {name}", symbol and int(symbol.group(1), 16) == 0x50000 + 35008 + slot * 2048)
            require(f"{ident}: BF16 projection finish precedes activation", calls.index("w4a16_prefill_reuse_finish") < calls.index("silu_mul_bf16"))
        core_results.append(dict(column=col, row=row, role="up_and_silu" if odd else "gate", s2mm_channels=s2mm, mm2s_channels=mm2s,
            graph_buffer_bytes=sum(b["bytes"] for b in own_buffers), stack_reserved_bytes=2048,
            elf_data_bytes=sum(s["bytes"] for s in data_sections.values()),
            static_sram_high_water_bytes=intervals[-1][1], static_sram_headroom_bytes=65536-intervals[-1][1],
            program_text_bytes=sections[".text"]["bytes"],
            buffer_intervals=[dict(begin=a, end=b, name=c) for a,b,c in intervals]))

    out.mkdir(parents=True, exist_ok=True)
    hashes = {str(p.relative_to(build)): {"sha256": sha(p), "bytes": p.stat().st_size} for p in evidence_paths}
    # Binary files are fingerprinted but never copied into the evidence directory.
    for path in (build / "final.xclbin", build / "insts.bin", build / "final.pdi"):
        hashes[str(path.relative_to(build))] = {"sha256": sha(path), "bytes": path.stat().st_size}
    report = dict(schema_version=1, classification="compiled artifact audit", build_directory_name=build.name,
        scope=dict(m=128, k=128, channels=128, reuse=2), target_mlir_aie_commit=manifest["target_mlir_aie_commit"],
        source_sha256=contract["source_sha256"], all_checks_passed=all(c["passed"] for c in checks),
        explicit_check_count=len(checks), checks=checks, cores=core_results,
        summary=dict(projection_cores=32, pointwise_cores=16, shared_gate_pools=16, shared_gate_buffers=32,
            gate_dma_descriptors=0, per_core_s2mm_channels=2, output_columns=[1,3,5,7],
            gate_static_sram_high_water_bytes=39104, up_static_sram_high_water_bytes=45248,
            gate_static_sram_headroom_bytes=26432, up_static_sram_headroom_bytes=20288),
        limitations=["This exact compiled allocation audit covers only M128/K128/P128 with reuse=2.",
            "Static allocation plus reserved stack is not a runtime stack high-water measurement or a bank-contention profile.",
            "The retained .stack_sizes section is incomplete for the linked call graph; no dynamic stack bound is inferred.",
            "No claim about model-size correctness or performance is derived from this compiler audit."],
        evidence=hashes)
    (out / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    excerpts = ["# Lowered artifact excerpts\n", f"Source: final.prj/input_with_addresses.mlir\nSHA256: {sha(lowered_path)}\n"]
    for i, line in enumerate(lowered.splitlines(), 1):
        if ("swiglu_gate_0_0_buff" in line or "aie.flow(%tile_" in line or "aie.shim_dma_allocation @swiglu_z_host" in line
                or "func.call @silu_mul_bf16" in line):
            excerpts.append(f"{i}: {line}\n")
    for ident in ("0_2", "1_2"):
        excerpts.append(f"\n# Compute tile {ident} DMA region\n{dma_blocks[tuple(map(int, ident.split('_')))]}\n")
        excerpts.append(f"\n# Core {ident} ELF sections (readelf -SW)\n{section_outputs[ident]}\n")
        excerpts.append(f"\n# Core {ident} linker script\n{(prj / f'ldScripts_main_core_{ident}.ld.script').read_text()}\n")
    (out / "evidence_excerpts.txt").write_text("".join(excerpts))
    print(json.dumps({"all_checks_passed": report["all_checks_passed"], "explicit_check_count": len(checks), "summary": report["summary"]}, indent=2))


if __name__ == "__main__":
    main()
