import subprocess
import tempfile
import unittest
from pathlib import Path

from src.part7.lifecycle import assert_transition, can_lock
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
        self.assertTrue(can_lock(gates_pass=64, gates_blocked=0, gates_fail=0, replay_status="FINAL_REPLAY_COMPLETE"))
        self.assertFalse(can_lock(gates_pass=63, gates_blocked=1, gates_fail=0, replay_status="FINAL_REPLAY_COMPLETE"))

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


if __name__ == "__main__":
    unittest.main()
