from dataclasses import dataclass


@dataclass(frozen=True)
class HelpGroup:
    name: str
    description: str
    cog_names: tuple[str, ...]


HELP_GROUPS = (
    HelpGroup(
        "General",
        "Everyday commands, plus help and bot info.",
        ("General", "Help & Info"),
    ),
    HelpGroup(
        "Games",
        "Play against me or other members, and climb the XP board.",
        ("Games", "SoloGames", "Leveling"),
    ),
    HelpGroup(
        "Fun & Tools",
        "Silly answers, quick decisions and reminders.",
        ("Fun", "Tools", "Reminders"),
    ),
    HelpGroup("Music", "Play music in voice channels.", ("Music",)),
    HelpGroup(
        "Moderation",
        "Kick, ban, time out, warn and keep channels tidy.",
        ("Discipline", "Moderation", "Warnings"),
    ),
    HelpGroup(
        "Info & Settings",
        "Look up members, roles and the server, and change settings.",
        ("Information", "Settings", "Presence"),
    ),
)

GROUP_BY_COG_NAME = {cog_name: group for group in HELP_GROUPS for cog_name in group.cog_names}
GROUP_POSITION = {group.name: position for position, group in enumerate(HELP_GROUPS)}
