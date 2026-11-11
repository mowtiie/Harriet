import math
from collections.abc import Sequence
from functools import partial

import discord
from discord import ui

from features.leveling.curve import format_bar, progress_for
from features.leveling.ranking import RankedMember
from views.restricted_view import RestrictedView
from views.style import ACCENT_COLOR, divider

PAGE_SIZE = 10
EMPTY_BOARD_TEXT = "No one has earned XP yet. Win a game to get on the board."


def rank_fields(xp: int) -> list[tuple[str, str]]:
    progress = progress_for(xp)
    return [
        ("Level", str(progress.level)),
        ("Total XP", f"{xp:,}"),
        ("Next level", f"{progress.xp_into_level:,} / {progress.xp_for_next:,} XP"),
        ("Progress", format_bar(progress.fraction)),
    ]


def page_count(member_count: int) -> int:
    return max(1, math.ceil(member_count / PAGE_SIZE))


def format_leaderboard_page(members: Sequence[RankedMember], page: int) -> str:
    if not members:
        return EMPTY_BOARD_TEXT
    start = page * PAGE_SIZE
    return "\n".join(
        f"`{member.position}.` **{member.name}** · Level {member.level} · {member.xp:,} XP"
        for member in members[start : start + PAGE_SIZE]
    )


class LeaderboardView(RestrictedView):
    def __init__(
        self, members: Sequence[RankedMember], author_id: int, timeout_seconds: float
    ) -> None:
        super().__init__([author_id], timeout_seconds)
        self._members = members
        self._pages = page_count(len(members))
        self._page = 0
        self._render()

    def _render(self) -> None:
        items: list[ui.Item] = [
            ui.TextDisplay(f"# Leaderboard\n-# Page {self._page + 1} of {self._pages}"),
            divider(),
            ui.TextDisplay(format_leaderboard_page(self._members, self._page)),
        ]
        if self._pages > 1:
            items += [divider(), ui.ActionRow(*self._build_buttons())]
        self.clear_items()
        self.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))

    def _build_buttons(self) -> list[ui.Button]:
        previous_button = ui.Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            disabled=self._timed_out or self._page == 0,
        )
        next_button = ui.Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
            disabled=self._timed_out or self._page == self._pages - 1,
        )
        previous_button.callback = partial(self._turn_page, -1)
        next_button.callback = partial(self._turn_page, 1)
        return [previous_button, next_button]

    async def _turn_page(self, step: int, interaction: discord.Interaction) -> None:
        self._page = min(max(self._page + step, 0), self._pages - 1)
        self._render()
        await interaction.response.edit_message(view=self)
