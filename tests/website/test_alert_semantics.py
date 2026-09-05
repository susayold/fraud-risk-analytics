from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-8.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-8.js").read_text(encoding="utf-8")


class AlertSemanticsTests(unittest.TestCase):
    def test_alert_register_distinguishes_failure_and_gate(self):
        for text in ("ALERT REGISTER GATED", "persistent", "INVESTIGATE"):
            self.assertIn(text, HTML)
        self.assertIn("ALERT REGISTER UNAVAILABLE", JS)
        self.assertIn("alertError", JS)
        self.assertIn("alerts?.alerts", JS)
        self.assertNotIn('set(\'alert-state\', \'0\')', JS)

    def test_alert_source_is_independent(self):
        self.assertIn("Promise.allSettled", JS)
        self.assertIn("not the same as zero alerts", JS)


if __name__ == "__main__":
    unittest.main()
