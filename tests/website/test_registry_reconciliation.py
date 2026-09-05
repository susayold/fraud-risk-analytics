from pathlib import Path
import csv
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / "js" / "part-9-audit.js").read_text(encoding="utf-8")


class RegistryReconciliationTests(unittest.TestCase):
    def test_current_registry_counts_and_hashes(self):
        with (ROOT / "reports/part9/part9_source_registry.csv").open(encoding="utf-8", newline="") as handle:
            sources = list(csv.DictReader(handle))
        with (ROOT / "reports/part9/part9_metric_registry.csv").open(encoding="utf-8", newline="") as handle:
            metrics = list(csv.DictReader(handle))
        self.assertEqual(len(sources), 16)
        self.assertEqual(len(metrics), 14)
        self.assertTrue(all(row["sha256"] and row["bytes"] for row in sources))
        self.assertIn("source-count", JS)
        self.assertIn("metric-count", JS)

    def test_release_reconciliation_is_pass(self):
        summary = json.loads((ROOT / "reports/part9/PART9_SOURCE_RECONCILIATION.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "PASS")
        self.assertIn("not replaced with fabricated metrics", summary["notes"])


if __name__ == "__main__":
    unittest.main()
