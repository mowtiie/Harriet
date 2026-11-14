import random
from collections.abc import Mapping, Sequence
from functools import partial

import discord
from discord import ui

from features.games.connect_four import (
    COLUMNS,
    FIRST_MARK,
    ROWS,
    SECOND_MARK,
    ConnectFourGame,
)
from features.games.connect_four_bot import pick_column
from features.games.game_view import WinHandler
from features.games.turn_view import TurnBasedView
from views.style import ACCENT_COLOR, divider

DISC_EMOJI = {"": "⚪", FIRST_MARK: "🔴", SECOND_MARK: "🟡"}
COLUMN_HEADER = "".join(f"{number}️⃣" for number in range(1, COLUMNS + 1))
BUTTONS_PER_ROW = 4


def board_text(board: Sequence[str]) -> str:
    rows = [
        "".join(DISC_EMOJI[board[row * COLUMNS + column]] for column in range(COLUMNS))
        for row in range(ROWS)
    ]
    return "\n".join([COLUMN_HEADER, *rows])


def status_text(game: ConnectFourGame, names: Mapping[int, str], timed_out: bool) -> str:
    winner_id = game.winner_id
    if winner_id is not None:
        return f"**{names[winner_id]}** wins."
    if game.is_draw:
        return "It's a draw."
    current = names[game.current_player_id]
    if timed_out:
        return f"Game expired. **{current}** didn't move in time."
    return f"**{current}**'s turn ({DISC_EMOJI[game.turn]})."


class ConnectFourView(TurnBasedView):
    def __init__(
        self,
        game: ConnectFourGame,
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
            f"# Connect four\n-# {DISC_EMOJI[FIRST_MARK]}: {self._names[first]} · "
            f"{DISC_EMOJI[SECOND_MARK]}: {self._names[second]}"
        )
        status = status_text(self._game, self._names, self._timed_out)
        self.clear_items()
        self.add_item(
            ui.Container(
                ui.TextDisplay(header),
                divider(),
                ui.TextDisplay(board_text(self._game.board)),
                ui.TextDisplay(status),
                *self._note_items(),
                divider(),
                *self._build_rows(),
                accent_colour=ACCENT_COLOR,
            )
        )

    def _build_rows(self) -> list[ui.ActionRow]:
        locked = self._game.is_over or self._timed_out
        buttons = []
        for column in range(COLUMNS):
            button = ui.Button(
                label=str(column + 1),
                style=discord.ButtonStyle.secondary,
                disabled=locked or self._game.is_column_full(column),
            )
            button.callback = partial(self._on_press, column)
            buttons.append(button)
        return [
            ui.ActionRow(*buttons[start : start + BUTTONS_PER_ROW])
            for start in range(0, COLUMNS, BUTTONS_PER_ROW)
        ]

    def _pick_bot_move(self) -> int:
        mark = self._game.turn
        opponent_mark = FIRST_MARK if mark == SECOND_MARK else SECOND_MARK
        return pick_column(self._game.board, mark, opponent_mark, self._rng)
