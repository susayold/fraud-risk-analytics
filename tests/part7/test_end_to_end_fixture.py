import unittest
from unittest.mock import patch

import pandas as pd

from src.part7.backtest import evaluate_variants, select_policy
from src.part7.bootstrap import weekly_paired_bootstrap
from src.part7.contracts import PolicyConfig
from src.part7.decision_runtime import decide
from src.part7.economics import EconomicAssumptions
from src.part7.evaluation_runtime import evaluate_decisions
from src.part7.exposure import add_exposure_bases
from src.part7.final_replay import load_and_verify_freeze, replay
from src.part7.freeze_policy import freeze_policy
from src.part7.replay_contract import verify_freeze


class EndToEndFixtureTests(unittest.TestCase):
    def test_fixture_runs_without_using_oot_for_selection(self):
        rows = []
        for i in range(240):
            day = i // 20 + 1
            split = "P7_POLICY_TUNE" if i < 120 else ("P7_POLICY_CONFIRM" if i < 200 else "FINAL_OOT")
            rows.append({"source_row_id": i + 1, "transaction_timestamp": f"2026-01-{day:02d}T00:00:00Z", "risk_score": .9 if i % 7 == 0 else .1, "amount": 100 + i, "fraud_label": int(i % 7 == 0), "split_name": split, "pair_new": bool(i % 5 == 0), "cold_card": bool(i % 11 == 0), "new_merchant": bool(i % 13 == 0), "cross_community": False})
        frame = add_exposure_bases(pd.DataFrame(rows))
        assumptions = EconomicAssumptions(.7, .95, 1, .8, .01, .5, .02, .05)
        tune = frame[frame.split_name.eq("P7_POLICY_TUNE")]
        confirm = frame[frame.split_name.eq("P7_POLICY_CONFIRM")]
        oot = frame[frame.split_name.eq("FINAL_OOT")]
        metrics, actions = evaluate_variants(tune, [.5, .8], [.01], assumptions, False, 100, max_threshold_pairs=4)
        self.assertTrue(metrics[metrics.variant.isin(["P2", "P3", "P4", "P5"])].policy_version.notna().all())
        selected = select_policy(metrics, {"max_review_rate": .10, "max_block_rate": .20, "max_legitimate_block_rate": .20, "allowed_priority_methods": ["SCORE_ONLY", "EXPOSURE_WEIGHTED_RANK", "GRAPH_NOVELTY"], "amount_priority_enabled": True}, "minimize_total_simulated_cost")
        self.assertIsNotNone(selected)
        config = PolicyConfig(selected.policy_version, float(selected.review_threshold), float(selected.block_threshold), float(selected.review_capacity), str(selected.priority_method))
        decisions = decide(confirm.drop(columns=["fraud_label"]), config, False)
        evaluated = evaluate_decisions(decisions, confirm[["source_row_id", "fraud_label"]], assumptions)
        self.assertGreater(evaluated["transactions"], 0)
        self.assertTrue(oot.source_row_id.isin(tune.source_row_id).sum() == 0)
        p0 = confirm.drop(columns=["fraud_label"]).assign(action="ALLOW", candidate_action="ALLOW", review_priority=0.0, reason_codes="")
        paired = weekly_paired_bootstrap(confirm, decisions, p0, assumptions, draws=500)
        self.assertEqual(int(paired.draws.iloc[0]), 500)


if __name__ == "__main__":
    unittest.main()
