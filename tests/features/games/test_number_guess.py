"""Tests for the number guessing game and its view."""

import random
import unittest
from unittest import mock

from features.games.errors import GameError
from features.games.game_view import solo_winner_id
from features.games.number_guess import (
    MAX_GUESSES,
    MAX_NUMBER,
    MIN_NUMBER,
    Hint,
    NumberGuessGame,
    parse_guess,
    pick_number,
)
from features.games.number_guess_view import (
    GuessModal,
    NumberGuessView,
    attempts_text,
    guesses_phrase,
    status_text,
)
from tests.features.games.test_game_views import RecordingHandler, make_interaction, notes_in

PLAYER, BOT = 1, 3
NAMES = {PLAYER: "Alice", BOT: "Harriet"}
SECRET = 42


def make_view(on_finish=None) -> NumberGuessView:
    return NumberGuessView(
        NumberGuessGame(SECRET),
        NAMES,
        player_id=PLAYER,
        bot_id=BOT,
        timeout_seconds=60,
        on_finish=on_finish,
    )


class ParseGuessTests(unittest.TestCase):
    def test_accepts_whole_numbers_with_surrounding_spaces(self) -> None:
        self.assertEqual(parse_guess(" 42 "), 42)

    def test_rejects_anything_else(self) -> None:
        for text in ("", "abc", "4.5", "-3", "1e2", "²"):
            with self.subTest(text=text), self.assertRaises(GameError):
                parse_guess(text)

    def test_pick_number_stays_in_range(self) -> None:
        rng = random.Random(0)
        picks = {pick_number(rng) for _ in range(500)}
        self.assertTrue(all(MIN_NUMBER <= pick <= MAX_NUMBER for pick in picks))


class NumberGuessGameTests(unittest.TestCase):
    def test_hints_point_towards_the_secret(self) -> None:
        game = NumberGuessGame(SECRET)
        self.assertIs(game.guess(10), Hint.TOO_LOW)
        self.assertIs(game.guess(90), Hint.TOO_HIGH)
        self.assertIs(game.guess(SECRET), Hint.CORRECT)

    def test_range_narrows_with_each_hint(self) -> None:
        game = NumberGuessGame(SECRET)
        self.assertEqual((game.lowest_possible, game.highest_possible), (1, 100))
        game.guess(10)
        game.guess(90)
        game.guess(30)
        game.guess(60)
        self.assertEqual((game.lowest_possible, game.highest_possible), (31, 59))

    def test_a_correct_guess_wins(self) -> None:
        game = NumberGuessGame(SECRET)
        game.guess(SECRET)
        self.assertTrue(game.is_won)
        self.assertTrue(game.is_over)
        self.assertFalse(game.is_lost)

    def test_running_out_of_guesses_loses(self) -> None:
        game = NumberGuessGame(SECRET)
        for number in range(1, MAX_GUESSES + 1):
            game.guess(number)
        self.assertEqual(game.guesses_left, 0)
        self.assertTrue(game.is_lost)
        self.assertFalse(game.is_won)

    def test_winning_on_the_last_guess_is_not_a_loss(self) -> None:
        game = NumberGuessGame(SECRET)
        for number in range(1, MAX_GUESSES):
            game.guess(number)
        game.guess(SECRET)
        self.assertTrue(game.is_won)
        self.assertFalse(game.is_lost)

    def test_invalid_guesses_cost_nothing(self) -> None:
        game = NumberGuessGame(SECRET)
        game.guess(10)
        for bad in (0, 101, -5, 10):
            with self.subTest(guess=bad), self.assertRaises(GameError):
                game.guess(bad)
        self.assertEqual(game.guesses_left, MAX_GUESSES - 1)

    def test_no_guesses_after_the_game_is_over(self) -> None:
        game = NumberGuessGame(SECRET)
        game.guess(SECRET)
        with self.assertRaises(GameError):
            game.guess(1)

    def test_the_best_strategy_always_wins_within_the_limit(self) -> None:
        for secret in range(MIN_NUMBER, MAX_NUMBER + 1):
            game = NumberGuessGame(secret)
            while not game.is_over:
                game.guess((game.lowest_possible + game.highest_possible) // 2)
            self.assertTrue(game.is_won, secret)


class DisplayTests(unittest.TestCase):
    def test_attempts_text(self) -> None:
        game = NumberGuessGame(SECRET)
        self.assertEqual(attempts_text(game), "-# No guesses yet.")
        game.guess(10)
        game.guess(90)
        self.assertEqual(attempts_text(game), "`10` Too low\n`90` Too high")

    def test_guesses_phrase_is_singular_once(self) -> None:
        self.assertEqual(guesses_phrase(1), "1 guess")
        self.assertEqual(guesses_phrase(3), "3 guesses")

    def test_status_covers_progress_win_loss_and_timeout(self) -> None:
        game = NumberGuessGame(SECRET)
        game.guess(10)
        self.assertEqual(
            status_text(game, "Alice", False), "It's between **11** and **100**. 7 guesses left."
        )
        self.assertIn("Timed out", status_text(game, "Alice", True))
        game.guess(SECRET)
        self.assertEqual(
            status_text(game, "Alice", False), "**Alice** got it: **42**, in 2 guesses."
        )
        lost = NumberGuessGame(SECRET)
        for number in range(1, MAX_GUESSES + 1):
            lost.guess(number)
        self.assertEqual(
            status_text(lost, "Alice", False), "Out of guesses. The number was **42**."
        )

    def test_solo_winner_id_maps_the_result(self) -> None:
        self.assertEqual(solo_winner_id(True, False, PLAYER, BOT), PLAYER)
        self.assertEqual(solo_winner_id(False, True, PLAYER, BOT), BOT)
        self.assertIsNone(solo_winner_id(False, False, PLAYER, BOT))


class NumberGuessViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_guess_updates_the_game_and_the_message(self) -> None:
        view = make_view()
        interaction = make_interaction(PLAYER)
        await view.submit_guess("10", interaction)
        self.assertEqual(view._game.attempts[0].number, 10)
        interaction.response.edit_message.assert_awaited_once()
        self.assertFalse(view.is_finished())

    async def test_bad_input_is_refused_privately_and_costs_nothing(self) -> None:
        view = make_view()
        for text in ("abc", "0", "500"):
            interaction = make_interaction(PLAYER)
            await view.submit_guess(text, interaction)
            self.assertTrue(interaction.response.send_message.await_args.kwargs["ephemeral"])
        self.assertEqual(view._game.guesses_left, MAX_GUESSES)

    async def test_a_repeat_guess_is_refused(self) -> None:
        view = make_view()
        await view.submit_guess("10", make_interaction(PLAYER))
        again = make_interaction(PLAYER)
        await view.submit_guess("10", again)
        self.assertIn("already", again.response.send_message.await_args.args[0])

    async def test_winning_reports_the_player_and_shows_the_note(self) -> None:
        handler = RecordingHandler()
        view = make_view(on_finish=handler)
        await view.submit_guess("10", make_interaction(PLAYER))
        self.assertEqual(handler.winners, [])
        await view.submit_guess(str(SECRET), make_interaction(PLAYER))
        self.assertEqual(handler.winners, [PLAYER])
        self.assertTrue(view.is_finished())
        self.assertIn("-# +50 XP", notes_in(view))

    async def test_losing_reports_the_bot(self) -> None:
        handler = RecordingHandler(note=None)
        view = make_view(on_finish=handler)
        for number in range(1, MAX_GUESSES + 1):
            await view.submit_guess(str(number), make_interaction(PLAYER))
        self.assertEqual(handler.winners, [BOT])

    async def test_pressing_the_button_opens_the_form(self) -> None:
        view = make_view()
        interaction = make_interaction(PLAYER)
        interaction.response.send_modal = mock.AsyncMock()
        await view._on_press(interaction)
        modal = interaction.response.send_modal.await_args.args[0]
        self.assertIsInstance(modal, GuessModal)

    async def test_submitting_the_form_forwards_the_typed_text(self) -> None:
        received = []

        async def record(text, interaction) -> None:
            received.append(text)

        modal = GuessModal(record)
        modal._input._value = "37"
        await modal.on_submit(make_interaction(PLAYER))
        self.assertEqual(received, ["37"])

    async def test_only_the_player_may_press(self) -> None:
        view = make_view()
        self.assertTrue(await view.interaction_check(make_interaction(PLAYER)))
        self.assertFalse(await view.interaction_check(make_interaction(BOT)))


if __name__ == "__main__":
    unittest.main()
