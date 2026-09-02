import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.part7.final_replay import load_and_verify_freeze
from src.part7.freeze_policy import freeze_policy
from src.part7.io import write_json


class ReplayVerificationTests(unittest.TestCase):
    def setUp(self):
        self.freeze_path = Path("reports/part7/PART7_POLICY_FREEZE.json")
        self.replay_report = Path("reports/part7/PART7_REPLAY_VERIFICATION.json")
        self.selected_path = Path("reports/part7/PART7_SELECTED_POLICY.json")
        self.manifest_path = Path("reports/part7/P7_CONFIRMATION_SCOPE_MANIFEST.json")
        self.configs = [Path("config/part7/economic_assumptions.yaml"), Path("config/part7/graph_routing_policy.yaml"), Path("config/part7/reason_codes.yaml")]

    def tearDown(self):
        for path in (self.freeze_path, self.replay_report, self.selected_path, self.manifest_path):
            if path.exists(): path.unlink()

    def _make_freeze(self, priority_method="SCORE_ONLY"):
        descriptor, filename = tempfile.mkstemp(suffix=".csv")
        import os
        os.close(descriptor)
        score = Path(filename); score.write_text("source_row_id,risk_score\n1,0.9\n", encoding="utf-8")
        self.addCleanup(lambda: score.unlink(missing_ok=True))
        selected = {"policy_version": "TEST_POLICY", "profile": "balanced", "priority_method": priority_method, "review_threshold": .5, "block_threshold": .9, "review_capacity": .01}
        write_json(self.selected_path, selected)
        write_json(self.manifest_path, {"scope": "P7_POLICY_CONFIRM", "confirmation_scope_hash": "CONFIRM_HASH"})
        self.addCleanup(lambda: self.selected_path.unlink(missing_ok=True))
        self.addCleanup(lambda: self.manifest_path.unlink(missing_ok=True))
        with patch("src.part7.freeze_policy.git_metadata", return_value=("TESTCOMMIT", False)):
            return freeze_policy(selected, self.configs, "TEST_SCORE", "TEST_MODEL", "TEST_CAL", score_status="PROBABILITY_USABLE", score_path=score, confirmation_scope_hash="CONFIRM_HASH", selected_policy_path=self.selected_path, confirmation_manifest_path=self.manifest_path), score

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

    def test_replay_rejects_confirmation_manifest_mutation(self):
        freeze, score = self._make_freeze()
        self.manifest_path.write_text('{"scope":"P7_POLICY_CONFIRM","confirmation_scope_hash":"CONFIRM_HASH","tampered":true}\n', encoding="utf-8")
        with patch("src.part7.replay_contract.git_metadata", return_value=("TESTCOMMIT", False)), self.assertRaises(RuntimeError):
            load_and_verify_freeze(freeze, score_path=score)

    def test_replay_rejects_confirmation_scope_hash_mismatch(self):
        freeze, score = self._make_freeze()
        self.manifest_path.write_text('{"scope":"P7_POLICY_CONFIRM","confirmation_scope_hash":"OTHER_HASH"}\n', encoding="utf-8")
        with patch("src.part7.replay_contract.git_metadata", return_value=("TESTCOMMIT", False)), self.assertRaises(RuntimeError):
            load_and_verify_freeze(freeze, score_path=score)

    def test_ranking_only_freeze_allows_null_calibration(self):
        freeze, score = self._make_freeze_ranking("SCORE_ONLY")
        with patch("src.part7.replay_contract.git_metadata", return_value=("TESTCOMMIT", False)):
            loaded = load_and_verify_freeze(freeze, score_path=score)
        self.assertEqual(loaded["score_status"], "RANKING_ONLY")
        self.assertIsNone(loaded["calibration_version"])

    def test_probability_score_allows_expected_value_priority(self):
        freeze, score = self._make_freeze("EXPOSURE_WEIGHTED_PROBABILITY")
        with patch("src.part7.replay_contract.git_metadata", return_value=("TESTCOMMIT", False)):
            loaded = load_and_verify_freeze(freeze, score_path=score)
        self.assertEqual(loaded["priority_method"], "EXPOSURE_WEIGHTED_PROBABILITY")

    def test_ranking_only_rejects_probability_priority(self):
        with self.assertRaises(ValueError):
            self._make_freeze_ranking("EXPOSURE_WEIGHTED_PROBABILITY")

    def _make_freeze_ranking(self, priority_method):
        descriptor, filename = tempfile.mkstemp(suffix=".csv")
        import os
        os.close(descriptor)
        score = Path(filename); score.write_text("source_row_id,risk_score\n1,0.9\n", encoding="utf-8")
        self.addCleanup(lambda: score.unlink(missing_ok=True))
        selected = {"policy_version": "TEST_RANKING", "profile": "balanced", "priority_method": priority_method, "review_threshold": .5, "block_threshold": .9, "review_capacity": .01}
        write_json(self.selected_path, selected)
        write_json(self.manifest_path, {"scope": "P7_POLICY_CONFIRM", "confirmation_scope_hash": "CONFIRM_HASH"})
        self.addCleanup(lambda: self.selected_path.unlink(missing_ok=True))
        self.addCleanup(lambda: self.manifest_path.unlink(missing_ok=True))
        with patch("src.part7.freeze_policy.git_metadata", return_value=("TESTCOMMIT", False)):
            return freeze_policy(selected, self.configs, "TEST_RANKING_SCORE", "TEST_MODEL", None, score_status="RANKING_ONLY", score_path=score, confirmation_scope_hash="CONFIRM_HASH", selected_policy_path=self.selected_path, confirmation_manifest_path=self.manifest_path), score


if __name__ == "__main__":
    unittest.main()
