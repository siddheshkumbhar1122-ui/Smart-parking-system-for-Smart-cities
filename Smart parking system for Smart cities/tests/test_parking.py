import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from server import ParkingState


class ParkingStateTests(unittest.TestCase):
    def setUp(self):
        self.state = ParkingState(3)

    def test_book_and_cancel_available_slot(self):
        ok, _ = self.state.book(1, "Test Driver", "KA 01 AB 1234")
        self.assertTrue(ok)
        self.assertEqual(self.state.snapshot()["slots"][0]["status"], "booked")
        ok, _ = self.state.cancel(1)
        self.assertTrue(ok)
        self.assertEqual(self.state.snapshot()["slots"][0]["status"], "available")

    def test_sensor_updates_slot(self):
        ok, _ = self.state.sensor_event(3, True)
        self.assertTrue(ok)
        self.assertEqual(self.state.snapshot()["slots"][2]["status"], "occupied")

    def test_cannot_book_occupied_slot(self):
        self.state.sensor_event(1, True)
        ok, _ = self.state.book(1, "Test", "TEST")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
