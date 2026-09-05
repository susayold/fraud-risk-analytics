from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-9.html").read_text(encoding="utf-8")


class AuditNavigationTests(unittest.TestCase):
    def test_methodology_is_a_utility_not_a_seventh_primary_layer(self):
        nav = HTML.split('<nav class="part-nav primary-nav"', 1)[1].split('</nav>', 1)[0]
        self.assertEqual(nav.count('<a '), 6)
        self.assertIn('class="active" href="part-9.html"', HTML)

    def test_page_map_and_cta_links_are_present(self):
        for page in ("part-1.html", "part-2.html", "part-5.html", "part-6.html", "part-7.html", "part-8.html", "part-9.html"):
            self.assertIn(f'href="{page}"', HTML)
        for artifact in ("part9_source_registry.csv", "part9_metric_registry.csv", "part9_validation_report.csv"):
            self.assertIn(artifact, HTML)


if __name__ == "__main__":
    unittest.main()
