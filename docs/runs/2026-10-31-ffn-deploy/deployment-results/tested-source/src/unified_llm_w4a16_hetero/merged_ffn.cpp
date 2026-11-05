#include "heteromega/merged_ffn.hpp"
#include "heteromega/gpu_ffn.hpp"
#include "npu_matmul_func/npu_execution.hpp"
#include <c10/hip/HIPGuard.h>
#include <c10/hip/HIPStream.h>
#include <xrt/xrt_bo.h>
#include <xrt/xrt_device.h>
#include <xrt/xrt_kernel.h>
#include <xrt/xrt_hw_context.h>
#include <openssl/evp.h>
#include <array>
#include <atomic>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>
#include <unordered_map>
#include <vector>

namespace heteromega {
namespace {
void hip_check(hipError_t err) {
    TORCH_CHECK(err == hipSuccess, "merged FFN HIP error: ", hipGetErrorString(err));
}

std::string sha256_file(const std::filesystem::path &path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) throw std::runtime_error("merged FFN: cannot read " + path.string());
    std::unique_ptr<EVP_MD_CTX, decltype(&EVP_MD_CTX_free)> ctx(EVP_MD_CTX_new(), EVP_MD_CTX_free);
    if (!ctx || EVP_DigestInit_ex(ctx.get(), EVP_sha256(), nullptr) != 1)
        throw std::runtime_error("merged FFN: cannot initialize SHA256");
    std::array<char, 65536> block;
    while (file) {
        file.read(block.data(), block.size());
        if (EVP_DigestUpdate(ctx.get(), block.data(), static_cast<size_t>(file.gcount())) != 1)
            throw std::runtime_error("merged FFN: SHA256 update failed");
    }
    if (!file.eof()) throw std::runtime_error("merged FFN: artifact read failed");
    std::array<unsigned char, EVP_MAX_MD_SIZE> digest;
    unsigned length = 0;
    if (EVP_DigestFinal_ex(ctx.get(), digest.data(), &length) != 1 || length != 32)
        throw std::runtime_error("merged FFN: SHA256 failed");
    std::ostringstream result;
    for (unsigned i = 0; i < length; ++i)
        result << std::hex << std::setfill('0') << std::setw(2) << unsigned(digest[i]);
    return result.str();
}

std::string checked_xclbin(const MergedFfnConfig &c) {
    const auto xclbin = c.artifact_dir / "final.xclbin", insts = c.artifact_dir / "insts.bin";
    TORCH_CHECK(sha256_file(xclbin) == c.xclbin_sha256, "merged FFN: XCLBIN hash mismatch");
    TORCH_CHECK(sha256_file(insts) == c.insts_sha256, "merged FFN: instruction hash mismatch");
    return xclbin.string();
}

xrt::uuid register_binary(xrt::device &device, const xrt::xclbin &binary) {
    device.register_xclbin(binary);
    return binary.get_uuid();
}

struct Event {
    hipEvent_t value = nullptr;
    Event() { hip_check(hipEventCreateWithFlags(&value, hipEventDisableTiming)); }
    ~Event() { if (value) (void)hipEventDestroy(value); }
    Event(const Event &) = delete;
    Event &operator=(const Event &) = delete;
};
struct Stream {
    hipStream_t value = nullptr;
    Stream() { hip_check(hipStreamCreateWithFlags(&value, hipStreamNonBlocking)); }
    ~Stream() {
        if (value) {
            (void)hipStreamSynchronize(value);
            (void)hipStreamDestroy(value);
        }
    }
    Stream(const Stream &) = delete;
    Stream &operator=(const Stream &) = delete;
};

void require_finite_bf16(const torch::Tensor &host, const char *name) {
    const auto *bits = static_cast<const uint16_t *>(host.data_ptr());
    for (int64_t i = 0; i < host.numel(); ++i)
        TORCH_CHECK((bits[i] & 0x7f80) != 0x7f80, "merged FFN: nonfinite ", name, " at element ", i);
}

// One shared NPU workspace. Every access is protected by npu_execution_mutex(),
// from input write through output readback, including failure/abort handling.
struct Runtime {
    xrt::device device;
    xrt::xclbin binary;
    xrt::hw_context context;
    xrt::kernel kernel;
    xrt::bo instructions, x, z, y;
    uint32_t instruction_bytes = 0;
    bool poisoned = false;

    explicit Runtime(const MergedFfnConfig &c)
        : device(c.device_index), binary(checked_xclbin(c)),
          context(device, register_binary(device, binary)), kernel(context, "MLIR_AIE") {
        const auto path = c.artifact_dir / "insts.bin";
        const auto length = std::filesystem::file_size(path);
        TORCH_CHECK(length > 0 && length % 4 == 0 && length <= UINT32_MAX,
                    "merged FFN: instructions must contain whole uint32 words and fit a uint32 byte length");
        instruction_bytes = static_cast<uint32_t>(length);
        std::vector<char> bytes(length);
        std::ifstream file(path, std::ios::binary);
        TORCH_CHECK(bool(file.read(bytes.data(), bytes.size())), "merged FFN: truncated instructions");
        instructions = xrt::bo(device, length, xrt::bo::flags::cacheable, kernel.group_id(1));
        instructions.write(bytes.data(), bytes.size(), 0);
        instructions.sync(XCL_BO_SYNC_BO_TO_DEVICE);
        x = xrt::bo(device, c.activation_bytes(), xrt::bo::flags::host_only, kernel.group_id(3));
        z = xrt::bo(device, c.intermediate_bytes(), xrt::bo::flags::host_only, kernel.group_id(7));
        y = xrt::bo(device, c.activation_bytes(), xrt::bo::flags::host_only, kernel.group_id(8));
    }
};

struct Layer {
    std::array<torch::Tensor, 3> originals;
    FfnSliceWeights gpu;
    std::array<xrt::bo, 3> npu;
    bool ready = false;
};

struct Slot {
    std::mutex mutex;
    int device_index;
    Stream transfer;
    Event input_ready, output_ready, done;
    bool pending = false;
    GpuFfnBuffers gpu;
    torch::Tensor host_x, host_y, y_gpu, y_npu;
    Slot(const MergedFfnConfig &c, const torch::Device &device)
        : device_index(device.index()),
          gpu(GpuFfnBuffers::allocate(c.m, c.intermediate - c.npu_channels, c.hidden, device)) {
        const auto host = torch::TensorOptions().device(torch::kCPU).dtype(torch::kBFloat16).pinned_memory(true);
        host_x = torch::empty({c.m, c.hidden}, host);
        host_y = torch::empty({c.m, c.hidden}, host);
        y_gpu = torch::empty({c.m, c.hidden}, host.pinned_memory(false).device(device));
        y_npu = torch::empty_like(y_gpu);
    }
    ~Slot() {
        // In particular, pinned host_y must outlive an asynchronous H2D copy.
        int previous = -1;
        (void)hipGetDevice(&previous);
        (void)hipSetDevice(device_index);
        if (pending) (void)hipEventSynchronize(done.value);
        (void)hipStreamSynchronize(transfer.value);
        if (previous >= 0) (void)hipSetDevice(previous);
    }
};
} // namespace

struct MergedFfn::Impl {
    MergedFfnConfig config;
    std::mutex setup_mutex;
    std::unique_ptr<Runtime> runtime;
    std::vector<std::shared_ptr<Layer>> layers;
    std::unordered_map<hipStream_t, std::shared_ptr<Slot>> slots;
    std::atomic<uint64_t> completed{0};
    int gpu_device = -1;

    explicit Impl(const std::string &path) : config(MergedFfnConfig::load(path)) {}
    ~Impl() {
        slots.clear(); // Complete GPU reads/copies before releasing weights or pinned buffers.
        std::lock_guard<std::mutex> npu_lock(npu_execution_mutex());
        layers.clear();
        runtime.reset();
    }

    std::pair<std::shared_ptr<Layer>, std::shared_ptr<Slot>> prepare(int64_t index, const torch::Tensor &x,
                                                                  hipStream_t stream) {
        std::lock_guard<std::mutex> lock(setup_mutex);
        TORCH_CHECK(index >= 0 && static_cast<size_t>(index) < layers.size(), "merged FFN: missing layer ", index);
        TORCH_CHECK(gpu_device == -1 || gpu_device == x.get_device(), "merged FFN: device changed; rebuild executor");
        gpu_device = x.get_device();
        auto layer = layers[index];
        if (!layer->ready) {
            for (const auto &w : layer->originals)
                TORCH_CHECK(w.device() == x.device(), "merged FFN: weight/input devices differ");
            layer->gpu = slice_packed_ffn(layer->originals[0], layer->originals[1], layer->originals[2],
                config.hidden, config.intermediate, config.npu_channels, config.intermediate, GateUpLayout::kInterleaved);
            // Setup only: make packing visible to every future chunk stream.
            hip_check(hipStreamSynchronize(stream));
            std::lock_guard<std::mutex> npu_lock(npu_execution_mutex());
            if (!runtime) runtime = std::make_unique<Runtime>(config);
            TORCH_CHECK(!runtime->poisoned, "merged FFN: executor is poisoned after a launch failure");
            for (size_t i = 0; i < 3; ++i) {
                auto host = layer->originals[i].to(torch::kCPU).contiguous();
                layer->npu[i] = xrt::bo(runtime->device, config.weight_bytes(), xrt::bo::flags::host_only,
                                       runtime->kernel.group_id(static_cast<int>(i) + 4));
                layer->npu[i].write(host.data_ptr(), config.weight_bytes(), 0);
                layer->npu[i].sync(XCL_BO_SYNC_BO_TO_DEVICE);
            }
            layer->ready = true;
        }
        auto &slot = slots[stream];
        if (!slot) slot = std::make_shared<Slot>(config, x.device());
        return {layer, slot};
    }
};

MergedFfn::MergedFfn(const std::string &path) : impl_(std::make_unique<Impl>(path)) {
    const auto &c = impl_->config;
    std::cout << "HeteroMega merged FFN configured: M=" << c.m << " H=" << c.hidden << " I=" << c.intermediate
              << " NPU=[0," << c.npu_channels << ") GPU=[" << c.npu_channels << "," << c.intermediate
              << ") accuracy_policy=report; host staging, numerical equivalence unvalidated" << std::endl;
}
MergedFfn::~MergedFfn() = default;
const MergedFfnConfig &MergedFfn::config() const { return impl_->config; }
bool MergedFfn::supports(int64_t m, int64_t h, int64_t inter) const { return config().supports(m, h, inter); }
uint64_t MergedFfn::completed_dispatches() const { return impl_->completed.load(); }

void MergedFfn::add_layer(const torch::Tensor &gate, const torch::Tensor &up, const torch::Tensor &down) {
    std::lock_guard<std::mutex> lock(impl_->setup_mutex);
    TORCH_CHECK(impl_->slots.empty(), "merged FFN: add layers before execution");
    auto layer = std::make_shared<Layer>();
    layer->originals = {gate, up, down};
    for (const auto &w : layer->originals)
        TORCH_CHECK(w.defined() && w.is_cuda() && w.scalar_type() == torch::kUInt8 && w.is_contiguous() &&
                    w.numel() == static_cast<int64_t>(config().weight_bytes()),
                    "merged FFN: requires original full packed uint8 weights, padPackedWeights=0, group128");
    impl_->layers.push_back(std::move(layer));
}

MergedFfnResult MergedFfn::forward(int64_t index, const torch::Tensor &x, torch::Tensor output,
                                  hipStream_t current_stream, bool serial) {
    const auto &c = config();
    TORCH_CHECK(x.is_cuda() && x.dim() == 2 && x.size(0) == c.m && x.size(1) == c.hidden &&
                x.scalar_type() == torch::kBFloat16 && x.is_contiguous(), "merged FFN: expected contiguous GPU BF16 [M,H]");
    TORCH_CHECK(output.device() == x.device() && output.sizes() == x.sizes() && output.is_contiguous() &&
                output.scalar_type() == torch::kBFloat16, "merged FFN: invalid output");
    c10::hip::HIPStreamGuard device_guard(c10::hip::getCurrentHIPStream(x.get_device()));
    TORCH_CHECK(current_stream == c10::hip::getCurrentHIPStream().stream(),
                "merged FFN: caller stream must be Torch's current HIP stream");
    const auto prepared = impl_->prepare(index, x, current_stream);
    auto &layer = *prepared.first;
    auto &slot = *prepared.second;
    std::lock_guard<std::mutex> slot_lock(slot.mutex);
    if (slot.pending) hip_check(hipEventSynchronize(slot.done.value));
    hip_check(hipStreamSynchronize(slot.transfer.value));
    // Capture input readiness BEFORE queuing GPU FFN; the D2H branch need not wait for that FFN.
    hip_check(hipEventRecord(slot.input_ready.value, current_stream));
    try {
        gpu_ffn_slice_forward(layer.gpu, x, slot.gpu, slot.y_gpu, current_stream);
        hip_check(hipGetLastError());
    } catch (...) {
        // A later kernel's validation may fail after an earlier kernel was enqueued.
        (void)hipStreamSynchronize(current_stream);
        throw;
    }
    hip_check(hipEventRecord(slot.done.value, current_stream));
    slot.pending = true; // Also protects scratch if a subsequent host/XRT operation throws.
    if (serial) hip_check(hipEventSynchronize(slot.done.value));
    hip_check(hipStreamWaitEvent(slot.transfer.value, slot.input_ready.value, 0));
    hip_check(hipMemcpyAsync(slot.host_x.data_ptr(), x.data_ptr(), c.activation_bytes(), hipMemcpyDeviceToHost,
                             slot.transfer.value));
    hip_check(hipStreamSynchronize(slot.transfer.value));
    require_finite_bf16(slot.host_x, "input");
    {
        std::lock_guard<std::mutex> npu_lock(npu_execution_mutex());
        auto &r = *impl_->runtime;
        TORCH_CHECK(!r.poisoned, "merged FFN: executor is poisoned after a launch failure");
        xrt::run run;
        bool started = false;
        try {
            r.x.write(slot.host_x.data_ptr(), c.activation_bytes(), 0);
            r.x.sync(XCL_BO_SYNC_BO_TO_DEVICE);
            // Instruction length is BYTES, following the pinned Python XRTHostRuntime.
            run = r.kernel(3, r.instructions, r.instruction_bytes,
                           r.x, layer.npu[0], layer.npu[1], layer.npu[2], r.z, r.y);
            started = true;
            const auto state = run.wait(c.timeout_ms);
            TORCH_CHECK(state == ERT_CMD_STATE_COMPLETED, "merged FFN: NPU failed/timed out; state=", int(state));
            started = false;
            ++impl_->completed;
            r.y.sync(XCL_BO_SYNC_BO_FROM_DEVICE);
            r.y.read(slot.host_y.data_ptr(), c.activation_bytes(), 0);
        } catch (...) {
            r.poisoned = true;
            if (started) (void)run.abort(); // Abort synchronously before permitting another NPU submission.
            throw;
        }
    }
    require_finite_bf16(slot.host_y, "NPU output");
    hip_check(hipMemcpyAsync(slot.y_npu.data_ptr(), slot.host_y.data_ptr(), c.activation_bytes(), hipMemcpyHostToDevice,
                             slot.transfer.value));
    hip_check(hipEventRecord(slot.output_ready.value, slot.transfer.value));
    hip_check(hipStreamWaitEvent(current_stream, slot.output_ready.value, 0));
    // Both partials are on the caller stream now. No residual is included here.
    torch::add_out(output, slot.y_gpu, slot.y_npu);
    hip_check(hipEventRecord(slot.done.value, current_stream));
    return {output, slot.y_gpu, slot.y_npu};
}
} // namespace heteromega
