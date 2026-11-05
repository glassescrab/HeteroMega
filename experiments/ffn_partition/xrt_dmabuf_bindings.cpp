// An XRT-only extension: do not compile this through Torch's pybind/ABI flags.
// pyxrt owns the registered xrt::bo and xrt::device Python classes.
#include <pybind11/pybind11.h>
#include <xrt/xrt_bo.h>
#include <xrt/xrt_device.h>

#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>
#include <unistd.h>

namespace py = pybind11;

namespace {
py::dict registry() {
    auto binding = py::module_::import("pyxrt");
    const auto* bo = py::detail::get_type_info(typeid(xrt::bo), false);
    const auto* device = py::detail::get_type_info(typeid(xrt::device), false);
    const bool shared = bo && device &&
        reinterpret_cast<PyObject*>(bo->type) == binding.attr("bo").ptr() &&
        reinterpret_cast<PyObject*>(device->type) == binding.attr("device").ptr();
    py::dict result;
    result["pybind_internals_id"] = PYBIND11_INTERNALS_ID;
    result["registered_types_shared"] = shared;
    result["gxx_abi_version"] = __GXX_ABI_VERSION;
    result["glibcxx_cxx11_abi"] = _GLIBCXX_USE_CXX11_ABI;
    return result;
}

void require_registry() {
    if (!registry()["registered_types_shared"].cast<bool>())
        throw std::runtime_error("pyxrt and bridge do not share their registered C++ types; refusing import");
}

py::dict describe(const xrt::bo& bo) {
    py::dict result;
    result["nbytes"] = bo.size();
    result["address"] = bo.address();
    result["group_id"] = bo.get_memory_group();
    result["bank_id"] = bo.get_memory_group() & 0xffffu;
    result["flags"] = static_cast<uint32_t>(bo.get_flags());
    result["flags_name"] = bo.get_flags() == xrt::bo::flags::normal ? "normal" :
        bo.get_flags() == xrt::bo::flags::host_only ? "host_only" : "unsupported";
    return result;
}

xrt::bo import_fd(const xrt::device& device, int fd, size_t nbytes,
                  uint32_t expected_group, py::object /* HIP allocation owner */) {
    require_registry();
    if (fd < 0 || !nbytes || nbytes % 4096)
        throw std::invalid_argument("DMA-BUF import requires a valid FD and a whole-page extent");
    const auto extent = lseek(fd, 0, SEEK_END);
    if (extent < 0 || static_cast<uint64_t>(extent) != nbytes)
        throw std::invalid_argument("DMA-BUF backing extent mismatch: expected=" + std::to_string(nbytes) +
                                    ", observed=" + std::to_string(extent));
    if (lseek(fd, 0, SEEK_SET) != 0)
        throw std::runtime_error("could not restore DMA-BUF file offset");
    // PRIME_FD_TO_HANDLE imports the backing allocation. The exporting owner
    // is retained by py::keep_alive, independently of the caller closing fd.
    xrt::bo result(device, static_cast<xrt::bo::export_handle>(fd));
    if (result.size() != nbytes || !result.address() ||
        result.address() == std::numeric_limits<uint64_t>::max() || result.address() % 4096)
        throw std::runtime_error("imported XRT BO has an invalid extent/address/alignment");
    if ((result.get_memory_group() & 0xffffu) != (expected_group & 0xffffu))
        throw std::runtime_error("imported BO bank differs from the kernel argument bank");
    const auto flags = result.get_flags();
    if (flags != xrt::bo::flags::normal && flags != xrt::bo::flags::host_only)
        throw std::runtime_error("unsupported imported BO flags; refusing an implicit conversion");
    return result;
}

xrt::bo sub_buffer(const xrt::bo& parent, size_t nbytes, size_t offset,
                   py::object /* same HIP allocation owner */) {
    require_registry();
    if (!nbytes || nbytes % 4096 || offset % 4096 || offset > parent.size() ||
        nbytes > parent.size() - offset)
        throw std::invalid_argument("DMA-BUF sub-buffer requires a page-aligned bounded extent");
    // The public sub-buffer API retains the parent C++ allocation. Separately
    // retain its HIP owner on the returned Python BO, since the parent's
    // Python wrapper (which also has keep_alive) may be released first.
    xrt::bo result(parent, nbytes, offset);
    if (result.size() != nbytes ||
        result.address() != parent.address() + offset ||
        result.get_memory_group() != parent.get_memory_group() || result.get_flags() != parent.get_flags())
        throw std::runtime_error("DMA-BUF sub-buffer address/extent/group/flags changed unexpectedly");
    return result;
}
} // namespace

PYBIND11_MODULE(HETEROMEGA_XRT_MODULE, module) {
    // Deliberately never register xrt::bo/device a second time.
    module.def("registry", &registry);
    module.def("describe", &describe);
    module.def("import_fd", &import_fd, py::arg("device"), py::arg("fd"),
               py::arg("nbytes"), py::arg("expected_group"), py::arg("owner"),
               py::keep_alive<0, 5>());
    module.def("sub_buffer", &sub_buffer, py::arg("parent"), py::arg("nbytes"),
               py::arg("offset"), py::arg("owner"), py::keep_alive<0, 4>());
}
