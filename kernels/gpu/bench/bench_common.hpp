// Small helpers shared by the benchmarks.
#pragma once

#include <hip/hip_runtime.h>

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace bench {

inline void hip_check(hipError_t err, const char *what) {
    if (err != hipSuccess) {
        throw std::runtime_error(std::string(what) + ": " + hipGetErrorString(err));
    }
}

// "1,128,512" -> {1, 128, 512}
inline std::vector<int64_t> parse_list(const std::string &s) {
    std::vector<int64_t> out;
    std::stringstream ss(s);
    std::string item;
    while (std::getline(ss, item, ',')) {
        if (!item.empty()) {
            out.push_back(std::stoll(item));
        }
    }
    return out;
}

// Value of "--name v" or the default.
inline std::string arg(int argc, char **argv, const char *name, const std::string &def) {
    for (int i = 1; i + 1 < argc; ++i) {
        if (std::strcmp(argv[i], name) == 0) {
            return argv[i + 1];
        }
    }
    return def;
}

inline bool flag(int argc, char **argv, const char *name) {
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], name) == 0) {
            return true;
        }
    }
    return false;
}

inline double median(std::vector<double> v) {
    if (v.empty()) {
        return 0.0;
    }
    std::sort(v.begin(), v.end());
    const size_t n = v.size();
    return n % 2 ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]);
}

// Records events on a stream and returns the elapsed milliseconds between two marks.
// Record all marks first and call ms() after the loop. A sync inside the loop leaves the GPU idle
// at the next mark, so the host launch time gets counted as kernel time.
class EventTimer {
  public:
    EventTimer(hipStream_t stream, int marks) : stream_(stream), events_(marks) {
        for (auto &e : events_) {
            hip_check(hipEventCreate(&e), "hipEventCreate");
        }
    }
    ~EventTimer() {
        for (auto &e : events_) {
            (void)hipEventDestroy(e);
        }
    }
    void mark(int i) { hip_check(hipEventRecord(events_[i], stream_), "hipEventRecord"); }
    float ms(int from, int to) {
        hip_check(hipEventSynchronize(events_[to]), "hipEventSynchronize");
        float t = 0.0f;
        hip_check(hipEventElapsedTime(&t, events_[from], events_[to]), "hipEventElapsedTime");
        return t;
    }

  private:
    hipStream_t stream_;
    std::vector<hipEvent_t> events_;
};

} // namespace bench
