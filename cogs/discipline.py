from collections.abc import Awaitable, Callable
from datetime import timedelta
from functools import partial

import discord
from discord import app_commands
from discord.ext import commands

from core.durations import parse_duration
from core.errors import UserError
from modtools.actions import audit_reason, confirmation_text, enforce
from modtools.hierarchy import ensure_can_moderate
from modtools.models import DEFAULT_REASON, ModAction

MAX_TIMEOUT = timedelta(days=28)


class Discipline(commands.Cog, description="Kick, ban and time out members."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="kick",
        description="Kick a member from the server",
        extras={"examples": ["kick @user spamming links"]},
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @app_commands.describe(member="Member to kick", reason="Why they are being kicked")
    async def kick(
        self, ctx: commands.Context, member: discord.Member, *, reason: str = DEFAULT_REASON
    ) -> None:
        ensure_can_moderate(ctx, member)
        action = ModAction("Kick", "kicked", ctx.guild, ctx.author, member, reason)
        await self._enforce(ctx, action, partial(member.kick, reason=audit_reason(action)))

    @commands.hybrid_command(
        name="ban",
        description="Ban a user from the server",
        extras={"examples": ["ban @user repeated harassment"]},
    )
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(user="User to ban", reason="Why they are being banned")
    async def ban(
        self, ctx: commands.Context, user: discord.User, *, reason: str = DEFAULT_REASON
    ) -> None:
        member = ctx.guild.get_member(user.id)
        if member is not None:
            ensure_can_moderate(ctx, member)
        action = ModAction("Ban", "banned", ctx.guild, ctx.author, user, reason)
        await self._enforce(ctx, action, partial(ctx.guild.ban, user, reason=audit_reason(action)))

    @commands.hybrid_command(
        name="unban",
        description="Unban a user",
        extras={"examples": ["unban 123456789012345678 appealed"]},
    )
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @app_commands.describe(user="User to unban", reason="Why they are being unbanned")
    async def unban(
        self, ctx: commands.Context, user: discord.User, *, reason: str = DEFAULT_REASON
    ) -> None:
        action = ModAction("Unban", "unbanned", ctx.guild, ctx.author, user, reason)

        async def lift_ban() -> None:
            try:
                await ctx.guild.unban(user, reason=audit_reason(action))
            except discord.NotFound as error:
                raise UserError("That user isn't banned.") from error

        await self._enforce(ctx, action, lift_ban, notify=False)

    @commands.hybrid_command(
        name="timeout",
        description="Time a member out so they can't talk or react",
        extras={"examples": ["timeout @user 30m cooling off", "timeout @user 1d"]},
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.describe(
        member="Member to time out",
        duration="How long, like 30m, 2h, 3d or 1h30m (up to 28 days)",
        reason="Why they are being timed out",
    )
    async def timeout(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = DEFAULT_REASON,
    ) -> None:
        ensure_can_moderate(ctx, member)
        try:
            length = parse_duration(duration, MAX_TIMEOUT)
        except ValueError as error:
            raise commands.BadArgument(str(error)) from error
        action = ModAction("Timeout", "timed out", ctx.guild, ctx.author, member, reason, length)
        await self._enforce(
            ctx, action, partial(member.timeout, length, reason=audit_reason(action))
        )

    @commands.hybrid_command(
        name="untimeout",
        description="End a member's timeout early",
        extras={"examples": ["untimeout @user"]},
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to release", reason="Why the timeout is ending")
    async def untimeout(
        self, ctx: commands.Context, member: discord.Member, *, reason: str = DEFAULT_REASON
    ) -> None:
        ensure_can_moderate(ctx, member)
        action = ModAction("Timeout ended", "released", ctx.guild, ctx.author, member, reason)
        await self._enforce(
            ctx, action, partial(member.timeout, None, reason=audit_reason(action)), notify=False
        )

    async def _enforce(
        self,
        ctx: commands.Context,
        action: ModAction,
        perform: Callable[[], Awaitable[object]],
        notify: bool = True,
    ) -> None:
        notified = await enforce(self.bot, action, perform, notify)
        await ctx.send(confirmation_text(action, notified), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Discipline(bot))
