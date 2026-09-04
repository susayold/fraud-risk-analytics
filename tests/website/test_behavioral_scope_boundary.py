import unittest

from _helpers import read


class BehavioralScopeBoundaryTests(unittest.TestCase):
    def test_behavioral_boundary_is_visible(self):
        html = read("part-5.html")
        for phrase in ("deterministic QA execution slice", "not a representative full-population behavior claim", "Not full-population", "ASSOCIATION ONLY", "history_timestamp &lt; current_timestamp"):
            self.assertIn(phrase, html)

    def test_source_scope_is_not_claimed_as_full_population(self):
        script = read("js/part-5.js")
        self.assertIn("execution.rows", script)
        self.assertIn("history_coverage_status", script)


if __name__ == "__main__":
    unittest.main()
