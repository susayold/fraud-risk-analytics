import unittest

from _helpers import read


class ModelDiagnosticsBoundaryTests(unittest.TestCase):
    def test_missing_diagnostic_resolution_is_not_invented(self):
        html = read("part-5.html")
        script = read("js/part-5.js")
        self.assertIn("Exact calibration bins: NOT RETAINED", html)
        self.assertIn("not published as an exact 95% confidence interval", html)
        self.assertIn("part5_calibration.json", script)

    def test_low_support_subgroup_is_visible(self):
        self.assertIn("LOW SUPPORT", read("js/part-5.js"))
        self.assertIn("no performance claim", read("part-5.html"))


if __name__ == "__main__":
    unittest.main()
