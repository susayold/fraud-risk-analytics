from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "part-9.html").read_text(encoding="utf-8")
JS = (ROOT / "js" / "part-9.js").read_text(encoding="utf-8")


class StatusDimensionSemanticsTests(unittest.TestCase):
    def test_presentation_does_not_mean_all_execution_is_locked(self):
        self.assertIn("PRESENTATION_READY", HTML)
        self.assertIn("PART7_PART8_INPUT_BLOCKED", HTML)
        self.assertIn("presentation_status", JS)
        self.assertIn("execution_summary", JS)

    def test_part7_part8_live_status_is_reconciled(self):
        project = json.loads((ROOT / "assets/data/project_status.json").read_text(encoding="utf-8"))
        part7 = json.loads((ROOT / "assets/data/part7_summary.json").read_text(encoding="utf-8"))
        part8 = json.loads((ROOT / "assets/data/part8_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(project["layers"]["part7"]["status"], part7["status"])
        self.assertEqual(project["layers"]["part8"]["status"], part8["status"])
        self.assertIn("SOURCE MISMATCH", JS)


if __name__ == "__main__":
    unittest.main()
