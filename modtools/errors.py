from discord.ext import commands


class ModerationError(commands.CommandError):
    """Raised when a moderation request is refused; the message is shown to the user."""
