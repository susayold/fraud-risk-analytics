import re
import unittest

from _helpers import read


class ModelPageNavigationTests(unittest.TestCase):
    def test_model_navigation_is_recruiter_facing(self):
        html = read("part-5.html")
        nav = re.search(r'<nav class="part-nav primary-nav".*?</nav>', html, re.S).group(0)
        for label in ("Overview", "Data", "Model", "Network", "Decision", "Monitoring"):
            self.assertIn(f">{label}</a>", nav)
        self.assertIn('href="part-5.html"', nav)
        self.assertNotIn("05 ML", nav)

    def test_prior_pages_route_behavior_to_canonical_model_page(self):
        self.assertIn('href="part-5.html#behavioral-intelligence"', read("part-1.html"))
        self.assertIn('href="part-5.html#risk-modeling"', read("part-1.html"))
        self.assertIn('href="part-5.html#behavioral-intelligence"', read("part-2.html"))


if __name__ == "__main__":
    unittest.main()
