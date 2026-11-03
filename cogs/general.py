"""General-purpose commands."""

import discord
from discord.ext import commands

INVITE_PERMISSIONS = discord.Permissions(
    send_messages=True,
    read_message_history=True,
    manage_messages=True,
)


def build_invite_url(client_id: int) -> str:
    """Return the OAuth2 URL that adds the bot with the permissions it needs."""
    return discord.utils.oauth_url(
        client_id,
        permissions=INVITE_PERMISSIONS,
        scopes=("bot", "applications.commands"),
    )


class General(commands.Cog):
    """Everyday commands available to everyone."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Replies with pong and current latency")
    async def ping(self, ctx: commands.Context) -> None:
        """Reply with the gateway latency."""
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! ({latency_ms}ms)")

    @commands.hybrid_command(name="hello", description="Say hello!")
    async def hello(self, ctx: commands.Context) -> None:
        """Greet the user."""
        await ctx.send(f"Hello {ctx.author.mention}!")

    @commands.hybrid_command(name="invite", description="Get the bot's invite link (owner only)")
    @commands.is_owner()
    async def invite(self, ctx: commands.Context) -> None:
        """Send the invite link with the bot's current permissions."""
        await ctx.send(build_invite_url(self.bot.user.id), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Register the General cog."""
    await bot.add_cog(General(bot))
