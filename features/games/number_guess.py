import random
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from features.games.errors import GameError

MIN_NUMBER = 1
MAX_NUMBER = 100
MAX_GUESSES = 8


class Hint(Enum):
    TOO_LOW = "Too low"
    TOO_HIGH = "Too high"
    CORRECT = "Correct"


@dataclass(frozen=True)
class Attempt:
    number: int
    hint: Hint


def pick_number(rng: random.Random) -> int:
    return rng.randint(MIN_NUMBER, MAX_NUMBER)


def parse_guess(text: str) -> int:
    text = text.strip()
    if not (text.isascii() and text.isdigit()):
        raise GameError("Enter a whole number.")
    return int(text)


class NumberGuessGame:
    def __init__(self, secret: int, max_guesses: int = MAX_GUESSES) -> None:
        self.secret = secret
        self.max_guesses = max_guesses
        self._attempts: list[Attempt] = []

    @property
    def attempts(self) -> Sequence[Attempt]:
        return tuple(self._attempts)

    @property
    def guesses_left(self) -> int:
        return self.max_guesses - len(self._attempts)

    @property
    def lowest_possible(self) -> int:
        too_low = [
            attempt.number + 1 for attempt in self._attempts if attempt.hint is Hint.TOO_LOW
        ]
        return max([MIN_NUMBER, *too_low])

    @property
    def highest_possible(self) -> int:
        too_high = [
            attempt.number - 1 for attempt in self._attempts if attempt.hint is Hint.TOO_HIGH
        ]
        return min([MAX_NUMBER, *too_high])

    @property
    def is_won(self) -> bool:
        return any(attempt.hint is Hint.CORRECT for attempt in self._attempts)

    @property
    def is_lost(self) -> bool:
        return not self.is_won and self.guesses_left <= 0

    @property
    def is_over(self) -> bool:
        return self.is_won or self.is_lost

    def guess(self, number: int) -> Hint:
        if self.is_over:
            raise GameError("The game is over.")
        if not MIN_NUMBER <= number <= MAX_NUMBER:
            raise GameError(f"Pick a number from {MIN_NUMBER} to {MAX_NUMBER}.")
        if any(attempt.number == number for attempt in self._attempts):
            raise GameError(f"You already guessed {number}.")
        hint = self._hint_for(number)
        self._attempts.append(Attempt(number, hint))
        return hint

    def _hint_for(self, number: int) -> Hint:
        if number == self.secret:
            return Hint.CORRECT
        return Hint.TOO_LOW if number < self.secret else Hint.TOO_HIGH
