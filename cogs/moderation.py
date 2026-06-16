import logging

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="clear", description="Delete the last N messages in this channel")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount="How many messages to delete (default 5)")
    async def clear(self, ctx: commands.Context, amount: int = 5):
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        deleted = await ctx.channel.purge(limit=amount)
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
