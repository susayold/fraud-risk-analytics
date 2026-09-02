import unittest
import pandas as pd

from src.part7.economics import EconomicAssumptions, evaluate_economics
from src.part7.exposure import add_exposure_bases


class Part7EconomicsTests(unittest.TestCase):
    def test_positive_exposure_never_negative_and_costs_reconcile(self):
        frame = add_exposure_bases(pd.DataFrame([
            {"source_row_id": 1, "risk_score": .9, "amount": -10, "action": "ALLOW", "fraud_label": 1},
            {"source_row_id": 2, "risk_score": .1, "amount": 10, "action": "BLOCK", "fraud_label": 0},
        ]))
        a = EconomicAssumptions(.7, .95, 1.0, .8, .01, .5, .02, .05)
        m = evaluate_economics(frame, a)
        self.assertGreaterEqual(frame.positive_exposure.min(), 0)
        self.assertGreaterEqual(m["simulated_total_cost"], 0)
        self.assertEqual(m["transactions"], m["allow_count"] + m["review_count"] + m["block_count"])


if __name__ == "__main__":
    unittest.main()
