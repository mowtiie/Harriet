import random
from collections.abc import Mapping, Sequence
from functools import partial

import discord
from discord import ui

from features.games.battleship import (
    COLUMN_LETTERS,
    SIZE,
    SQUARES,
    BattleshipGame,
    Board,
    Shot,
    square_name,
)
from features.games.battleship_bot import pick_target
from features.games.game_view import WinHandler
from features.games.turn_view import TurnBasedView
from views.style import ACCENT_COLOR, divider

SHIP = "🚢"
HIT = "💥"
SUNK = "🔥"
MISS = "🌊"
WATER = "⬜"
CORNER = "⬛"
RECENT_SHOTS_SHOWN = 2
FLEET_BUTTON_LABEL = "My fleet"


def column_header() -> str:
    letters = "".join(chr(0x1F1E6 + position) for position in range(len(COLUMN_LETTERS)))
    return CORNER + letters


def row_label(row: int) -> str:
    return f"{row + 1}️⃣"


def fleet_square(board: Board, index: int) -> str:
    on_ship, shot = index in board.ship_squares, index in board.shots
    if on_ship and shot:
        return HIT
    if on_ship:
        return SHIP
    return MISS if shot else WATER


def own_fleet_text(board: Board) -> str:
    rows = [
        row_label(row) + "".join(fleet_square(board, row * SIZE + column) for column in range(SIZE))
        for row in range(SIZE)
    ]
    footer = f"-# {board.ships_afloat} ship(s) afloat"
    return "\n".join(["**Your fleet**", column_header(), *rows, footer])


def describe_shot(shot: Shot, names: Mapping[int, str]) -> str:
    where = f"**{names[shot.player_id]}** fired at `{square_name(shot.index)}`:"
    if not shot.result.hit:
        return f"{where} miss."
    if shot.result.sunk_size is None:
        return f"{where} hit!"
    return f"{where} hit and sunk a {shot.result.sunk_size}-square ship!"


def status_text(game: BattleshipGame, names: Mapping[int, str], timed_out: bool) -> str:
    winner_id = game.winner_id
    if winner_id is not None:
        return f"**{names[winner_id]}** sank the whole fleet and wins."
    current = names[game.current_player_id]
    if timed_out:
        return f"Game expired. **{current}** didn't fire in time."
    target = names[game.opponent_of(game.current_player_id)]
    return f"**{current}**'s turn. Fire at **{target}**'s waters."


def fleets_text(game: BattleshipGame, names: Mapping[int, str]) -> str:
    afloat = " · ".join(
        f"{names[player_id]}: {game.board_of(player_id).ships_afloat}"
        for player_id in game.player_ids
    )
    return f"-# Ships afloat — {afloat}"


class BattleshipView(TurnBasedView):
    def __init__(
        self,
        game: BattleshipGame,
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
        header = f"# Battleship\n-# {self._names[first]} vs {self._names[second]}"
        playing = not (self._game.is_over or self._timed_out)
        self.clear_items()
        self.add_item(
            ui.Container(
                ui.TextDisplay(header),
                divider(),
                ui.TextDisplay(self._summary()),
                *self._note_items(),
                divider(),
                *self._build_rows(),
                *([ui.ActionRow(self._build_fleet_button())] if playing else []),
                accent_colour=ACCENT_COLOR,
            )
        )

    def _summary(self) -> str:
        recent = self._game.history[-RECENT_SHOTS_SHOWN:]
        lines = [status_text(self._game, self._names, self._timed_out)]
        lines += [describe_shot(shot, self._names) for shot in recent]
        lines.append(fleets_text(self._game, self._names))
        return "\n".join(lines)

    def _build_rows(self) -> list[ui.ActionRow]:
        board = self._game.target_board
        locked = self._game.is_over or self._timed_out
        return [
            ui.ActionRow(
                *(self._build_square(board, index, locked) for index in range(start, start + SIZE))
            )
            for start in range(0, SQUARES, SIZE)
        ]

    def _build_square(self, board: Board, index: int, locked: bool) -> ui.Button:
        if index in board.sunk_squares:
            button = ui.Button(emoji=SUNK, style=discord.ButtonStyle.danger, disabled=True)
        elif index in board.hit_squares:
            button = ui.Button(emoji=HIT, style=discord.ButtonStyle.danger, disabled=True)
        elif index in board.shots:
            button = ui.Button(emoji=MISS, style=discord.ButtonStyle.secondary, disabled=True)
        else:
            button = ui.Button(
                label=square_name(index), style=discord.ButtonStyle.secondary, disabled=locked
            )
        button.callback = partial(self._on_press, index)
        return button

    def _build_fleet_button(self) -> ui.Button:
        button = ui.Button(label=FLEET_BUTTON_LABEL, style=discord.ButtonStyle.primary)
        button.callback = self._on_fleet
        return button

    async def _on_fleet(self, interaction: discord.Interaction) -> None:
        board = self._game.board_of(interaction.user.id)
        await interaction.response.send_message(own_fleet_text(board), ephemeral=True)

    def _pick_bot_move(self) -> int:
        return pick_target(self._game.target_board, self._rng)
