import unittest

from _helpers import read


class OotGeneralizationTests(unittest.TestCase):
    def test_oot_is_compared_without_causal_explanation(self):
        html = read("part-5.html")
        script = read("js/part-5.js")
        for phrase in ("FINAL OUT-OF-TIME GENERALIZATION", "Observed temporal generalization degradation", "No causal explanation"):
            self.assertIn(phrase, html)
        self.assertIn("degradation.relative_delta", script)
        self.assertIn("degradation.absolute_delta", script)


if __name__ == "__main__":
    unittest.main()
