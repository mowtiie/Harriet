import string
from collections.abc import Sequence

from features.games.errors import GameError

MAX_MISSES = 6
MASK = "_"


class HangmanGame:
    def __init__(self, word: str, max_misses: int = MAX_MISSES) -> None:
        self.word = word.upper()
        self.max_misses = max_misses
        self._guessed: list[str] = []

    @property
    def guessed(self) -> Sequence[str]:
        return tuple(self._guessed)

    @property
    def misses(self) -> Sequence[str]:
        return tuple(letter for letter in self._guessed if letter not in self.word)

    @property
    def masked_letters(self) -> Sequence[str]:
        return tuple(letter if letter in self._guessed else MASK for letter in self.word)

    @property
    def is_won(self) -> bool:
        return all(letter in self._guessed for letter in self.word)

    @property
    def is_lost(self) -> bool:
        return len(self.misses) >= self.max_misses

    @property
    def is_over(self) -> bool:
        return self.is_won or self.is_lost

    def guess(self, letter: str) -> None:
        letter = letter.upper()
        if self.is_over:
            raise GameError("The game is over.")
        if len(letter) != 1 or letter not in string.ascii_uppercase:
            raise GameError("Guess a single letter.")
        if letter in self._guessed:
            raise GameError(f"You already guessed {letter}.")
        self._guessed.append(letter)
