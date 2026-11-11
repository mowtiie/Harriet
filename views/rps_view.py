import random
from collections.abc import Mapping
from functools import partial

import discord
from discord import ui

from games.errors import GameError
from games.rps import Move, RpsGame, random_move
from views.restricted_view import GameView, WinHandler
from views.style import ACCENT_COLOR, divider

BOT_WAITING_HINT = "Pick a move below."
PVP_WAITING_HINT = "Both players pick a move. Picks stay hidden until both have chosen."
TIMED_OUT_TEXT = "Timed out before the game finished."


def describe_result(game: RpsGame, names: Mapping[int, str]) -> str:
    lines = [
        f"**{names[player_id]}** picked {game.move_of(player_id).value}"
        for player_id in game.player_ids
    ]
    winner_id = game.winner_id
    lines.append(f"**{names[winner_id]}** wins." if winner_id is not None else "It's a tie.")
    return "\n".join(lines)


class RpsView(GameView):
    def __init__(
        self,
        game: RpsGame,
        names: Mapping[int, str],
        *,
        human_ids: tuple[int, ...],
        bot_id: int | None,
        rng: random.Random,
        timeout_seconds: float,
        on_finish: WinHandler | None = None,
    ) -> None:
        super().__init__(human_ids, timeout_seconds, on_finish)
        self._game = game
        self._names = names
        self._bot_id = bot_id
        self._rng = rng
        self._render()

    def _render(self) -> None:
        first, second = self._game.player_ids
        header = f"# Rock paper scissors\n-# {self._names[first]} vs {self._names[second]}"
        items: list[ui.Item] = [
            ui.TextDisplay(header),
            divider(),
            ui.TextDisplay(self._status()),
            *self._note_items(),
        ]
        if not (self._game.is_finished or self._timed_out):
            items += [divider(), ui.ActionRow(*self._build_buttons())]
        self.clear_items()
        self.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))

    def _status(self) -> str:
        if self._game.is_finished:
            return describe_result(self._game, self._names)
        if self._timed_out:
            return TIMED_OUT_TEXT
        return BOT_WAITING_HINT if self._bot_id is not None else PVP_WAITING_HINT

    def _build_buttons(self) -> list[ui.Button]:
        buttons = []
        for move in Move:
            button = ui.Button(label=move.value, style=discord.ButtonStyle.secondary)
            button.callback = partial(self._on_pick, move)
            buttons.append(button)
        return buttons

    async def _on_pick(self, move: Move, interaction: discord.Interaction) -> None:
        try:
            self._game.pick(interaction.user.id, move)
        except GameError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return

        if self._bot_id is not None:
            self._game.pick(self._bot_id, random_move(self._rng))
        if not self._game.is_finished:
            opponent = self._names[self._game.opponent_of(interaction.user.id)]
            text = f"You picked {move.value}. Waiting for {opponent}."
            await interaction.response.send_message(text, ephemeral=True)
            return

        await self._record_result(self._game.winner_id)
        self._render()
        self.stop()
        await interaction.response.edit_message(view=self)
