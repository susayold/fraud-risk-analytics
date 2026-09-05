from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-8.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-8.js").read_text(encoding="utf-8")


class DriftEvaluabilityTests(unittest.TestCase):
    def test_missing_metric_is_not_green(self):
        self.assertIn("NaN ≠ GREEN", HTML)
        self.assertIn("NOT_EVALUABLE", HTML)
        self.assertIn("data-metric-status=", HTML)

    def test_metric_family_alignment_and_missing_value_logic(self):
        self.assertIn("const setMetric", JS)
        self.assertIn("Number.isFinite", JS)
        self.assertIn("metric.includes('psi')", JS)
        self.assertIn("metric.includes('wasserstein')", JS)
        self.assertIn("status === 'GREEN'", JS)


if __name__ == "__main__":
    unittest.main()
