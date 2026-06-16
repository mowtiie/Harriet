import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = "do "
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
