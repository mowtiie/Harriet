import random
from collections import deque

from features.games.errors import GameError

SIZE = 5
SQUARES = SIZE * SIZE
MINE_COUNT = 5


def neighbors(index: int) -> tuple[int, ...]:
    row, column = divmod(index, SIZE)
    return tuple(
        near_row * SIZE + near_column
        for near_row in range(max(0, row - 1), min(SIZE, row + 2))
        for near_column in range(max(0, column - 1), min(SIZE, column + 2))
        if (near_row, near_column) != (row, column)
    )


class MinesweeperGame:
    """Mines are laid out on the first reveal, which is always safe and opens a clearing."""

    def __init__(self, rng: random.Random, mine_count: int = MINE_COUNT) -> None:
        self._rng = rng
        self._mine_count = mine_count
        self._mines: frozenset[int] = frozenset()
        self._revealed: set[int] = set()
        self._started = False
        self.exploded_at: int | None = None

    @property
    def mines(self) -> frozenset[int]:
        return self._mines

    @property
    def revealed(self) -> frozenset[int]:
        return frozenset(self._revealed)

    @property
    def safe_squares_left(self) -> int:
        return SQUARES - self._mine_count - len(self._revealed)

    @property
    def is_lost(self) -> bool:
        return self.exploded_at is not None

    @property
    def is_won(self) -> bool:
        return self._started and not self.is_lost and self.safe_squares_left == 0

    @property
    def is_over(self) -> bool:
        return self.is_won or self.is_lost

    def adjacent_mine_count(self, index: int) -> int:
        return sum(near in self._mines for near in neighbors(index))

    def reveal(self, index: int) -> None:
        if self.is_over:
            raise GameError("The game is over.")
        if index in self._revealed:
            raise GameError("That square is already open.")
        if not self._started:
            self._place_mines(first_index=index)
        if index in self._mines:
            self.exploded_at = index
            return
        self._open_from(index)

    def _place_mines(self, first_index: int) -> None:
        excluded = {first_index, *neighbors(first_index)}
        candidates = [index for index in range(SQUARES) if index not in excluded]
        self._mines = frozenset(self._rng.sample(candidates, self._mine_count))
        self._started = True

    def _open_from(self, index: int) -> None:
        pending = deque([index])
        while pending:
            square = pending.popleft()
            if square in self._revealed:
                continue
            self._revealed.add(square)
            if self.adjacent_mine_count(square) == 0:
                pending.extend(near for near in neighbors(square) if near not in self._revealed)
