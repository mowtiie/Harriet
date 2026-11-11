import random
from enum import Enum

from features.games.errors import GameError


class Move(Enum):
    ROCK = "Rock"
    PAPER = "Paper"
    SCISSORS = "Scissors"


BEATS = {Move.ROCK: Move.SCISSORS, Move.PAPER: Move.ROCK, Move.SCISSORS: Move.PAPER}


def random_move(rng: random.Random) -> Move:
    return rng.choice(list(Move))


class RpsGame:
    def __init__(self, first_id: int, second_id: int) -> None:
        self.player_ids = (first_id, second_id)
        self._picks: dict[int, Move] = {}

    @property
    def is_finished(self) -> bool:
        return len(self._picks) == len(self.player_ids)

    @property
    def winner_id(self) -> int | None:
        if not self.is_finished:
            return None
        first, second = (self._picks[player_id] for player_id in self.player_ids)
        if first == second:
            return None
        return self.player_ids[0] if BEATS[first] == second else self.player_ids[1]

    def pick(self, player_id: int, move: Move) -> None:
        if player_id not in self.player_ids:
            raise GameError("You're not in this game.")
        if player_id in self._picks:
            raise GameError("You already picked.")
        self._picks[player_id] = move

    def move_of(self, player_id: int) -> Move | None:
        return self._picks.get(player_id)

    def opponent_of(self, player_id: int) -> int:
        first, second = self.player_ids
        return second if player_id == first else first
