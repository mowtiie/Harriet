from dataclasses import dataclass
from datetime import timedelta

import discord

DEFAULT_REASON = "No reason provided"


@dataclass(frozen=True)
class ModAction:
    name: str
    past_tense: str
    guild: discord.Guild
    moderator: discord.abc.User
    target: discord.abc.User
    reason: str
    duration: timedelta | None = None
