from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-6.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-6.js").read_text(encoding="utf-8")


class GraphSplitBoundaryTests(unittest.TestCase):
    def test_network_page_contract_and_monthly_scope(self):
        self.assertIn('data-current-part="6"', HTML)
        self.assertIn('data-monthly-chart', HTML)
        self.assertIn('class="monthly-chart"', HTML)
        self.assertIn("monthly_stability", JS)
        self.assertIn("data.monthly_stability?.rows", JS)
        self.assertIn("retained months only", HTML)

    def test_no_public_raw_graph_artifacts_are_embedded(self):
        for forbidden in ("raw_ids.csv", "raw_edges.csv", ".embeddings", ".cbm"):
            self.assertNotIn(forbidden, HTML)


if __name__ == "__main__":
    unittest.main()
