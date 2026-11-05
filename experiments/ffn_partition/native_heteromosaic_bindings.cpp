// Thin adapter to the existing native HeteroMosaic shared-buffer runtime.
// Link an already built model .so: no copied kernels or replacement dispatcher.
#include "unified_llm_w4a16_hetero/npuSetup.hpp"
#include "unified_llm_w4a16_hetero/hetero_compute.hpp"
#include "hipkernels/w4a16_gemm_packed.hpp"
#include <c10/hip/HIPStream.h>
#include <torch/extension.h>
#include <pybind11/stl.h>
#include <chrono>
#include <limits>

namespace py = pybind11;
namespace {
using Clock = std::chrono::steady_clock;
uint64_t completed = 0;
bool initialized = false;

void sync(hipStream_t stream) {
    auto status = hipStreamSynchronize(stream);
    TORCH_CHECK(status == hipSuccess, "HIP synchronization failed: ", hipGetErrorString(status));
}

void require_tensor(const torch::Tensor &tensor, int64_t rows, int64_t cols) {
    TORCH_CHECK(tensor.is_cuda() && tensor.is_contiguous() &&
                    tensor.scalar_type() == torch::kBFloat16 && tensor.dim() == 2 &&
                    tensor.size(0) == rows && tensor.size(1) == cols,
                "expected contiguous ROCm BF16 tensor [", rows, ",", cols, "]");
}

py::dict initialize(const std::string &config, int npu_rows) {
    TORCH_CHECK(!initialized, "native adapter is single-initialization; use a fresh process");
    TORCH_CHECK(config_map.empty() && ptr_to_handle_map.empty(),
                "native runtime globals are already populated; use a fresh process");
    TORCH_CHECK(npu_rows == 256, "bounded native baseline requires npu_rows=256");
    read_npu_config(config);
    TORCH_CHECK(hw_target == "hetero", "configuration must select hetero");
    TORCH_CHECK(use_packed_weights && pad_packed_weights == 0,
                "native benchmark requires packed weights without padding");
    TORCH_CHECK(initialize_xdna_driver("/dev/accel/accel0") == 0, "XDNA initialization failed");
    init_npu();
    load_npu_kernels(xdna_drv_fd, config);
    init_gemm_resources();
    py::dict selected;
    for (const auto &name : {"gate", "up"}) {
        NPUKey key = {512, 4096, 14336, get_layer_id(name), 0};
        auto found = config_map.find(key);
        TORCH_CHECK(found != config_map.end(), "required native config missing: ", name);
        const auto &v = found->second;
        TORCH_CHECK(v.npuM == npu_rows && v.npuK == 4096 && v.npuN == 14336 &&
                        v.split_type == -1 && v.hw_idx >= 0 && v.inst_idx >= 0 &&
                        v.hw_idx < static_cast<int>(hwctxt_array.size()) &&
                        v.inst_idx < static_cast<int>(instctxt_array.size()),
                    "native config does not implement the required M-split: ", name);
        TORCH_CHECK(hwctxt_array[v.hw_idx].pdi_handle != 0 &&
                        instctxt_array[v.inst_idx].dpu_0_handle != 0 &&
                        instctxt_array[v.inst_idx].num_dpu_0_insts > 0,
                    "native artifact context is incomplete: ", name);
        py::dict item;
        item["npu_m"] = v.npuM; item["npu_k"] = v.npuK; item["npu_n"] = v.npuN;
        item["hardware_context"] = v.hw_idx; item["instruction_context"] = v.inst_idx;
        selected[name] = item;
    }
    TORCH_CHECK(config_map.find({512, 14336, 4096, get_layer_id("down"), 0}) == config_map.end(),
                "this recorded baseline requires GPU-only down");
    initialized = true;
    return selected;
}

uint32_t import_tensor(torch::Tensor tensor) {
    TORCH_CHECK(initialized && tensor.is_cuda() && tensor.is_contiguous(),
                "initialize native runtime and supply contiguous GPU tensor");
    TORCH_CHECK(tensor.scalar_type() == torch::kBFloat16 || tensor.scalar_type() == torch::kUInt8,
                "only BF16 activations and uint8 packed weights are imported");
    auto handle = import_dma_buf_to_xdna(tensor.data_ptr(), tensor.numel(), tensor.element_size());
    auto found = ptr_to_handle_map.find(tensor.data_ptr());
    TORCH_CHECK(handle != 0 && handle < std::numeric_limits<int32_t>::max() &&
                    found != ptr_to_handle_map.end() && found->second == handle,
                "DMA-BUF import failed; native fallback is forbidden");
    return handle;
}

// capture=true is only for untimed correctness. It copies projection outputs
// before the native in-place SiLU/multiply overwrites gate.
py::dict run(torch::Tensor input, torch::Tensor gate, torch::Tensor up,
             torch::Tensor output, std::vector<torch::Tensor> weights,
             bool native, bool diagnostic, bool capture) {
    TORCH_CHECK(initialized, "initialize must precede all runs");
    require_tensor(input, 512, 4096); require_tensor(gate, 512, 14336);
    require_tensor(up, 512, 14336); require_tensor(output, 512, 4096);
    TORCH_CHECK(weights.size() == 3, "expected packed gate/up/down weights");
    for (int i = 0; i < 3; ++i) {
        TORCH_CHECK(weights[i].is_cuda() && weights[i].is_contiguous() &&
                        weights[i].scalar_type() == torch::kUInt8 && weights[i].dim() == 1 &&
                        weights[i].numel() == (4096 / 128) * (14336 / 64) * 4352,
                    "packed weight contract mismatch");
        TORCH_CHECK(weights[i].device() == input.device(), "weights must share input device");
    }
    TORCH_CHECK(gate.device() == input.device() && up.device() == input.device() &&
                    output.device() == input.device(), "activations must share input device");
    int current_device = -1;
    TORCH_CHECK(hipGetDevice(&current_device) == hipSuccess && current_device == input.get_device(),
                "set the current HIP device to the input device before invoking the adapter");
    auto stream = c10::hip::getCurrentHIPStream().stream();
    sync(stream); // Input readiness is outside the measured boundary.
    const auto before_count = completed;
    auto start = Clock::now();
    auto stage_start = start;
    std::map<std::string, double> stages;
    auto finish_stage = [&](const char *name) {
        if (!diagnostic) return;
        sync(stream);
        auto now = Clock::now();
        stages[name] = std::chrono::duration<double, std::micro>(now - stage_start).count();
        stage_start = now;
    };
    if (native) {
        // Preserve original ordering: issue both projections, then wait both.
        // The original path retains its event readiness and global NPU mutex.
        auto gate_future = hetero_matmul_out_gemm_packed_M(gate, input, weights[0], 4096, 14336, "gate", 0);
        auto up_future = hetero_matmul_out_gemm_packed_M(up, input, weights[1], 4096, 14336, "up", 0);
        const bool gate_valid = gate_future.valid(), up_valid = up_future.valid();
        // Drain both futures even on failure, before any buffer can be reused.
        const int gate_rc = gate_valid ? gate_future.get() : -999;
        if (gate_valid && gate_rc == 0) ++completed;
        const int up_rc = up_valid ? up_future.get() : -999;
        if (up_valid && up_rc == 0) ++completed;
        TORCH_CHECK(gate_valid && up_valid, "native dispatcher fell back: two NPU futures required");
        TORCH_CHECK(gate_rc == 0 && up_rc == 0, "native NPU completion failed: gate=", gate_rc, " up=", up_rc);
    } else {
        hipkernels::w4a16_gemm_fused_packed(gate, input, weights[0], 4096, 14336, stream);
        hipkernels::w4a16_gemm_fused_packed(up, input, weights[1], 4096, 14336, stream);
    }
    finish_stage("gate_up");
    torch::Tensor captured_gate, captured_up;
    if (capture) { captured_gate = gate.clone(); captured_up = up.clone(); }
    torch::silu_(gate);
    gate.mul_(up);
    finish_stage("silu_multiply");
    hipkernels::w4a16_gemm_fused_packed(output, gate, weights[2], 14336, 4096, stream);
    if (!diagnostic) sync(stream); // Complete FFN including native branch.
    finish_stage("down");
    auto stop = Clock::now();
    py::dict result;
    result["wall_us"] = std::chrono::duration<double, std::micro>(stop - start).count();
    result["completed_npu_dispatches"] = completed - before_count;
    result["expected_npu_dispatches"] = native ? 2 : 0;
    result["stages_host_us"] = stages;
    result["stages_completion_aware"] = diagnostic;
    result["capture_overhead_included"] = capture;
    if (capture) { result["gate"] = captured_gate; result["up"] = captured_up; }
    return result;
}
} // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("initialize", &initialize);
    m.def("import_tensor", &import_tensor);
    m.def("run", &run);
    m.def("completed_npu_dispatches", []() { return completed; });
}
