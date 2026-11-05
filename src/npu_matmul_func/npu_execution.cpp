#include "npu_matmul_func/npu_execution.hpp"
namespace heteromega {
std::mutex &npu_execution_mutex() {
    static std::mutex mutex;
    return mutex;
}
}
