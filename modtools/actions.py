import logging
from collections.abc import Awaitable, Callable

import discord
from discord.ext import commands

from guild_settings import MODLOG_CHANNEL_KEY
from modtools.models import ModAction
from time_format import format_elapsed
from views.modlog_view import build_modlog_view

log = logging.getLogger(__name__)

AUDIT_REASON_LIMIT = 512


def audit_reason(action: ModAction) -> str:
    return f"{action.moderator} ({action.moderator.id}): {action.reason}"[:AUDIT_REASON_LIMIT]


def format_dm(action: ModAction) -> str:
    duration = f" for {format_elapsed(action.duration)}" if action.duration else ""
    return f"You were {action.past_tense}{duration} in **{action.guild.name}**.\nReason: {action.reason}"


def confirmation_text(action: ModAction, notified: bool | None) -> str:
    text = f"{action.past_tense.capitalize()} **{action.target}**."
    if notified is None:
        return text
    return f"{text} They were notified by DM." if notified else f"{text} I couldn't DM them."


async def enforce(
    bot: commands.Bot,
    action: ModAction,
    perform: Callable[[], Awaitable[object]],
    notify: bool = True,
) -> bool | None:
    """DMs the target first, since they can't be reached once kicked or banned."""
    notified = await _notify_target(action) if notify else None
    await perform()
    log.info(
        "%s (id=%s) %s %s (id=%s) in guild=%s | reason: %s",
        action.moderator,
        action.moderator.id,
        action.past_tense,
        action.target,
        action.target.id,
        action.guild,
        action.reason,
    )
    await _post_to_modlog(bot, action)
    return notified


async def _notify_target(action: ModAction) -> bool:
    try:
        await action.target.send(format_dm(action))
    except discord.HTTPException:
        return False
    return True


async def _post_to_modlog(bot: commands.Bot, action: ModAction) -> None:
    raw_channel_id = await bot.guild_settings.get(action.guild.id, MODLOG_CHANNEL_KEY)
    if raw_channel_id is None:
        return
    channel = action.guild.get_channel(int(raw_channel_id))
    if not isinstance(channel, discord.TextChannel):
        return
    try:
        await channel.send(view=build_modlog_view(action))
    except discord.HTTPException:
        log.warning("Could not post to the mod-log channel %s", channel, exc_info=True)
