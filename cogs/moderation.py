import logging

from discord import app_commands
from discord.ext import commands

import config

log = logging.getLogger(__name__)

CONFIRMATION_DELETE_DELAY_SECONDS = 3


def purge_limit(amount: int, invoked_by_message: bool) -> int:
    """Prefix commands also match their own message, so they need one extra slot."""
    return amount + 1 if invoked_by_message else amount


def deleted_count(purged: int, invoked_by_message: bool) -> int:
    return max(purged - 1, 0) if invoked_by_message else purged


def clear_summary(count: int) -> str:
    return f"Deleted {count} message(s)."


async def send_confirmation(ctx: commands.Context, text: str) -> None:
    if ctx.interaction:
        await ctx.send(text, ephemeral=True)
        return
    confirmation = await ctx.send(text)
    await confirmation.delete(delay=CONFIRMATION_DELETE_DELAY_SECONDS)


class Moderation(commands.Cog, description="Keep your channels tidy."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="clear",
        description="Delete the last N messages in this channel",
        extras={"examples": ["clear", "clear 10"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.describe(amount="How many messages to delete (default 5)")
    async def clear(
        self,
        ctx: commands.Context,
        amount: app_commands.Range[int, 1, config.MAX_CLEAR_AMOUNT] = 5,
    ) -> None:
        invoked_by_message = ctx.interaction is None
        if not invoked_by_message:
            await ctx.defer(ephemeral=True)

        purged = await ctx.channel.purge(limit=purge_limit(amount, invoked_by_message))
        count = deleted_count(len(purged), invoked_by_message)
        log.info(
            "%s (id=%s) cleared %d message(s) in #%s (guild=%s)",
            ctx.author,
            ctx.author.id,
            count,
            ctx.channel,
            ctx.guild,
        )
        await send_confirmation(ctx, clear_summary(count))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
