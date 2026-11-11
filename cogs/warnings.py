import logging

import discord
from discord import app_commands
from discord.ext import commands

from modtools.actions import confirmation_text, enforce
from modtools.hierarchy import ensure_can_moderate
from modtools.models import ModAction
from views.warnings_view import build_warnings_view

log = logging.getLogger(__name__)


class Warnings(commands.Cog, description="Keep a record of warnings for each member."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="warn",
        description="Warn a member and keep a record of it",
        extras={"examples": ["warn @user please keep chat on topic"]},
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to warn", reason="What they are being warned about")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str) -> None:
        ensure_can_moderate(ctx, member)
        action = ModAction("Warning", "warned", ctx.guild, ctx.author, member, reason)
        total = 0

        async def record_warning() -> None:
            nonlocal total
            total = await self.bot.warning_store.add(
                ctx.guild.id, member.id, ctx.author.id, reason
            )

        notified = await enforce(self.bot, action, record_warning)
        await ctx.send(
            f"{confirmation_text(action, notified)} They now have {total} warning(s).",
            ephemeral=True,
        )

    @commands.hybrid_command(
        name="warnings",
        description="Show a member's warnings",
        extras={"examples": ["warnings @user"]},
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to look up")
    async def warnings(self, ctx: commands.Context, member: discord.Member) -> None:
        records = await self.bot.warning_store.list_for(ctx.guild.id, member.id)
        await ctx.send(view=build_warnings_view(str(member), records), ephemeral=True)

    @commands.hybrid_command(
        name="clearwarnings",
        description="Remove all of a member's warnings",
        extras={"examples": ["clearwarnings @user"]},
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member whose warnings to remove")
    async def clearwarnings(self, ctx: commands.Context, member: discord.Member) -> None:
        removed = await self.bot.warning_store.clear(ctx.guild.id, member.id)
        log.info(
            "%s (id=%s) cleared %d warning(s) for %s (id=%s) in guild=%s",
            ctx.author,
            ctx.author.id,
            removed,
            member,
            member.id,
            ctx.guild,
        )
        await ctx.send(f"Removed {removed} warning(s) from **{member}**.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Warnings(bot))
