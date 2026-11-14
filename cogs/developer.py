import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from core.reloading import discover_extensions, format_report, plan_reload, reload_extensions

log = logging.getLogger(__name__)

COGS_DIR = Path(__file__).parent
OWN_EXTENSION = __name__
AUTOCOMPLETE_LIMIT = 25


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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Developer(bot))
