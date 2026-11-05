# Source the matching MLIR-AIE ironenv before invoking this makefile.
SHELL := /bin/bash
PYTHON ?= python3
length ?= 14336
tile_size ?= 1024
cols ?= 1
iterations ?= 20
build_dir ?= build

.PHONY: all compile run mlir clean
all: compile

# Always invoke the explicit-output JIT compilation. Its final.prj object
# cache is keyed by filename; the generator includes source hash and tile
# geometry in that filename so source/shape edits cannot reuse stale code.
compile:
	mkdir -p $(build_dir)
	$(PYTHON) silu_mul.py -d npu2 -l $(length) --tile-size $(tile_size) -co $(cols) \
		--xclbin-path $(build_dir)/final.xclbin --insts-path $(build_dir)/insts.bin \
		--pdi-path $(build_dir)/final.pdi

run: compile
	$(PYTHON) run_silu_mul.py --xclbin $(build_dir)/final.xclbin \
		--insts $(build_dir)/insts.bin --length $(length) --iterations $(iterations)

mlir:
	$(PYTHON) silu_mul.py -d npu2 -l $(length) --tile-size $(tile_size) -co $(cols) --emit-mlir

clean:
	rm -rf $(build_dir)
