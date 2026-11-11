from collections.abc import Sequence
from datetime import datetime

import discord

MAX_ROLES_SHOWN = 10
AVATAR_SIZE = 1024
NONE_LABEL = "None"
NOTABLE_PERMISSIONS = (
    ("manage_guild", "Manage Server"),
    ("manage_roles", "Manage Roles"),
    ("manage_channels", "Manage Channels"),
    ("kick_members", "Kick Members"),
    ("ban_members", "Ban Members"),
    ("moderate_members", "Moderate Members"),
    ("manage_messages", "Manage Messages"),
    ("mention_everyone", "Mention Everyone"),
)

Fields = list[tuple[str, str]]


def format_date(moment: datetime) -> str:
    return f"{discord.utils.format_dt(moment, 'D')} ({discord.utils.format_dt(moment, 'R')})"


def format_roles(roles: Sequence[discord.Role]) -> str:
    if not roles:
        return NONE_LABEL
    shown = ", ".join(role.mention for role in roles[:MAX_ROLES_SHOWN])
    hidden = len(roles) - MAX_ROLES_SHOWN
    return f"{shown} and {hidden} more" if hidden > 0 else shown


def key_permissions(permissions: discord.Permissions) -> list[str]:
    if permissions.administrator:
        return ["Administrator"]
    return [label for name, label in NOTABLE_PERMISSIONS if getattr(permissions, name)]


def user_fields(member: discord.Member) -> Fields:
    roles = [role for role in reversed(member.roles) if not role.is_default()]
    fields: Fields = [
        ("ID", f"`{member.id}`"),
        ("Created", format_date(member.created_at)),
        ("Joined", format_date(member.joined_at) if member.joined_at else "Unknown"),
        ("Top role", member.top_role.mention),
        (f"Roles ({len(roles)})", format_roles(roles)),
    ]
    if member.premium_since:
        fields.append(("Boosting since", format_date(member.premium_since)))
    if member.timed_out_until:
        fields.append(("Timed out until", discord.utils.format_dt(member.timed_out_until, "f")))
    if member.bot:
        fields.append(("Bot", "Yes"))
    return fields


def server_fields(guild: discord.Guild) -> Fields:
    return [
        ("Owner", f"<@{guild.owner_id}>"),
        ("ID", f"`{guild.id}`"),
        ("Created", format_date(guild.created_at)),
        ("Members", str(guild.member_count)),
        (
            "Channels",
            f"{len(guild.text_channels)} text, {len(guild.voice_channels)} voice, "
            f"{len(guild.categories)} categories",
        ),
        ("Roles", str(len(guild.roles) - 1)),
        ("Emojis", str(len(guild.emojis))),
        ("Boosts", f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)"),
        ("Verification", guild.verification_level.name.replace("_", " ").title()),
    ]


def role_fields(role: discord.Role) -> Fields:
    permissions = key_permissions(role.permissions)
    return [
        ("ID", f"`{role.id}`"),
        ("Created", format_date(role.created_at)),
        ("Color", str(role.colour) if role.colour.value else "Default"),
        ("Position", str(role.position)),
        ("Members", str(len(role.members))),
        ("Displayed separately", "Yes" if role.hoist else "No"),
        ("Mentionable", "Yes" if role.mentionable else "No"),
        ("Key permissions", ", ".join(permissions) if permissions else NONE_LABEL),
    ]


def avatar_urls(member: discord.Member) -> list[tuple[str, str]]:
    """Returns the server avatar first when the member has one, then their global avatar."""
    global_avatar = (member.avatar or member.default_avatar).with_size(AVATAR_SIZE).url
    if member.guild_avatar is None:
        return [("Avatar", global_avatar)]
    server_avatar = member.guild_avatar.with_size(AVATAR_SIZE).url
    return [("Server avatar", server_avatar), ("Global avatar", global_avatar)]
