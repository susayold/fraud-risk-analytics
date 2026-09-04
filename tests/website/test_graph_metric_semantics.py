from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-6.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-6.js").read_text(encoding="utf-8")


class GraphMetricSemanticsTests(unittest.TestCase):
    def test_link_prediction_metric_is_distinguished_from_fraud_classification(self):
        self.assertIn("Temporal link-prediction PR-AUC", HTML)
        self.assertIn("Not fraud-classification PR-AUC", HTML)
        self.assertIn("downstream fraud-classification score", HTML)
        self.assertIn("link_ap", JS)

    def test_temporal_contract_is_visible(self):
        self.assertIn("No fraud label in community construction", HTML)
        self.assertIn("Validation/Test labels only for post-hoc diagnostics", HTML)
        self.assertIn("positive_links", JS)
        self.assertIn("card_embedding_dim", JS)


if __name__ == "__main__":
    unittest.main()
