from discord.ext import commands


class GameError(ValueError):
    """A move that breaks the rules; the message is shown privately to the player."""


class FunError(commands.CommandError):
    """Raised when a fun command is refused; the message is shown to the user."""
