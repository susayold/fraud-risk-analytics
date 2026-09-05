from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-7.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-7.js").read_text(encoding="utf-8")


class PolicyThresholdSemanticsTests(unittest.TestCase):
    def test_threshold_order_is_explicit(self):
        self.assertIn("0 ≤ review_threshold", HTML)
        self.assertIn("block_threshold ≤ 1", HTML)
        self.assertIn("review_threshold", JS)
        self.assertIn("block_threshold", JS)

    def test_capacity_is_not_mislabeled_as_a_probability_threshold(self):
        self.assertIn("Review capacity", HTML)
        self.assertIn("finite queue", HTML)
        self.assertIn("eligibility does not guarantee selection", HTML)


if __name__ == "__main__":
    unittest.main()
