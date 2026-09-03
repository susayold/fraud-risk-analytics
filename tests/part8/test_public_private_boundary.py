import unittest
import tempfile
from pathlib import Path
import pandas as pd

from src.part8.public_export import export_aggregate


class BoundaryTests(unittest.TestCase):
    def test_public_export_rejects_row_level_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                export_aggregate(pd.DataFrame({"risk_score": [0.2]}), Path(tmp) / "bad.csv")

