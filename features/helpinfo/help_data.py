from collections.abc import Iterable
from dataclasses import dataclass

from discord.ext import commands

from features.helpinfo.help_groups import GROUP_BY_COG_NAME, GROUP_POSITION

DEFAULT_CATEGORY_NAME = "Other"
NO_DESCRIPTION = "No description provided."


@dataclass(frozen=True)
class CommandHelp:
    name: str
    description: str
    signature: str
    examples: tuple[str, ...]
    category_name: str


@dataclass(frozen=True)
class CategoryHelp:
    name: str
    description: str
    commands: tuple[CommandHelp, ...]


def category_name_of(command: commands.Command) -> str:
    cog_name = command.cog_name or DEFAULT_CATEGORY_NAME
    group = GROUP_BY_COG_NAME.get(cog_name)
    return group.name if group else cog_name


def describe_command(command: commands.Command) -> CommandHelp:
    return CommandHelp(
        name=command.qualified_name,
        description=command.description or NO_DESCRIPTION,
        signature=command.signature,
        examples=tuple(command.extras.get("examples", ())),
        category_name=category_name_of(command),
    )


def group_into_categories(candidates: Iterable[commands.Command]) -> list[CategoryHelp]:
    grouped: dict[str, list[commands.Command]] = {}
    for command in candidates:
        grouped.setdefault(category_name_of(command), []).append(command)
    ordered_names = sorted(grouped, key=_category_sort_key)
    return [_build_category(grouped[name]) for name in ordered_names]


def _category_sort_key(name: str) -> tuple[int, str]:
    """Known groups keep their declared order; any other cog follows, alphabetically."""
    return GROUP_POSITION.get(name, len(GROUP_POSITION)), name


def _build_category(members: list[commands.Command]) -> CategoryHelp:
    first = members[0]
    ordered = sorted(members, key=lambda command: command.qualified_name)
    return CategoryHelp(
        name=category_name_of(first),
        description=_description_of(first),
        commands=tuple(describe_command(command) for command in ordered),
    )


def _description_of(command: commands.Command) -> str:
    group = GROUP_BY_COG_NAME.get(command.cog_name or "")
    if group:
        return group.description
    return getattr(command.cog, "description", None) or ""


def find_command(candidates: Iterable[commands.Command], query: str) -> commands.Command | None:
    wanted = query.strip().lstrip("/").lower()
    return next((command for command in candidates if command.qualified_name == wanted), None)


def matching_command_names(
    candidates: Iterable[commands.Command], current: str, limit: int
) -> list[str]:
    needle = current.strip().lower()
    names = sorted(command.qualified_name for command in candidates if not command.hidden)
    return [name for name in names if needle in name][:limit]
