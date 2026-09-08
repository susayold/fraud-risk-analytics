import json
import unittest
from pathlib import Path


class StatusReconciliationTests(unittest.TestCase):
    def test_final_upstream_states_are_reconciled(self):
        status = json.loads(Path("assets/data/part9_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["project_status"], "FINAL_PORTFOLIO_RELEASE_LOCKED")
        self.assertEqual(status["layers"]["part7"]["status"], "LOCKED")
        self.assertEqual(status["layers"]["part7"]["execution_status"], "DECISION_POLICY_LOCKED")
        self.assertEqual(status["layers"]["part8"]["status"], "LOCKED")
        self.assertEqual(status["layers"]["part8"]["execution_status"], "MONITORING_GOVERNANCE_LOCKED")


if __name__ == "__main__":
    unittest.main()
