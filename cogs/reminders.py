import logging
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config
from core.durations import parse_duration
from utilities.errors import UtilityError
from utilities.reminder_store import Reminder
from views.reminders_view import build_reminders_view, format_delivery

log = logging.getLogger(__name__)

REMINDER_CHECK_SECONDS = 10
MAX_REMINDER_LENGTH = 200


class Reminders(commands.Cog, description="Get reminded about things later."):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self.deliver_due.start()

    async def cog_unload(self) -> None:
        self.deliver_due.cancel()

    @commands.hybrid_command(
        name="remind",
        description="Get a reminder after a delay",
        extras={"examples": ["remind 30m take the pizza out", "remind 1d renew the domain"]},
    )
    @app_commands.describe(
        duration="When, like 30m, 2h, 1d or 1h30m", text="What to remind you about"
    )
    async def remind(self, ctx: commands.Context, duration: str, *, text: str) -> None:
        text = text.strip()
        if len(text) > MAX_REMINDER_LENGTH:
            raise UtilityError(f"Keep reminders under {MAX_REMINDER_LENGTH} characters.")
        try:
            delay = parse_duration(duration, timedelta(days=config.MAX_REMINDER_DAYS))
        except ValueError as error:
            raise commands.BadArgument(str(error)) from error

        store = self.bot.reminder_store
        if await store.count_for(ctx.author.id) >= config.MAX_REMINDERS_PER_USER:
            raise UtilityError(
                f"You can have up to {config.MAX_REMINDERS_PER_USER} pending reminders. "
                "Cancel one with `/unremind` first."
            )
        due_at = discord.utils.utcnow() + delay
        reminder_id = await store.add(ctx.author.id, ctx.channel.id, text, due_at)
        when = discord.utils.format_dt(due_at, "R")
        await ctx.send(f"I'll remind you {when}. (`#{reminder_id}`)", ephemeral=True)

    @commands.hybrid_command(
        name="reminders",
        description="Show your pending reminders",
        extras={"examples": ["reminders"]},
    )
    async def reminders(self, ctx: commands.Context) -> None:
        pending = await self.bot.reminder_store.list_for(ctx.author.id)
        await ctx.send(view=build_reminders_view(pending), ephemeral=True)

    @commands.hybrid_command(
        name="unremind",
        description="Cancel one of your reminders",
        extras={"examples": ["unremind 3"]},
    )
    @app_commands.describe(reminder_id="The number shown by /reminders")
    async def unremind(self, ctx: commands.Context, reminder_id: int) -> None:
        if not await self.bot.reminder_store.cancel(ctx.author.id, reminder_id):
            raise UtilityError(f"You have no reminder `#{reminder_id}`.")
        await ctx.send(f"Cancelled reminder `#{reminder_id}`.", ephemeral=True)

    @tasks.loop(seconds=REMINDER_CHECK_SECONDS)
    async def deliver_due(self) -> None:
        for reminder in await self.bot.reminder_store.due(discord.utils.utcnow()):
            await self._deliver(reminder)
            await self.bot.reminder_store.complete(reminder.id)

    @deliver_due.before_loop
    async def wait_until_ready(self) -> None:
        await self.bot.wait_until_ready()

    async def _deliver(self, reminder: Reminder) -> None:
        content = format_delivery(reminder, discord.utils.utcnow())
        mentions = discord.AllowedMentions(
            users=[discord.Object(reminder.user_id)], roles=False, everyone=False
        )
        channel = self.bot.get_channel(reminder.channel_id)
        if channel is not None:
            try:
                await channel.send(content, allowed_mentions=mentions)
                return
            except discord.HTTPException:
                log.info("Could not post reminder #%d in its channel; trying a DM", reminder.id)
        try:
            user = await self.bot.fetch_user(reminder.user_id)
            await user.send(content)
        except discord.HTTPException:
            log.warning("Could not deliver reminder #%d to user %d", reminder.id, reminder.user_id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reminders(bot))
