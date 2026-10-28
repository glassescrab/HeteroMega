#!/usr/bin/env python3
"""Audit the exported v9 split-M32 + preconverted-B physical NPU graph.

This reads compiler outputs; it neither compiles nor runs an accelerator. The
export contains a relocatable projection object, not linked core ELFs. Thus the
data-buffer map is confirmed while final program size/static-data placement is
explicitly outside the available evidence.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def object_sections(path):
    """Read ELF32 section headers without requiring AIE binutils."""
    data = path.read_bytes()
    require(data[:6] == b"\x7fELF\x01\x01", "Expected little-endian ELF32")
    header = struct.unpack_from("<HHIIIIIHHHHHH", data, 16)
    elf_type, machine = header[:2]
    section_offset, section_size, section_count, strings_index = (
        header[5], header[10], header[11], header[12]
    )
    require(elf_type == 1 and section_size == 40, "Expected relocatable ELF32")
    raw = [struct.unpack_from("<IIIIIIIIII", data, section_offset + i * 40)
           for i in range(section_count)]
    strings = raw[strings_index]
    names = data[strings[4]:strings[4] + strings[5]]
    sections = []
    for record in raw:
        name = names[record[0]:].split(b"\0", 1)[0].decode()
        if record[2] & 2:  # SHF_ALLOC
            sections.append({"name": name, "bytes": record[5],
                             "executable": bool(record[2] & 4)})
    return {"elf_type": "ET_REL", "machine": machine,
            "allocated_sections": sections,
            "all_executable_sections_bytes": sum(
                s["bytes"] for s in sections if s["executable"]),
            "nonexecutable_allocated_bytes": sum(
                s["bytes"] for s in sections if not s["executable"]),
            "final_linked_core_program_bytes": None}


def category(name):
    for prefix, kind in [
        ("direct_a_broadcast_", "activation"), ("direct_a_host_", "activation_host"),
        ("direct_w_broadcast_", "weight"), ("direct_w_host_", "weight_host"),
        ("direct_acc", "accumulator"), ("direct_dequant_", "dequant_scratch"),
        ("direct_gate_", "gate_handoff"), ("direct_y_worker_", "output"),
        ("direct_y_host_", "output_host"),
    ]:
        if name.startswith(prefix):
            return kind
    raise ValueError(f"Unrecognized allocated buffer {name}")


def audit_stage(path, lut_source):
    logical_path = path / "aie.mlir"
    physical_path = path / "input_with_addresses.mlir"
    logical, physical = logical_path.read_text(), physical_path.read_text()
    require("aie.device(npu2)" in logical, "Expected npu2")
    tiles = {m[1]: (int(m[2]), int(m[3])) for m in re.finditer(
        r"%(\w+) = aie.tile\((\d+), (\d+)\)", physical)}
    buffers = defaultdict(list)
    for lineno, line in enumerate(physical.splitlines(), 1):
        if "= aie.buffer(" not in line:
            continue
        match = re.search(
            r'%(\w+) = aie.buffer\(%(\w+)\) \{address = (\d+) : i32, '
            r'sym_name = "([^\"]+)"\} : memref<(\d+)x(bf16|ui8|f32)>', line)
        require(match is not None, f"Unparsed buffer on physical MLIR line {lineno}")
        name, tile, address, symbol, elements, dtype = match.groups()
        require(name == symbol, f"Unexpected symbol alias {name}")
        size = int(elements) * {"bf16": 2, "ui8": 1, "f32": 4}[dtype]
        buffers[tile].append({"name": name, "category": category(name),
                              "address": int(address), "bytes": size,
                              "dtype": dtype, "line": lineno})
    core_re = (r"%core_\d+_\d+ = aie.core\(%(\w+)\) \{(.*?)"
               r"\n    \} \{([^\n]+)\}")
    cores = list(re.finditer(core_re, physical, re.S))
    require(len(cores) == 32, "Expected exactly 32 physical cores")
    require({tiles[m[1]] for m in cores} ==
            {(c, r) for c in range(8) for r in range(2, 6)}, "Expected 8 x 4 cores")
    roles = defaultdict(list)
    stage = path.name
    for match in cores:
        tile, body, attrs = match.groups()
        col, row = tiles[tile]
        role = "down" if stage == "down" else ("gate" if col % 2 == 0 else "up")
        stack = int(re.search(r"stack_size = (\d+)", attrs)[1])
        require(stack == 4096, f"Unexpected stack reservation on {tile}")
        allocated = sorted(buffers[tile], key=lambda b: b["address"])
        cursor = stack
        for buf in allocated:
            require(buf["address"] == cursor, f"Noncontiguous/overlapping map on {tile}")
            cursor += buf["bytes"]
        by_category = defaultdict(list)
        for buf in allocated:
            by_category[buf["category"]].append(buf["bytes"])
        expected = {"activation": [8192, 8192], "weight": [4352, 4352],
                    "dequant_scratch": [16384], "accumulator": [4096, 4096]}
        expected["gate_handoff" if role == "gate" else "output"] = (
            [4096] if role == "up" else [4096, 4096])
        require(dict(by_category) == expected, f"Unexpected allocated buffers on {tile}")
        # The compiled schedule must hold W through one pair dequant and both A
        # chunks, with each activation slot released after its paired MAC.
        operations = []
        for line in body.splitlines():
            if "func.call @w4a16_prefill_dequantize_pair(" in line:
                operations.append("dequant_pair")
            elif "func.call @w4a16_prefill_accumulate_pair_m0(" in line:
                operations.append("mac_m0")
            elif "func.call @w4a16_prefill_accumulate_pair_m1(" in line:
                operations.append("mac_m1")
            elif "aie.use_lock(%direct_w_broadcast_" in line:
                operations.append("weight_acquire" if "Acquire" in line else "weight_release")
            elif "aie.use_lock(%direct_a_broadcast_" in line:
                operations.append("activation_acquire" if "Acquire" in line else "activation_release")
        require(operations == ["weight_acquire", "dequant_pair", "activation_acquire",
                               "mac_m0", "activation_release", "activation_acquire",
                               "mac_m1", "activation_release", "weight_release"],
                f"Unexpected compiled split-A order on {tile}")
        linked_lut = 0
        if role == "up":
            digest = re.search(r'silu_mul_([0-9a-f]{64})_2048.o', attrs)
            require(digest is not None and digest[1] == sha256(lut_source),
                    "SiLU source does not match linked object name")
            require("func.call @w4a16_prefill_reuse_finish(" not in body,
                    "Up tile still contains a finish copy")
            calls = re.findall(r"func.call @silu_mul_bf16\(([^\n]+)", body)
            require(len(calls) == 2 and "direct_acc0_" in calls[0]
                    and "direct_acc1_" in calls[1], "SiLU must read C0/C1 directly")
            linked_lut = 4096
        require(cursor + linked_lut <= 65536, "Known core data exceeds 64 KiB")
        roles[role].append({"tile": [col, row], "stack_reserved_bytes": stack,
                            "assigned_buffer_bytes": cursor - stack,
                            "assigned_map_end_bytes": cursor,
                            "known_lut_source_bytes": linked_lut,
                            "known_data_plus_stack_bytes": cursor + linked_lut,
                            "nominal_remaining_bytes": 65536 - cursor - linked_lut,
                            "allocations": allocated})
    role_summary = {}
    for role, values in roles.items():
        representative = values[0]
        require(all(v["known_data_plus_stack_bytes"] == 61952 for v in values),
                f"Unexpected {role} footprint")
        role_summary[role] = {"tiles": [v["tile"] for v in values],
                              "count": len(values),
                              "representative": representative}
    memtiles = []
    for tile in sorted(buffers, key=lambda t: tiles[t]):
        if tiles[tile][1] != 1:
            continue
        allocated = sorted(buffers[tile], key=lambda b: b["address"])
        cursor = 0
        for buf in allocated:
            require(buf["address"] == cursor, f"Memtile overlap/gap on {tile}")
            cursor += buf["bytes"]
        memtiles.append({"tile": list(tiles[tile]), "assigned_bytes": cursor,
                         "by_category": dict(Counter(
                             {cat: sum(b["bytes"] for b in allocated if b["category"] == cat)
                              for cat in {b["category"] for b in allocated}}))})
    host_a = [b for arr in buffers.values() for b in arr
              if b["category"] == "activation_host"]
    require(len(host_a) == 8 and all(b["bytes"] == 16384 for b in host_a),
            "Expected four double-buffered 16-KiB memory-tile A streams")
    core_dma = re.findall(r"aie.dma_bd\(%direct_a_broadcast_[^\n]+", physical)
    host_dma = re.findall(r"aie.dma_bd\(%direct_a_host_[^\n]+", physical)
    require(len(core_dma) == 64 and all("len = 4096" in x for x in core_dma),
            "Expected two 4096-element DMA descriptors per core")
    require(len(host_dma) == 16 and all("len = 8192" in x for x in host_dma),
            "Expected full 8192-element memory-tile DMA descriptors")
    permutation_lines = [line for line in host_dma if "sizes =" in line]
    require(len(permutation_lines) == 8, "Expected one outgoing permutation per host A slot")
    require("direct_up_" not in logical and "direct_up_" not in physical,
            "Unexpected intermediate up scratch")
    lut_text = lut_source.read_text()
    require(all(re.search(rf"static float {name}\[512\]", lut_text)
                for name in ("sigmoid_ab", "sigmoid_cd")), "Unexpected LUT definitions")
    return {"status": "compiler_output_confirmed", "device": "npu2",
            "inputs": {name: sha256(path / name) for name in
                       ("aie.mlir", "input_with_addresses.mlir", "kernel.o", "kernel.dis")},
            "core_roles": role_summary, "memory_tiles": memtiles,
            "memory_tile_max_assigned_bytes": max(m["assigned_bytes"] for m in memtiles),
            "activation_dma": {"core_buffer_count": 64, "core_buffer_bytes": 8192,
                               "host_memory_tile_buffer_count": 8,
                               "host_memory_tile_buffer_bytes": 16384,
                               "core_dma_elements": 4096, "memory_tile_dma_elements": 8192,
                               "outgoing_permutation_example": permutation_lines[0].strip()},
            "split_order_all_cores_verified": True,
            "odd_up_scratch_absent": True,
            "projection_object": object_sections(path / "kernel.o")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler-dir", type=Path, required=True)
    parser.add_argument("--silu-source", type=Path,
                        default=Path(__file__).resolve().parents[3] / "npu/ffn/silu_mul.cc")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".json"))
    args = parser.parse_args()
    result = {"schema_version": 1, "scope": "v9 combined split-M32 A + preconverted B, P4096",
              "shape": {"M": 512, "H": 4096, "I": 14336, "P": 4096},
              "audit_script_sha256": sha256(Path(__file__)),
              "silu_source_sha256": sha256(args.silu_source),
              "stages": {stage: audit_stage(args.compiler_dir / stage, args.silu_source)
                         for stage in ("swiglu", "down")},
              "limitations": [
                  "Physical MLIR confirms buffer addresses and reserved stack, not actual maximum stack use.",
                  "The 4096-byte LUT is source-confirmed and its source hash matches the linked object name; its final linked address and other linker data are unavailable.",
                  "61952-byte known data plus stack leaves 3584 nominal bytes, not a proof of final linker headroom.",
                  "kernel.o is ET_REL. Its text total excludes generated main, pointwise code, linked runtime, alignment and dead-section removal; final program SRAM occupancy is unknown.",
                  "Buffer/DMA structure enables two A slots; it does not measure actual DMA/compute overlap or stalls.",
                  "v10 preconverted A uses existing scratch tail by source contract, but these v9 outputs do not prove v10 allocation identity.",
              ]}
    result["passed"] = True
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "output": str(args.output),
                      "known_max_core_bytes": 61952,
                      "projection_object_text_bytes": {
                          k: v["projection_object"]["all_executable_sections_bytes"]
                          for k, v in result["stages"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
