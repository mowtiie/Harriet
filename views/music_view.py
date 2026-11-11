from collections.abc import Sequence

from discord import ui

from playback.track import Track, format_duration
from views.style import ACCENT_COLOR, divider

MAX_QUEUE_LINES = 10


def format_track(track: Track) -> str:
    return f"**{track.title}**\n-# {format_duration(track.duration_seconds)} · requested by {track.requested_by}"


def format_queue_line(position: int, track: Track) -> str:
    return f"`{position}.` {track.title} · {format_duration(track.duration_seconds)}"


def format_upcoming(upcoming: Sequence[Track]) -> str:
    if not upcoming:
        return "Nothing queued."
    lines = [format_queue_line(i, track) for i, track in enumerate(upcoming[:MAX_QUEUE_LINES], 1)]
    hidden = len(upcoming) - MAX_QUEUE_LINES
    if hidden > 0:
        lines.append(f"-# and {hidden} more")
    return "\n".join(lines)


def _card(*items: ui.Item) -> ui.LayoutView:
    view = ui.LayoutView(timeout=None)
    view.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))
    return view


def build_now_playing_view(track: Track) -> ui.LayoutView:
    return _card(ui.TextDisplay("### Now playing"), ui.TextDisplay(format_track(track)))


def build_added_view(track: Track, position: int) -> ui.LayoutView:
    return _card(
        ui.TextDisplay(f"### Added to queue\n-# Position {position}"),
        ui.TextDisplay(format_track(track)),
    )


def build_queue_view(current: Track | None, upcoming: Sequence[Track]) -> ui.LayoutView:
    now_playing = format_track(current) if current else "Nothing is playing."
    return _card(
        ui.TextDisplay("# Queue"),
        divider(),
        ui.TextDisplay(f"### Now playing\n{now_playing}"),
        divider(),
        ui.TextDisplay(f"### Up next\n{format_upcoming(upcoming)}"),
    )
