import logging

import discord
from discord import app_commands
from discord.ext import commands

import config

log = logging.getLogger(__name__)


def purge_limit(amount: int, invoked_by_message: bool) -> int:
    """Return how many messages to scan so `amount` others are deleted.

    A prefix invocation's own message is in the channel history and counts
    toward the purge limit, so it needs one extra slot.
    """
    return amount + 1 if invoked_by_message else amount


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
    ):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        deleted = await ctx.channel.purge(limit=purge_limit(amount, ctx.interaction is None))
        log.info(
            f"{ctx.author} (id={ctx.author.id}) cleared {len(deleted)} message(s) "
            f"in #{ctx.channel} (guild={ctx.guild})"
        )

        if ctx.interaction:
            await ctx.send(f"Deleted {len(deleted)} message(s).", ephemeral=True)
        else:
            confirmation = await ctx.send(f"Deleted {len(deleted)} message(s).")
            await confirmation.delete(delay=3)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
