from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-7.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-7.js").read_text(encoding="utf-8")


class DecisionPageSourceTests(unittest.TestCase):
    def test_canonical_source_and_navigation(self):
        self.assertIn("part7_summary.json", JS)
        self.assertIn("project_status.json", JS)
        self.assertIn('href="part-7.html"', HTML)
        self.assertIn('aria-current="page"', HTML)
        for label in ("Overview", "Data", "Model", "Network", "Decision", "Monitoring"):
            self.assertIn(f">{label}<", HTML)

    def test_information_architecture_and_bindings(self):
        for anchor in ("decision-intelligence", "action-contract", "policy-lifecycle", "frozen-policy", "final-oot-actions", "review-capacity", "tradeoffs", "policy-generalization", "graph-handoff", "evidence"):
            self.assertIn(f'id="{anchor}"', HTML)
        for key in ("status", "mandatory-gates", "review-threshold", "block-threshold", "allow-rate", "fraud-capture", "selected-cost"):
            self.assertIn(f'data-decision="{key}"', HTML)

    def test_current_public_state_is_input_blocked(self):
        summary = json.loads((ROOT / "assets/data/part7_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "INPUT_BLOCKED")
        self.assertIn("Promise.allSettled", JS)


if __name__ == "__main__":
    unittest.main()
