from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-7.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-7.js").read_text(encoding="utf-8")


class ActionReconciliationTests(unittest.TestCase):
    def test_one_action_contract_and_action_mix(self):
        self.assertIn("ONE ROW → ONE ACTION", HTML)
        self.assertIn("ALLOW + REVIEW + BLOCK = 100%", HTML)
        for key in ("allow_rate", "review_rate", "block_rate"):
            self.assertIn(key, JS)
        self.assertIn("data-action-chart", HTML)

    def test_capture_is_review_plus_block_not_block_only(self):
        self.assertIn("fraud through REVIEW + BLOCK", HTML)
        self.assertNotIn("Blocked fraud capture", HTML)


if __name__ == "__main__":
    unittest.main()
