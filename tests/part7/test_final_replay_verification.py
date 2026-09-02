import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.part7.final_replay import load_and_verify_freeze
from src.part7.freeze_policy import freeze_policy


class ReplayVerificationTests(unittest.TestCase):
    def setUp(self):
        self.freeze_path = Path("reports/part7/PART7_POLICY_FREEZE.json")
        self.replay_report = Path("reports/part7/PART7_REPLAY_VERIFICATION.json")
        self.configs = [Path("config/part7/economic_assumptions.yaml"), Path("config/part7/graph_routing_policy.yaml"), Path("config/part7/reason_codes.yaml")]

    def tearDown(self):
        for path in (self.freeze_path, self.replay_report):
            if path.exists(): path.unlink()

    def _make_freeze(self):
        descriptor, filename = tempfile.mkstemp(suffix=".csv")
        import os
        os.close(descriptor)
        score = Path(filename); score.write_text("source_row_id,risk_score\n1,0.9\n", encoding="utf-8")
        self.addCleanup(lambda: score.unlink(missing_ok=True))
        selected = {"policy_version": "TEST_POLICY", "profile": "balanced", "priority_method": "SCORE_ONLY", "review_threshold": .5, "block_threshold": .9, "review_capacity": .01}
        with patch("src.part7.freeze_policy.git_metadata", return_value=("TESTCOMMIT", False)):
            return freeze_policy(selected, self.configs, "TEST_SCORE", "TEST_MODEL", "TEST_CAL", score_path=score, confirmation_scope_hash="CONFIRM_HASH"), score

    def test_replay_finds_config_in_config_part7(self):
        freeze, score = self._make_freeze()
        with patch("src.part7.replay_contract.git_metadata", return_value=("TESTCOMMIT", False)):
            loaded = load_and_verify_freeze(freeze, score_path=score)
        self.assertEqual(loaded["policy_version"], "TEST_POLICY")
        self.assertEqual(json.loads(self.replay_report.read_text(encoding="utf-8"))["status"], "PASS")

    def test_replay_rejects_each_mutated_freeze_hash(self):
        freeze, score = self._make_freeze()
        original = json.loads(freeze.read_text(encoding="utf-8"))
        with patch("src.part7.replay_contract.git_metadata", return_value=("TESTCOMMIT", False)):
            for key in ("review_queue_config_sha256", "action_precedence_sha256", "economic_assumption_sha256", "graph_routing_sha256", "reason_code_sha256", "config_bundle_sha256", "code_tree_hash"):
                mutated = dict(original); mutated[key] = "bad"
                candidate = freeze.with_name(f"mutated_{key}.json"); candidate.write_text(json.dumps(mutated), encoding="utf-8")
                with self.assertRaises(RuntimeError, msg=key):
                    load_and_verify_freeze(candidate, score_path=score)
                candidate.unlink()

    def test_replay_rejects_score_hash_change(self):
        freeze, score = self._make_freeze()
        other = score.with_name("other_score.csv"); other.write_text("different", encoding="utf-8"); self.addCleanup(lambda: other.unlink(missing_ok=True))
        with patch("src.part7.replay_contract.git_metadata", return_value=("TESTCOMMIT", False)), self.assertRaises(RuntimeError):
            load_and_verify_freeze(freeze, score_path=other)


if __name__ == "__main__":
    unittest.main()
