import unittest

import pandas as pd

from src.part7.contracts import PolicyConfig
from src.part7.decision_runtime import decide
from src.part7.economics import EconomicAssumptions
from src.part7.evaluation_runtime import evaluate_decisions
from src.part7.exposure import add_exposure_bases


class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.config = PolicyConfig("test", .5, .9, .5)
        self.assumptions = EconomicAssumptions(.7, .95, 1, .8, .01, .5, .02, .05)
        self.frame = add_exposure_bases(pd.DataFrame([{
            "source_row_id": 1, "transaction_timestamp": "2026-01-01T00:00:00Z", "risk_score": .8, "amount": 10
        }]))

    def test_decision_runtime_rejects_label(self):
        with self.assertRaises(ValueError):
            decide(self.frame.assign(fraud_label=1), self.config)

    def test_evaluation_is_post_decision_join(self):
        decisions = decide(self.frame, self.config)
        metrics = evaluate_decisions(decisions, pd.DataFrame({"source_row_id": [1], "fraud_label": [1]}), self.assumptions)
        self.assertEqual(metrics["transactions"], 1)


if __name__ == "__main__":
    unittest.main()
