import discord
from discord import ui

from core.errors import UserError
from views.style import ACCENT_COLOR, divider

MAX_MESSAGE_LENGTH = 2000
MAX_LOGGED_LENGTH = 500
SAY_COOLDOWN_SECONDS = 5


def prepare_message(text: str) -> str:
    """Slash fields are one line, so a typed `\\n` becomes a line break."""
    prepared = text.replace("\\n", "\n").strip()
    if not prepared:
        raise ValueError("Tell me what to say.")
    if len(prepared) > MAX_MESSAGE_LENGTH:
        raise ValueError(
            f"That's {len(prepared)} characters, and messages can be {MAX_MESSAGE_LENGTH} at most."
        )
    return prepared


def ensure_can_say(
    channel: discord.TextChannel, member: discord.Member, bot_member: discord.Member
) -> None:
    """Both of you must be able to post there, so `/say` can't get around channel permissions."""
    for who, subject in ((member, "You"), (bot_member, "I")):
        permissions = channel.permissions_for(who)
        if not (permissions.view_channel and permissions.send_messages):
            raise UserError(f"{subject} can't send messages in {channel.mention}.")


def mention_rules(can_mention_everyone: bool) -> discord.AllowedMentions:
    """People can be mentioned freely; @everyone, @here and roles need the permission to ping."""
    return discord.AllowedMentions(
        everyone=can_mention_everyone,
        roles=can_mention_everyone,
        users=True,
        replied_user=False,
    )


def quote_for_log(text: str) -> str:
    shortened = text if len(text) <= MAX_LOGGED_LENGTH else text[: MAX_LOGGED_LENGTH - 1] + "…"
    return "\n".join(f"> {line}" for line in shortened.splitlines())


def build_say_log_view(
    moderator: discord.abc.User, channel: discord.abc.GuildChannel, sent: discord.Message
) -> ui.LayoutView:
    timestamp = discord.utils.format_dt(discord.utils.utcnow(), "f")
    fields = "\n".join(
        [
            f"**Moderator** · {moderator.mention}",
            f"**Channel** · {channel.mention} ([jump]({sent.jump_url}))",
            f"**Message**\n{quote_for_log(sent.content)}",
        ]
    )
    view = ui.LayoutView(timeout=None)
    view.add_item(
        ui.Container(
            ui.TextDisplay(f"### Said as the bot\n-# {timestamp}"),
            divider(),
            ui.TextDisplay(fields),
            accent_colour=ACCENT_COLOR,
        )
    )
    return view
