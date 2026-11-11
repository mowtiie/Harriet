import discord
from discord.ext import commands

INVITE_PERMISSIONS = discord.Permissions(
    send_messages=True,
    read_message_history=True,
    manage_messages=True,
)


def build_invite_url(client_id: int) -> str:
    return discord.utils.oauth_url(
        client_id,
        permissions=INVITE_PERMISSIONS,
        scopes=("bot", "applications.commands"),
    )


class General(commands.Cog, description="Everyday commands for everyone."):
    icon = "🏠"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        description="Replies with pong and current latency",
        extras={"examples": ["ping"]},
    )
    async def ping(self, ctx: commands.Context) -> None:
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! ({latency_ms}ms)")

    @commands.hybrid_command(name="hello", description="Say hello!", extras={"examples": ["hello"]})
    async def hello(self, ctx: commands.Context) -> None:
        await ctx.send(f"Hello {ctx.author.mention}!")

    @commands.hybrid_command(
        name="invite",
        description="Get the bot's invite link (owner only)",
        extras={"examples": ["invite"]},
    )
    @commands.is_owner()
    async def invite(self, ctx: commands.Context) -> None:
        await ctx.send(build_invite_url(self.bot.user.id), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
