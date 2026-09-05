from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-8.html").read_text(encoding="utf-8")


class MonitoringClaimBoundaryTests(unittest.TestCase):
    def test_public_claim_boundaries(self):
        for text in ("OFFLINE RETROSPECTIVE MONITORING", "NOT LIVE PRODUCTION MONITORING", "FINAL OOT replay", "globally unseen", "governed version required", "source-driven"):
            self.assertIn(text, HTML)
        self.assertIn("graph context", HTML.lower())

    def test_row_level_publication_is_not_promised(self):
        self.assertIn("Row-level scores, decisions, labels", HTML)
        self.assertIn("aggregate", HTML.lower())


if __name__ == "__main__":
    unittest.main()
