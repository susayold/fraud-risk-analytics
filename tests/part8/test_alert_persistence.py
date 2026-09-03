import unittest

from src.part8.alert_persistence import persistence_status


class PersistenceTests(unittest.TestCase):
    def test_two_of_three_escalates(self):
        self.assertEqual(persistence_status(["RED", "GREEN"], True, "2_of_3"), "RED")

