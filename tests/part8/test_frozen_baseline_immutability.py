import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.part8.baseline import build_baseline
from src.part8.freeze_monitoring import freeze_monitoring, verify_freeze
from test_helpers import fixture_frame


class FrozenBaselineTests(unittest.TestCase):
    def test_mutating_frozen_distribution_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, report = Path(tmp) / "repo", Path(tmp) / "reports"
            (root / "src").mkdir(parents=True); (root / "config").mkdir(parents=True)
            shutil.copytree(Path("src/part8"), root / "src/part8"); shutil.copytree(Path("config/part8"), root / "config/part8")
            threshold = root / "config/part8/alert_thresholds.yaml"
            threshold.write_text(threshold.read_text().replace("final_numbers_frozen: false", "final_numbers_frozen: true").replace("amber: null, red: null", "amber: 0.01, red: 0.05"), encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True); subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True); subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True); subprocess.run(["git", "add", "."], cwd=root, check=True); subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
            with patch("src.part8.baseline.ROOT", root), patch("src.part8.baseline.REPORT_DIR", report):
                build_baseline(fixture_frame(40))
            freeze_monitoring(root, report)
            feature = report / "reference_feature_distributions.json"
            payload = json.loads(feature.read_text()); payload["feature_names"] = payload["feature_names"] + ["tampered"]
            feature.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                verify_freeze(root, report)

