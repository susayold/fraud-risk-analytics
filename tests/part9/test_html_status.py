import unittest
from pathlib import Path


class HtmlStatusTests(unittest.TestCase):
    def test_all_sections_and_accessibility_contracts_exist(self):
        html = Path("part-9.html").read_text(encoding="utf-8")
        sections = [
            "evidence-philosophy",
            "claim-taxonomy",
            "source-precedence",
            "status-registry",
            "evidence-registry",
            "metric-registry",
            "validation-gates",
            "methodology-controls",
            "version-lineage",
            "public-boundary",
            "reproducibility",
            "limitations",
            "evidence-map",
        ]
        for section in sections:
            self.assertIn(f'id="{section}"', html)
        self.assertIn('aria-label="Analytical layers"', html)
        self.assertIn('aria-label="Project utilities"', html)
        self.assertIn('aria-label="Footer navigation"', html)
        self.assertIn("Recruiter-facing site = 7 analytical pages", html)
        self.assertIn("Execution backend = 9 technical parts", html)
        self.assertIn("64 / 64", html)
        self.assertIn("72 / 72", html)
