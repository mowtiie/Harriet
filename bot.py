import asyncio
import logging
import os
import sys
import traceback

import discord
from discord import app_commands
from discord.ext import commands

import config
from logger import setup_logging

setup_logging(config.LOG_LEVEL)
log = logging.getLogger("bot")

if not config.TOKEN:
    log.critical("DISCORD_TOKEN is missing. Add it to your .env file.")
    sys.exit(1)


STATUS_MAP = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible,
}

ACTIVITY_MAP = {
    "playing": discord.ActivityType.playing,
    "listening": discord.ActivityType.listening,
    "watching": discord.ActivityType.watching,
    "competing": discord.ActivityType.competing,
}


def build_presence(status: str, activity_type: str, activity_name: str):
    discord_status = STATUS_MAP.get(status.lower(), discord.Status.online)
    activity = discord.Activity(
        type=ACTIVITY_MAP.get(activity_type.lower(), discord.ActivityType.playing),
        name=activity_name,
    )
    return discord_status, activity


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)
bot.build_presence = build_presence


@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    log.info(f"Connected to {len(bot.guilds)} guild(s)")

    status, activity = build_presence(
        config.BOT_STATUS, config.BOT_ACTIVITY_TYPE, config.BOT_ACTIVITY_NAME
    )
    await bot.change_presence(status=status, activity=activity)
    log.info(
        f"Presence: {config.BOT_STATUS} | "
        f"{config.BOT_ACTIVITY_TYPE} {config.BOT_ACTIVITY_NAME}"
    )

    try:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} slash command(s)")
    except Exception:
        log.exception("Slash command sync failed")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to do that.")
        return
    if isinstance(error, commands.NotOwner):
        await ctx.send("This command is restricted to the bot owner.")
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"Bad argument: {error}")
        return

    log.error(
        f"Unhandled error in '{ctx.command}' invoked by {ctx.author} in #{ctx.channel}",
        exc_info=error,
    )
    await ctx.send("Something went wrong. The error has been logged.")


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    log.error(
        f"Unhandled error in slash command '{interaction.command}' "
        f"invoked by {interaction.user}",
        exc_info=error,
    )
    msg = "Something went wrong. The error has been logged."
    if interaction.response.is_done():
        await interaction.followup.send(msg, ephemeral=True)
    else:
        await interaction.response.send_message(msg, ephemeral=True)


@bot.event
async def on_error(event_method: str, *args, **kwargs):
    log.error(f"Unhandled exception in event '{event_method}'")
    log.error(traceback.format_exc())


async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            extension = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(extension)
                log.info(f"Loaded cog: {extension}")
            except Exception:
                log.exception(f"Failed to load cog: {extension}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(config.TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bot stopped by user")
