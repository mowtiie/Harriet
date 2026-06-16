import logging
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

import bot as bot_module

log = logging.getLogger(__name__)


class Presence(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="setpresence",
        description="Change the bot's status and activity (owner only)",
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
    ):
        discord_status, activity = bot_module.build_presence(status, activity_type, text)
        await self.bot.change_presence(status=discord_status, activity=activity)
        log.info(
            f"{ctx.author} changed presence to: {status} | {activity_type} {text}"
        )
        await ctx.send(
            f"Presence updated: **{status}** | {activity_type} **{text}**",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Presence(bot))
