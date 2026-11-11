from discord.ext import commands


class VoiceStateError(commands.CheckFailure):
    """Raised by voice checks; the message is shown to the user as-is."""


class QueueFullError(Exception):
    pass


class ResolveError(Exception):
    pass
