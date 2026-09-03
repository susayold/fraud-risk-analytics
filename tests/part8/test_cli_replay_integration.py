import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_helpers import fixture_frame


class CliIntegrationTests(unittest.TestCase):
    def test_audit_input_uses_governed_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "monitor.csv"
            report = root / "reports"
            fixture_frame(12, False).to_csv(input_path, index=False)
            env = os.environ.copy()
            env.update({"PART8_ROOT": str(root), "PART8_REPORT_DIR": str(report)})
            result = subprocess.run([sys.executable, "-m", "src.part8.run_part8_pipeline", "audit-input", "--input", str(input_path)], capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((report / "part8_input_audit.json").exists(), True)

