"""Tests for tic-tac-toe rules."""

import unittest

from games.errors import GameError
from games.tictactoe import WINNING_LINES, TicTacToeGame

ALICE, BOB = 1, 2


def play_moves(*moves: int) -> TicTacToeGame:
    """Alice (X) plays the first move, then players alternate."""
    game = TicTacToeGame(ALICE, BOB)
    for number, index in enumerate(moves):
        game.play(ALICE if number % 2 == 0 else BOB, index)
    return game


class TicTacToeGameTests(unittest.TestCase):
    def test_x_moves_first_and_turns_alternate(self) -> None:
        game = TicTacToeGame(ALICE, BOB)
        self.assertEqual(game.current_player_id, ALICE)
        game.play(ALICE, 4)
        self.assertEqual(game.current_player_id, BOB)
        self.assertEqual(game.board[4], "X")

    def test_wrong_player_cannot_move(self) -> None:
        game = TicTacToeGame(ALICE, BOB)
        with self.assertRaises(GameError):
            game.play(BOB, 0)
        with self.assertRaises(GameError):
            game.play(99, 0)

    def test_taken_square_is_refused_and_turn_is_kept(self) -> None:
        game = play_moves(0)
        with self.assertRaises(GameError):
            game.play(BOB, 0)
        self.assertEqual(game.current_player_id, BOB)

    def test_every_winning_line_wins(self) -> None:
        for line in WINNING_LINES:
            others = [i for i in range(9) if i not in line][:2]
            moves = [line[0], others[0], line[1], others[1], line[2]]
            with self.subTest(line=line):
                game = play_moves(*moves)
                self.assertEqual(game.winning_line, line)
                self.assertEqual(game.winner_id, ALICE)
                self.assertTrue(game.is_over)
                self.assertFalse(game.is_draw)

    def test_second_player_can_win(self) -> None:
        game = play_moves(0, 3, 1, 4, 8, 5)
        self.assertEqual(game.winner_id, BOB)

    def test_full_board_without_a_line_is_a_draw(self) -> None:
        game = play_moves(0, 1, 2, 4, 3, 5, 7, 6, 8)
        self.assertTrue(game.is_draw)
        self.assertTrue(game.is_over)
        self.assertIsNone(game.winner_id)

    def test_no_moves_after_the_game_is_over(self) -> None:
        game = play_moves(0, 3, 1, 4, 2)
        with self.assertRaises(GameError):
            game.play(BOB, 8)

    def test_unfinished_game_has_no_winner(self) -> None:
        game = play_moves(0, 1)
        self.assertIsNone(game.winner_id)
        self.assertFalse(game.is_over)


if __name__ == "__main__":
    unittest.main()
