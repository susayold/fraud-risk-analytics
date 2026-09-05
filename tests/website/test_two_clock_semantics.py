from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-8.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-8.js").read_text(encoding="utf-8")


class TwoClockSemanticsTests(unittest.TestCase):
    def test_clock_labels_and_boundary_are_explicit(self):
        for text in ("OPERATIONS_NOW", "OUTCOMES_MATURED", "LABEL-FREE", "RETROSPECTIVE", "label-arrival timestamps are not available"):
            self.assertIn(text, HTML)

    def test_sources_load_independently(self):
        self.assertIn("Promise.allSettled", JS)
        self.assertIn("part8_monitoring_timeline.json", JS)
        self.assertIn("matured_outcome_rows", JS)


if __name__ == "__main__":
    unittest.main()
