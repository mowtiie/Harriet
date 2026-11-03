import asyncio
import logging
import sys
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config
from error_messages import GENERIC_ERROR_MESSAGE, describe_error
from logger import setup_logging
from presence_utils import build_presence

log = logging.getLogger("bot")

COGS_DIR = Path(__file__).parent / "cogs"


async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    if isinstance(error, commands.CommandNotFound):
        return

    message = describe_error(error)
    if message is None:
        log.error(
            "Unhandled error in '%s' invoked by %s in #%s",
            ctx.command,
            ctx.author,
            ctx.channel,
            exc_info=error,
        )
        message = GENERIC_ERROR_MESSAGE
    try:
        await ctx.send(message, ephemeral=True)
    except discord.HTTPException:
        log.warning(
            "Could not send error reply for '%s'; the interaction may have expired",
            ctx.command,
            exc_info=True,
        )


async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    message = describe_error(error)
    if message is None:
        log.error(
            "Unhandled error in slash command '%s' invoked by %s",
            interaction.command,
            interaction.user,
            exc_info=error,
        )
        message = GENERIC_ERROR_MESSAGE
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


async def on_error(event_method: str, *args: object, **kwargs: object) -> None:
    log.exception("Unhandled exception in event '%s'", event_method)


async def load_cogs(bot: commands.Bot) -> None:
    for path in sorted(COGS_DIR.glob("[!_]*.py")):
        extension = f"cogs.{path.stem}"
        try:
            await bot.load_extension(extension)
            log.info("Loaded cog: %s", extension)
        except Exception:
            log.exception("Failed to load cog: %s", extension)


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    status, activity = build_presence(
        config.BOT_STATUS, config.BOT_ACTIVITY_TYPE, config.BOT_ACTIVITY_NAME
    )
    bot = commands.Bot(
        command_prefix=config.COMMAND_PREFIX,
        intents=intents,
        status=status,
        activity=activity,
    )

    async def setup_hook() -> None:
        """Runs once per process, unlike on_ready."""
        await load_cogs(bot)
        try:
            synced = await bot.tree.sync()
            log.info("Synced %d slash command(s)", len(synced))
        except Exception:
            log.exception("Slash command sync failed")

    async def on_ready() -> None:
        """Runs again on every reconnect, so only log here."""
        log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
        log.info("Connected to %d guild(s)", len(bot.guilds))

    bot.event(setup_hook)
    bot.event(on_ready)
    bot.event(on_command_error)
    bot.event(on_error)
    bot.tree.error(on_app_command_error)
    return bot


async def run(bot: commands.Bot) -> None:
    async with bot:
        await bot.start(config.TOKEN)


def main() -> None:
    setup_logging(config.LOG_LEVEL)
    if not config.TOKEN:
        log.critical("DISCORD_TOKEN is missing. Add it to your .env file.")
        sys.exit(1)

    try:
        asyncio.run(run(create_bot()))
    except KeyboardInterrupt:
        log.info("Bot stopped by user")


if __name__ == "__main__":
    main()
