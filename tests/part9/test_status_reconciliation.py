import json
import unittest


class StatusReconciliationTests(unittest.TestCase):
    def test_blocked_upstream_states_are_preserved(self):
        status = json.loads(__import__("pathlib").Path("assets/data/part9_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["project_status"], "FINAL_PORTFOLIO_RELEASE_LOCKED")
        self.assertEqual(status["layers"]["part7"]["status"], "INPUT_BLOCKED")
        self.assertEqual(status["layers"]["part8"]["status"], "INPUT_BLOCKED")
