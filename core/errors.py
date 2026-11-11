from discord import app_commands
from discord.ext import commands

GENERIC_ERROR_MESSAGE = "Something went wrong. The error has been logged."


class UserError(commands.CommandError):
    """A refusal whose message is safe to show to the user as-is."""


def describe_error(error: Exception) -> str | None:
    """Return a user-facing message, or None if the error is unexpected."""
    if isinstance(error, (commands.MissingPermissions, app_commands.MissingPermissions)):
        return "You don't have permission to do that."
    if isinstance(error, commands.BotMissingPermissions):
        missing = ", ".join(error.missing_permissions)
        return f"I need the following permissions to do that: {missing}."
    if isinstance(error, commands.NotOwner):
        return "This command is restricted to the bot owner."
    if isinstance(error, commands.NoPrivateMessage):
        return "This command can only be used in a server."
    if isinstance(error, commands.CommandOnCooldown):
        return f"Slow down! Try again in {error.retry_after:.1f}s."
    if isinstance(error, commands.MissingRequiredArgument):
        return f"Missing argument: `{error.param.name}`"
    if isinstance(error, commands.BadLiteralArgument):
        options = ", ".join(f"`{value}`" for value in error.literals)
        return f"Invalid value for `{error.param.name}`. Choose one of: {options}"
    if isinstance(error, commands.BadArgument):
        return f"Bad argument: {error}"
    if isinstance(error, UserError):
        return str(error)
    if isinstance(error, (commands.CheckFailure, app_commands.CheckFailure)):
        return "You can't use this command here."
    return None
