"""CPU regressions for legacy preservation and array8 multicast accounting."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

try:
    from .analyze_bottleneck import HERE, analyze, projection_accounting
except ImportError:
    from analyze_bottleneck import HERE, analyze, projection_accounting


def manifest(m, k, n, *, reuse=2):
    n_columns = 4 if (n // 32) % 8 else 8
    return dict(design="array8", m=m, k=k, n=n, tile_m=16, tile_k=128,
                tile_n=32, weight_tile_bytes=2144, cols=8, compute_rows=4,
                worker_count=32, m_reuse=reuse, n_columns=n_columns,
                m_column_groups=8 // n_columns)


class BottleneckAnalysisTests(unittest.TestCase):
    def test_existing_legacy_fields_are_preserved(self):
        # The saved historical analysis is deliberately not regenerated.
        # Check every old field, while permitting additional architecture data.
        saved = json.loads((HERE / "results/bottleneck_analysis.json").read_text())
        for filename in sorted({row["report"] for row in saved["rows"]}):
            current = analyze(HERE / "results" / filename)
            old = [row for row in saved["rows"] if row["report"] == filename]
            self.assertEqual(len(current), len(old))
            for now, previous in zip(current, old):
                for key, value in previous.items():
                    self.assertEqual(now[key], value, (filename, key))
                self.assertEqual(now["architecture"], "legacy")

    def test_array8_formula_distinguishes_shim_from_core_work(self):
        # M512/K4096/N512: 16384 native work tiles, R2, eight N columns.
        info = projection_accounting(manifest(512, 4096, 512), 512, 4096, 512)
        self.assertEqual(info["worker_count"], 32)
        self.assertEqual(info["unique_packed_weight_bytes"], 1_097_728)
        self.assertEqual(info["a_shim_payload_bytes"], 8_388_608)
        self.assertEqual(info["weight_shim_payload_bytes"], 4_390_912)
        self.assertEqual(info["a_core_payload_bytes"], 67_108_864)
        self.assertEqual(info["weight_core_payload_bytes"], 17_563_648)
        self.assertEqual(info["dequantization_calls"], 8192)
        self.assertEqual(info["weight_shim_replays_per_unique_tile"], 4)
        self.assertEqual(info["dequant_replays_per_unique_tile"], 16)

    def test_mock_array8_manifest_has_mixed_gate_and_down_reuse(self):
        # Modify manifests only: these are synthetic accounting inputs, not
        # claimed array8 timing measurements. M128/P128 gate/up use R1 while
        # down uses R2, so applying a blanket8x traffic reduction is wrong.
        report = json.loads((HERE / "results/ffn_m128_h4096_i14336_hx370.json").read_text())
        report["partitions"] = [copy.deepcopy(report["partitions"][0])]
        report["config"]["columns"] = 8
        part = report["partitions"][0]
        part["npu"]["artifacts"]["gate_up"]["manifest"] = manifest(128, 4096, 128, reuse=1)
        part["npu"]["artifacts"]["down"]["manifest"] = manifest(128, 128, 4096, reuse=2)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic_manifest_only.json"
            path.write_text(json.dumps(report))
            row, = analyze(path)
        self.assertEqual(row["architecture"], "array8")
        self.assertEqual(row["projection_workers"], {"gate_up": 32, "down": 32})
        self.assertEqual(row["effective_m_reuse"], {"gate_up": 1, "down": 2})
        self.assertEqual(row["calculated_bytes"]["projection_graph_weight_payload"], 1_372_160)
        self.assertEqual(row["calculated_bytes"]["projection_graph_a_payload"], 2_621_440)
        self.assertEqual(row["projection_dequantization_calls"], 2560)
        self.assertNotIn("weight_dma_and_dequant_replays", row)
        self.assertEqual(row["projection_details"]["gate"]["weight_shim_replays_per_unique_tile"], 2)
        self.assertEqual(row["projection_details"]["gate"]["dequant_replays_per_unique_tile"], 8)
        self.assertEqual(row["projection_details"]["down"]["weight_shim_replays_per_unique_tile"], 1)
        self.assertEqual(row["projection_details"]["down"]["dequant_replays_per_unique_tile"], 4)

    def test_rejects_unrecognized_or_inconsistent_manifests(self):
        base = manifest(512, 4096, 512)
        for change in ({"design": "unknown"}, {"worker_count": 8}, {"compute_rows": 1},
                       {"n_columns": 4}, {"m_reuse": 3}, {"n": 1024}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                projection_accounting(dict(base, **change), 512, 4096, 512)


if __name__ == "__main__":
    unittest.main()
