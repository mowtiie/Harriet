from collections.abc import Sequence

from discord import ui

from views.style import ACCENT_COLOR, divider

MAX_ANSWER_LENGTH = 300
MAX_QUOTE_LENGTH = 600
ELLIPSIS = "…"


def shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - len(ELLIPSIS)] + ELLIPSIS


def quote_block(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.splitlines())


def build_result_card(
    title: str,
    answer: str,
    *,
    quote: str | None = None,
    notes: Sequence[str] = (),
) -> ui.LayoutView:
    """A small card for a command's answer: a title, what was asked, the answer, fine print."""
    items: list[ui.Item] = [ui.TextDisplay(f"### {title}"), divider()]
    if quote:
        items.append(ui.TextDisplay(quote_block(shorten(quote, MAX_QUOTE_LENGTH))))
    one_line_answer = " ".join(answer.split())
    items.append(ui.TextDisplay(f"## {shorten(one_line_answer, MAX_ANSWER_LENGTH)}"))
    if notes:
        items.append(ui.TextDisplay("\n".join(f"-# {note}" for note in notes)))
    view = ui.LayoutView(timeout=None)
    view.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))
    return view
