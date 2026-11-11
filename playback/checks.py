from discord.ext import commands

from core.errors import UserError

JOIN_FIRST_MESSAGE = "Join a voice channel first."
SAME_CHANNEL_MESSAGE = "You need to be in the same voice channel as me."
NOT_CONNECTED_MESSAGE = "I'm not in a voice channel."


def voice_state_error(
    user_channel_id: int | None, bot_channel_id: int | None, require_bot: bool
) -> str | None:
    if user_channel_id is None:
        return JOIN_FIRST_MESSAGE
    if bot_channel_id is None:
        return NOT_CONNECTED_MESSAGE if require_bot else None
    if bot_channel_id != user_channel_id:
        return SAME_CHANNEL_MESSAGE
    return None


def _check_voice(ctx: commands.Context, require_bot: bool) -> bool:
    user_voice = getattr(ctx.author, "voice", None)
    voice_client = ctx.guild.voice_client if ctx.guild else None
    message = voice_state_error(
        user_voice.channel.id if user_voice and user_voice.channel else None,
        voice_client.channel.id if voice_client else None,
        require_bot,
    )
    if message:
        raise UserError(message)
    return True


def in_voice_channel() -> commands.Check:
    return commands.check(lambda ctx: _check_voice(ctx, require_bot=False))


def with_active_player() -> commands.Check:
    return commands.check(lambda ctx: _check_voice(ctx, require_bot=True))
