import random
from collections.abc import Sequence

from features.games.connect_four import COLUMNS, find_winning_line, landing_square


def _board_after(board: Sequence[str], column: int, mark: str) -> list[str]:
    after = list(board)
    after[landing_square(board, column)] = mark
    return after


def _wins_by_playing(board: Sequence[str], column: int, mark: str) -> bool:
    if landing_square(board, column) is None:
        return False
    return find_winning_line(_board_after(board, column, mark)) is not None


def _lets_opponent_win(board: Sequence[str], column: int, mark: str, opponent_mark: str) -> bool:
    return _wins_by_playing(_board_after(board, column, mark), column, opponent_mark)


def pick_column(board: Sequence[str], mark: str, opponent_mark: str, rng: random.Random) -> int:
    """Win if possible, otherwise block, otherwise avoid handing the opponent a win."""
    open_columns = [
        column for column in range(COLUMNS) if landing_square(board, column) is not None
    ]
    for candidate in (mark, opponent_mark):
        for column in open_columns:
            if _wins_by_playing(board, column, candidate):
                return column
    safe_columns = [
        column
        for column in open_columns
        if not _lets_opponent_win(board, column, mark, opponent_mark)
    ]
    return rng.choice(safe_columns or open_columns)
