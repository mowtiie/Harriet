"""Moderation commands."""

import logging

from discord import app_commands
from discord.ext import commands

import config

log = logging.getLogger(__name__)

CONFIRMATION_DELETE_DELAY_SECONDS = 3


def purge_limit(amount: int, invoked_by_message: bool) -> int:
    """Return how many messages to scan so `amount` others are deleted.

    A prefix invocation's own message is in the channel history and counts
    toward the purge limit, so it needs one extra slot.
    """
    return amount + 1 if invoked_by_message else amount


def deleted_count(purged: int, invoked_by_message: bool) -> int:
    """Return how many messages the user asked to delete, excluding the command itself."""
    return max(purged - 1, 0) if invoked_by_message else purged


def clear_summary(count: int) -> str:
    """Return the confirmation text shown after a clear."""
    return f"Deleted {count} message(s)."


async def send_confirmation(ctx: commands.Context, text: str) -> None:
    """Send a private reply for slash use, or a short-lived one for prefix use."""
    if ctx.interaction:
        await ctx.send(text, ephemeral=True)
        return
    confirmation = await ctx.send(text)
    await confirmation.delete(delay=CONFIRMATION_DELETE_DELAY_SECONDS)


class Moderation(commands.Cog):
    """Commands for keeping channels tidy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="clear", description="Delete the last N messages in this channel")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.describe(amount="How many messages to delete (default 5)")
    async def clear(
        self,
        ctx: commands.Context,
        amount: app_commands.Range[int, 1, config.MAX_CLEAR_AMOUNT] = 5,
    ) -> None:
        """Delete the last `amount` messages in the current channel."""
        invoked_by_message = ctx.interaction is None
        if not invoked_by_message:
            await ctx.defer(ephemeral=True)

        purged = await ctx.channel.purge(limit=purge_limit(amount, invoked_by_message))
        count = deleted_count(len(purged), invoked_by_message)
        log.info(
            f"{ctx.author} (id={ctx.author.id}) cleared {count} message(s) "
            f"in #{ctx.channel} (guild={ctx.guild})"
        )
        await send_confirmation(ctx, clear_summary(count))


async def setup(bot: commands.Bot) -> None:
    """Register the Moderation cog."""
    await bot.add_cog(Moderation(bot))
