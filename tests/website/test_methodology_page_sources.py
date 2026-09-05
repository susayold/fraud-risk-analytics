from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-9.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-9.js").read_text(encoding="utf-8")


class MethodologyPageSourceTests(unittest.TestCase):
    def test_canonical_page_and_navigation(self):
        self.assertIn("Evidence &amp; Audit", HTML)
        self.assertIn('rel="canonical" href="https://susayold.github.io/fraud-risk-analytics/part-9.html"', HTML)
        self.assertIn('aria-current="page"', HTML)
        for label in ("Overview", "Data", "Model", "Network", "Decision", "Monitoring", "Methodology"):
            self.assertIn(f">{label}<", HTML)
        self.assertIn("GitHub ↗", HTML)

    def test_audit_anchors_and_source_loading(self):
        for anchor in ("evidence-philosophy", "claim-taxonomy", "source-precedence", "status-registry", "evidence-registry", "metric-registry", "validation-gates", "methodology-controls", "version-lineage", "public-boundary", "reproducibility", "limitations", "source-health", "evidence-map"):
            self.assertIn(f'id="{anchor}"', HTML)
        for source in ("project_status.json", "part7_summary.json", "part8_summary.json", "part9_source_registry.csv", "part9_metric_registry.csv", "part9_validation_report.csv"):
            self.assertIn(source, JS)
        self.assertIn("Promise.allSettled", JS)

    def test_presentation_status_schema_is_explicit(self):
        status = json.loads((ROOT / "assets/data/project_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["presentation_status"], "PRESENTATION_READY")
        self.assertEqual(status["execution_summary"], "PART7_PART8_INPUT_BLOCKED")
        self.assertEqual(status["source_reconciliation_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
