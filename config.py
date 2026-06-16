import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "do ")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

BOT_STATUS = os.getenv("BOT_STATUS", "online")
BOT_ACTIVITY_TYPE = os.getenv("BOT_ACTIVITY_TYPE", "playing")
BOT_ACTIVITY_NAME = os.getenv("BOT_ACTIVITY_NAME", "with discord.py")
