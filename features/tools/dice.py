import random
import re
from dataclasses import dataclass

MAX_DICE = 100
MAX_SIDES = 1000
MAX_MODIFIER = 1000
MAX_ROLLS_SHOWN = 20
DICE_HINT = "Use dice notation like `d20`, `2d6` or `4d8+3`."

_NOTATION = re.compile(r"(\d*)d(\d+)([+-]\d+)?")


@dataclass(frozen=True)
class DiceRoll:
    count: int
    sides: int
    modifier: int

    @property
    def notation(self) -> str:
        count = "" if self.count == 1 else self.count
        modifier = f"{self.modifier:+d}" if self.modifier else ""
        return f"{count}d{self.sides}{modifier}"


@dataclass(frozen=True)
class RollResult:
    total: int
    breakdown: str | None


def parse_dice(text: str) -> DiceRoll:
    match = _NOTATION.fullmatch("".join(text.lower().split()))
    if match is None:
        raise ValueError(f"Couldn't read `{text}` as dice. {DICE_HINT}")

    count = int(match.group(1) or 1)
    sides = int(match.group(2))
    modifier = int(match.group(3) or 0)
    if not 1 <= count <= MAX_DICE:
        raise ValueError(f"Roll between 1 and {MAX_DICE} dice at a time.")
    if not 2 <= sides <= MAX_SIDES:
        raise ValueError(f"Dice need between 2 and {MAX_SIDES} sides.")
    if abs(modifier) > MAX_MODIFIER:
        raise ValueError(f"The modifier can't be larger than {MAX_MODIFIER}.")
    return DiceRoll(count, sides, modifier)


def roll_dice(dice: DiceRoll, rng: random.Random) -> list[int]:
    return [rng.randint(1, dice.sides) for _ in range(dice.count)]


def summarize_roll(dice: DiceRoll, rolls: list[int]) -> RollResult:
    total = sum(rolls) + dice.modifier
    if len(rolls) == 1 and not dice.modifier:
        return RollResult(total, None)
    shown = " + ".join(str(roll) for roll in rolls[:MAX_ROLLS_SHOWN])
    if len(rolls) > MAX_ROLLS_SHOWN:
        shown += " + ..."
    modifier = f" {'+' if dice.modifier > 0 else '-'} {abs(dice.modifier)}" if dice.modifier else ""
    return RollResult(total, shown + modifier)
