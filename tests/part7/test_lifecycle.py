import subprocess
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.part7.lifecycle import assert_transition, can_lock, lock_eligibility
from src.part7.freeze_policy import freeze_policy


class LifecycleTests(unittest.TestCase):
    def test_only_sequential_transitions_are_allowed(self):
        assert_transition("INPUT_BLOCKED", "TECHNICALLY_READY")
        assert_transition("TECHNICALLY_READY", "POLICY_SELECTED")
        with self.assertRaises(ValueError):
            assert_transition("POLICY_SELECTED", "FINAL_REPLAY_COMPLETE")
        with self.assertRaises(ValueError):
            assert_transition("POLICY_FROZEN", "POLICY_SELECTED")

    def test_lock_requires_complete_replay_evidence(self):
        self.assertFalse(can_lock(gates_pass=64, gates_blocked=0, gates_fail=0, replay_status="POLICY_FROZEN"))
        self.assertTrue(can_lock(gates_pass=63, gates_blocked=0, gates_fail=0, replay_status="FINAL_REPLAY_COMPLETE"))
        self.assertFalse(can_lock(gates_pass=63, gates_blocked=1, gates_fail=0, replay_status="FINAL_REPLAY_COMPLETE"))

    def test_gate64_lock_eligibility_is_not_circular(self):
        first_63 = pd.DataFrame({"status": ["PASS"] * 63})
        self.assertTrue(lock_eligibility(first_63, "FINAL_REPLAY_COMPLETE"))
        self.assertFalse(lock_eligibility(first_63, "DECISION_POLICY_LOCKED"))

    def test_real_temporary_git_clean_then_dirty(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
            git("init", "-q")
            git("config", "user.email", "part7-test@example.invalid")
            git("config", "user.name", "Part 7 Test")
            (root / "sentinel.txt").write_text("clean\n", encoding="utf-8")
            git("add", "sentinel.txt")
            git("commit", "-qm", "test: clean lifecycle checkpoint")
            self.assertEqual(git("status", "--porcelain").stdout, "")
            (root / "sentinel.txt").write_text("dirty\n", encoding="utf-8")
            self.assertNotEqual(git("status", "--porcelain").stdout, "")

    def test_freeze_policy_rejects_real_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
            git("init", "-q")
            git("config", "user.email", "part7-test@example.invalid")
            git("config", "user.name", "Part 7 Test")
            (root / "sentinel.txt").write_text("clean\n", encoding="utf-8")
            git("add", "sentinel.txt")
            git("commit", "-qm", "test: clean lifecycle checkpoint")
            (root / "sentinel.txt").write_text("dirty\n", encoding="utf-8")
            selected = {"policy_version": "TEST", "profile": "balanced", "review_threshold": .2, "block_threshold": .8, "review_capacity": .01}
            with self.assertRaisesRegex(RuntimeError, "clean Git worktree"):
                freeze_policy(selected, [], "SCORE", "MODEL", None, score_status="RANKING_ONLY", repo_root=root)

    def test_freeze_policy_succeeds_after_real_commit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report_dir = root / "reports" / "part7"
            selected_path = root / "PART7_SELECTED_POLICY.json"
            manifest_path = root / "P7_CONFIRMATION_SCOPE_MANIFEST.json"
            score_path = root / "score.csv"
            def git(*args):
                return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=True)
            git("init", "-q")
            git("config", "user.email", "part7-test@example.invalid")
            git("config", "user.name", "Part 7 Test")
            selected_path.write_text('{"policy_version":"TEST","profile":"balanced","priority_method":"SCORE_ONLY","review_threshold":0.2,"block_threshold":0.8,"review_capacity":0.01}\n', encoding="utf-8")
            manifest_path.write_text('{"scope":"P7_POLICY_CONFIRM","confirmation_scope_hash":"CONFIRM_HASH"}\n', encoding="utf-8")
            score_path.write_text("source_row_id,risk_score\n1,0.9\n", encoding="utf-8")
            git("add", ".")
            git("commit", "-qm", "test: commit confirmation handoff")
            freeze_path = freeze_policy(
                {"policy_version": "TEST", "profile": "balanced", "priority_method": "SCORE_ONLY", "review_threshold": .2, "block_threshold": .8, "review_capacity": .01},
                [Path("config/part7/economic_assumptions.yaml"), Path("config/part7/graph_routing_policy.yaml"), Path("config/part7/reason_codes.yaml")],
                "SCORE", "MODEL", None, score_status="RANKING_ONLY", score_path=score_path,
                confirmation_scope_hash="CONFIRM_HASH", selected_policy_path=selected_path,
                confirmation_manifest_path=manifest_path, repo_root=root, report_dir=report_dir,
            )
            self.assertTrue(freeze_path.exists())
            # Freeze is permitted to make the repository dirty by writing the
            # immutable record; the clean check applies at freeze entry.
            self.assertNotEqual(git("status", "--porcelain").stdout, "")

    def test_full_synthetic_lifecycle_reaches_locked_state_in_temp_repo(self):
        """Software-only proof of develop -> commit -> freeze -> replay -> lock."""
        with tempfile.TemporaryDirectory() as workspace:
            workspace_path = Path(workspace)
            source_repo = Path(__file__).resolve().parents[2]
            temp_repo = workspace_path / "repo"
            shutil.copytree(source_repo, temp_repo, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
            score_path = workspace_path / "synthetic_score.csv"
            rows = []
            for index in range(180):
                if index < 80:
                    split = "P7_POLICY_TUNE"
                elif index < 140:
                    split = "P7_POLICY_CONFIRM"
                else:
                    split = "FINAL_OOT"
                timestamp = pd.Timestamp("2026-01-01T00:00:00Z") + pd.Timedelta(hours=index)
                fraud = int(index % 9 == 0)
                rows.append({"source_row_id": index + 1, "transaction_timestamp": timestamp.isoformat(), "risk_score": .92 if fraud else .12, "amount": 100.0 + index, "fraud_label": fraud, "split_name": split, "pair_new": index % 5 == 0, "cold_card": index % 11 == 0, "new_merchant": index % 13 == 0, "cross_community": index % 17 == 0, "channel": "ONLINE" if index % 2 else "CHIP"})
            pd.DataFrame(rows).to_csv(score_path, index=False)

            def git(*args):
                return subprocess.run(["git", *args], cwd=temp_repo, text=True, capture_output=True, check=True)

            git("init", "-q")
            git("config", "user.email", "part7-test@example.invalid")
            git("config", "user.name", "Part 7 Test")
            git("add", ".")
            git("commit", "-qm", "test: synthetic clean baseline")

            def run_stage(stage, *extra):
                return subprocess.run(["python", "-m", "src.part7.run_part7_pipeline", stage, "--input", str(score_path), *extra], cwd=temp_repo, text=True, capture_output=True, check=False)

            developed = run_stage("develop", "--score-status", "RANKING_ONLY", "--score-version", "TEST_SCORE_V1", "--model-version", "TEST_MODEL_V1", "--profile", "balanced")
            self.assertEqual(developed.returncode, 0, developed.stderr + developed.stdout)
            git("add", "reports", "assets")
            git("commit", "-qm", "test: commit synthetic confirmation evidence")
            frozen = run_stage("freeze")
            self.assertEqual(frozen.returncode, 0, frozen.stderr + frozen.stdout)
            self.assertTrue((temp_repo / "reports/part7/PART7_FREEZE_VERIFICATION.json").exists())
            replayed = run_stage("replay")
            self.assertEqual(replayed.returncode, 0, replayed.stderr + replayed.stdout)
            summary = json.loads((temp_repo / "reports/part7/PART7_FINAL_SUMMARY.json").read_text(encoding="utf-8"))
            validation = pd.read_csv(temp_repo / "reports/part7/part7_validation_report.csv")
            counts = validation.status.value_counts().to_dict()
            failures = validation.loc[validation.status == "FAIL", ["check_name", "observed_value"]].to_dict("records")
            self.assertEqual(summary["status"], "DECISION_POLICY_LOCKED", f"summary={summary}; validation={counts}; failures={failures}")
            self.assertEqual((validation.status == "PASS").sum(), 64)
            self.assertEqual((validation.status == "BLOCKED").sum(), 0)
            self.assertEqual((validation.status == "FAIL").sum(), 0)
            self.assertTrue((temp_repo / "reports/part7/final_oot/final_oot_bootstrap_policy_ci.csv").exists())


if __name__ == "__main__":
    unittest.main()
