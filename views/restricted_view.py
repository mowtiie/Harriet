import logging
from collections.abc import Iterable

import discord
from discord import ui

log = logging.getLogger(__name__)


class RestrictedView(ui.LayoutView):
    """A view only the listed users can press, which locks itself when it expires."""

    def __init__(self, allowed_user_ids: Iterable[int], timeout_seconds: float) -> None:
        super().__init__(timeout=timeout_seconds)
        self.message: discord.Message | None = None
        self._allowed_user_ids = frozenset(allowed_user_ids)
        self._timed_out = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in self._allowed_user_ids:
            return True
        await interaction.response.send_message(
            "This one belongs to someone else.", ephemeral=True
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
            log.warning("Could not update the expired message", exc_info=True)

    def _render(self) -> None:
        raise NotImplementedError
