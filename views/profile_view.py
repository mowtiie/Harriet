from collections.abc import Sequence

import discord
from discord import ui

from views.style import ACCENT_COLOR, divider


def format_fields(fields: Sequence[tuple[str, str]]) -> str:
    return "\n".join(f"**{label}** · {value}" for label, value in fields)


def _card(*items: ui.Item) -> ui.LayoutView:
    view = ui.LayoutView(timeout=None)
    view.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))
    return view


def build_profile_view(
    title: str,
    subtitle: str,
    fields: Sequence[tuple[str, str]],
    thumbnail_url: str | None = None,
) -> ui.LayoutView:
    heading = f"# {title}"
    caption = f"-# {subtitle}"
    header = (
        ui.Section(heading, caption, accessory=ui.Thumbnail(thumbnail_url))
        if thumbnail_url
        else ui.TextDisplay(f"{heading}\n{caption}")
    )
    return _card(header, divider(), ui.TextDisplay(format_fields(fields)))


def build_avatar_view(name: str, avatar_urls: Sequence[tuple[str, str]]) -> ui.LayoutView:
    items = (discord.MediaGalleryItem(url, description=label) for label, url in avatar_urls)
    gallery = ui.MediaGallery(*items)
    captions = " · ".join(label for label, _ in avatar_urls)
    return _card(ui.TextDisplay(f"# {name}\n-# {captions}"), gallery)
