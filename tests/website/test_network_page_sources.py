from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-6.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-6.js").read_text(encoding="utf-8")


class NetworkPageSourceTests(unittest.TestCase):
    def test_page_uses_canonical_source_and_six_part_navigation(self):
        self.assertIn("part6_summary.json", JS)
        self.assertIn("assets/data/${file}", JS)
        self.assertIn("Promise.allSettled", JS)
        for label in ("Overview", "Data", "Model", "Network", "Decision", "Monitoring"):
            self.assertIn(f">{label}<", HTML)
        self.assertIn('aria-current="page"', HTML)
        self.assertIn('href="part-6.html"', HTML)

    def test_dynamic_renderers_cover_required_evidence(self):
        for renderer in ("renderClassification", "renderNovelty", "renderCommunity", "renderMonthly", "renderAblations", "renderShap"):
            self.assertIn(f"function {renderer}", JS)
        self.assertIn("NETWORK EVIDENCE UNAVAILABLE", JS)


if __name__ == "__main__":
    unittest.main()
