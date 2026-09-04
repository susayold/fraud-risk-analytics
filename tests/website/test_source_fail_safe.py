import unittest

from _helpers import read


class SourceFailSafeTests(unittest.TestCase):
    def test_overview_has_no_stale_success_values(self):
        html = read("part-1.html")
        script = read("js/overview.js")
        for stale in ("64 / 64 PASS", "72 / 72 PASS", "DECISION_POLICY_LOCKED", "MONITORING_GOVERNANCE_LOCKED"):
            self.assertNotIn(stale, html)
        self.assertIn("EVIDENCE UNAVAILABLE", script)
        self.assertIn("Promise.allSettled", script)

    def test_data_page_fails_closed(self):
        script = read("js/part-2.js")
        self.assertIn("EVIDENCE UNAVAILABLE", script)
        self.assertIn("setUnavailable", script)
        self.assertIn(".catch(() =>", script)
        self.assertIn("RECONCILIATION ERROR", script)


if __name__ == "__main__":
    unittest.main()
