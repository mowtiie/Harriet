import logging
from collections.abc import Callable, Mapping

import discord
from discord import ui

from features.games.cookie_case import SUSPECT_COUNT
from features.games.cookie_case_view import CookieCaseView
from views.style import ACCENT_COLOR, divider

log = logging.getLogger(__name__)

StartCase = Callable[[Mapping[int, str]], CookieCaseView]

INTRO = (
    "Someone raided Harriet's cookie jar! Join the investigation and you become a suspect too. "
    f"Up to {SUSPECT_COUNT} detectives, and fictional suspects fill the empty seats."
)
CLOSED_TEXT = "Nobody opened the case in time."


class CookieLobbyView(ui.LayoutView):
    def __init__(
        self,
        host_id: int,
        host_name: str,
        start_case: StartCase,
        timeout_seconds: float,
    ) -> None:
        super().__init__(timeout=timeout_seconds)
        self.message: discord.Message | None = None
        self._host_id = host_id
        self._players = {host_id: host_name}
        self._start_case = start_case
        self._closed = False
        self._render()

    async def on_timeout(self) -> None:
        self._closed = True
        self._render()
        if self.message is None:
            return
        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            log.warning("Could not close the expired cookie lobby", exc_info=True)

    def _render(self) -> None:
        names = ", ".join(self._players.values())
        host = self._players[self._host_id]
        footer = CLOSED_TEXT if self._closed else f"-# {host} presses Start when everyone is in."
        items: list[ui.Item] = [
            ui.TextDisplay("# Who stole Harriet's cookie?"),
            divider(),
            ui.TextDisplay(INTRO),
            ui.TextDisplay(f"**Detectives ({len(self._players)}/{SUSPECT_COUNT}):** {names}"),
            ui.TextDisplay(footer),
        ]
        if not self._closed:
            items += [divider(), ui.ActionRow(self._build_join(), self._build_start())]
        self.clear_items()
        self.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))

    def _build_join(self) -> ui.Button:
        button = ui.Button(label="Join", style=discord.ButtonStyle.success)
        button.callback = self._on_join
        return button

    def _build_start(self) -> ui.Button:
        button = ui.Button(label="Start the case", style=discord.ButtonStyle.primary)
        button.callback = self._on_start
        return button

    async def _on_join(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        if user.id in self._players:
            await interaction.response.send_message("You're already in.", ephemeral=True)
            return
        if len(self._players) >= SUSPECT_COUNT:
            await interaction.response.send_message("The case is full.", ephemeral=True)
            return
        self._players[user.id] = user.display_name
        self._render()
        await interaction.response.edit_message(view=self)

    async def _on_start(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self._host_id:
            host = self._players[self._host_id]
            await interaction.response.send_message(f"Only {host} can start.", ephemeral=True)
            return
        case_view = self._start_case(self._players)
        case_view.message = interaction.message
        self.stop()
        await interaction.response.edit_message(view=case_view)
