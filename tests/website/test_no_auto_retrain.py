from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-8.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-8.js").read_text(encoding="utf-8")


class NoAutoRetrainTests(unittest.TestCase):
    def test_governance_boundary_is_explicit(self):
        for text in ("NO AUTO-RETRAIN", "NO AUTO-RECALIBRATION", "NO AUTO-POLICY CHANGE", "investigation"):
            self.assertIn(text, HTML)

    def test_frontend_contains_no_mutation_operation(self):
        self.assertNotIn("function retrain", JS.lower())
        self.assertNotIn("function mutate", JS.lower())


if __name__ == "__main__":
    unittest.main()
