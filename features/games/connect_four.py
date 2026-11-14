from collections.abc import Sequence

from features.games.errors import GameError

ROWS = 6
COLUMNS = 7
CONNECT = 4
FIRST_MARK = "R"
SECOND_MARK = "Y"
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def _build_winning_lines() -> tuple[tuple[int, ...], ...]:
    lines = []
    for row in range(ROWS):
        for column in range(COLUMNS):
            for row_step, column_step in DIRECTIONS:
                end_row = row + row_step * (CONNECT - 1)
                end_column = column + column_step * (CONNECT - 1)
                if 0 <= end_row < ROWS and 0 <= end_column < COLUMNS:
                    lines.append(
                        tuple(
                            (row + row_step * step) * COLUMNS + column + column_step * step
                            for step in range(CONNECT)
                        )
                    )
    return tuple(lines)


WINNING_LINES = _build_winning_lines()


def landing_square(board: Sequence[str], column: int) -> int | None:
    """Index a disc dropped in the column lands on, or None when it is full."""
    for row in reversed(range(ROWS)):
        index = row * COLUMNS + column
        if not board[index]:
            return index
    return None


def find_winning_line(board: Sequence[str]) -> tuple[int, ...] | None:
    for line in WINNING_LINES:
        marks = {board[index] for index in line}
        if len(marks) == 1 and marks != {""}:
            return line
    return None


class ConnectFourGame:
    def __init__(self, first_id: int, second_id: int) -> None:
        self._ids = {FIRST_MARK: first_id, SECOND_MARK: second_id}
        self._board = [""] * (ROWS * COLUMNS)
        self.turn = FIRST_MARK

    @property
    def board(self) -> tuple[str, ...]:
        return tuple(self._board)

    @property
    def player_ids(self) -> tuple[int, int]:
        return self._ids[FIRST_MARK], self._ids[SECOND_MARK]

    @property
    def current_player_id(self) -> int:
        return self._ids[self.turn]

    @property
    def winning_line(self) -> tuple[int, ...] | None:
        return find_winning_line(self._board)

    @property
    def winner_id(self) -> int | None:
        line = self.winning_line
        return self._ids[self._board[line[0]]] if line else None

    @property
    def is_draw(self) -> bool:
        return self.winning_line is None and all(self._board[:COLUMNS])

    @property
    def is_over(self) -> bool:
        return self.winning_line is not None or self.is_draw

    def is_column_full(self, column: int) -> bool:
        return landing_square(self._board, column) is None

    def play(self, player_id: int, column: int) -> None:
        if self.is_over:
            raise GameError("The game is over.")
        if player_id != self.current_player_id:
            raise GameError("It's not your turn.")
        square = landing_square(self._board, column)
        if square is None:
            raise GameError("That column is full.")
        self._board[square] = self.turn
        if not self.is_over:
            self.turn = SECOND_MARK if self.turn == FIRST_MARK else FIRST_MARK
