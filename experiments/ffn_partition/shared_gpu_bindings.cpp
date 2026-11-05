// Experimental GPU access to an existing XRT CPU mapping. No NPU runtime,
// weight format, kernel, or model-baseline code is changed by this helper.
#include <hip/hip_runtime_api.h>
#include <torch/extension.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <limits>
#include <memory>
#include <string>
#include <vector>

namespace py = pybind11;

namespace {
void hip_check(hipError_t result, const char *operation) {
    TORCH_CHECK(result == hipSuccess, operation, ": ", hipGetErrorString(result));
}

class DeviceScope {
    int original_ = -1;
public:
    explicit DeviceScope(int device) {
        hip_check(hipGetDevice(&original_), "hipGetDevice");
        if (device != original_) hip_check(hipSetDevice(device), "hipSetDevice");
    }
    ~DeviceScope() {
        if (original_ >= 0) (void)hipSetDevice(original_);
    }
};

class RegisteredHost : public std::enable_shared_from_this<RegisteredHost> {
    void *host_ = nullptr;
    void *mapped_ = nullptr;
    size_t bytes_ = 0;
    int device_ = 0;
    PyObject *owner_ = nullptr;

public:
    RegisteredHost(py::buffer buffer, py::object owner, int device) : device_(device) {
        const auto info = buffer.request();
        TORCH_CHECK(!info.readonly && info.ptr && info.size > 0 && info.itemsize > 0,
                    "mapping must expose a nonempty writable buffer");
        size_t stride = static_cast<size_t>(info.itemsize);
        for (int axis = static_cast<int>(info.ndim) - 1; axis >= 0; --axis) {
            TORCH_CHECK(info.shape[axis] > 0 &&
                        (info.shape[axis] == 1 || info.strides[axis] == static_cast<py::ssize_t>(stride)),
                        "mapping must be contiguous");
            TORCH_CHECK(static_cast<size_t>(info.shape[axis]) <= std::numeric_limits<size_t>::max() / stride,
                        "mapping size overflow");
            stride *= static_cast<size_t>(info.shape[axis]);
        }
        host_ = info.ptr;
        bytes_ = stride;
        TORCH_CHECK(reinterpret_cast<uintptr_t>(host_) % 64 == 0,
                    "register the whole cache-line-aligned XRT mapping, not an unaligned slice");
        auto keepalive = py::make_tuple(owner, buffer);
        DeviceScope scope(device_);
        hip_check(hipHostRegister(host_, bytes_, hipHostRegisterMapped), "hipHostRegister(XRT mapping)");
        const auto result = hipHostGetDevicePointer(&mapped_, host_, 0);
        if (result != hipSuccess) {
            (void)hipHostUnregister(host_);
            hip_check(result, "hipHostGetDevicePointer(XRT mapping)");
        }
        // A Tensor may outlive the Python facade. Keep the BO and its mapping
        // alive until the final Tensor/storage alias releases this registration.
        owner_ = keepalive.ptr();
        Py_INCREF(owner_);
    }

    ~RegisteredHost() noexcept {
        // Cleanup is outside benchmark timing. The caller must also complete
        // all NPU runs before dropping a shared BO; HIP cannot wait on XRT.
        int original = -1;
        (void)hipGetDevice(&original);
        (void)hipSetDevice(device_);
        (void)hipDeviceSynchronize();
        (void)hipHostUnregister(host_);
        if (original >= 0) (void)hipSetDevice(original);
        if (owner_ && Py_IsInitialized()) {
            auto state = PyGILState_Ensure();
            Py_DECREF(owner_);
            PyGILState_Release(state);
        }
    }

    torch::Tensor tensor(const std::vector<int64_t> &shape, const std::string &dtype,
                         size_t byte_offset) {
        TORCH_CHECK(!shape.empty(), "tensor shape must not be empty");
        torch::ScalarType scalar = torch::kUInt8;
        size_t width = 1;
        if (dtype == "bf16") { scalar = torch::kBFloat16; width = 2; }
        else if (dtype == "uint8") { scalar = torch::kUInt8; width = 1; }
        else if (dtype == "fp32") { scalar = torch::kFloat32; width = 4; }
        else { TORCH_CHECK(false, "dtype must be bf16, uint8, or fp32"); }
        size_t size = width;
        for (const auto dimension : shape) {
            TORCH_CHECK(dimension > 0 && static_cast<uint64_t>(dimension) <=
                        std::numeric_limits<size_t>::max() / size, "invalid tensor shape");
            size *= static_cast<size_t>(dimension);
        }
        TORCH_CHECK(byte_offset % width == 0 && byte_offset <= bytes_ && size <= bytes_ - byte_offset,
                    "tensor view exceeds registered mapping or has an unaligned offset");
        auto registration = shared_from_this();
        auto pointer = static_cast<uint8_t *>(mapped_) + byte_offset;
        return torch::from_blob(pointer, shape,
            [registration](void *) {},
            torch::TensorOptions().dtype(scalar).device(torch::Device(torch::kCUDA, device_)));
    }

    py::dict metadata() const {
        py::dict result;
        result["host_pointer"] = reinterpret_cast<uintptr_t>(host_);
        result["device_pointer"] = reinterpret_cast<uintptr_t>(mapped_);
        result["registered_bytes"] = bytes_;
        result["device_index"] = device_;
        result["registration"] = "hipHostRegisterMapped";
        result["ownership"] = "registration retains BO/mapping; Tensor storage retains registration";
        return result;
    }
};
} // namespace

PYBIND11_MODULE(TORCH_EXTENSION_NAME, module) {
    py::class_<RegisteredHost, std::shared_ptr<RegisteredHost>>(module, "RegisteredHost")
        .def(py::init<py::buffer, py::object, int>(), py::arg("buffer"), py::arg("owner"), py::arg("device"))
        .def("tensor", &RegisteredHost::tensor, py::arg("shape"), py::arg("dtype") = "bf16", py::arg("byte_offset") = 0)
        .def("metadata", &RegisteredHost::metadata);
}
