import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.part7.contracts import PolicyConfig
from src.part7.economics import EconomicAssumptions
from src.part7.exposure import add_exposure_bases
from src.part7.decision_runtime import decide
from src.part7.graph_routing import load_graph_weights
from src.part7.run_part7_pipeline import _write_final_oot_evidence


class FinalOotEvidenceTests(unittest.TestCase):
    def test_replay_writes_dedicated_final_oot_namespace(self):
        with tempfile.TemporaryDirectory() as folder:
            report_dir = Path(folder) / "reports" / "part7"
            raw = pd.DataFrame([
                {"source_row_id": 1, "transaction_timestamp": "2026-01-01T00:00:00Z", "risk_score": .95, "amount": 100.0, "fraud_label": 1, "split_name": "FINAL_OOT", "pair_new": True, "channel": "ONLINE"},
                {"source_row_id": 2, "transaction_timestamp": "2026-01-01T01:00:00Z", "risk_score": .10, "amount": 50.0, "fraud_label": 0, "split_name": "FINAL_OOT", "pair_new": False, "channel": "CHIP"},
            ])
            oot = add_exposure_bases(raw)
            actions = decide(oot.drop(columns=["fraud_label"]), PolicyConfig("TEST", .5, .9, .5), False)
            assumptions = EconomicAssumptions(.7, .95, 1, .8, .01, .5, .05, .05)
            weights = load_graph_weights(Path("config/part7/graph_routing_policy.yaml"))
            with patch("src.part7.run_part7_pipeline.REPORT_DIR", report_dir):
                metrics = _write_final_oot_evidence(oot, actions, assumptions, {"freeze_id": "TEST_FREEZE"}, weights)
            final_dir = report_dir / "final_oot"
            self.assertEqual(metrics["transactions"], 2)
            for name in ("final_oot_policy_metrics.csv", "final_oot_action_summary.csv", "final_oot_review_capacity_by_day.csv", "final_oot_daily_reconciliation.json", "final_oot_segment_reconciliation.json", "final_oot_delta_reconciliation.json", "final_oot_bootstrap_policy_ci.csv"):
                self.assertTrue((final_dir / name).exists(), name)
            self.assertFalse((report_dir / "bootstrap_policy_ci.csv").exists())


if __name__ == "__main__":
    unittest.main()
