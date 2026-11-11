import discord
from discord import ui

from core.time_format import format_elapsed
from modtools.models import ModAction
from views.style import ACCENT_COLOR, divider


def format_modlog_fields(action: ModAction) -> str:
    lines = [
        f"**Member** · {action.target.mention} (`{action.target.id}`)",
        f"**Moderator** · {action.moderator.mention}",
    ]
    if action.duration:
        lines.append(f"**Duration** · {format_elapsed(action.duration)}")
    lines.append(f"**Reason** · {action.reason}")
    return "\n".join(lines)


def build_modlog_view(action: ModAction) -> ui.LayoutView:
    timestamp = discord.utils.format_dt(discord.utils.utcnow(), "f")
    view = ui.LayoutView(timeout=None)
    view.add_item(
        ui.Container(
            ui.TextDisplay(f"### {action.name}\n-# {timestamp}"),
            divider(),
            ui.TextDisplay(format_modlog_fields(action)),
            accent_colour=ACCENT_COLOR,
        )
    )
    return view
