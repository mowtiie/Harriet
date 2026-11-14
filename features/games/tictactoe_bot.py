import random
from collections.abc import Sequence

from features.games.tictactoe import WINNING_LINES


def completing_square(board: Sequence[str], mark: str) -> int | None:
    for line in WINNING_LINES:
        marks = [board[index] for index in line]
        if marks.count(mark) == 2 and marks.count("") == 1:
            return line[marks.index("")]
    return None


def pick_square(board: Sequence[str], mark: str, opponent_mark: str, rng: random.Random) -> int:
    """Win if possible, otherwise block, otherwise pick any free square."""
    for candidate in (mark, opponent_mark):
        square = completing_square(board, candidate)
        if square is not None:
            return square
    return rng.choice([index for index, taken in enumerate(board) if not taken])
