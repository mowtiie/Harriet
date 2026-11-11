import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from core.errors import UserError
from core.guild_settings import MODLOG_CHANNEL_KEY, VOLUME_KEY
from features.settings.settings_view import build_settings_view

log = logging.getLogger(__name__)

NOT_SET_LABEL = "Not set"


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
        store = self.bot.guild_settings
        volume = await store.get_int(ctx.guild.id, VOLUME_KEY, config.DEFAULT_VOLUME)
        modlog = await self._modlog_label(ctx.guild)
        await ctx.send(view=build_settings_view(ctx.guild.name, volume, modlog), ephemeral=True)

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

    @commands.hybrid_command(
        name="setmodlog",
        description="Set the channel where moderation actions are logged",
        extras={"examples": ["setmodlog #mod-log", "setmodlog"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(channel="Channel for the log (leave empty to turn it off)")
    async def setmodlog(
        self, ctx: commands.Context, channel: discord.TextChannel | None = None
    ) -> None:
        if channel is None:
            await self.bot.guild_settings.delete(ctx.guild.id, MODLOG_CHANNEL_KEY)
            text = "Mod-log turned off."
        else:
            if not channel.permissions_for(ctx.guild.me).send_messages:
                raise UserError(f"I can't send messages in {channel.mention}.")
            await self.bot.guild_settings.set(ctx.guild.id, MODLOG_CHANNEL_KEY, str(channel.id))
            text = f"Moderation actions will be logged in {channel.mention}."
        log.info("%s (id=%s) changed the mod-log channel in guild=%s", ctx.author, ctx.author.id, ctx.guild)
        await ctx.send(text, ephemeral=True)

    async def _modlog_label(self, guild: discord.Guild) -> str:
        raw_channel_id = await self.bot.guild_settings.get(guild.id, MODLOG_CHANNEL_KEY)
        channel = guild.get_channel(int(raw_channel_id)) if raw_channel_id else None
        return channel.mention if channel else NOT_SET_LABEL


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Settings(bot))
