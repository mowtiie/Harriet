import random
from collections.abc import Mapping
from functools import partial

import discord
from discord import ui

from features.games.errors import GameError
from features.games.game_view import GameView, WinHandler
from features.games.tictactoe import FIRST_MARK, SECOND_MARK, SIZE, TicTacToeGame
from features.games.tictactoe_bot import pick_square
from views.style import ACCENT_COLOR, divider

EMPTY_SQUARE = "-"


def status_text(game: TicTacToeGame, names: Mapping[int, str], timed_out: bool) -> str:
    winner_id = game.winner_id
    if winner_id is not None:
        return f"**{names[winner_id]}** wins."
    if game.is_draw:
        return "It's a draw."
    current = names[game.current_player_id]
    if timed_out:
        return f"Game expired. **{current}** didn't move in time."
    return f"**{current}**'s turn ({game.turn})."


class TicTacToeView(GameView):
    def __init__(
        self,
        game: TicTacToeGame,
        names: Mapping[int, str],
        timeout_seconds: float,
        on_finish: WinHandler | None = None,
        *,
        bot_id: int | None = None,
        rng: random.Random | None = None,
    ) -> None:
        human_ids = tuple(player for player in game.player_ids if player != bot_id)
        super().__init__(human_ids, timeout_seconds, on_finish)
        self._game = game
        self._names = names
        self._bot_id = bot_id
        self._rng = rng or random.Random()
        self._render()

    def _render(self) -> None:
        first, second = self._game.player_ids
        header = (
            f"# Tic tac toe\n-# {FIRST_MARK}: {self._names[first]} · "
            f"{SECOND_MARK}: {self._names[second]}"
        )
        status = status_text(self._game, self._names, self._timed_out)
        self.clear_items()
        self.add_item(
            ui.Container(
                ui.TextDisplay(header),
                divider(),
                ui.TextDisplay(status),
                *self._note_items(),
                divider(),
                *self._build_rows(),
                accent_colour=ACCENT_COLOR,
            )
        )

    def _build_rows(self) -> list[ui.ActionRow]:
        board = self._game.board
        locked = self._game.is_over or self._timed_out
        rows = []
        for row_start in range(0, len(board), SIZE):
            buttons = []
            for index in range(row_start, row_start + SIZE):
                button = ui.Button(
                    label=board[index] or EMPTY_SQUARE,
                    style=discord.ButtonStyle.secondary,
                    disabled=locked or bool(board[index]),
                )
                button.callback = partial(self._on_press, index)
                buttons.append(button)
            rows.append(ui.ActionRow(*buttons))
        return rows

    async def _on_press(self, index: int, interaction: discord.Interaction) -> None:
        try:
            self._game.play(interaction.user.id, index)
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
        if self._game.current_player_id != self._bot_id:
            return
        mark = self._game.turn
        opponent_mark = FIRST_MARK if mark == SECOND_MARK else SECOND_MARK
        square = pick_square(self._game.board, mark, opponent_mark, self._rng)
        self._game.play(self._bot_id, square)
