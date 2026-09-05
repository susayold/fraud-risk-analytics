from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-8.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-8.js").read_text(encoding="utf-8")


class MonitoringPageSourceTests(unittest.TestCase):
    def test_canonical_sources_and_navigation(self):
        for source in ("part8_summary.json", "part8_alert_summary.json", "part8_monitoring_timeline.json"):
            self.assertIn(source, JS)
        self.assertIn('href="part-8.html"', HTML)
        self.assertIn('aria-current="page"', HTML)
        for label in ("Overview", "Data", "Model", "Network", "Decision", "Monitoring"):
            self.assertIn(f">{label}<", HTML)

    def test_required_information_architecture_and_bindings(self):
        for anchor in ("two-clocks", "reference-contract", "operations-now", "drift-evaluability", "policy-monitoring", "outcomes-matured", "performance-monitoring", "alerts", "monitoring-boundaries", "governance-actions", "evidence"):
            self.assertIn(f'id="{anchor}"', HTML)
        for key in ("status", "mandatory-gates", "pass-gates", "blocked-gates", "fail-gates", "alert-register-status", "matured-state"):
            self.assertIn(f'data-monitor="{key}"', HTML)

    def test_public_source_is_input_blocked(self):
        summary = json.loads((ROOT / "assets/data/part8_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["status"], "INPUT_BLOCKED")
        self.assertEqual(summary["validation"]["blocked"], 52)
        self.assertIn("Promise.allSettled", JS)


if __name__ == "__main__":
    unittest.main()
