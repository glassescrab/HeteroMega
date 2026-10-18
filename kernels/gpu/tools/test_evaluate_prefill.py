"""CPU checks; synthetic timings are test fixtures, never hardware measurements."""
import importlib.util
import contextlib
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch
import subprocess
import sys

spec = importlib.util.spec_from_file_location("evaluation", Path(__file__).with_name("evaluate_prefill.py"))
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
spec = importlib.util.spec_from_file_location("model_runner", Path(__file__).with_name("run_model_ffn.py"))
model_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_runner)


class EvaluationTests(unittest.TestCase):
    def test_native_runner_uses_selected_input_and_keeps_timer_boundaries(self):
        def generate(ids, max_new_tokens, temperature):
            result = MagicMock()
            result.__getitem__.side_effect = lambda index: types.SimpleNamespace(
                tolist=lambda: ([11, 12] + [77] * max_new_tokens)[index[1]])
            return result
        torch = MagicMock(__version__="CPU fixture")
        torch.no_grad = contextlib.nullcontext
        torch.cuda.get_device_name.return_value = "CPU fixture"
        torch.cuda.max_memory_allocated.return_value = 0
        torch.tensor.return_value.cpu.return_value.numpy.return_value.tobytes.return_value = b"fixture"
        frontend = MagicMock()
        frontend.load_config_with_comments.return_value = {"chunking": True}
        frontend.LLaMA3W4A16Model.return_value.generate.side_effect = generate
        modules = {"torch": torch, "unified_llm_w4a16_hetero_libtorch": types.SimpleNamespace(__file__="fixture.so"),
                   "llama3_8b_w4a16_model": frontend}
        with tempfile.TemporaryDirectory() as tmp:
            ref, out = Path(tmp) / "ref.json", Path(tmp) / "out.json"
            ref.write_text(json.dumps(dict(input_ids=[[11, 12, 13, 14]], generated_ids=[77, 78])))
            argv = ["runner", "--model", tmp, "--ref", str(ref), "--out", str(out), "--prompt-tokens", "2",
                    "--heterogeneity", "hetero", "--reps", "1", "--new-tokens", "2"]
            with patch.dict(sys.modules, modules), patch.object(sys, "argv", argv), \
                    patch.object(model_runner, "stub_missing_modules"), patch.object(model_runner, "merge_shards"):
                model_runner.main()
            result = json.loads(out.read_text())
            config = json.loads(Path(result["config"]).read_text())
        self.assertEqual((config["heterogeneity"], config["prompt_len"], config["chunking"]), ("hetero", 2, True))
        self.assertEqual(torch.tensor.call_args.args[0], [[11, 12]])
        self.assertEqual(result["reps"][0]["prefill_ids"], [77])
        self.assertIsNone(result["matches_reference"])
        self.assertEqual(torch.cuda.synchronize.call_count, 6)

    def test_case_order_and_complete_gpu_control(self):
        args = types.SimpleNamespace(prompt_tokens=[512], rounds=2, methods=["gpu_original", "gpu_ffn_all"],
                                     out=Path("out"), ref=Path("ref"), build="build-model", config="config",
                                     reps=5, new_tokens=64, dummy=True, model=None)
        with patch.dict(evaluation.os.environ, HETEROMEGA_GPU_FFN_SPLIT="7168,14336"):
            cases = list(evaluation.cases(args))
        self.assertEqual([c[0] for c in cases], ["gpu_original", "gpu_ffn_all", "gpu_ffn_all", "gpu_original"])
        self.assertEqual([c[4]["HETEROMEGA_GPU_FFN"] for c in cases], ["0", "1", "1", "0"])
        self.assertTrue(all("HETEROMEGA_GPU_FFN_SPLIT" not in c[4] for c in cases))
        args.methods = ["heteromosaic"]
        command = next(evaluation.cases(args))[3]
        self.assertEqual(command[command.index("--heterogeneity") + 1], "hetero")

    def test_long_prompt_cannot_silently_reuse_short_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(Path(evaluation.__file__)), "--out", tmp,
                                     "--prompt-tokens", "2048", "--dry-run"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("reference has 1024 tokens", result.stderr)

    def test_summary_excludes_warmup_and_distinguishes_prompt_lengths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for method, length, times in [("gpu_original", 512, [1, 3, 2]), ("gpu_ffn_all", 512, [0.5, 1, 1.5]), ("gpu_original", 1024, [9])]:
                r = dict(method=method, prompt_tokens=length, warmup_s=999, warmup_ids=[7], matches_reference=None,
                         gpu_ffn_active=True, reps=[dict(prefill_s=t, prefill_ids=[7], generated_ids=[7, 8]) for t in times])
                (root / f"{method}-{length}.result.json").write_text(json.dumps(r))
            rows = evaluation.summarize(root)
            new = next(r for r in rows if r["method"] == "gpu_ffn_all")
            self.assertEqual((new["samples"], new["prefill_median_ms"], new["prefill_min_ms"], new["prefill_max_ms"], new["speedup_vs_gpu"]), (3, 1000, 500, 1500, 2))
            self.assertTrue((root / "summary.csv").exists())

    def test_mismatch_or_inactive_ffn_has_no_speedup_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = dict(method="gpu_original", prompt_tokens=512, warmup_ids=[7], matches_reference=True,
                        gpu_ffn_active=False, reps=[dict(prefill_s=2, prefill_ids=[7], generated_ids=[7])])
            (root / "base.result.json").write_text(json.dumps(base))
            for active, tokens, reference in [(True, [8], True), (False, [7], True), (True, [7], False)]:
                new = dict(base, method="gpu_ffn_all", gpu_ffn_active=active, matches_reference=reference,
                           reps=[dict(prefill_s=1, prefill_ids=[7], generated_ids=tokens)])
                (root / "new.result.json").write_text(json.dumps(new))
                self.assertEqual(evaluation.summarize(root)[0]["speedup_vs_gpu"], "")


if __name__ == "__main__":
    unittest.main()
