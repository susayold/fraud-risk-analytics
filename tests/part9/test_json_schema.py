import json
import unittest


class JsonSchemaTests(unittest.TestCase):
    def test_public_payload_shapes(self):
        from pathlib import Path
        summary = json.loads(Path("assets/data/part9_summary.json").read_text(encoding="utf-8"))
        charts = json.loads(Path("assets/data/part9_charts.json").read_text(encoding="utf-8"))
        self.assertIn("metrics", summary); self.assertIn("project", summary)
        for chart in charts.values():
            self.assertTrue({"status", "source_artifact", "claim_class", "data"} <= set(chart))
