from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-6.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-6.js").read_text(encoding="utf-8")


class GraphNoveltySegmentTests(unittest.TestCase):
    def test_three_source_driven_novelty_segments_exist(self):
        self.assertIn("data-novelty-cards", HTML)
        for segment in ("WARM_PAIR_SEEN", "WARM_PAIR_NEW", "NEW_CARD_ONLY"):
            self.assertIn(segment, JS)
        self.assertIn("novelty_segments", JS)

    def test_deltas_are_computed_from_a_and_c(self):
        self.assertIn("c_pr_auc", JS)
        self.assertIn("a_pr_auc", JS)
        self.assertIn("const delta", JS)
        self.assertNotIn("+0.010736", HTML)


if __name__ == "__main__":
    unittest.main()
