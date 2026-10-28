"""CPU checks for the candidate adapter contract; HIP math needs hardware."""
from contextlib import nullcontext
from types import SimpleNamespace
import unittest

import numpy as np

from .teammate_gpu import TeammateGPUBranch, _validate_packed, source_hashes


class PackedContractTests(unittest.TestCase):
    def test_uneven_eight_column_suffix_accepted_without_mutation(self):
        # The teammate CLI skips this suffix, but its API supports 128 alignment.
        h, i, p = 128, 14336, 2816
        source = np.arange((h // 128) * (i // 64) * 4352, dtype=np.uint8)
        source.flags.writeable = False
        arrays, *shape = _validate_packed((source,) * 3, h, i, p, i)
        self.assertEqual(shape, [h, i, p, i])
        self.assertEqual(i - p, 11520)
        self.assertTrue(all(a is source for a in arrays))
        self.assertFalse(source.flags.writeable)

    def test_invalid_partition_and_storage_rejected(self):
        source = np.zeros(2 * 4352, dtype=np.uint8)
        for begin, end in ((True, 128), (1, 128), (128, 128), (0, 256)):
            with self.subTest(begin=begin, end=end), self.assertRaises(ValueError):
                _validate_packed((source,) * 3, 128, 128, begin, end)
        for invalid in (source[:-1], source.astype(np.int8), source.reshape(2, -1), source[::2]):
            with self.subTest(shape=invalid.shape), self.assertRaises(ValueError):
                _validate_packed((invalid, source, source), 128, 128, 0, 128)

    def test_source_manifest_covers_implementation_headers_and_wrapper(self):
        hashes = source_hashes()
        for path in ("kernels/gpu/src/gpu_ffn.cpp", "kernels/gpu/src/pack_w4a16.cpp",
                     "kernels/gpu/src/silu_mul.cu", "kernels/gpu/src/bf16_device.hpp",
                     "kernels/gpu/include/heteromega/gpu_ffn.hpp",
                     "src/hipkernels/w4a16_gemm_packed.cu",
                     "experiments/ffn_partition/teammate_gpu_bindings.cpp"):
            self.assertEqual(len(hashes[path]), 64)


class AsyncContractTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.stream_a = self.make_stream(11)
        self.stream_b = self.make_stream(22)
        self.branch = TeammateGPUBranch.__new__(TeammateGPUBranch)
        b = self.branch
        b.m, b.hidden, b.channels, b.device = 128, 256, 11520, "cuda:0"
        b.output, b.weights = object(), [object(), object()]
        b.gate_up_output, b.activation, b.x_pad = object(), object(), object()
        b._has_run, b._last_stream = False, self.stream_a
        b._done = SimpleNamespace(record=lambda stream: self.events.append(("record", stream.cuda_stream)))
        b._module = SimpleNamespace(forward=lambda *args: self.events.append(("forward", args)))
        b._torch = SimpleNamespace(bfloat16="bf16", cuda=SimpleNamespace(
            device=lambda device: nullcontext(), stream=lambda stream: nullcontext(),
            current_stream=lambda device: self.stream_a))
        self.x = SimpleNamespace(device="cuda:0", dtype="bf16", shape=(128, 256), is_contiguous=lambda: True)

    def make_stream(self, handle):
        return SimpleNamespace(device="cuda:0", cuda_stream=handle,
            wait_event=lambda event: self.events.append(("wait", handle)),
            synchronize=lambda: self.events.append(("sync", handle)))

    def test_three_kernel_call_reuses_buffers_and_has_no_host_wait(self):
        output = self.branch.enqueue(self.x, self.stream_a)
        self.assertIs(output, self.branch.output)
        self.assertEqual([e[0] for e in self.events], ["forward", "record"])
        args = self.events[0][1]
        self.assertEqual(args[-3:], (256, 11520, 11))
        self.assertIs(args[0], output)
        self.assertIs(args[1], self.x)

    def test_cross_stream_reuse_waits_on_previous_event(self):
        self.branch.enqueue(self.x, self.stream_a)
        self.events.clear()
        self.branch.enqueue(self.x, self.stream_b)
        self.assertEqual([e[0] for e in self.events], ["wait", "forward", "record"])
        self.branch.synchronize()
        self.assertEqual(self.events[-1], ("sync", 22))

    def test_bad_input_and_wrong_stream_fail_before_dispatch(self):
        self.x.is_contiguous = lambda: False
        with self.assertRaises(ValueError):
            self.branch.enqueue(self.x)
        self.x.is_contiguous = lambda: True
        self.stream_b.device = "cuda:1"
        with self.assertRaises(ValueError):
            self.branch.enqueue(self.x, self.stream_b)
        self.assertEqual(self.events, [])


if __name__ == "__main__":
    unittest.main()
