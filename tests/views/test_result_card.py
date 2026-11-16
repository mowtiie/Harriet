"""Tests for the shared result card."""

import unittest

from discord import ui

from views.result_card import (
    ELLIPSIS,
    MAX_ANSWER_LENGTH,
    MAX_QUOTE_LENGTH,
    build_result_card,
    quote_block,
    shorten,
)
from views.style import ACCENT_COLOR

TEXT_DISPLAY_LIMIT = 4000
COMPONENT_LIMIT = 40


def texts_in(view: ui.LayoutView) -> list[str]:
    return [item.content for item in view.walk_children() if isinstance(item, ui.TextDisplay)]


class ShortenTests(unittest.TestCase):
    def test_short_text_is_unchanged(self) -> None:
        self.assertEqual(shorten("hello", 10), "hello")
        self.assertEqual(shorten("x" * 10, 10), "x" * 10)

    def test_long_text_is_cut_to_exactly_the_limit_with_an_ellipsis(self) -> None:
        shortened = shorten("x" * 50, 10)
        self.assertEqual(len(shortened), 10)
        self.assertTrue(shortened.endswith(ELLIPSIS))


class QuoteBlockTests(unittest.TestCase):
    def test_every_line_gets_a_quote_marker(self) -> None:
        self.assertEqual(quote_block("one\ntwo"), "> one\n> two")


class BuildResultCardTests(unittest.TestCase):
    def test_a_card_has_a_title_a_divider_and_a_large_answer(self) -> None:
        card = build_result_card("🪙 Coin flip", "Heads")
        self.assertEqual(texts_in(card), ["### 🪙 Coin flip", "## Heads"])
        self.assertEqual(len([i for i in card.walk_children() if isinstance(i, ui.Separator)]), 1)

    def test_the_question_is_quoted_above_the_answer(self) -> None:
        card = build_result_card("Ask", "Yes.", quote="Will it rain?")
        self.assertEqual(texts_in(card), ["### Ask", "> Will it rain?", "## Yes."])

    def test_notes_become_small_print_below_the_answer(self) -> None:
        card = build_result_card("Roll", "7", notes=["2d6", "3 + 4"])
        self.assertEqual(texts_in(card)[-1], "-# 2d6\n-# 3 + 4")

    def test_without_a_quote_or_notes_there_is_nothing_extra(self) -> None:
        self.assertEqual(len(texts_in(build_result_card("T", "A"))), 2)

    def test_the_answer_always_stays_on_one_line(self) -> None:
        card = build_result_card("T", "line one\n\nline   two")
        self.assertEqual(texts_in(card)[-1], "## line one line two")

    def test_a_huge_answer_or_question_is_cut_so_the_card_still_sends(self) -> None:
        card = build_result_card("T", "a" * 5000, quote="q" * 5000, notes=["note"])
        quote, answer = texts_in(card)[1], texts_in(card)[2]
        self.assertLessEqual(len(answer), len("## ") + MAX_ANSWER_LENGTH)
        self.assertLessEqual(len(quote), len("> ") + MAX_QUOTE_LENGTH)
        self.assertLess(sum(len(text) for text in texts_in(card)), TEXT_DISPLAY_LIMIT)

    def test_it_uses_the_bots_accent_colour_and_never_times_out(self) -> None:
        card = build_result_card("T", "A")
        container = next(item for item in card.walk_children() if isinstance(item, ui.Container))
        self.assertEqual(container.accent_colour, ACCENT_COLOR)
        self.assertIsNone(card.timeout)

    def test_the_card_is_small_enough_for_discord(self) -> None:
        card = build_result_card("T", "A", quote="Q", notes=["a", "b"])
        self.assertLessEqual(len(list(card.walk_children())), COMPONENT_LIMIT)


if __name__ == "__main__":
    unittest.main()
