"""Tests for the 8-ball and coin flip cards."""

import unittest

from discord import ui

from features.games.answer_cards import build_coinflip_card, build_eightball_card


def texts_in(view: ui.LayoutView) -> list[str]:
    return [item.content for item in view.walk_children() if isinstance(item, ui.TextDisplay)]


class AnswerCardTests(unittest.TestCase):
    def test_the_eightball_card_quotes_the_question_and_names_who_asked(self) -> None:
        card = build_eightball_card("Will it rain tomorrow?", "Signs point to yes.", "Alice")
        self.assertEqual(
            texts_in(card),
            [
                "### 🎱 Magic 8-ball",
                "> Will it rain tomorrow?",
                "## Signs point to yes.",
                "-# Asked by Alice",
            ],
        )

    def test_the_coin_flip_card_is_just_the_side(self) -> None:
        self.assertEqual(texts_in(build_coinflip_card("Heads")), ["### 🪙 Coin flip", "## Heads"])


if __name__ == "__main__":
    unittest.main()
