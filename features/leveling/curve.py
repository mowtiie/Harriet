from dataclasses import dataclass

BASE_XP = 100
XP_STEP = 50
BAR_WIDTH = 10
BAR_FILLED = "█"
BAR_EMPTY = "░"


@dataclass(frozen=True)
class LevelProgress:
    level: int
    xp_into_level: int
    xp_for_next: int

    @property
    def fraction(self) -> float:
        return self.xp_into_level / self.xp_for_next


def xp_for_next_level(level: int) -> int:
    return BASE_XP + XP_STEP * level


def xp_to_reach(level: int) -> int:
    return BASE_XP * level + XP_STEP * level * (level - 1) // 2


def level_for(xp: int) -> int:
    level = 0
    while xp_to_reach(level + 1) <= xp:
        level += 1
    return level


def progress_for(xp: int) -> LevelProgress:
    level = level_for(xp)
    return LevelProgress(level, xp - xp_to_reach(level), xp_for_next_level(level))


def format_bar(fraction: float) -> str:
    filled = int(fraction * BAR_WIDTH)
    return BAR_FILLED * filled + BAR_EMPTY * (BAR_WIDTH - filled)
