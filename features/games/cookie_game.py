from collections.abc import Sequence
from dataclasses import dataclass

from features.games.cookie_case import Case
from features.games.cookie_clues import Clue
from features.games.errors import GameError

STARTING_CLUES = 2


@dataclass(frozen=True)
class Accusation:
    player_id: int
    suspect: int
    correct: bool


class CookieGame:
    """Detectives reveal clues together, then each gets a single accusation."""

    def __init__(self, case: Case, player_ids: Sequence[int]) -> None:
        self.case = case
        self._player_ids = tuple(player_ids)
        self._revealed = min(STARTING_CLUES, len(case.clues))
        self._out: set[int] = set()
        self.accusations: list[Accusation] = []
        self.solver_id: int | None = None

    @property
    def player_ids(self) -> tuple[int, ...]:
        return self._player_ids

    @property
    def visible_clues(self) -> tuple[Clue, ...]:
        return self.case.clues[: self._revealed]

    @property
    def has_hidden_clues(self) -> bool:
        return self._revealed < len(self.case.clues)

    @property
    def eliminated(self) -> frozenset[int]:
        return frozenset(self._out)

    @property
    def is_solved(self) -> bool:
        return self.solver_id is not None

    @property
    def is_failed(self) -> bool:
        return not self.is_solved and len(self._out) == len(self._player_ids)

    @property
    def is_over(self) -> bool:
        return self.is_solved or self.is_failed

    def reveal_next_clue(self) -> None:
        self._ensure_in_progress()
        if not self.has_hidden_clues:
            raise GameError("Every clue is already out.")
        self._revealed += 1

    def accuse(self, player_id: int, suspect: int) -> Accusation:
        self._ensure_in_progress()
        if player_id not in self._player_ids:
            raise GameError("You're not on this case.")
        if player_id in self._out:
            raise GameError("You already used your accusation.")
        accusation = Accusation(player_id, suspect, correct=suspect == self.case.thief)
        self.accusations.append(accusation)
        if accusation.correct:
            self.solver_id = player_id
        else:
            self._out.add(player_id)
        return accusation

    def _ensure_in_progress(self) -> None:
        if self.is_over:
            raise GameError("The case is closed.")
