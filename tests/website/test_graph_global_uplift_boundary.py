from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-6.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-6.js").read_text(encoding="utf-8")


class GraphGlobalUpliftBoundaryTests(unittest.TestCase):
    def test_global_uplift_is_not_overclaimed(self):
        for text in ("GLOBAL FRAUD-CLASSIFICATION UPLIFT: NON-ROBUST / SEGMENT-DEPENDENT", "GLOBAL INCREMENTAL GNN UPLIFT: NON-ROBUST / INCONCLUSIVE", "Segment-specific C − A", "Test does not override Validation freeze"):
            self.assertIn(text, HTML)
        self.assertIn("test_warm_delta", JS)
        self.assertIn("ci95_low", JS)

    def test_graph_experiment_split_is_separate(self):
        self.assertIn("GRAPH EXPERIMENT SPLIT ≠ PAGE 3 MODEL OOT SPLIT", HTML)
        self.assertIn("Do not compare these PR-AUC values", HTML)
        self.assertIn("test_warm_delta", JS)


if __name__ == "__main__":
    unittest.main()
