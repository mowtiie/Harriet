from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from features.leveling.curve import level_for


@dataclass(frozen=True)
class RankedMember:
    position: int
    user_id: int
    name: str
    xp: int

    @property
    def level(self) -> int:
        return level_for(self.xp)


def rank_members(
    ranking: Sequence[tuple[int, int]], names: Mapping[int, str]
) -> list[RankedMember]:
    """Ranks members who are still in the server, so leavers never appear."""
    present = [(user_id, xp) for user_id, xp in ranking if user_id in names]
    return [
        RankedMember(position, user_id, names[user_id], xp)
        for position, (user_id, xp) in enumerate(present, start=1)
    ]


def find_member(ranked: Sequence[RankedMember], user_id: int) -> RankedMember | None:
    return next((member for member in ranked if member.user_id == user_id), None)
