"""Entry point: builds the bot, wires global handlers and starts it."""

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
    """Reply to prefix and hybrid command failures, logging unexpected ones."""
    if isinstance(error, commands.CommandNotFound):
        return

    message = describe_error(error)
    if message is None:
        log.error(
            f"Unhandled error in '{ctx.command}' invoked by {ctx.author} in #{ctx.channel}",
            exc_info=error,
        )
        message = GENERIC_ERROR_MESSAGE
    await ctx.send(message, ephemeral=True)


async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    """Reply to plain slash command failures, logging unexpected ones."""
    message = describe_error(error)
    if message is None:
        log.error(
            f"Unhandled error in slash command '{interaction.command}' "
            f"invoked by {interaction.user}",
            exc_info=error,
        )
        message = GENERIC_ERROR_MESSAGE
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


async def on_error(event_method: str, *args: object, **kwargs: object) -> None:
    """Log exceptions raised inside event handlers."""
    log.exception(f"Unhandled exception in event '{event_method}'")


async def load_cogs(bot: commands.Bot) -> None:
    """Load every public module in the cogs directory, logging failures."""
    for path in sorted(COGS_DIR.glob("[!_]*.py")):
        extension = f"cogs.{path.stem}"
        try:
            await bot.load_extension(extension)
            log.info(f"Loaded cog: {extension}")
        except Exception:
            log.exception(f"Failed to load cog: {extension}")


def create_bot() -> commands.Bot:
    """Build the bot with intents, initial presence and global handlers."""
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
        """Load cogs and sync slash commands once, before the first connect."""
        await load_cogs(bot)
        try:
            synced = await bot.tree.sync()
            log.info(f"Synced {len(synced)} slash command(s)")
        except Exception:
            log.exception("Slash command sync failed")

    async def on_ready() -> None:
        """Log connection details; runs again on every reconnect."""
        log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        log.info(f"Connected to {len(bot.guilds)} guild(s)")

    bot.event(setup_hook)
    bot.event(on_ready)
    bot.event(on_command_error)
    bot.event(on_error)
    bot.tree.error(on_app_command_error)
    return bot


async def run(bot: commands.Bot) -> None:
    """Connect the bot to Discord and block until it stops."""
    async with bot:
        await bot.start(config.TOKEN)


def main() -> None:
    """Configure logging, check the token and run the bot."""
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
