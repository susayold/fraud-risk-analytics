from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-7.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-7.js").read_text(encoding="utf-8")


class DecisionFailClosedTests(unittest.TestCase):
    def test_locked_state_requires_validator_conditions(self):
        for text in ("DECISION_POLICY_LOCKED", "final_lock_eligible", "validation.pass === validation.mandatory_gates", "validation.blocked === 0", "validation.fail === 0"):
            self.assertIn(text, JS)

    def test_blocked_state_withholds_final_values(self):
        for text in ("hideLockedEvidence", "FINAL REPLAY EVIDENCE UNAVAILABLE", "Thresholds remain withheld rather than guessed", "EVIDENCE UNAVAILABLE"):
            self.assertIn(text, HTML + JS)
        for forbidden in ("0.561869", "0.003910", "72,326.2", "103,934.5"):
            self.assertNotIn(forbidden, HTML)


if __name__ == "__main__":
    unittest.main()
