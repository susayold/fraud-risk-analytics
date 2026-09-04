import re
import unittest

from _helpers import read


class NavigationArchitectureTests(unittest.TestCase):
    def test_primary_navigation_has_six_recruiter_layers(self):
        for page in ("part-1.html", "part-2.html"):
            html = read(page)
            match = re.search(r'<nav class="part-nav primary-nav".*?</nav>', html, re.S)
            self.assertIsNotNone(match, page)
            nav = match.group(0)
            for label in ("Overview", "Data", "Model", "Network", "Decision", "Monitoring"):
                self.assertIn(f">{label}</a>", nav)
            self.assertNotIn(">03 Portfolio</a>", nav)
            self.assertNotIn(">04 Behavior</a>", nav)
            self.assertNotIn(">09 Deliver</a>", nav)

    def test_legacy_portfolio_link_routes_to_page2(self):
        html = read("part-1.html")
        self.assertIn('href="part-2.html#portfolio-baseline"', html)
        self.assertIn("Explore Behavior", html)


if __name__ == "__main__":
    unittest.main()
