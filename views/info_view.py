from dataclasses import dataclass
from datetime import timedelta

import discord
from discord import ui

from time_format import format_elapsed
from views.style import ACCENT_COLOR, divider


@dataclass(frozen=True)
class BotInfo:
    name: str
    tagline: str
    avatar_url: str
    version: str
    prefix: str
    latency_ms: int
    uptime: timedelta
    guild_count: int
    owner_mention: str
    python_version: str
    discord_version: str
    repo_url: str
    support_url: str


def format_getting_started(prefix: str) -> str:
    return "\n".join(
        [
            "### Getting started",
            f"**Text commands** · `{prefix}<command>`",
            "**Slash commands** · `/<command>`",
            f"**See everything I can do** · `/help` or `{prefix}help`",
        ]
    )


def format_stats(info: BotInfo) -> str:
    return "\n".join(
        [
            "### Stats",
            f"**Latency** · {info.latency_ms} ms",
            f"**Uptime** · {format_elapsed(info.uptime)}",
            f"**Servers** · {info.guild_count}",
        ]
    )


def format_details(info: BotInfo) -> str:
    return "\n".join(
        [
            "### Details",
            f"**Owner** · {info.owner_mention}",
            f"**Python** · {info.python_version}",
            f"**discord.py** · {info.discord_version}",
        ]
    )


def build_link_buttons(info: BotInfo) -> list[ui.Button]:
    links = (("Source code", info.repo_url), ("Support", info.support_url))
    return [
        ui.Button(style=discord.ButtonStyle.link, label=label, url=url)
        for label, url in links
        if url
    ]


def build_info_view(info: BotInfo) -> ui.LayoutView:
    items: list[ui.Item] = [
        ui.Section(
            f"# {info.name}",
            info.tagline,
            f"-# Version {info.version}",
            accessory=ui.Thumbnail(info.avatar_url),
        ),
        divider(),
        ui.TextDisplay(format_getting_started(info.prefix)),
        divider(),
        ui.TextDisplay(format_stats(info)),
        divider(),
        ui.TextDisplay(format_details(info)),
    ]
    buttons = build_link_buttons(info)
    if buttons:
        items += [divider(), ui.ActionRow(*buttons)]

    view = ui.LayoutView(timeout=None)
    view.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))
    return view
