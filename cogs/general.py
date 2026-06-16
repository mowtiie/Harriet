import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Replies with pong and current latency")
    async def ping(self, ctx: commands.Context):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! ({latency_ms}ms)")

    @commands.hybrid_command(name="hello", description="Say hello!")
    async def hello(self, ctx: commands.Context):
        await ctx.send(f"Hello {ctx.author.mention}!")


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
