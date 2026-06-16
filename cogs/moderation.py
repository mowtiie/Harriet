import logging

from discord.ext import commands

log = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount: int = 5):
        deleted = await ctx.channel.purge(limit=amount + 1)
        count = len(deleted) - 1
        log.info(
            f"{ctx.author} (id={ctx.author.id}) cleared {count} message(s) "
            f"in #{ctx.channel} (guild={ctx.guild})"
        )
        confirmation = await ctx.send(f"Deleted {count} message(s).")
        await confirmation.delete(delay=3)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
