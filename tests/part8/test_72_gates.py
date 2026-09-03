import unittest

from src.part8.validate_part8 import gate_catalog, validate


class GateTests(unittest.TestCase):
    def test_exactly_72_gate_catalog(self):
        self.assertEqual(len(gate_catalog()), 72)

    def test_synthetic_fixture_can_reach_all_pass(self):
        result = validate(synthetic=True)
        self.assertEqual(result.status.value_counts().to_dict(), {"PASS": 72})

