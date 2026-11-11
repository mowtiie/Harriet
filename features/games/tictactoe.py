from features.games.errors import GameError

SIZE = 3
SQUARES = SIZE * SIZE
FIRST_MARK = "X"
SECOND_MARK = "O"
WINNING_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


class TicTacToeGame:
    def __init__(self, first_id: int, second_id: int) -> None:
        self._ids = {FIRST_MARK: first_id, SECOND_MARK: second_id}
        self._board = [""] * SQUARES
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
    def winning_line(self) -> tuple[int, int, int] | None:
        for line in WINNING_LINES:
            marks = {self._board[index] for index in line}
            if len(marks) == 1 and marks != {""}:
                return line
        return None

    @property
    def winner_id(self) -> int | None:
        line = self.winning_line
        return self._ids[self._board[line[0]]] if line else None

    @property
    def is_draw(self) -> bool:
        return self.winning_line is None and all(self._board)

    @property
    def is_over(self) -> bool:
        return self.winning_line is not None or self.is_draw

    def play(self, player_id: int, index: int) -> None:
        if self.is_over:
            raise GameError("The game is over.")
        if player_id != self.current_player_id:
            raise GameError("It's not your turn.")
        if self._board[index]:
            raise GameError("That square is taken.")
        self._board[index] = self.turn
        if not self.is_over:
            self.turn = SECOND_MARK if self.turn == FIRST_MARK else FIRST_MARK
