// Standalone HIP storage exported to XDNA. This module does not depend on XRT
// or exchange Torch's pybind C++ types with the independently compiled bridge.
#include <hip/hip_runtime_api.h>
#include <hsa/hsa_ext_amd.h>
#include <torch/extension.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <limits>
#include <memory>
#include <unistd.h>
#include <vector>

namespace py = pybind11;

namespace {
void check(hipError_t status, const char* operation) {
    TORCH_CHECK(status == hipSuccess, operation, ": ", hipGetErrorString(status));
}

class DeviceScope {
    int previous_ = -1;
public:
    explicit DeviceScope(int device) {
        check(hipGetDevice(&previous_), "hipGetDevice");
        if (previous_ != device) check(hipSetDevice(device), "hipSetDevice");
    }
    ~DeviceScope() { if (previous_ >= 0) (void)hipSetDevice(previous_); }
};

class HipAllocation : public std::enable_shared_from_this<HipAllocation> {
    void* pointer_ = nullptr;
    size_t bytes_ = 0, backing_bytes_ = 0;
    int device_ = 0, fd_ = -1;
    uint64_t offset_ = 0;

    void release() noexcept {
        int previous = -1;
        (void)hipGetDevice(&previous);
        (void)hipSetDevice(device_);
        if (fd_ >= 0) { close(fd_); fd_ = -1; }
        if (pointer_) {
            // Teardown only. The caller must have completed XRT before
            // releasing its BO; HIP cannot wait for an outstanding NPU run.
            (void)hipDeviceSynchronize();
            (void)hipFree(pointer_);
            pointer_ = nullptr;
        }
        if (previous >= 0) (void)hipSetDevice(previous);
    }

public:
    HipAllocation(size_t bytes, int device) : bytes_(bytes), device_(device) {
        TORCH_CHECK(bytes && bytes % 4096 == 0, "output extent must contain whole 4096-byte pages");
        DeviceScope scope(device_);
        try {
            check(hipMalloc(&pointer_, bytes_), "hipMalloc DMA-BUF output");
            TORCH_CHECK(reinterpret_cast<uintptr_t>(pointer_) % 4096 == 0,
                        "HIP allocation is not page aligned");
            const auto status = hsa_amd_portable_export_dmabuf(pointer_, bytes_, &fd_, &offset_);
            TORCH_CHECK(status == HSA_STATUS_SUCCESS && fd_ >= 0,
                        "hsa_amd_portable_export_dmabuf failed: ", static_cast<int>(status));
            // Torch allocator slices and ROCm pool allocations may return a
            // nonzero offset or a larger backing extent. Retain both exactly;
            // the XRT bridge creates a correctly offset logical sub-buffer.
            const auto extent = lseek(fd_, 0, SEEK_END);
            TORCH_CHECK(offset_ % 4096 == 0, "DMA-BUF export offset is not page aligned: offset=",
                        offset_, ", logical_bytes=", bytes_, ", backing_bytes=", extent);
            TORCH_CHECK(extent >= 0 && extent % 4096 == 0 &&
                        offset_ <= static_cast<uint64_t>(extent) &&
                        bytes_ <= static_cast<uint64_t>(extent) - offset_,
                        "DMA-BUF backing extent does not contain the whole-page logical allocation: offset=",
                        offset_, ", logical_bytes=", bytes_, ", backing_bytes=", extent);
            backing_bytes_ = static_cast<size_t>(extent);
            TORCH_CHECK(lseek(fd_, 0, SEEK_SET) == 0, "could not restore DMA-BUF file offset");
        } catch (...) { release(); throw; }
    }

    ~HipAllocation() noexcept { release(); }

    int fd() const {
        TORCH_CHECK(fd_ >= 0, "DMA-BUF export FD was already closed");
        return fd_;
    }

    void close_export() {
        TORCH_CHECK(fd_ >= 0, "DMA-BUF export FD was already closed");
        const int fd = fd_;
        fd_ = -1;
        TORCH_CHECK(close(fd) == 0, "close DMA-BUF export FD failed");
    }

    torch::Tensor tensor(const std::vector<int64_t>& shape) {
        size_t bytes = sizeof(at::BFloat16);
        TORCH_CHECK(!shape.empty(), "output shape must not be empty");
        for (auto dim : shape) {
            TORCH_CHECK(dim > 0 && static_cast<uint64_t>(dim) <=
                        std::numeric_limits<size_t>::max() / bytes, "invalid output shape");
            bytes *= static_cast<size_t>(dim);
        }
        TORCH_CHECK(bytes == bytes_, "BF16 tensor must cover the whole allocation");
        auto owner = shared_from_this();
        return torch::from_blob(pointer_, shape, [owner](void*) {},
            torch::TensorOptions().dtype(torch::kBFloat16).device(torch::Device(torch::kCUDA, device_)));
    }

    py::dict metadata() const {
        py::dict result;
        result["device_index"] = device_;
        result["gpu_pointer"] = reinterpret_cast<uintptr_t>(pointer_);
        result["nbytes"] = bytes_;
        result["backing_nbytes"] = backing_bytes_;
        result["export_offset"] = offset_;
        result["export_fd_closed"] = fd_ < 0;
        result["allocation"] = "hipMalloc standalone allocation";
        result["export"] = "hsa_amd_portable_export_dmabuf";
        return result;
    }
};
} // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, module) {
    py::class_<HipAllocation, std::shared_ptr<HipAllocation>>(module, "HipAllocation")
        .def(py::init<size_t, int>())
        .def("fd", &HipAllocation::fd)
        .def("close_export", &HipAllocation::close_export)
        .def("tensor", &HipAllocation::tensor)
        .def("metadata", &HipAllocation::metadata);
}
