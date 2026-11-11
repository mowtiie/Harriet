from discord import ui

from views.style import ACCENT_COLOR, divider


def build_settings_view(guild_name: str, volume_percent: int) -> ui.LayoutView:
    view = ui.LayoutView(timeout=None)
    view.add_item(
        ui.Container(
            ui.TextDisplay(f"# Settings\n-# {guild_name}"),
            divider(),
            ui.TextDisplay(f"**Volume** · {volume_percent}%"),
            accent_colour=ACCENT_COLOR,
        )
    )
    return view
