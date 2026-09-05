from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-9.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-9.js").read_text(encoding="utf-8")


class SourcePrecedenceTests(unittest.TestCase):
    def test_precedence_and_conflict_rule_are_explicit(self):
        for text in ("FINAL EXECUTION ARTIFACT", "LOCKED PUBLIC SUMMARY", "DIAGNOSTIC ARTIFACT", "REGISTRY / VALIDATOR", "README → HTML", "Flag → select → record"):
            self.assertIn(text, HTML)
        self.assertIn("HTML is a view, not the source of truth", HTML)

    def test_runtime_does_not_promote_unavailable_sources(self):
        self.assertIn("SOURCE UNAVAILABLE", JS)
        self.assertIn("source-health", JS)
        self.assertIn("INPUT_BLOCKED", HTML)


if __name__ == "__main__":
    unittest.main()
