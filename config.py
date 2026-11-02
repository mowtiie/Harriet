"""Settings loaded from the environment (``.env``) and validated at import time."""

import os
from collections.abc import Collection

from dotenv import load_dotenv

from presence_utils import ACTIVITY_MAP, STATUS_MAP

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class ConfigError(ValueError):
    """Raised when an environment variable holds an unusable value."""


def parse_choice(name: str, raw: str, allowed: Collection[str]) -> str:
    """Return `raw` normalized to lowercase if it is one of `allowed`.

    `allowed` values are compared case-insensitively against `raw`.
    """
    value = raw.strip().lower()
    if value not in {option.lower() for option in allowed}:
        options = ", ".join(allowed)
        raise ConfigError(f"{name} must be one of: {options} (got {raw!r})")
    return value


def parse_positive_int(name: str, raw: str) -> int:
    """Return `raw` as an integer greater than zero."""
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
