import unittest

from _helpers import read


class ModelPageSourceTests(unittest.TestCase):
    def test_model_page_uses_all_required_public_sources(self):
        script = read("js/part-5.js")
        for source in ("part4_summary.json", "part5_final_summary.json", "part5_model_selection.json", "part5_topk.json", "part5_calibration.json", "part5_subgroups.json", "part5_uncertainty.json"):
            self.assertIn(source, script)
        self.assertIn("Promise.allSettled", script)

    def test_page_has_canonical_model_anchors(self):
        html = read("part-5.html")
        for anchor in ("behavioral-intelligence", "pit-contract", "feature-system", "behavioral-signals", "risk-modeling", "champion-selection", "oot-generalization", "model-diagnostics", "model-risk", "evidence"):
            self.assertIn(f'id="{anchor}"', html)


if __name__ == "__main__":
    unittest.main()
