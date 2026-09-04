import unittest

from _helpers import read


class DataPageSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.html = read("part-2.html")
        self.script = read("js/part-2.js")

    def test_missingness_governance_is_precise(self):
        self.assertIn("<span>Use Chip</span><b>MODEL_OK · CATEGORICAL</b>", self.html)
        self.assertIn("<span>Merchant City</span><b>MODEL_OK · CATEGORICAL</b>", self.html)
        self.assertIn("<span>Merchant State / Zip</span><b>MODEL_OK_WITH_MISSINGNESS</b>", self.html)

    def test_discovery_boundary_uses_portfolio_language(self):
        self.assertIn("DETAILED PORTFOLIO DISCOVERY USES DEVELOPMENT ONLY.", self.html)
        self.assertNotIn("DETAILED PART 3 DISCOVERY USES DEVELOPMENT ONLY.", self.html)

    def test_reconciliation_is_calculated_not_assumed(self):
        for layer in ("SOURCE_CSV", "PARQUET", "DUCKDB_RAW", "STANDARDIZED", "TRANSACTION_BASE", "MODEL_SPLITS"):
            self.assertIn(f'data-p2-recon="{layer}"', self.html)
        self.assertIn("allRowsReconcile", self.script)
        self.assertIn("RECONCILIATION ERROR", self.script)
        self.assertIn("data.split_summary", self.script)


if __name__ == "__main__":
    unittest.main()
