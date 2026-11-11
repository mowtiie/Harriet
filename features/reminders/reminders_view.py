from collections.abc import Sequence
from datetime import datetime, timedelta

import discord
from discord import ui

from features.reminders.store import Reminder
from views.style import ACCENT_COLOR, divider

MAX_TEXT_SHOWN = 100
LATE_AFTER = timedelta(minutes=1)
ELLIPSIS = "..."


def shorten(text: str) -> str:
    if len(text) <= MAX_TEXT_SHOWN:
        return text
    return text[: MAX_TEXT_SHOWN - len(ELLIPSIS)] + ELLIPSIS


def format_reminder_line(reminder: Reminder) -> str:
    due = discord.utils.format_dt(reminder.due_at, "R")
    return f"`#{reminder.id}` {due} · {shorten(reminder.text)}"


def format_reminders(reminders: Sequence[Reminder]) -> str:
    if not reminders:
        return "You have no pending reminders."
    return "\n".join(format_reminder_line(reminder) for reminder in reminders)


def build_reminders_view(reminders: Sequence[Reminder]) -> ui.LayoutView:
    view = ui.LayoutView(timeout=None)
    view.add_item(
        ui.Container(
            ui.TextDisplay(f"# Reminders\n-# {len(reminders)} pending"),
            divider(),
            ui.TextDisplay(format_reminders(reminders)),
            accent_colour=ACCENT_COLOR,
        )
    )
    return view


def format_delivery(reminder: Reminder, now: datetime) -> str:
    message = f"<@{reminder.user_id}> Reminder: {reminder.text}"
    if now - reminder.due_at > LATE_AFTER:
        due = discord.utils.format_dt(reminder.due_at, "f")
        message += f"\n-# This was set for {due} and arrived late."
    return message
