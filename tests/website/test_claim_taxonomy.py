from pathlib import Path
import csv
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-9.html").read_text(encoding="utf-8")


class ClaimTaxonomyTests(unittest.TestCase):
    def test_primary_claim_classes_are_visible(self):
        for claim_class in ("OBSERVED", "DERIVED", "SIMULATED", "GOVERNANCE / CONTRACT", "DEFINITION", "POST-HOC DIAGNOSTIC"):
            self.assertIn(claim_class, HTML)
        self.assertIn("NOT ACTUAL SAVINGS", HTML)

    def test_registered_metrics_have_class_source_and_status(self):
        with (ROOT / "reports/part9/part9_metric_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(rows)
        for row in rows:
            self.assertTrue(row["claim_class"])
            self.assertTrue(row["source_artifact"])
            self.assertTrue(row["status"])


if __name__ == "__main__":
    unittest.main()
