import logging

from discord import app_commands
from discord.ext import commands

import config
from guild_settings import VOLUME_KEY
from views.settings_view import build_settings_view

log = logging.getLogger(__name__)


class Settings(commands.Cog, description="View and change this server's settings."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="settings",
        description="Show this server's settings",
        extras={"examples": ["settings"]},
    )
    @commands.guild_only()
    async def settings(self, ctx: commands.Context) -> None:
        volume = await self.bot.guild_settings.get_int(
            ctx.guild.id, VOLUME_KEY, config.DEFAULT_VOLUME
        )
        await ctx.send(view=build_settings_view(ctx.guild.name, volume), ephemeral=True)

    @commands.hybrid_command(
        name="setvolume",
        description="Set the music volume for this server",
        extras={"examples": ["setvolume 40"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(level="Volume from 0 to 100")
    async def setvolume(
        self, ctx: commands.Context, level: app_commands.Range[int, 0, config.MAX_VOLUME_PERCENT]
    ) -> None:
        await self.bot.guild_settings.set(ctx.guild.id, VOLUME_KEY, str(level))
        log.info(
            "%s (id=%s) set volume to %d%% in guild=%s", ctx.author, ctx.author.id, level, ctx.guild
        )
        await ctx.send(f"Volume set to {level}%. It applies from the next track.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Settings(bot))
