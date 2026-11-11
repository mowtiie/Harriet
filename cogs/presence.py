import logging
from typing import Literal

from discord import app_commands
from discord.ext import commands

from presence_utils import build_presence

log = logging.getLogger(__name__)


class Presence(commands.Cog, description="Change what the bot is up to."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="setpresence",
        description="Change the bot's status and activity (owner only)",
        extras={
            "examples": [
                "setpresence online watching the server",
                "setpresence dnd playing hide and seek",
            ]
        },
    )
    @commands.is_owner()
    @app_commands.describe(
        status="Online status",
        activity_type="Type of activity to show",
        text="Text shown after the activity type",
    )
    async def setpresence(
        self,
        ctx: commands.Context,
        status: Literal["online", "idle", "dnd", "invisible"],
        activity_type: Literal["playing", "listening", "watching", "competing"],
        *,
        text: str,
    ) -> None:
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        discord_status, activity = build_presence(status, activity_type, text)
        await self.bot.change_presence(status=discord_status, activity=activity)
        log.info("%s changed presence to: %s | %s %s", ctx.author, status, activity_type, text)
        await ctx.send(
            f"Presence updated: **{status}** | {activity_type} **{text}**",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Presence(bot))
