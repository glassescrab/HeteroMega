// Test seam for the SAME C++ executor called by UnifiedLLMW4A16Impl.
#include "heteromega/merged_ffn.hpp"
#include <c10/hip/HIPGuard.h>
#include <c10/hip/HIPStream.h>
#include <torch/extension.h>
#include <pybind11/stl.h>

PYBIND11_MODULE(heteromega_ffn_deploy, m) {
    pybind11::class_<heteromega::MergedFfn>(m, "MergedFfn")
        .def(pybind11::init<const std::string &>())
        .def("add_layer", &heteromega::MergedFfn::add_layer)
        .def("supports", &heteromega::MergedFfn::supports)
        .def("completed_dispatches", &heteromega::MergedFfn::completed_dispatches)
        .def("forward_out", [](heteromega::MergedFfn &self, int64_t layer, const torch::Tensor &x,
                                torch::Tensor output, bool serial) {
            c10::hip::HIPStreamGuard guard(c10::hip::getCurrentHIPStream(x.get_device()));
            auto result = self.forward(layer, x, output, c10::hip::getCurrentHIPStream().stream(), serial);
            return std::vector<torch::Tensor>{result.output, result.gpu_partial, result.npu_partial};
        }, pybind11::arg("layer"), pybind11::arg("normalized"), pybind11::arg("output"),
           pybind11::arg("serial") = false, pybind11::call_guard<pybind11::gil_scoped_release>())
        .def("forward", [](heteromega::MergedFfn &self, int64_t layer, const torch::Tensor &x, bool serial) {
            c10::hip::HIPStreamGuard guard(c10::hip::getCurrentHIPStream(x.get_device()));
            auto result = self.forward(layer, x, torch::empty_like(x), c10::hip::getCurrentHIPStream().stream(), serial);
            return std::vector<torch::Tensor>{result.output, result.gpu_partial, result.npu_partial};
        }, pybind11::arg("layer"), pybind11::arg("normalized"), pybind11::arg("serial") = false,
           pybind11::call_guard<pybind11::gil_scoped_release>());
}
