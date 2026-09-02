import unittest

import pandas as pd

from src.part7.backtest import evaluate_variants, select_policy
from src.part7.economics import EconomicAssumptions
from src.part7.exposure import add_exposure_bases


class CandidateMetadataTests(unittest.TestCase):
    def setUp(self):
        rows = []
        for i in range(200):
            score = 0.95 if i < 20 else (0.70 if i < 70 else 0.05)
            rows.append({"source_row_id": i + 1, "transaction_timestamp": "2026-01-01T00:00:00Z", "risk_score": score, "amount": 100.0, "fraud_label": int(i < 20), "pair_new": bool(i % 3 == 0)})
        self.frame = add_exposure_bases(pd.DataFrame(rows))
        self.assumptions = EconomicAssumptions(.90, .99, .1, .95, .01, .5, .02, .05)

    def test_candidate_metadata_complete(self):
        metrics, _ = evaluate_variants(self.frame, [.5, .7, .9], [.01], self.assumptions, False, 100, max_threshold_pairs=6)
        candidates = metrics[metrics.variant.isin(["P2", "P3", "P4", "P5"])]
        fields = ["policy_version", "priority_method", "review_threshold", "block_threshold", "review_capacity"]
        self.assertFalse(candidates.empty)
        self.assertTrue(candidates[fields].notna().all().all())

    def test_each_candidate_variant_has_metadata(self):
        metrics, _ = evaluate_variants(self.frame, [.5, .7, .9], [.01], self.assumptions, False, 100, max_threshold_pairs=6)
        for variant in ("P2", "P3", "P4", "P5"):
            subset = metrics[metrics.variant.eq(variant)]
            self.assertFalse(subset.empty, variant)
            self.assertTrue(subset.policy_version.notna().all())
            self.assertTrue(subset.priority_method.notna().all())

    def test_balanced_profile_can_select_non_p0_policy(self):
        metrics, _ = evaluate_variants(self.frame, [.5, .7, .9], [.01], self.assumptions, False, 100, max_threshold_pairs=6)
        selected = select_policy(metrics, {"max_review_rate": .02, "max_block_rate": .20, "max_legitimate_block_rate": .20, "allowed_priority_methods": ["SCORE_ONLY", "EXPOSURE_WEIGHTED_RANK"], "amount_priority_enabled": True}, "minimize_total_simulated_cost")
        self.assertIsNotNone(selected)
        self.assertNotEqual(selected.policy_version, "PART7_P0_ALLOW_ALL")


if __name__ == "__main__":
    unittest.main()
