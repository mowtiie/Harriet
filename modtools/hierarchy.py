from dataclasses import dataclass

import discord
from discord.ext import commands

from modtools.errors import ModerationError


@dataclass(frozen=True)
class Standing:
    member_id: int
    top_role_position: int


def hierarchy_error(actor: Standing, target: Standing, bot: Standing, owner_id: int) -> str | None:
    if target.member_id == actor.member_id:
        return "You can't do that to yourself."
    if target.member_id == bot.member_id:
        return "I can't do that to myself."
    if target.member_id == owner_id:
        return "You can't do that to the server owner."
    if actor.member_id != owner_id and target.top_role_position >= actor.top_role_position:
        return "Their top role is equal to or higher than yours."
    if target.top_role_position >= bot.top_role_position:
        return "Their top role is equal to or higher than mine."
    return None


def ensure_can_moderate(ctx: commands.Context, target: discord.Member) -> None:
    guild = ctx.guild
    error = hierarchy_error(
        _standing_of(ctx.author), _standing_of(target), _standing_of(guild.me), guild.owner_id
    )
    if error:
        raise ModerationError(error)


def _standing_of(member: discord.Member) -> Standing:
    return Standing(member.id, member.top_role.position)
