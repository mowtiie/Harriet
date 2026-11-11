import logging
from collections.abc import Awaitable, Callable, Iterable

import discord
from discord import ui

log = logging.getLogger(__name__)

WinHandler = Callable[[int | None], Awaitable[str | None]]


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


class GameView(RestrictedView):
    """A game that can hand its winner to a callback and show the note it returns."""

    def __init__(
        self,
        player_ids: Iterable[int],
        timeout_seconds: float,
        on_finish: WinHandler | None,
    ) -> None:
        super().__init__(player_ids, timeout_seconds)
        self._on_finish = on_finish
        self._result_note: str | None = None

    async def _record_result(self, winner_id: int | None) -> None:
        if self._on_finish is not None:
            self._result_note = await self._on_finish(winner_id)

    def _note_items(self) -> list[ui.Item]:
        return [ui.TextDisplay(f"-# {self._result_note}")] if self._result_note else []
