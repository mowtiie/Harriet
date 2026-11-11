"""Tests for rock paper scissors rules and random answers."""

import random
import unittest

from features.games.answers import COIN_SIDES, EIGHT_BALL_ANSWERS, flip_coin, pick_answer
from features.games.errors import GameError
from features.games.rps import Move, RpsGame, random_move

ALICE, BOB = 1, 2


def play(first: Move, second: Move) -> RpsGame:
    game = RpsGame(ALICE, BOB)
    game.pick(ALICE, first)
    game.pick(BOB, second)
    return game


class RpsGameTests(unittest.TestCase):
    def test_every_matchup_has_the_right_winner(self) -> None:
        cases = {
            (Move.ROCK, Move.SCISSORS): ALICE,
            (Move.PAPER, Move.ROCK): ALICE,
            (Move.SCISSORS, Move.PAPER): ALICE,
            (Move.SCISSORS, Move.ROCK): BOB,
            (Move.ROCK, Move.PAPER): BOB,
            (Move.PAPER, Move.SCISSORS): BOB,
        }
        for (first, second), winner in cases.items():
            with self.subTest(first=first, second=second):
                self.assertEqual(play(first, second).winner_id, winner)

    def test_same_moves_tie(self) -> None:
        for move in Move:
            game = play(move, move)
            self.assertTrue(game.is_finished)
            self.assertIsNone(game.winner_id)

    def test_game_is_unfinished_until_both_players_pick(self) -> None:
        game = RpsGame(ALICE, BOB)
        game.pick(ALICE, Move.ROCK)
        self.assertFalse(game.is_finished)
        self.assertIsNone(game.winner_id)

    def test_cannot_pick_twice(self) -> None:
        game = RpsGame(ALICE, BOB)
        game.pick(ALICE, Move.ROCK)
        with self.assertRaises(GameError):
            game.pick(ALICE, Move.PAPER)
        self.assertEqual(game.move_of(ALICE), Move.ROCK)

    def test_strangers_cannot_pick(self) -> None:
        with self.assertRaises(GameError):
            RpsGame(ALICE, BOB).pick(3, Move.ROCK)

    def test_opponent_of(self) -> None:
        game = RpsGame(ALICE, BOB)
        self.assertEqual(game.opponent_of(ALICE), BOB)
        self.assertEqual(game.opponent_of(BOB), ALICE)

    def test_random_move_is_a_valid_move(self) -> None:
        self.assertIn(random_move(random.Random(3)), list(Move))


class AnswerTests(unittest.TestCase):
    def test_answers_come_from_the_fixed_lists(self) -> None:
        rng = random.Random(5)
        self.assertIn(pick_answer(rng), EIGHT_BALL_ANSWERS)
        self.assertIn(flip_coin(rng), COIN_SIDES)

    def test_same_seed_gives_same_answer(self) -> None:
        self.assertEqual(pick_answer(random.Random(9)), pick_answer(random.Random(9)))


if __name__ == "__main__":
    unittest.main()
