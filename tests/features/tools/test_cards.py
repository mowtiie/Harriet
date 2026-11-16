"""Tests for the dice and choice cards."""

import unittest

from discord import ui

from features.tools.cards import build_choose_card, build_roll_card
from features.tools.dice import DiceRoll, RollResult


def texts_in(view: ui.LayoutView) -> list[str]:
    return [item.content for item in view.walk_children() if isinstance(item, ui.TextDisplay)]


class RollCardTests(unittest.TestCase):
    def test_a_single_die_shows_the_total_and_the_dice(self) -> None:
        card = build_roll_card(DiceRoll(1, 20, 0), RollResult(14, None))
        self.assertEqual(texts_in(card), ["### 🎲 Dice roll", "## 14", "-# d20"])

    def test_several_dice_show_what_added_up(self) -> None:
        card = build_roll_card(DiceRoll(2, 6, 3), RollResult(10, "4 + 3 + 3"))
        self.assertEqual(texts_in(card)[1:], ["## 10", "-# 2d6+3 · 4 + 3 + 3"])

    def test_the_card_never_repeats_what_the_user_typed(self) -> None:
        card = build_roll_card(DiceRoll(1, 20, 0), RollResult(3, None))
        self.assertNotIn("@everyone", "".join(texts_in(card)))


class ChooseCardTests(unittest.TestCase):
    def test_the_card_shows_the_options_and_the_pick(self) -> None:
        card = build_choose_card(["pizza", "sushi", "tacos"], "sushi")
        expected = [
            "### 🎯 Choose",
            "> pizza · sushi · tacos",
            "## sushi",
            "-# Picked from 3 options",
        ]
        self.assertEqual(texts_in(card), expected)

    def test_options_with_line_breaks_are_kept_on_one_line(self) -> None:
        card = build_choose_card(["a\nb", "c"], "a\nb")
        self.assertIn("> a b · c", texts_in(card))
        self.assertIn("## a b", texts_in(card))

    def test_very_long_options_are_cut_so_the_card_still_sends(self) -> None:
        options = ["x" * 600 for _ in range(25)]
        card = build_choose_card(options, options[0])
        self.assertLess(sum(len(text) for text in texts_in(card)), 4000)


if __name__ == "__main__":
    unittest.main()
