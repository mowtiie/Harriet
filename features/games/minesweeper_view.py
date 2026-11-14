from collections.abc import Mapping
from functools import partial

import discord
from discord import ui

from features.games.errors import GameError
from features.games.game_view import GameView, WinHandler, solo_winner_id
from features.games.minesweeper import MINE_COUNT, SIZE, SQUARES, MinesweeperGame
from views.style import ACCENT_COLOR, divider

HIDDEN_LABEL = "?"
EMPTY_LABEL = "·"
MINE_EMOJI = "💣"


def square_label(adjacent_mines: int) -> str:
    return str(adjacent_mines) if adjacent_mines else EMPTY_LABEL


def status_text(game: MinesweeperGame, player_name: str, timed_out: bool) -> str:
    if game.is_won:
        return f"**{player_name}** cleared the field."
    if game.is_lost:
        return f"**{player_name}** hit a mine."
    if timed_out:
        return "Timed out before the game finished."
    return f"{game.safe_squares_left} safe squares left. Don't hit a mine."


class MinesweeperView(GameView):
    def __init__(
        self,
        game: MinesweeperGame,
        names: Mapping[int, str],
        *,
        player_id: int,
        bot_id: int,
        timeout_seconds: float,
        on_finish: WinHandler | None = None,
    ) -> None:
        super().__init__((player_id,), timeout_seconds, on_finish)
        self._game = game
        self._names = names
        self._player_id = player_id
        self._bot_id = bot_id
        self._render()

    def _render(self) -> None:
        player_name = self._names[self._player_id]
        self.clear_items()
        self.add_item(
            ui.Container(
                ui.TextDisplay(f"# Minesweeper\n-# {player_name} · {MINE_COUNT} mines hidden"),
                divider(),
                ui.TextDisplay(status_text(self._game, player_name, self._timed_out)),
                *self._note_items(),
                divider(),
                *self._build_rows(),
                accent_colour=ACCENT_COLOR,
            )
        )

    def _build_rows(self) -> list[ui.ActionRow]:
        return [
            ui.ActionRow(*(self._build_button(index) for index in range(start, start + SIZE)))
            for start in range(0, SQUARES, SIZE)
        ]

    def _build_button(self, index: int) -> ui.Button:
        game = self._game
        if index in game.revealed:
            button = ui.Button(
                label=square_label(game.adjacent_mine_count(index)),
                style=discord.ButtonStyle.success,
                disabled=True,
            )
        elif game.is_over and index in game.mines:
            style = discord.ButtonStyle.danger if game.is_lost else discord.ButtonStyle.secondary
            button = ui.Button(emoji=MINE_EMOJI, style=style, disabled=True)
        else:
            button = ui.Button(
                label=HIDDEN_LABEL,
                style=discord.ButtonStyle.secondary,
                disabled=game.is_over or self._timed_out,
            )
        button.callback = partial(self._on_press, index)
        return button

    async def _on_press(self, index: int, interaction: discord.Interaction) -> None:
        try:
            self._game.reveal(index)
        except GameError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        if self._game.is_over:
            winner_id = solo_winner_id(
                self._game.is_won, self._game.is_lost, self._player_id, self._bot_id
            )
            await self._record_result(winner_id)
            self.stop()
        self._render()
        await interaction.response.edit_message(view=self)
