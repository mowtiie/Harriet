"""Tests for duration formatting."""

import unittest
from datetime import timedelta

from core.time_format import format_elapsed


class FormatElapsedTests(unittest.TestCase):
    def test_zero_duration(self) -> None:
        self.assertEqual(format_elapsed(timedelta()), "0s")

    def test_skips_zero_units(self) -> None:
        self.assertEqual(format_elapsed(timedelta(days=1, seconds=3)), "1d 3s")

    def test_shows_at_most_three_units(self) -> None:
        duration = timedelta(days=2, hours=3, minutes=4, seconds=5)
        self.assertEqual(format_elapsed(duration), "2d 3h 4m")


if __name__ == "__main__":
    unittest.main()
