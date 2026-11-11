from discord.ext import commands


class UtilityError(commands.CommandError):
    """Raised when a utility request is refused; the message is shown to the user."""
