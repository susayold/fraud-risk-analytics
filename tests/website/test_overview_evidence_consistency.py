import unittest

from _helpers import read, read_json


class OverviewEvidenceConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.html = read("part-1.html")
        self.script = read("js/overview.js")

    def test_part7_and_part8_are_source_bound(self):
        self.assertIn('data-overview="p7-summary"', self.html)
        self.assertIn('data-overview="p8-summary"', self.html)
        self.assertNotIn("64 / 64 PASS", self.html)
        self.assertNotIn("72 / 72 PASS", self.html)

        registry = read_json("assets/data/project_status.json")
        part7 = read_json("assets/data/part7_summary.json")
        part8 = read_json("assets/data/part8_summary.json")
        self.assertEqual(registry["layers"]["part7"]["status"], part7["status"])
        self.assertEqual(registry["layers"]["part8"]["status"], part8["status"])

    def test_scale_and_finding_sources_are_bound(self):
        for key in ("transactions", "fraud-transactions", "fraud-rate", "users", "cards", "merchants"):
            self.assertIn(f'data-overview="{key}"', self.html)
        for key in ("online-lift", "validation-pr-auc", "oot-pr-auc", "link-pr-auc", "p7-review-threshold"):
            self.assertIn(f'data-overview="{key}"', self.html)
        self.assertIn("part2_summary.json", self.script)
        self.assertIn("part3_summary.json", self.script)
        self.assertIn("part5_final_summary.json", self.script)
        self.assertIn("part6_summary.json", self.script)


if __name__ == "__main__":
    unittest.main()
