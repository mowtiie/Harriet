"""Tests for the tic-tac-toe bot player."""

import random
import unittest

from features.games.tictactoe import TicTacToeGame
from features.games.tictactoe_bot import completing_square, pick_square
from features.games.tictactoe_view import TicTacToeView
from tests.features.games.test_game_views import make_interaction

ALICE, BOT = 1, 3
NAMES = {ALICE: "Alice", BOT: "Harriet"}


def board_of(text: str) -> list[str]:
    return ["" if char == "-" else char for char in text]


class PickSquareTests(unittest.TestCase):
    def test_completing_square_finds_the_gap_in_a_line(self) -> None:
        self.assertEqual(completing_square(board_of("XX-------"), "X"), 2)
        self.assertIsNone(completing_square(board_of("XXO------"), "X"))

    def test_takes_a_winning_square(self) -> None:
        board = board_of("OO-XX----")
        self.assertEqual(pick_square(board, "O", "X", random.Random()), 2)

    def test_blocks_the_opponent_when_it_cannot_win(self) -> None:
        board = board_of("XX--O----")
        self.assertEqual(pick_square(board, "O", "X", random.Random()), 2)

    def test_prefers_winning_over_blocking(self) -> None:
        board = board_of("XX-OO----")
        self.assertEqual(pick_square(board, "O", "X", random.Random()), 5)

    def test_otherwise_picks_a_free_square(self) -> None:
        board = board_of("X--------")
        for seed in range(20):
            square = pick_square(board, "O", "X", random.Random(seed))
            self.assertNotEqual(square, 0)


class BotGameViewTests(unittest.IsolatedAsyncioTestCase):
    def make_view(self) -> TicTacToeView:
        return TicTacToeView(
            TicTacToeGame(ALICE, BOT), NAMES, 60, bot_id=BOT, rng=random.Random(0)
        )

    async def test_bot_replies_after_the_human_moves(self) -> None:
        view = self.make_view()
        await view._on_press(4, make_interaction(ALICE))
        marks = [mark for mark in view._game.board if mark]
        self.assertEqual(sorted(marks), ["O", "X"])
        self.assertEqual(view._game.current_player_id, ALICE)

    async def test_bot_is_not_a_restricted_player(self) -> None:
        view = self.make_view()
        self.assertTrue(await view.interaction_check(make_interaction(ALICE)))
        self.assertFalse(await view.interaction_check(make_interaction(BOT)))


if __name__ == "__main__":
    unittest.main()
