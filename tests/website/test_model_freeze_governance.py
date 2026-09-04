import unittest

from _helpers import read


class ModelFreezeGovernanceTests(unittest.TestCase):
    def test_freeze_and_no_retuning_are_explicit(self):
        html = read("part-5.html")
        script = read("js/part-5.js")
        for phrase in ("VALIDATION-SELECTED FROZEN CHAMPION", "FROZEN BEFORE OOT LABEL OPEN", "NO OOT RETUNING", "C00–C10"):
            self.assertIn(phrase, html)
        self.assertIn("oot_used_for_retuning", script)

    def test_score_policy_boundary_is_explicit(self):
        html = read("part-5.html")
        self.assertIn("MODEL RANKS RISK", html)
        self.assertIn("POLICY PRODUCES ALLOW / REVIEW / BLOCK", html)


if __name__ == "__main__":
    unittest.main()
