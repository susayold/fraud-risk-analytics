from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-7.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-7.js").read_text(encoding="utf-8")


class DecisionOotGovernanceTests(unittest.TestCase):
    def test_final_oot_is_replay_not_tuning(self):
        self.assertIn("FINAL OOT IS NOT A POLICY-TUNING SET", HTML)
        self.assertIn("NO FINAL OOT RETUNING", HTML)
        self.assertIn("renderGeneralization", JS)

    def test_oot_boundary_is_visible(self):
        self.assertIn("FINAL OOT replay, not globally unseen data", HTML)
        self.assertIn("CONFIRMATION", HTML)
        self.assertIn("Retrospective replay", JS)


if __name__ == "__main__":
    unittest.main()
