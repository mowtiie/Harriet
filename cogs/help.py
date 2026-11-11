import logging
import platform

import discord
from discord import app_commands
from discord.ext import commands

import config
from core.errors import UserError
from views.help_data import (
    describe_command,
    find_command,
    group_into_categories,
    matching_command_names,
)
from views.help_view import HelpView, build_command_view
from views.info_view import BotInfo, build_info_view
from views.style import NO_MENTIONS

log = logging.getLogger(__name__)

AUTOCOMPLETE_LIMIT = 25
MILLISECONDS_PER_SECOND = 1000
TAGLINE = "Just a simple and helpful Discord bot that productively wants to make you happy."


async def is_visible_to(command: commands.Command, ctx: commands.Context) -> bool:
    if command.hidden:
        return False
    try:
        return await command.can_run(ctx)
    except UserError:
        # A check that explains itself (like needing to be in voice) means the command is available.
        return True
    except commands.CommandError:
        return False


class Help(
    commands.Cog,
    name="Help & Info",
    description="Learn what the bot can do and how to use it.",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._slash_mentions: dict[str, str] | None = None
        self._started_at = discord.utils.utcnow()

    @commands.hybrid_command(
        name="help",
        description="Browse commands, or get details for one",
        extras={"examples": ["help", "help clear"]},
    )
    @app_commands.describe(command="Command to show usage and examples for")
    async def show_help(self, ctx: commands.Context, command: str | None = None) -> None:
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        visible = [c for c in self.bot.walk_commands() if await is_visible_to(c, ctx)]
        mentions = await self._load_slash_mentions()

        if command is None:
            view = HelpView(
                group_into_categories(visible),
                prefix=config.COMMAND_PREFIX,
                mentions=mentions,
                author_id=ctx.author.id,
            )
            view.message = await ctx.send(view=view, ephemeral=True)
            return

        match = find_command(visible, command)
        if match is None:
            await ctx.send(f"No command named `{command}` is available to you.", ephemeral=True)
            return
        view = build_command_view(describe_command(match), config.COMMAND_PREFIX, mentions)
        await ctx.send(view=view, ephemeral=True)

    @show_help.autocomplete("command")
    async def autocomplete_command(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        names = matching_command_names(self.bot.walk_commands(), current, AUTOCOMPLETE_LIMIT)
        return [app_commands.Choice(name=name, value=name) for name in names]

    @commands.hybrid_command(
        name="info",
        description="Show information about the bot and how to use it",
        extras={"examples": ["info"]},
    )
    async def info(self, ctx: commands.Context) -> None:
        if ctx.interaction:
            await ctx.defer()
        application = await self.bot.application_info()
        await ctx.send(
            view=build_info_view(self._collect_info(application.owner)),
            allowed_mentions=NO_MENTIONS,
        )

    def _collect_info(self, owner: discord.User) -> BotInfo:
        return BotInfo(
            name=self.bot.user.display_name,
            tagline=TAGLINE,
            avatar_url=self.bot.user.display_avatar.url,
            version=config.BOT_VERSION,
            prefix=config.COMMAND_PREFIX,
            latency_ms=round(self.bot.latency * MILLISECONDS_PER_SECOND),
            uptime=discord.utils.utcnow() - self._started_at,
            guild_count=len(self.bot.guilds),
            owner_mention=owner.mention,
            python_version=platform.python_version(),
            discord_version=discord.__version__,
            repo_url=config.BOT_REPO_URL,
            support_url=config.BOT_SUPPORT_URL,
        )

    async def _load_slash_mentions(self) -> dict[str, str]:
        if self._slash_mentions is None:
            try:
                synced = await self.bot.tree.fetch_commands()
            except discord.HTTPException:
                log.warning("Could not fetch slash commands for mentions", exc_info=True)
                return {}
            self._slash_mentions = {command.name: command.mention for command in synced}
        return self._slash_mentions


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
