import unittest
from pathlib import Path


class HtmlStatusTests(unittest.TestCase):
    def test_all_sections_and_accessibility_contracts_exist(self):
        html = Path("part-9.html").read_text(encoding="utf-8")
        for section in range(15):
            self.assertIn(f'id="s{section:02d}"', html)
        self.assertEqual(html.count('class="chart-alt"'), 23)
        self.assertIn('aria-label="Case study parts"', html)
