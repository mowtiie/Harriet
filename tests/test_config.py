"""Tests for config parsing helpers."""

import unittest

from config import ConfigError, parse_choice, parse_positive_int


class ParseChoiceTests(unittest.TestCase):
    def test_accepts_and_lowercases_valid_value(self) -> None:
        self.assertEqual(parse_choice("X", " IDLE ", ["online", "idle"]), "idle")

    def test_rejects_unknown_value(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            parse_choice("BOT_STATUS", "away", ["online", "idle"])
        self.assertIn("BOT_STATUS", str(caught.exception))


class ParsePositiveIntTests(unittest.TestCase):
    def test_accepts_positive_integer(self) -> None:
        self.assertEqual(parse_positive_int("X", "25"), 25)

    def test_rejects_non_integer(self) -> None:
        with self.assertRaises(ConfigError):
            parse_positive_int("X", "many")

    def test_rejects_zero_and_negative(self) -> None:
        for raw in ("0", "-3"):
            with self.subTest(raw=raw), self.assertRaises(ConfigError):
                parse_positive_int("X", raw)


if __name__ == "__main__":
    unittest.main()
