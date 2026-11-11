from dataclasses import dataclass
from datetime import timedelta

import discord
from discord import ui

from views.style import ACCENT_COLOR, divider

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
MAX_UPTIME_PARTS = 3


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


def format_uptime(uptime: timedelta) -> str:
    days, remainder = divmod(int(uptime.total_seconds()), SECONDS_PER_DAY)
    hours, remainder = divmod(remainder, SECONDS_PER_HOUR)
    minutes, seconds = divmod(remainder, SECONDS_PER_MINUTE)
    amounts = ((days, "d"), (hours, "h"), (minutes, "m"), (seconds, "s"))
    parts = [f"{value}{unit}" for value, unit in amounts if value]
    return " ".join(parts[:MAX_UPTIME_PARTS]) or "0s"


def format_getting_started(prefix: str) -> str:
    return "\n".join(
        [
            "### 🚀 Getting started",
            f"💬 **Text commands** · `{prefix}<command>`",
            "⚡ **Slash commands** · `/<command>`",
            f"📖 **See everything I can do** · `/help` or `{prefix}help`",
        ]
    )


def format_stats(info: BotInfo) -> str:
    return "\n".join(
        [
            "### 📊 Stats",
            f"🏓 **Latency** · {info.latency_ms} ms",
            f"⏱️ **Uptime** · {format_uptime(info.uptime)}",
            f"🌐 **Servers** · {info.guild_count}",
        ]
    )


def format_details(info: BotInfo) -> str:
    return "\n".join(
        [
            "### 🛠️ Details",
            f"👤 **Owner** · {info.owner_mention}",
            f"🐍 **Python** · {info.python_version}",
            f"📦 **discord.py** · {info.discord_version}",
        ]
    )


def build_link_buttons(info: BotInfo) -> list[ui.Button]:
    links = (("Source code", "📂", info.repo_url), ("Support", "💬", info.support_url))
    return [
        ui.Button(style=discord.ButtonStyle.link, label=label, emoji=emoji, url=url)
        for label, emoji, url in links
        if url
    ]


def build_info_view(info: BotInfo) -> ui.LayoutView:
    items: list[ui.Item] = [
        ui.Section(
            f"# 🤖 {info.name}",
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
