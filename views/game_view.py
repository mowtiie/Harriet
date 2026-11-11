import logging
from collections.abc import Iterable

import discord
from discord import ui

log = logging.getLogger(__name__)


class GameView(ui.LayoutView):
    """Shared behavior for turn-based games played with buttons."""

    def __init__(self, player_ids: Iterable[int], timeout_seconds: float) -> None:
        super().__init__(timeout=timeout_seconds)
        self.message: discord.Message | None = None
        self._player_ids = frozenset(player_ids)
        self._timed_out = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in self._player_ids:
            return True
        await interaction.response.send_message(
            "This game belongs to someone else.", ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        self._timed_out = True
        self._render()
        if self.message is None:
            return
        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            log.warning("Could not update the expired game message", exc_info=True)

    def _render(self) -> None:
        raise NotImplementedError
