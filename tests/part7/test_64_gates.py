import unittest

from src.part7.validate_part7 import GATE_NAMES, validate


class EvidenceGateTests(unittest.TestCase):
    def test_exactly_64_evidence_gates(self):
        self.assertEqual(len(GATE_NAMES), 64)
        frame = validate()
        self.assertEqual(len(frame), 64)
        self.assertIn("evidence_artifact", frame.columns)
        self.assertNotIn("lifecycle", frame.columns)


if __name__ == "__main__":
    unittest.main()
