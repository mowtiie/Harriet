import discord

STATUS_MAP = {
    "online": discord.Status.online,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible,
}

ACTIVITY_MAP = {
    "playing": discord.ActivityType.playing,
    "listening": discord.ActivityType.listening,
    "watching": discord.ActivityType.watching,
    "competing": discord.ActivityType.competing,
}


def build_presence(
    status: str, activity_type: str, activity_name: str
) -> tuple[discord.Status, discord.Activity]:
    """Unknown values fall back to online and playing."""
    discord_status = STATUS_MAP.get(status.lower(), discord.Status.online)
    activity = discord.Activity(
        type=ACTIVITY_MAP.get(activity_type.lower(), discord.ActivityType.playing),
        name=activity_name,
    )
    return discord_status, activity
