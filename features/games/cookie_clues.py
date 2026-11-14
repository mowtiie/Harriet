from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations, permutations
from typing import Protocol

ROOM_COUNT = 5
ALL_ASSIGNMENTS = tuple(permutations(range(ROOM_COUNT)))


class Clue(Protocol):
    def holds(self, positions: Sequence[int]) -> bool:
        """`positions[suspect]` is the room that suspect stood in."""

    def render(self, names: Sequence[str], rooms: Sequence[str]) -> str: ...


def _bold(text: str) -> str:
    return f"**{text}**"


@dataclass(frozen=True)
class NotInRoom:
    suspect: int
    room: int

    def holds(self, positions: Sequence[int]) -> bool:
        return positions[self.suspect] != self.room

    def render(self, names: Sequence[str], rooms: Sequence[str]) -> str:
        return f"{_bold(names[self.suspect])} was not in the {_bold(rooms[self.room])}."


@dataclass(frozen=True)
class NextTo:
    first: int
    second: int

    def holds(self, positions: Sequence[int]) -> bool:
        return abs(positions[self.first] - positions[self.second]) == 1

    def render(self, names: Sequence[str], rooms: Sequence[str]) -> str:
        first, second = _bold(names[self.first]), _bold(names[self.second])
        return f"{first} was in a room right next to {second}'s."


@dataclass(frozen=True)
class NotNextTo:
    first: int
    second: int

    def holds(self, positions: Sequence[int]) -> bool:
        return abs(positions[self.first] - positions[self.second]) != 1

    def render(self, names: Sequence[str], rooms: Sequence[str]) -> str:
        first, second = _bold(names[self.first]), _bold(names[self.second])
        return f"{first} was not in a room next to {second}'s."


@dataclass(frozen=True)
class FurtherAlong:
    first: int
    second: int

    def holds(self, positions: Sequence[int]) -> bool:
        return positions[self.first] > positions[self.second]

    def render(self, names: Sequence[str], rooms: Sequence[str]) -> str:
        return (
            f"{_bold(names[self.first])} was further along the corridor "
            f"than {_bold(names[self.second])}."
        )


def true_clues(positions: Sequence[int]) -> list[Clue]:
    """Every clue of every kind that is true for these positions."""
    suspects = range(len(positions))
    clues: list[Clue] = [
        NotInRoom(suspect, room)
        for suspect in suspects
        for room in range(ROOM_COUNT)
        if room != positions[suspect]
    ]
    for first, second in combinations(suspects, 2):
        close = abs(positions[first] - positions[second]) == 1
        clues.append(NextTo(first, second) if close else NotNextTo(first, second))
    for first in suspects:
        clues += [
            FurtherAlong(first, second)
            for second in suspects
            if positions[first] > positions[second]
        ]
    return clues


def possible_thieves(clues: Sequence[Clue], cookie_room: int) -> set[int]:
    """Every suspect who could have been in the cookie room without breaking a clue."""
    return {
        positions.index(cookie_room)
        for positions in ALL_ASSIGNMENTS
        if all(clue.holds(positions) for clue in clues)
    }
