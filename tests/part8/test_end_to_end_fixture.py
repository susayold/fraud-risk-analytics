import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.part8.baseline import build_baseline
from src.part8.freeze_monitoring import freeze_monitoring
from src.part8.label_maturity import build_operational_view, build_matured_outcome_view
from src.part8.lifecycle import assert_transition
from src.part8.replay_monitoring import replay
from src.part8.windowing import assign_windows
from test_helpers import fixture_frame


class EndToEndFixtureTests(unittest.TestCase):
    def test_software_lifecycle_reaches_lock_without_publicing_fixture(self):
        frame = assign_windows(fixture_frame(120))
        build_operational_view(frame.drop(columns=["fraud_label"]))
        build_matured_outcome_view(frame)
        states = ["INPUT_BLOCKED", "MONITORING_FRAMEWORK_READY", "BASELINE_READY", "MONITORING_BASELINE_FROZEN", "MONITORING_REPLAY_COMPLETE", "MONITORING_GOVERNANCE_LOCKED"]
        for current, target in zip(states, states[1:]): assert_transition(current, target)

    def test_fixture_runs_baseline_freeze_replay_in_temp_workspace(self):
        frame = fixture_frame(120)
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp) / "repo"
            temp_report = Path(tmp) / "reports"
            (temp_root / "src").mkdir(parents=True)
            (temp_root / "config").mkdir(parents=True)
            shutil.copytree(Path("src/part8"), temp_root / "src/part8")
            shutil.copytree(Path("config/part8"), temp_root / "config/part8")
            threshold_path = temp_root / "config/part8/alert_thresholds.yaml"
            threshold_path.write_text(threshold_path.read_text(encoding="utf-8").replace("final_numbers_frozen: false", "final_numbers_frozen: true").replace("amber: null, red: null", "amber: 0.01, red: 0.05"), encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=temp_root, check=True)
            subprocess.run(["git", "config", "user.email", "part8-test@example.invalid"], cwd=temp_root, check=True)
            subprocess.run(["git", "config", "user.name", "Part 8 Test"], cwd=temp_root, check=True)
            subprocess.run(["git", "add", "."], cwd=temp_root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture baseline"], cwd=temp_root, check=True)
            with patch("src.part8.io.ROOT", temp_root), patch("src.part8.io.REPORT_DIR", temp_report), patch("src.part8.baseline.ROOT", temp_root), patch("src.part8.baseline.REPORT_DIR", temp_report), patch("src.part8.replay_monitoring.ROOT", temp_root), patch("src.part8.replay_monitoring.REPORT_DIR", temp_report):
                baseline = build_baseline(frame)
                self.assertTrue(baseline["baseline_id"].startswith("P8_BASELINE_"))
                frozen = freeze_monitoring(temp_root, temp_report)
                self.assertEqual(frozen["status"], "MONITORING_BASELINE_FROZEN")
                threshold_hash = threshold_path.read_bytes()
                replayed = replay(frame, temp_report / "PART8_MONITORING_BASELINE_FREEZE.json", thresholds={"score_js": {"amber": 0.01, "red": 0.05, "min_support": 1}})
                self.assertEqual(replayed["status"], "MONITORING_REPLAY_COMPLETE")
                self.assertTrue((temp_report / "alert_log.csv").exists())
                self.assertEqual(threshold_path.read_bytes(), threshold_hash)
            self.assertFalse((Path("reports") / "part8" / "reference_baseline_metadata.json").exists())
