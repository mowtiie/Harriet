from collections.abc import Sequence
from datetime import datetime

from discord import ui

from features.tools.dice import DiceRoll, RollResult
from features.tools.timezones import describe_zone, format_utc_offset
from views.result_card import build_result_card

OPTION_SEPARATOR = " · "


def build_roll_card(dice: DiceRoll, result: RollResult) -> ui.LayoutView:
    details = [dice.notation] + ([result.breakdown] if result.breakdown else [])
    note = OPTION_SEPARATOR.join(details)
    return build_result_card("🎲 Dice roll", str(result.total), notes=[note])


def build_choose_card(options: Sequence[str], choice: str) -> ui.LayoutView:
    return build_result_card(
        "🎯 Choose",
        choice,
        quote=OPTION_SEPARATOR.join(" ".join(option.split()) for option in options),
        notes=[f"Picked from {len(options)} options"],
    )


def build_time_card(moment: datetime) -> ui.LayoutView:
    stamp = int(moment.timestamp())
    full, short, relative = (f"<t:{stamp}:{style}>" for style in "FtR")
    zone = f"{describe_zone(moment.tzinfo)} ({format_utc_offset(moment)})"
    return build_result_card(
        "🕒 Time",
        full,
        notes=[
            f"{relative} · Read as {moment:%a %d %b %Y, %H:%M} in {zone}",
            f"Copy for others: `{full}` · `{short}` · `{relative}`",
        ],
    )
