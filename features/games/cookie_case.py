import random
from collections.abc import Sequence
from dataclasses import dataclass

from features.games.cookie_clues import ROOM_COUNT, Clue, possible_thieves, true_clues

SUSPECT_COUNT = ROOM_COUNT
MIN_CLUES = 4


@dataclass(frozen=True)
class Room:
    emoji: str
    name: str


ROOMS = (
    Room("🍳", "Kitchen"),
    Room("🥫", "Pantry"),
    Room("📚", "Library"),
    Room("🌳", "Garden"),
    Room("🕸️", "Attic"),
)
FICTIONAL_SUSPECTS = (
    "Sir Crumbsalot",
    "Madame Muffin",
    "Professor Sprinkles",
    "Biscuit the Butler",
    "Count Cupcake",
    "Lady Marmalade",
    "Captain Custard",
    "The Mysterious Gnome",
)


@dataclass(frozen=True)
class Case:
    suspects: tuple[str, ...]
    positions: tuple[int, ...]
    cookie_room: int
    thief: int
    clues: tuple[Clue, ...]

    @property
    def room_names(self) -> tuple[str, ...]:
        return tuple(room.name for room in ROOMS)


def choose_suspects(player_names: Sequence[str], rng: random.Random) -> list[str]:
    """The players first, made unique, then fictional characters until there are enough."""
    suspects: list[str] = []
    for name in player_names[:SUSPECT_COUNT]:
        unique, copy = name, 2
        while unique in suspects:
            unique, copy = f"{name} ({copy})", copy + 1
        suspects.append(unique)
    spare = [name for name in FICTIONAL_SUSPECTS if name not in suspects]
    suspects += rng.sample(spare, SUSPECT_COUNT - len(suspects))
    rng.shuffle(suspects)
    return suspects


def _enough_clues(pool: list[Clue], cookie_room: int) -> list[Clue]:
    chosen: list[Clue] = []
    for clue in pool:
        if len(possible_thieves(chosen, cookie_room)) == 1:
            break
        chosen.append(clue)
    return chosen


def _without_redundant(clues: list[Clue], cookie_room: int, thief: int) -> list[Clue]:
    for clue in list(clues):
        rest = [other for other in clues if other != clue]
        if possible_thieves(rest, cookie_room) == {thief}:
            clues = rest
    return clues


def generate_case(rng: random.Random, suspects: Sequence[str]) -> Case:
    """A random case whose clues leave exactly one possible thief."""
    positions = list(range(ROOM_COUNT))
    rng.shuffle(positions)
    cookie_room = rng.randrange(ROOM_COUNT)
    thief = positions.index(cookie_room)

    pool = true_clues(positions)
    rng.shuffle(pool)
    clues = _without_redundant(_enough_clues(pool, cookie_room), cookie_room, thief)
    spare = [clue for clue in pool if clue not in clues]
    while len(clues) < MIN_CLUES:
        clues.append(spare.pop())
    rng.shuffle(clues)
    return Case(tuple(suspects), tuple(positions), cookie_room, thief, tuple(clues))
