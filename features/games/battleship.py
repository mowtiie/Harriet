import random
import string
from collections.abc import Sequence
from dataclasses import dataclass

from features.games.errors import GameError

SIZE = 5
SQUARES = SIZE * SIZE
FLEET_SIZES = (3, 2, 2)
COLUMN_LETTERS = string.ascii_uppercase[:SIZE]

Ship = frozenset[int]


def square_name(index: int) -> str:
    row, column = divmod(index, SIZE)
    return f"{COLUMN_LETTERS[column]}{row + 1}"


def orthogonal_neighbors(index: int) -> tuple[int, ...]:
    row, column = divmod(index, SIZE)
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    return tuple(
        (row + row_step) * SIZE + column + column_step
        for row_step, column_step in steps
        if 0 <= row + row_step < SIZE and 0 <= column + column_step < SIZE
    )


def _ship_placements(length: int) -> list[Ship]:
    placements = []
    for row in range(SIZE):
        for column in range(SIZE):
            if column + length <= SIZE:
                placements.append(frozenset(row * SIZE + column + step for step in range(length)))
            if row + length <= SIZE:
                placements.append(frozenset((row + step) * SIZE + column for step in range(length)))
    return placements


def _try_place_fleet(rng: random.Random, sizes: Sequence[int]) -> list[Ship] | None:
    taken: set[int] = set()
    fleet = []
    for length in sizes:
        options = [ship for ship in _ship_placements(length) if not ship & taken]
        if not options:
            return None
        ship = rng.choice(options)
        fleet.append(ship)
        taken |= ship
    return fleet


def place_fleet(rng: random.Random, sizes: Sequence[int] = FLEET_SIZES) -> list[Ship]:
    while True:
        fleet = _try_place_fleet(rng, sizes)
        if fleet is not None:
            return fleet


@dataclass(frozen=True)
class ShotResult:
    hit: bool
    sunk_size: int | None = None


@dataclass(frozen=True)
class Shot:
    player_id: int
    index: int
    result: ShotResult


class Board:
    """One player's waters: where their ships are and where they have been shot at."""

    def __init__(self, ships: Sequence[Ship]) -> None:
        self._ships = tuple(ships)
        self._shots: set[int] = set()

    @property
    def shots(self) -> frozenset[int]:
        return frozenset(self._shots)

    @property
    def ship_squares(self) -> frozenset[int]:
        return frozenset().union(*self._ships)

    @property
    def hit_squares(self) -> frozenset[int]:
        return self.shots & self.ship_squares

    @property
    def sunk_squares(self) -> frozenset[int]:
        return frozenset().union(*(ship for ship in self._ships if ship <= self._shots))

    @property
    def live_hits(self) -> frozenset[int]:
        """Hits on ships that are still afloat."""
        return self.hit_squares - self.sunk_squares

    @property
    def ships_afloat(self) -> int:
        return sum(1 for ship in self._ships if not ship <= self._shots)

    @property
    def is_defeated(self) -> bool:
        return self.ships_afloat == 0

    def fire(self, index: int) -> ShotResult:
        if index in self._shots:
            raise GameError(f"{square_name(index)} was already shot.")
        self._shots.add(index)
        ship = next((ship for ship in self._ships if index in ship), None)
        if ship is None:
            return ShotResult(hit=False)
        return ShotResult(hit=True, sunk_size=len(ship) if ship <= self._shots else None)


class BattleshipGame:
    def __init__(
        self,
        first_id: int,
        second_id: int,
        first_fleet: Sequence[Ship],
        second_fleet: Sequence[Ship],
    ) -> None:
        self._boards = {first_id: Board(first_fleet), second_id: Board(second_fleet)}
        self._player_ids = (first_id, second_id)
        self.current_player_id = first_id
        self.history: list[Shot] = []

    @property
    def player_ids(self) -> tuple[int, int]:
        return self._player_ids

    @property
    def target_board(self) -> Board:
        """The waters the player whose turn it is has to shoot at."""
        return self._boards[self.opponent_of(self.current_player_id)]

    @property
    def winner_id(self) -> int | None:
        for player_id, board in self._boards.items():
            if board.is_defeated:
                return self.opponent_of(player_id)
        return None

    @property
    def is_over(self) -> bool:
        return self.winner_id is not None

    def board_of(self, player_id: int) -> Board:
        return self._boards[player_id]

    def opponent_of(self, player_id: int) -> int:
        first, second = self._player_ids
        return second if player_id == first else first

    def play(self, player_id: int, index: int) -> ShotResult:
        if self.is_over:
            raise GameError("The game is over.")
        if player_id != self.current_player_id:
            raise GameError("It's not your turn.")
        result = self.target_board.fire(index)
        self.history.append(Shot(player_id, index, result))
        if not self.is_over:
            self.current_player_id = self.opponent_of(player_id)
        return result


def new_battleship_game(first_id: int, second_id: int, rng: random.Random) -> BattleshipGame:
    return BattleshipGame(first_id, second_id, place_fleet(rng), place_fleet(rng))
