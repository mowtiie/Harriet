import os
from collections.abc import Collection
from pathlib import Path

from dotenv import load_dotenv

from presence_utils import ACTIVITY_MAP, STATUS_MAP

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class ConfigError(ValueError):
    pass


def parse_choice(name: str, raw: str, allowed: Collection[str]) -> str:
    value = raw.strip().lower()
    if value not in {option.lower() for option in allowed}:
        options = ", ".join(allowed)
        raise ConfigError(f"{name} must be one of: {options} (got {raw!r})")
    return value


def parse_int_range(name: str, raw: str, minimum: int, maximum: int) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer (got {raw!r})") from None
    if not minimum <= value <= maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum} (got {value})")
    return value


def parse_positive_int(name: str, raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer (got {raw!r})") from None
    if value < 1:
        raise ConfigError(f"{name} must be at least 1 (got {value})")
    return value


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "do ")
LOG_LEVEL = parse_choice("LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO"), LOG_LEVELS).upper()

BOT_STATUS = parse_choice("BOT_STATUS", os.getenv("BOT_STATUS", "online"), STATUS_MAP)
BOT_ACTIVITY_TYPE = parse_choice(
    "BOT_ACTIVITY_TYPE", os.getenv("BOT_ACTIVITY_TYPE", "playing"), ACTIVITY_MAP
)
BOT_ACTIVITY_NAME = os.getenv("BOT_ACTIVITY_NAME", "with discord.py")

MAX_CLEAR_AMOUNT = parse_positive_int("MAX_CLEAR_AMOUNT", os.getenv("MAX_CLEAR_AMOUNT", "100"))

BOT_VERSION = os.getenv("BOT_VERSION", "1.0.0")
BOT_REPO_URL = os.getenv("BOT_REPO_URL", "https://github.com/mowtiie/Harriet")
BOT_SUPPORT_URL = os.getenv("BOT_SUPPORT_URL", "")

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/harriet.db"))
MUSIC_DIR = Path(os.getenv("MUSIC_DIR", "music"))
MAX_VOLUME_PERCENT = 100
DEFAULT_VOLUME = parse_int_range(
    "DEFAULT_VOLUME", os.getenv("DEFAULT_VOLUME", "50"), 0, MAX_VOLUME_PERCENT
)
MAX_QUEUE_SIZE = parse_positive_int("MAX_QUEUE_SIZE", os.getenv("MAX_QUEUE_SIZE", "50"))
MUSIC_IDLE_TIMEOUT_SECONDS = parse_positive_int(
    "MUSIC_IDLE_TIMEOUT_SECONDS", os.getenv("MUSIC_IDLE_TIMEOUT_SECONDS", "120")
)

MAX_REMINDERS_PER_USER = parse_positive_int(
    "MAX_REMINDERS_PER_USER", os.getenv("MAX_REMINDERS_PER_USER", "10")
)
MAX_REMINDER_DAYS = parse_positive_int("MAX_REMINDER_DAYS", os.getenv("MAX_REMINDER_DAYS", "365"))

GAME_TIMEOUT_SECONDS = parse_positive_int(
    "GAME_TIMEOUT_SECONDS", os.getenv("GAME_TIMEOUT_SECONDS", "60")
)
