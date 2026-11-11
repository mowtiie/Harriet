from collections.abc import Sequence

import discord
from discord import ui

from features.modtools.warning_store import WarningRecord
from views.style import ACCENT_COLOR, divider

MAX_WARNINGS_SHOWN = 10


def format_warning_line(record: WarningRecord) -> str:
    date = discord.utils.format_dt(record.created_at, "d")
    return f"`#{record.id}` {date} · {record.reason} · <@{record.moderator_id}>"


def format_warnings(records: Sequence[WarningRecord]) -> str:
    if not records:
        return "No warnings."
    lines = [format_warning_line(record) for record in records[-MAX_WARNINGS_SHOWN:]]
    hidden = len(records) - MAX_WARNINGS_SHOWN
    if hidden > 0:
        lines.append(f"-# {hidden} older warning(s) not shown")
    return "\n".join(lines)


def build_warnings_view(member_name: str, records: Sequence[WarningRecord]) -> ui.LayoutView:
    view = ui.LayoutView(timeout=None)
    view.add_item(
        ui.Container(
            ui.TextDisplay(f"# Warnings\n-# {member_name} · {len(records)} total"),
            divider(),
            ui.TextDisplay(format_warnings(records)),
            accent_colour=ACCENT_COLOR,
        )
    )
    return view
