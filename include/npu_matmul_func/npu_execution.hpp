#pragma once
#include <mutex>

namespace heteromega {
// One execution lock for the native direct-XDNA path and the opt-in XRT FFN.
// This coordinates submissions in this application, not other cloud users/processes.
std::mutex &npu_execution_mutex();
}
