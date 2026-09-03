import json
import unittest


class ChartRegistryTests(unittest.TestCase):
    def test_every_chart_has_status_source_and_render_condition(self):
        charts = json.loads(__import__("pathlib").Path("assets/data/part9_charts.json").read_text(encoding="utf-8"))
        self.assertEqual(len(charts), 23)
        for chart in charts.values():
            self.assertTrue(chart["source_artifact"])
            self.assertEqual(chart["render_condition"], "status == AVAILABLE")
            if chart["status"] != "AVAILABLE":
                self.assertEqual(chart["data"], [])
