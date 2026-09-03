import json
import re
import unittest
from pathlib import Path


class NoFakeMetricsTests(unittest.TestCase):
    def test_rendered_metrics_are_registry_backed_and_no_fake_words_exist(self):
        root = Path(".")
        html = (root / "part-9.html").read_text(encoding="utf-8")
        summary = json.loads((root / "assets/data/part9_summary.json").read_text(encoding="utf-8"))
        ids = set(re.findall(r'data-metric="([^"]+)"', html))
        self.assertTrue(ids <= set(summary["metrics"]))
        corpus = " ".join([html.lower(), (root / "assets/data/part9_summary.json").read_text(encoding="utf-8").lower(), (root / "assets/data/part9_charts.json").read_text(encoding="utf-8").lower(), (root / "assets/data/part9_status.json").read_text(encoding="utf-8").lower()])
        for token in ("dummy", "example metric", "sample pr-auc", "fake", "placeholder score"):
            self.assertNotIn(token, corpus)
