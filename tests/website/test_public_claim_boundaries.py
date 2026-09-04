import unittest

from _helpers import read


class PublicClaimBoundaryTests(unittest.TestCase):
    def test_simulated_and_offline_boundaries_are_visible(self):
        overview = read("part-1.html")
        data = read("part-2.html")
        self.assertIn("SIMULATED ECONOMICS WHERE APPLICABLE", overview)
        self.assertIn("No production deployment", overview)
        self.assertIn("not realized bank loss", data)
        self.assertIn("not a production transaction threshold", data)
        self.assertIn("Aggregate public evidence only", data)

    def test_graph_metric_is_labeled_as_link_prediction(self):
        html = read("part-1.html")
        self.assertIn("link-prediction PR-AUC", html)
        self.assertIn("not fraud-classification PR-AUC", html)


if __name__ == "__main__":
    unittest.main()
