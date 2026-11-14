import asyncio
import io
import logging
from pathlib import Path
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

import config
from core.errors import UserError
from core.live_views import count_unfinished
from core.reloading import discover_extensions, format_report, plan_reload, reload_extensions
from features.devtools.backup import BackupError, backup_filename, snapshot_database
from features.devtools.git_info import current_commit, has_uncommitted_changes
from features.devtools.logs import (
    DEFAULT_LINES,
    build_log_reply,
    error_entries,
    read_log_tail,
    summarize_error,
)
from features.devtools.status import MILLISECONDS_PER_SECOND, StatusInfo, format_size, format_status
from logger import LOG_FILE

log = logging.getLogger(__name__)

COGS_DIR = Path(__file__).parent
ROOT_DIR = COGS_DIR.parent
OWN_EXTENSION = __name__
AUTOCOMPLETE_LIMIT = 25
LOG_FILE_NAME = "bot-log.txt"
DM_BLOCKED_TEXT = "I can't DM you. Allow DMs from this server, or use the slash command."


async def deliver_privately(
    ctx: commands.Context, content: str, file: discord.File | None = None
) -> None:
    """Only the owner may see this: a private reply, or a DM when run with the prefix."""
    if ctx.interaction:
        await ctx.send(content, file=file, ephemeral=True)
        return
    try:
        await ctx.author.send(content, file=file)
    except discord.Forbidden as error:
        raise UserError(DM_BLOCKED_TEXT) from error
    await ctx.send("Sent you a DM.")


class Developer(commands.Cog, description="Tools for the bot owner."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="reload",
        description="Reload cogs without restarting the bot (owner only)",
        extras={"examples": ["reload", "reload games"]},
    )
    @commands.is_owner()
    @app_commands.describe(cog="Cog file to reload, like games (leave empty for all)")
    async def reload(self, ctx: commands.Context, cog: str | None = None) -> None:
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        plan = plan_reload(
            available=discover_extensions(COGS_DIR),
            loaded=self.bot.extensions,
            requested=f"{COGS_DIR.name}.{cog.strip().lower()}" if cog else None,
            reload_last=OWN_EXTENSION,
        )
        report = await reload_extensions(self.bot, plan, self.bot.core_modules)
        target = cog or "all cogs"
        log.info("%s ran reload for %s (%d changes)", ctx.author, target, len(report.results))
        await ctx.send(format_report(report), ephemeral=True)

    @reload.autocomplete("cog")
    async def autocomplete_cog(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if not await self.bot.is_owner(interaction.user):
            return []
        names = (extension.rsplit(".", 1)[-1] for extension in discover_extensions(COGS_DIR))
        matching = [name for name in names if current.strip().lower() in name]
        return [app_commands.Choice(name=n, value=n) for n in matching[:AUTOCOMPLETE_LIMIT]]

    @commands.hybrid_command(
        name="status",
        description="Show how the bot is doing (owner only)",
        extras={"examples": ["status"]},
    )
    @commands.is_owner()
    async def status(self, ctx: commands.Context) -> None:
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        await deliver_privately(ctx, format_status(await self._collect_status()))

    @commands.hybrid_command(
        name="logs",
        description="Show the end of the bot's log (owner only)",
        extras={"examples": ["logs", "logs 50", "logs 40 errors"]},
    )
    @commands.is_owner()
    @app_commands.describe(lines="How many lines to show", show="Everything, or only errors")
    async def logs(
        self,
        ctx: commands.Context,
        lines: int = DEFAULT_LINES,
        show: Literal["all", "errors"] = "all",
    ) -> None:
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        text = await asyncio.to_thread(read_log_tail, LOG_FILE)
        reply = build_log_reply(text, lines, errors_only=show == "errors")
        attachment = None
        if reply.attachment is not None:
            attachment = discord.File(io.BytesIO(reply.attachment.encode()), filename=LOG_FILE_NAME)
        log.info("%s read the log (%s, %d lines)", ctx.author, show, lines)
        await deliver_privately(ctx, reply.message, attachment)

    @commands.hybrid_command(
        name="backup",
        description="Send you a copy of the database (owner only)",
        extras={"examples": ["backup"]},
    )
    @commands.is_owner()
    async def backup(self, ctx: commands.Context) -> None:
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
        try:
            data = await asyncio.to_thread(snapshot_database, config.DATABASE_PATH)
        except BackupError as error:
            raise UserError(str(error)) from error
        filename = backup_filename(discord.utils.utcnow())
        log.info("%s took a database backup (%d bytes)", ctx.author, len(data))
        message = f"Database snapshot, {format_size(len(data))}. It holds user IDs and warnings."
        await deliver_privately(ctx, message, discord.File(io.BytesIO(data), filename=filename))

    async def _collect_status(self) -> StatusInfo:
        bot = self.bot
        log_text = await asyncio.to_thread(read_log_tail, LOG_FILE)
        errors = error_entries(log_text)
        commit, dirty = await asyncio.gather(
            asyncio.to_thread(current_commit, ROOT_DIR),
            asyncio.to_thread(has_uncommitted_changes, ROOT_DIR),
        )
        database = config.DATABASE_PATH
        return StatusInfo(
            uptime=discord.utils.utcnow() - bot.started_at,
            latency_ms=round(bot.latency * MILLISECONDS_PER_SECOND),
            guild_count=len(bot.guilds),
            voice_connections=len(bot.voice_clients),
            active_games=count_unfinished(),
            commit=commit,
            started_commit=bot.started_commit,
            has_uncommitted_changes=dirty,
            loaded_cogs=len(bot.extensions),
            unloaded_cogs=tuple(
                name for name in discover_extensions(COGS_DIR) if name not in bot.extensions
            ),
            command_count=len(bot.tree.get_commands()),
            database_bytes=database.stat().st_size if database.is_file() else None,
            error_count=len(errors),
            last_error=summarize_error(errors[-1]) if errors else None,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Developer(bot))
