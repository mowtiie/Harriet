import logging

import discord
from discord import app_commands
from discord.ext import commands

import config
from modtools.errors import ModerationError
from time_format import SECONDS_PER_HOUR

log = logging.getLogger(__name__)

CONFIRMATION_DELETE_DELAY_SECONDS = 3
MAX_SLOWMODE_SECONDS = 6 * SECONDS_PER_HOUR


def purge_limit(amount: int, invoked_by_message: bool) -> int:
    """Prefix commands also match their own message, so they need one extra slot."""
    return amount + 1 if invoked_by_message else amount


def deleted_count(purged: int, invoked_by_message: bool) -> int:
    return max(purged - 1, 0) if invoked_by_message else purged


def clear_summary(count: int) -> str:
    return f"Deleted {count} message(s)."


def audit_reason(ctx: commands.Context, action: str) -> str:
    return f"{action} by {ctx.author} ({ctx.author.id})"


def text_channel_of(ctx: commands.Context) -> discord.TextChannel:
    if not isinstance(ctx.channel, discord.TextChannel):
        raise ModerationError("This only works in text channels.")
    return ctx.channel


async def send_confirmation(ctx: commands.Context, text: str) -> None:
    if ctx.interaction:
        await ctx.send(text, ephemeral=True)
        return
    confirmation = await ctx.send(text)
    await confirmation.delete(delay=CONFIRMATION_DELETE_DELAY_SECONDS)


class Moderation(commands.Cog, description="Keep your channels tidy."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="clear",
        description="Delete the last N messages in this channel",
        extras={"examples": ["clear", "clear 10"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @app_commands.describe(amount="How many messages to delete (default 5)")
    async def clear(
        self,
        ctx: commands.Context,
        amount: app_commands.Range[int, 1, config.MAX_CLEAR_AMOUNT] = 5,
    ) -> None:
        invoked_by_message = ctx.interaction is None
        if not invoked_by_message:
            await ctx.defer(ephemeral=True)

        purged = await ctx.channel.purge(limit=purge_limit(amount, invoked_by_message))
        count = deleted_count(len(purged), invoked_by_message)
        log.info(
            "%s (id=%s) cleared %d message(s) in #%s (guild=%s)",
            ctx.author,
            ctx.author.id,
            count,
            ctx.channel,
            ctx.guild,
        )
        await send_confirmation(ctx, clear_summary(count))

    @commands.hybrid_command(
        name="slowmode",
        description="Set how often members can send messages in this channel",
        extras={"examples": ["slowmode 10", "slowmode 0"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Seconds between messages (0 turns it off)")
    async def slowmode(
        self, ctx: commands.Context, seconds: app_commands.Range[int, 0, MAX_SLOWMODE_SECONDS]
    ) -> None:
        channel = text_channel_of(ctx)
        await channel.edit(slowmode_delay=seconds, reason=audit_reason(ctx, "Slowmode"))
        log.info(
            "%s (id=%s) set slowmode to %ds in #%s", ctx.author, ctx.author.id, seconds, channel
        )
        text = f"Slowmode set to {seconds}s." if seconds else "Slowmode turned off."
        await ctx.send(text, ephemeral=True)

    @commands.hybrid_command(
        name="lock",
        description="Stop everyone from sending messages in this channel",
        extras={"examples": ["lock"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def lock(self, ctx: commands.Context) -> None:
        await self._set_send_permission(ctx, allowed=False, label="Locked")

    @commands.hybrid_command(
        name="unlock",
        description="Let everyone send messages in this channel again",
        extras={"examples": ["unlock"]},
    )
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unlock(self, ctx: commands.Context) -> None:
        await self._set_send_permission(ctx, allowed=None, label="Unlocked")

    async def _set_send_permission(
        self, ctx: commands.Context, allowed: bool | None, label: str
    ) -> None:
        channel = text_channel_of(ctx)
        everyone = ctx.guild.default_role
        overwrite = channel.overwrites_for(everyone)
        overwrite.send_messages = allowed
        await channel.set_permissions(
            everyone,
            overwrite=None if overwrite.is_empty() else overwrite,
            reason=audit_reason(ctx, label),
        )
        log.info("%s (id=%s) %s #%s", ctx.author, ctx.author.id, label.lower(), channel)
        await ctx.send(f"{label} {channel.mention}.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
