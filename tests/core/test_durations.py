"""Tests for duration parsing."""

import unittest
from datetime import timedelta

from core.durations import parse_duration

MAXIMUM = timedelta(days=28)


class ParseDurationTests(unittest.TestCase):
    def test_single_units(self) -> None:
        self.assertEqual(parse_duration("30s", MAXIMUM), timedelta(seconds=30))
        self.assertEqual(parse_duration("10m", MAXIMUM), timedelta(minutes=10))
        self.assertEqual(parse_duration("2h", MAXIMUM), timedelta(hours=2))
        self.assertEqual(parse_duration("3d", MAXIMUM), timedelta(days=3))
        self.assertEqual(parse_duration("1w", MAXIMUM), timedelta(weeks=1))

    def test_combined_units_ignoring_case_and_spaces(self) -> None:
        self.assertEqual(parse_duration("1H 30m", MAXIMUM), timedelta(hours=1, minutes=30))

    def test_rejects_unreadable_text(self) -> None:
        for text in ("", "soon", "10", "5x", "1h later", "-5m"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_duration(text, MAXIMUM)

    def test_rejects_zero(self) -> None:
        with self.assertRaises(ValueError):
            parse_duration("0m", MAXIMUM)

    def test_rejects_more_than_the_given_maximum(self) -> None:
        self.assertEqual(parse_duration("28d", MAXIMUM), timedelta(days=28))
        with self.assertRaises(ValueError):
            parse_duration("29d", MAXIMUM)
        self.assertEqual(parse_duration("365d", timedelta(days=365)), timedelta(days=365))


if __name__ == "__main__":
    unittest.main()
