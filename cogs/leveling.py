import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from leveling.ranking import RankedMember, find_member, rank_members
from views.profile_view import build_profile_view
from views.rank_view import LeaderboardView, rank_fields
from views.style import NO_MENTIONS

log = logging.getLogger(__name__)

LEADERBOARD_TIMEOUT_SECONDS = 120
MAX_SET_XP = 10_000_000


class Leveling(commands.Cog, description="Earn XP by winning games and climb the board."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="rank",
        description="Show a member's level and XP",
        extras={"examples": ["rank", "rank @user"]},
    )
    @commands.guild_only()
    @app_commands.describe(member="Member to look up (defaults to you)")
    async def rank(self, ctx: commands.Context, member: discord.Member | None = None) -> None:
        member = member or ctx.author
        ranked = await self._ranked_members(ctx.guild)
        entry = find_member(ranked, member.id)
        xp = entry.xp if entry else await self.bot.experience_store.get(ctx.guild.id, member.id)
        subtitle = f"Rank {entry.position} of {len(ranked)}" if entry else "Unranked"
        view = build_profile_view(
            member.display_name, subtitle, rank_fields(xp), member.display_avatar.url
        )
        await ctx.send(view=view, allowed_mentions=NO_MENTIONS)

    @commands.hybrid_command(
        name="leaderboard",
        description="Show the server's XP leaderboard",
        extras={"examples": ["leaderboard"]},
    )
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context) -> None:
        ranked = await self._ranked_members(ctx.guild)
        view = LeaderboardView(ranked, ctx.author.id, LEADERBOARD_TIMEOUT_SECONDS)
        view.message = await ctx.send(view=view, allowed_mentions=NO_MENTIONS)

    @commands.hybrid_command(
        name="setxp",
        description="Set a member's total XP",
        extras={"examples": ["setxp @user 500"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(member="Member to change", amount="Their new total XP")
    async def setxp(
        self,
        ctx: commands.Context,
        member: discord.Member,
        amount: app_commands.Range[int, 0, MAX_SET_XP],
    ) -> None:
        await self.bot.experience_store.set(ctx.guild.id, member.id, amount)
        self._log_admin_change(ctx, member, f"set XP to {amount}")
        await ctx.send(f"Set **{member.display_name}** to {amount:,} XP.", ephemeral=True)

    @commands.hybrid_command(
        name="resetxp",
        description="Remove all of a member's XP",
        extras={"examples": ["resetxp @user"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(member="Member to reset")
    async def resetxp(self, ctx: commands.Context, member: discord.Member) -> None:
        await self.bot.experience_store.reset(ctx.guild.id, member.id)
        self._log_admin_change(ctx, member, "reset XP")
        await ctx.send(f"Reset **{member.display_name}**'s XP.", ephemeral=True)

    async def _ranked_members(self, guild: discord.Guild) -> list[RankedMember]:
        names = {member.id: member.display_name for member in guild.members if not member.bot}
        ranking = await self.bot.experience_store.ranking(guild.id)
        return rank_members(ranking, names)

    @staticmethod
    def _log_admin_change(ctx: commands.Context, member: discord.Member, change: str) -> None:
        log.info(
            "%s (id=%s) %s for %s (id=%s) in guild=%s",
            ctx.author,
            ctx.author.id,
            change,
            member,
            member.id,
            ctx.guild,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leveling(bot))
