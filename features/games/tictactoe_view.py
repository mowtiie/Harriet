import random
from collections.abc import Mapping
from functools import partial

import discord
from discord import ui

from features.games.game_view import WinHandler
from features.games.tictactoe import FIRST_MARK, SECOND_MARK, SIZE, TicTacToeGame
from features.games.tictactoe_bot import pick_square
from features.games.turn_view import TurnBasedView
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


class TicTacToeView(TurnBasedView):
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
        super().__init__(game, names, timeout_seconds, on_finish, bot_id=bot_id, rng=rng)
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

    def _pick_bot_move(self) -> int:
        mark = self._game.turn
        opponent_mark = FIRST_MARK if mark == SECOND_MARK else SECOND_MARK
        return pick_square(self._game.board, mark, opponent_mark, self._rng)
