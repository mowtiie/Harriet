"""Tests for minesweeper rules and the view."""

import random
import unittest
from unittest import mock

from discord import ui

from features.games.errors import GameError
from features.games.minesweeper import MINE_COUNT, SIZE, SQUARES, MinesweeperGame, neighbors
from features.games.minesweeper_view import (
    EMPTY_LABEL,
    MINE_EMOJI,
    MinesweeperView,
    square_label,
    status_text,
)
from tests.features.games.test_game_views import RecordingHandler, make_interaction, notes_in

PLAYER, BOT = 1, 3
NAMES = {PLAYER: "Alice", BOT: "Harriet"}
BOTTOM_ROW = (20, 21, 22, 23, 24)
SCATTERED = (12, 13, 14, 17, 18)
COMPONENT_LIMIT = 40


class FixedMines:
    """Stands in for random.Random and always lays the mines where the test says."""

    def __init__(self, mines: tuple[int, ...]) -> None:
        self._mines = mines
        self.population: list[int] = []

    def sample(self, population: list[int], count: int) -> list[int]:
        self.population = list(population)
        return list(self._mines)


def game_with(mines: tuple[int, ...]) -> MinesweeperGame:
    return MinesweeperGame(FixedMines(mines), mine_count=len(mines))


def make_view(mines: tuple[int, ...] = SCATTERED, on_finish=None) -> MinesweeperView:
    return MinesweeperView(
        game_with(mines),
        NAMES,
        player_id=PLAYER,
        bot_id=BOT,
        timeout_seconds=60,
        on_finish=on_finish,
    )


def buttons_in(view: MinesweeperView) -> list[ui.Button]:
    return [item for item in view.walk_children() if isinstance(item, ui.Button)]


class NeighborTests(unittest.TestCase):
    def test_corner_edge_and_centre_have_the_right_neighbours(self) -> None:
        self.assertEqual(len(neighbors(0)), 3)
        self.assertEqual(len(neighbors(2)), 5)
        self.assertEqual(len(neighbors(12)), 8)
        self.assertNotIn(12, neighbors(12))

    def test_neighbours_do_not_wrap_around_the_edge(self) -> None:
        self.assertNotIn(SIZE - 1, neighbors(SIZE))
        self.assertEqual(sorted(neighbors(4)), [3, 8, 9])


class MinesweeperGameTests(unittest.TestCase):
    def test_first_square_and_its_neighbours_are_kept_clear(self) -> None:
        rng = FixedMines(SCATTERED)
        MinesweeperGame(rng).reveal(0)
        self.assertEqual(sorted(set(range(SQUARES)) - set(rng.population)), [0, 1, 5, 6])

    def test_the_first_move_is_always_safe_and_opens_a_clearing(self) -> None:
        for seed in range(30):
            for first in range(SQUARES):
                game = MinesweeperGame(random.Random(seed))
                game.reveal(first)
                with self.subTest(seed=seed, first=first):
                    self.assertEqual(len(game.mines), MINE_COUNT)
                    self.assertNotIn(first, game.mines)
                    self.assertEqual(game.adjacent_mine_count(first), 0)
                    self.assertTrue(set(neighbors(first)) <= game.revealed)

    def test_revealing_a_number_opens_only_that_square(self) -> None:
        game = game_with(SCATTERED)
        game.reveal(0)
        self.assertIn(6, game.revealed)
        self.assertEqual(game.adjacent_mine_count(6), 1)
        self.assertFalse(game.mines & game.revealed)
        self.assertNotIn(13, game.revealed)
        self.assertFalse(game.is_over)

    def test_a_clearing_opens_up_to_the_numbers_around_it(self) -> None:
        game = game_with(BOTTOM_ROW)
        game.reveal(0)
        self.assertTrue({10, 15, 19}.issubset(game.revealed))
        self.assertEqual(game.adjacent_mine_count(15), 2)

    def test_clearing_every_safe_square_wins(self) -> None:
        game = game_with(SCATTERED)
        for index in range(SQUARES):
            if index not in SCATTERED and index not in game.revealed:
                game.reveal(index)
        self.assertTrue(game.is_won)
        self.assertTrue(game.is_over)
        self.assertFalse(game.is_lost)
        self.assertEqual(game.safe_squares_left, 0)

    def test_one_reveal_can_win_the_whole_game(self) -> None:
        game = game_with(BOTTOM_ROW)
        game.reveal(0)
        self.assertTrue(game.is_won)

    def test_hitting_a_mine_loses(self) -> None:
        game = game_with(SCATTERED)
        game.reveal(0)
        game.reveal(13)
        self.assertTrue(game.is_lost)
        self.assertEqual(game.exploded_at, 13)
        self.assertFalse(game.is_won)
        self.assertTrue(game.is_over)

    def test_open_squares_and_finished_games_refuse_moves(self) -> None:
        game = game_with(SCATTERED)
        game.reveal(0)
        with self.assertRaises(GameError):
            game.reveal(0)
        game.reveal(13)
        with self.assertRaises(GameError):
            game.reveal(1)

    def test_safe_squares_left_counts_down(self) -> None:
        game = game_with(SCATTERED)
        self.assertEqual(game.safe_squares_left, SQUARES - len(SCATTERED))
        game.reveal(0)
        self.assertEqual(game.safe_squares_left, SQUARES - len(SCATTERED) - len(game.revealed))


class DisplayTests(unittest.TestCase):
    def test_labels_show_the_count_or_a_dot(self) -> None:
        self.assertEqual(square_label(0), EMPTY_LABEL)
        self.assertEqual(square_label(3), "3")

    def test_status_covers_progress_win_loss_and_timeout(self) -> None:
        playing = game_with(SCATTERED)
        self.assertIn("20 safe squares left", status_text(playing, "Alice", False))
        self.assertIn("Timed out", status_text(playing, "Alice", True))
        lost = game_with(SCATTERED)
        lost.reveal(0)
        lost.reveal(13)
        self.assertEqual(status_text(lost, "Alice", False), "**Alice** hit a mine.")
        won = game_with(BOTTOM_ROW)
        won.reveal(0)
        self.assertEqual(status_text(won, "Alice", False), "**Alice** cleared the field.")


class MinesweeperViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_a_press_reveals_squares_and_edits_the_message(self) -> None:
        view = make_view()
        interaction = make_interaction(PLAYER)
        await view._on_press(0, interaction)
        interaction.response.edit_message.assert_awaited_once()
        self.assertIn(0, view._game.revealed)
        self.assertFalse(view.is_finished())

    async def test_revealed_squares_are_locked_and_hidden_ones_are_not(self) -> None:
        view = make_view()
        await view._on_press(0, make_interaction(PLAYER))
        buttons = buttons_in(view)
        self.assertEqual(len(buttons), SQUARES)
        self.assertTrue(buttons[0].disabled)
        self.assertFalse(buttons[13].disabled)

    async def test_pressing_an_open_square_is_refused_privately(self) -> None:
        view = make_view()
        await view._on_press(0, make_interaction(PLAYER))
        again = make_interaction(PLAYER)
        await view._on_press(0, again)
        self.assertTrue(again.response.send_message.await_args.kwargs["ephemeral"])

    async def test_hitting_a_mine_reports_the_bot_and_shows_every_mine(self) -> None:
        handler = RecordingHandler(note=None)
        view = make_view(on_finish=handler)
        await view._on_press(0, make_interaction(PLAYER))
        await view._on_press(13, make_interaction(PLAYER))
        self.assertEqual(handler.winners, [BOT])
        self.assertTrue(view.is_finished())
        buttons = buttons_in(view)
        shown = [index for index, button in enumerate(buttons) if button.emoji is not None]
        self.assertEqual(shown, sorted(SCATTERED))
        self.assertEqual(str(buttons[13].emoji), MINE_EMOJI)
        self.assertTrue(all(button.disabled for button in buttons if button.emoji))

    async def test_clearing_the_field_reports_the_player_and_shows_the_note(self) -> None:
        handler = RecordingHandler()
        view = make_view(BOTTOM_ROW, on_finish=handler)
        await view._on_press(0, make_interaction(PLAYER))
        self.assertEqual(handler.winners, [PLAYER])
        self.assertTrue(view.is_finished())
        self.assertIn("-# +50 XP", notes_in(view))

    async def test_a_move_that_does_not_end_the_game_reports_nothing(self) -> None:
        handler = RecordingHandler()
        view = make_view(on_finish=handler)
        await view._on_press(0, make_interaction(PLAYER))
        self.assertEqual(handler.winners, [])

    async def test_timeout_locks_the_board(self) -> None:
        view = make_view()
        view.message = mock.Mock(edit=mock.AsyncMock())
        await view.on_timeout()
        view.message.edit.assert_awaited_once()
        self.assertTrue(all(button.disabled for button in buttons_in(view)))

    async def test_only_the_player_may_press(self) -> None:
        view = make_view()
        self.assertTrue(await view.interaction_check(make_interaction(PLAYER)))
        self.assertFalse(await view.interaction_check(make_interaction(BOT)))

    def test_the_layout_fits_discords_component_limit(self) -> None:
        view = make_view()
        self.assertLessEqual(len(list(view.walk_children())), COMPONENT_LIMIT)


if __name__ == "__main__":
    unittest.main()
