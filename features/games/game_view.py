from collections.abc import Awaitable, Callable, Iterable

from discord import ui

from views.restricted_view import RestrictedView

WinHandler = Callable[[int | None], Awaitable[str | None]]


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
