"""Tests for connect four rules, the bot player and the view."""

import random
import unittest

from features.games.connect_four import (
    COLUMNS,
    CONNECT,
    ROWS,
    WINNING_LINES,
    ConnectFourGame,
    landing_square,
)
from features.games.connect_four_bot import pick_column
from features.games.connect_four_view import ConnectFourView, board_text, status_text
from features.games.errors import GameError
from tests.features.games.test_game_views import make_interaction, notes_in, RecordingHandler

ALICE, BOB, BOT = 1, 2, 3
NAMES = {ALICE: "Alice", BOB: "Bob", BOT: "Harriet"}


def play_columns(*columns: int) -> ConnectFourGame:
    """Alice (red) drops the first disc, then players alternate."""
    game = ConnectFourGame(ALICE, BOB)
    for number, column in enumerate(columns):
        game.play(ALICE if number % 2 == 0 else BOB, column)
    return game


def board_with(**discs: str) -> list[str]:
    board = [""] * (ROWS * COLUMNS)
    for position, mark in discs.items():
        row, column = int(position[1]), int(position[3])
        board[row * COLUMNS + column] = mark
    return board


class ConnectFourGameTests(unittest.TestCase):
    def test_lines_cover_every_way_to_connect_four(self) -> None:
        self.assertEqual(len(WINNING_LINES), 69)
        self.assertTrue(all(len(line) == CONNECT for line in WINNING_LINES))

    def test_discs_fall_to_the_bottom_and_stack(self) -> None:
        game = play_columns(3, 3)
        bottom, above = (ROWS - 1) * COLUMNS + 3, (ROWS - 2) * COLUMNS + 3
        self.assertEqual(game.board[bottom], "R")
        self.assertEqual(game.board[above], "Y")

    def test_turns_alternate_and_wrong_player_is_refused(self) -> None:
        game = ConnectFourGame(ALICE, BOB)
        with self.assertRaises(GameError):
            game.play(BOB, 0)
        game.play(ALICE, 0)
        self.assertEqual(game.current_player_id, BOB)

    def test_full_column_is_refused_and_turn_is_kept(self) -> None:
        game = play_columns(0, 0, 0, 0, 0, 0)
        self.assertTrue(game.is_column_full(0))
        with self.assertRaises(GameError):
            game.play(ALICE, 0)
        self.assertEqual(game.current_player_id, ALICE)

    def test_horizontal_win(self) -> None:
        game = play_columns(0, 0, 1, 1, 2, 2, 3)
        self.assertEqual(game.winner_id, ALICE)
        self.assertTrue(game.is_over)

    def test_vertical_win(self) -> None:
        game = play_columns(0, 1, 0, 1, 0, 1, 0)
        self.assertEqual(game.winner_id, ALICE)

    def test_diagonal_win(self) -> None:
        game = play_columns(0, 1, 1, 2, 3, 2, 2, 3, 3, 6, 3)
        self.assertEqual(game.winner_id, ALICE)

    def test_second_player_can_win(self) -> None:
        game = play_columns(0, 1, 0, 1, 2, 1, 2, 1)
        self.assertEqual(game.winner_id, BOB)

    def test_no_moves_after_the_game_is_over(self) -> None:
        game = play_columns(0, 1, 0, 1, 0, 1, 0)
        with self.assertRaises(GameError):
            game.play(BOB, 5)

    def test_full_board_without_a_line_is_a_draw(self) -> None:
        game = ConnectFourGame(ALICE, BOB)
        game._board = list("RRYYRRY" "YYRRYYR" "RRYYRRY" "YYRRYYR" "RRYYRRY" "YYRRYYR")
        self.assertIsNone(game.winner_id)
        self.assertTrue(game.is_draw)
        self.assertTrue(game.is_over)

    def test_landing_square_is_none_for_a_full_column(self) -> None:
        board = board_with(r0c2="R", r1c2="Y", r2c2="R", r3c2="Y", r4c2="R", r5c2="Y")
        self.assertIsNone(landing_square(board, 2))
        self.assertEqual(landing_square(board, 3), 5 * COLUMNS + 3)


class PickColumnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rng = random.Random(0)

    def test_takes_a_winning_column(self) -> None:
        board = board_with(r5c0="Y", r5c1="Y", r5c2="Y", r5c5="R", r5c6="R")
        self.assertEqual(pick_column(board, "Y", "R", self.rng), 3)

    def test_blocks_the_opponent(self) -> None:
        board = board_with(r5c0="R", r5c1="R", r5c2="R", r5c6="Y")
        self.assertEqual(pick_column(board, "Y", "R", self.rng), 3)

    def test_prefers_winning_over_blocking(self) -> None:
        board = board_with(r5c0="R", r5c1="R", r5c2="R", r4c6="Y", r3c6="Y", r2c6="Y")
        self.assertEqual(pick_column(board, "Y", "R", self.rng), 6)

    def test_avoids_a_column_that_hands_the_opponent_a_win(self) -> None:
        board = board_with(r4c1="R", r4c2="R", r4c3="R", r5c1="Y", r5c2="R", r5c3="Y")
        for seed in range(30):
            column = pick_column(board, "Y", "R", random.Random(seed))
            self.assertNotIn(column, (0, 4))

    def test_never_picks_a_full_column(self) -> None:
        board = board_with(r0c0="R", r1c0="Y", r2c0="R", r3c0="Y", r4c0="R", r5c0="Y")
        for seed in range(30):
            self.assertNotEqual(pick_column(board, "Y", "R", random.Random(seed)), 0)


class ConnectFourViewTests(unittest.IsolatedAsyncioTestCase):
    def make_view(self, bot_id: int | None = None, handler=None) -> ConnectFourView:
        opponent = bot_id or BOB
        game = ConnectFourGame(ALICE, opponent)
        return ConnectFourView(game, NAMES, 60, handler, bot_id=bot_id, rng=random.Random(0))

    async def test_move_drops_a_disc_and_edits_the_message(self) -> None:
        view = self.make_view()
        interaction = make_interaction(ALICE)
        await view._on_press(3, interaction)
        self.assertEqual(view._game.board[(ROWS - 1) * COLUMNS + 3], "R")
        interaction.response.edit_message.assert_awaited_once()

    async def test_out_of_turn_press_is_refused_privately(self) -> None:
        view = self.make_view()
        interaction = make_interaction(BOB)
        await view._on_press(0, interaction)
        self.assertEqual(view._game.board.count("R"), 0)
        self.assertTrue(interaction.response.send_message.await_args.kwargs["ephemeral"])

    async def test_bot_replies_after_the_human_moves(self) -> None:
        view = self.make_view(bot_id=BOT)
        await view._on_press(3, make_interaction(ALICE))
        self.assertEqual(sorted(mark for mark in view._game.board if mark), ["R", "Y"])
        self.assertEqual(view._game.current_player_id, ALICE)

    async def test_bot_is_not_a_restricted_player(self) -> None:
        view = self.make_view(bot_id=BOT)
        self.assertTrue(await view.interaction_check(make_interaction(ALICE)))
        self.assertFalse(await view.interaction_check(make_interaction(BOT)))

    async def test_winner_is_reported_once_and_the_game_stops(self) -> None:
        handler = RecordingHandler()
        view = self.make_view(handler=handler)
        for user, column in ((ALICE, 0), (BOB, 1), (ALICE, 0), (BOB, 1), (ALICE, 0), (BOB, 1)):
            await view._on_press(column, make_interaction(user))
        self.assertEqual(handler.winners, [])
        await view._on_press(0, make_interaction(ALICE))
        self.assertEqual(handler.winners, [ALICE])
        self.assertTrue(view.is_finished())
        self.assertIn("-# +50 XP", notes_in(view))

    async def test_full_column_button_is_disabled(self) -> None:
        view = self.make_view()
        for number in range(ROWS):
            await view._on_press(0, make_interaction(ALICE if number % 2 == 0 else BOB))
        buttons = [item for item in view.walk_children() if hasattr(item, "disabled")]
        self.assertEqual([button.label for button in buttons if button.disabled], ["1"])


class DisplayTests(unittest.TestCase):
    def test_board_text_has_a_header_and_one_line_per_row(self) -> None:
        board = board_with(r5c0="R", r5c1="Y")
        lines = board_text(board).splitlines()
        self.assertEqual(len(lines), ROWS + 1)
        self.assertTrue(lines[-1].startswith("🔴🟡⚪"))

    def test_status_text_covers_turn_win_draw_and_timeout(self) -> None:
        game = ConnectFourGame(ALICE, BOB)
        self.assertEqual(status_text(game, NAMES, False), "**Alice**'s turn (🔴).")
        self.assertIn("didn't move in time", status_text(game, NAMES, True))
        won = play_columns(0, 1, 0, 1, 0, 1, 0)
        self.assertEqual(status_text(won, NAMES, False), "**Alice** wins.")


if __name__ == "__main__":
    unittest.main()
