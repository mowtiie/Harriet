"""Tests for dice notation and random choices."""

import random
import unittest

from features.tools.choices import MAX_CHOICES, split_choices
from features.tools.dice import (
    MAX_DICE,
    MAX_MODIFIER,
    MAX_ROLLS_SHOWN,
    MAX_SIDES,
    DiceRoll,
    RollResult,
    parse_dice,
    roll_dice,
    summarize_roll,
)


class ParseDiceTests(unittest.TestCase):
    def test_reads_count_sides_and_modifier(self) -> None:
        self.assertEqual(parse_dice("4d8+3"), DiceRoll(4, 8, 3))
        self.assertEqual(parse_dice("2d6-1"), DiceRoll(2, 6, -1))

    def test_count_defaults_to_one_and_input_is_forgiving(self) -> None:
        self.assertEqual(parse_dice("D20"), DiceRoll(1, 20, 0))
        self.assertEqual(parse_dice(" 2d6 + 3 "), DiceRoll(2, 6, 3))

    def test_rejects_unreadable_text(self) -> None:
        for text in ("", "20", "d", "2d", "dd6", "2d6+", "abc"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_dice(text)

    def test_rejects_values_outside_the_limits(self) -> None:
        for text in (
            "0d6",
            f"{MAX_DICE + 1}d6",
            "d1",
            f"d{MAX_SIDES + 1}",
            f"d6+{MAX_MODIFIER + 1}",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_dice(text)


class RollDiceTests(unittest.TestCase):
    def test_rolls_stay_within_the_sides(self) -> None:
        rolls = roll_dice(DiceRoll(50, 6, 0), random.Random(1))
        self.assertEqual(len(rolls), 50)
        self.assertTrue(all(1 <= roll <= 6 for roll in rolls))

    def test_same_seed_gives_same_rolls(self) -> None:
        dice = DiceRoll(5, 20, 0)
        self.assertEqual(roll_dice(dice, random.Random(7)), roll_dice(dice, random.Random(7)))


class SummarizeRollTests(unittest.TestCase):
    def test_single_die_has_nothing_to_break_down(self) -> None:
        self.assertEqual(summarize_roll(DiceRoll(1, 20, 0), [14]), RollResult(14, None))

    def test_multiple_dice_show_each_roll(self) -> None:
        self.assertEqual(summarize_roll(DiceRoll(2, 6, 0), [4, 2]), RollResult(6, "4 + 2"))

    def test_modifier_is_added_and_shown(self) -> None:
        self.assertEqual(summarize_roll(DiceRoll(2, 6, 3), [4, 2]), RollResult(9, "4 + 2 + 3"))
        self.assertEqual(summarize_roll(DiceRoll(1, 20, -2), [10]), RollResult(8, "10 - 2"))

    def test_long_roll_lists_are_truncated(self) -> None:
        rolls = [1] * (MAX_ROLLS_SHOWN + 5)
        result = summarize_roll(DiceRoll(len(rolls), 6, 0), rolls)
        self.assertEqual(result.total, len(rolls))
        self.assertTrue(result.breakdown.endswith(" + ..."))
        self.assertEqual(result.breakdown.count("1"), MAX_ROLLS_SHOWN)


class NotationTests(unittest.TestCase):
    def test_notation_is_written_the_usual_way(self) -> None:
        self.assertEqual(DiceRoll(1, 20, 0).notation, "d20")
        self.assertEqual(DiceRoll(2, 6, 3).notation, "2d6+3")
        self.assertEqual(DiceRoll(4, 8, -1).notation, "4d8-1")

    def test_notation_reads_back_to_the_same_roll(self) -> None:
        for dice in (DiceRoll(1, 20, 0), DiceRoll(2, 6, 3), DiceRoll(4, 8, -1)):
            self.assertEqual(parse_dice(dice.notation), dice)


class SplitChoicesTests(unittest.TestCase):
    def test_splits_on_commas_and_trims(self) -> None:
        self.assertEqual(split_choices(" pizza ,sushi, tacos "), ["pizza", "sushi", "tacos"])

    def test_ignores_empty_options(self) -> None:
        self.assertEqual(split_choices("a,,b,"), ["a", "b"])

    def test_needs_at_least_two_options(self) -> None:
        for text in ("", "only one", "a,,"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                split_choices(text)

    def test_rejects_too_many_options(self) -> None:
        with self.assertRaises(ValueError):
            split_choices(",".join(str(i) for i in range(MAX_CHOICES + 1)))


if __name__ == "__main__":
    unittest.main()
