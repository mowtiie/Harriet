import random
from collections.abc import Mapping
from typing import Protocol

import discord

from features.games.errors import GameError
from features.games.game_view import GameView, WinHandler


class TurnGame(Protocol):
    turn: str

    @property
    def player_ids(self) -> tuple[int, int]: ...

    @property
    def current_player_id(self) -> int: ...

    @property
    def winner_id(self) -> int | None: ...

    @property
    def is_over(self) -> bool: ...

    def play(self, player_id: int, move: int) -> None: ...


class TurnBasedView(GameView):
    """Two players alternate moves, and either side may be the bot."""

    def __init__(
        self,
        game: TurnGame,
        names: Mapping[int, str],
        timeout_seconds: float,
        on_finish: WinHandler | None,
        *,
        bot_id: int | None,
        rng: random.Random | None,
    ) -> None:
        human_ids = tuple(player for player in game.player_ids if player != bot_id)
        super().__init__(human_ids, timeout_seconds, on_finish)
        self._game = game
        self._names = names
        self._bot_id = bot_id
        self._rng = rng or random.Random()

    def _pick_bot_move(self) -> int:
        raise NotImplementedError

    async def _on_press(self, move: int, interaction: discord.Interaction) -> None:
        try:
            self._game.play(interaction.user.id, move)
        except GameError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        self._play_bot_turn()
        if self._game.is_over:
            await self._record_result(self._game.winner_id)
            self.stop()
        self._render()
        await interaction.response.edit_message(view=self)

    def _play_bot_turn(self) -> None:
        if self._bot_id is None or self._game.is_over:
            return
        if self._game.current_player_id == self._bot_id:
            self._game.play(self._bot_id, self._pick_bot_move())
