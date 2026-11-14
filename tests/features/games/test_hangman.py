"""Tests for hangman rules, assets and the view."""

import random
import string
import unittest

from discord import ui

from features.games.errors import GameError
from features.games.hangman import MAX_MISSES, HangmanGame
from features.games.hangman_art import STAGES
from features.games.hangman_view import (
    HangmanView,
    gallows_text,
    misses_text,
    status_text,
    word_text,
)
from features.games.hangman_words import WORDS, pick_word
from tests.features.games.test_game_views import RecordingHandler, make_interaction, notes_in

PLAYER, BOT = 1, 3
NAMES = {PLAYER: "Alice", BOT: "Harriet"}


def guess_all(game: HangmanGame, letters: str) -> None:
    for letter in letters:
        game.guess(letter)


def make_view(word: str = "cat", on_finish=None) -> HangmanView:
    return HangmanView(
        HangmanGame(word),
        NAMES,
        player_id=PLAYER,
        bot_id=BOT,
        timeout_seconds=60,
        on_finish=on_finish,
    )


def selects_in(view: HangmanView) -> list[ui.Select]:
    return [item for item in view.walk_children() if isinstance(item, ui.Select)]


class HangmanGameTests(unittest.TestCase):
    def test_correct_guesses_reveal_every_matching_letter(self) -> None:
        game = HangmanGame("balloon")
        game.guess("l")
        game.guess("O")
        self.assertEqual("".join(game.masked_letters), "__LLOO_")

    def test_wrong_guesses_are_tracked_in_order(self) -> None:
        game = HangmanGame("cat")
        guess_all(game, "zq")
        self.assertEqual(game.misses, ("Z", "Q"))
        self.assertFalse(game.is_over)

    def test_guessing_every_letter_wins(self) -> None:
        game = HangmanGame("cat")
        guess_all(game, "cat")
        self.assertTrue(game.is_won)
        self.assertTrue(game.is_over)
        self.assertFalse(game.is_lost)

    def test_too_many_misses_loses(self) -> None:
        game = HangmanGame("cat")
        guess_all(game, "bdefgh")
        self.assertEqual(len(game.misses), MAX_MISSES)
        self.assertTrue(game.is_lost)
        self.assertFalse(game.is_won)

    def test_repeat_and_invalid_guesses_are_refused_without_a_penalty(self) -> None:
        game = HangmanGame("cat")
        game.guess("z")
        for bad in ("z", "1", "ab", ""):
            with self.subTest(guess=bad), self.assertRaises(GameError):
                game.guess(bad)
        self.assertEqual(game.misses, ("Z",))

    def test_no_guesses_after_the_game_is_over(self) -> None:
        game = HangmanGame("a")
        game.guess("a")
        with self.assertRaises(GameError):
            game.guess("b")


class AssetTests(unittest.TestCase):
    def test_there_is_a_drawing_for_every_number_of_misses(self) -> None:
        self.assertEqual(len(STAGES), MAX_MISSES + 1)
        self.assertEqual(len(set(STAGES)), len(STAGES))

    def test_every_word_is_a_distinct_lowercase_word_of_letters(self) -> None:
        self.assertEqual(len(set(WORDS)), len(WORDS))
        for word in WORDS:
            with self.subTest(word=word):
                self.assertTrue(set(word) <= set(string.ascii_lowercase))

    def test_pick_word_comes_from_the_list(self) -> None:
        self.assertIn(pick_word(random.Random(0)), WORDS)


class DisplayTests(unittest.TestCase):
    def test_word_and_misses_text(self) -> None:
        game = HangmanGame("cat")
        guess_all(game, "az")
        self.assertEqual(word_text(game), "`_ A _`")
        self.assertEqual(misses_text(game), "-# Misses 1/6: Z")
        self.assertEqual(misses_text(HangmanGame("cat")), "-# Misses 0/6: none")

    def test_gallows_follows_the_misses(self) -> None:
        game = HangmanGame("cat")
        game.guess("z")
        self.assertIn(STAGES[1], gallows_text(game))

    def test_status_covers_progress_win_loss_and_timeout(self) -> None:
        playing = HangmanGame("cat")
        self.assertEqual(status_text(playing, "Alice", False), "Pick a letter below.")
        self.assertIn("**CAT**", status_text(playing, "Alice", True))
        won = HangmanGame("cat")
        guess_all(won, "cat")
        self.assertEqual(status_text(won, "Alice", False), "**Alice** guessed it: **CAT**.")
        lost = HangmanGame("cat")
        guess_all(lost, "bdefgh")
        self.assertIn("The word was **CAT**", status_text(lost, "Alice", False))

class HangmanViewTests(unittest.IsolatedAsyncioTestCase):
    def test_two_menus_cover_the_whole_alphabet(self) -> None:
        letters = [option.label for select in selects_in(make_view()) for option in select.options]
        self.assertEqual("".join(letters), string.ascii_uppercase)

    async def test_a_guess_updates_the_game_and_the_message(self) -> None:
        view = make_view()
        interaction = make_interaction(PLAYER)
        await view._guess("c", interaction)
        self.assertEqual(view._game.guessed, ("C",))
        interaction.response.edit_message.assert_awaited_once()

    async def test_guessed_letters_leave_the_menus(self) -> None:
        view = make_view()
        await view._guess("c", make_interaction(PLAYER))
        letters = [option.label for select in selects_in(view) for option in select.options]
        self.assertNotIn("C", letters)
        self.assertEqual(len(letters), 25)

    async def test_an_emptied_menu_is_dropped(self) -> None:
        view = make_view()
        view._game = HangmanGame("abcdefghijklmz")
        for letter in string.ascii_lowercase[:13]:
            await view._guess(letter, make_interaction(PLAYER))
        self.assertFalse(view._game.is_over)
        remaining = selects_in(view)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].options[0].label, "N")

    async def test_repeat_guess_is_refused_privately(self) -> None:
        view = make_view()
        await view._guess("z", make_interaction(PLAYER))
        again = make_interaction(PLAYER)
        await view._guess("z", again)
        self.assertTrue(again.response.send_message.await_args.kwargs["ephemeral"])

    async def test_winning_reports_the_player_and_shows_the_note(self) -> None:
        handler = RecordingHandler()
        view = make_view("cat", on_finish=handler)
        for letter in "ca":
            await view._guess(letter, make_interaction(PLAYER))
        self.assertEqual(handler.winners, [])
        await view._guess("t", make_interaction(PLAYER))
        self.assertEqual(handler.winners, [PLAYER])
        self.assertTrue(view.is_finished())
        self.assertIn("-# +50 XP", notes_in(view))
        self.assertEqual(selects_in(view), [])

    async def test_losing_reports_the_bot(self) -> None:
        handler = RecordingHandler(note=None)
        view = make_view("cat", on_finish=handler)
        for letter in "bdefgh":
            await view._guess(letter, make_interaction(PLAYER))
        self.assertEqual(handler.winners, [BOT])

    async def test_only_the_player_may_use_the_menus(self) -> None:
        view = make_view()
        self.assertTrue(await view.interaction_check(make_interaction(PLAYER)))
        self.assertFalse(await view.interaction_check(make_interaction(BOT)))


if __name__ == "__main__":
    unittest.main()
