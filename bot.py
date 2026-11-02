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

setup_logging(config.LOG_LEVEL)
log = logging.getLogger("bot")

if not config.TOKEN:
    log.critical("DISCORD_TOKEN is missing. Add it to your .env file.")
    sys.exit(1)


COGS_DIR = Path(__file__).parent / "cogs"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

initial_status, initial_activity = build_presence(
    config.BOT_STATUS, config.BOT_ACTIVITY_TYPE, config.BOT_ACTIVITY_NAME
)

bot = commands.Bot(
    command_prefix=config.COMMAND_PREFIX,
    intents=intents,
    status=initial_status,
    activity=initial_activity,
)


@bot.event
async def setup_hook():
    """Load cogs and sync slash commands once, before the first connect."""
    await load_cogs()
    try:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} slash command(s)")
    except Exception:
        log.exception("Slash command sync failed")


@bot.event
async def on_ready():
    """Log connection details; runs again on every reconnect."""
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    log.info(f"Connected to {len(bot.guilds)} guild(s)")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
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


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
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


@bot.event
async def on_error(event_method: str, *args, **kwargs):
    """Log exceptions raised inside event handlers."""
    log.exception(f"Unhandled exception in event '{event_method}'")


async def load_cogs():
    for path in sorted(COGS_DIR.glob("[!_]*.py")):
        extension = f"cogs.{path.stem}"
        try:
            await bot.load_extension(extension)
            log.info(f"Loaded cog: {extension}")
        except Exception:
            log.exception(f"Failed to load cog: {extension}")


async def main():
    async with bot:
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot stopped by user")
