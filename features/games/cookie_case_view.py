from collections.abc import Callable, Mapping
from functools import partial

import discord
from discord import ui

from features.games.cookie_game import CookieGame
from features.games.cookie_text import (
    accusation_text,
    clues_text,
    detectives_text,
    status_text,
    story_text,
    truth_text,
)
from features.games.errors import GameError
from features.games.game_view import GameView, WinHandler
from views.style import ACCENT_COLOR, divider

ACCUSE_PLACEHOLDER = "Accuse a suspect (one try each!)"
NEXT_CLUE_LABEL = "Next clue"


class CookieCaseView(GameView):
    def __init__(
        self,
        game: CookieGame,
        players: Mapping[int, str],
        *,
        bot_id: int,
        timeout_seconds: float,
        on_finish: WinHandler | None = None,
    ) -> None:
        super().__init__(game.player_ids, timeout_seconds, on_finish)
        self._game = game
        self._players = players
        self._bot_id = bot_id
        self._render()

    def _render(self) -> None:
        game = self._game
        closed = game.is_over or self._timed_out
        header = f"# Who stole Harriet's cookie?\n{detectives_text(game, self._players)}"
        items: list[ui.Item] = [
            ui.TextDisplay(header),
            divider(),
            ui.TextDisplay(story_text(game.case)),
            ui.TextDisplay(clues_text(game)),
            divider(),
            ui.TextDisplay(self._status()),
            *self._note_items(),
        ]
        if closed:
            items.append(ui.TextDisplay(truth_text(game.case)))
        else:
            items += [divider(), ui.ActionRow(self._build_select()), self._build_clue_row()]
        self.clear_items()
        self.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))

    def _status(self) -> str:
        lines = []
        if self._game.accusations:
            lines.append(accusation_text(self._game.accusations[-1], self._game, self._players))
        lines.append(status_text(self._game, self._players, self._timed_out))
        return "\n".join(lines)

    def _build_select(self) -> ui.Select:
        options = [
            discord.SelectOption(label=name, value=str(index))
            for index, name in enumerate(self._game.case.suspects)
        ]
        select = ui.Select(placeholder=ACCUSE_PLACEHOLDER, options=options)
        select.callback = partial(self._on_select, select)
        return select

    async def _on_select(self, select: ui.Select, interaction: discord.Interaction) -> None:
        await self._accuse(int(select.values[0]), interaction)

    def _build_clue_row(self) -> ui.ActionRow:
        button = ui.Button(
            label=NEXT_CLUE_LABEL,
            style=discord.ButtonStyle.primary,
            disabled=not self._game.has_hidden_clues,
        )
        button.callback = self._on_next_clue
        return ui.ActionRow(button)

    async def _on_next_clue(self, interaction: discord.Interaction) -> None:
        await self._apply(self._game.reveal_next_clue, interaction)

    async def _accuse(self, suspect: int, interaction: discord.Interaction) -> None:
        await self._apply(lambda: self._game.accuse(interaction.user.id, suspect), interaction)

    async def _apply(self, action: Callable[[], object], interaction: discord.Interaction) -> None:
        try:
            action()
        except GameError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        if self._game.is_over:
            winner_id = self._game.solver_id if self._game.is_solved else self._bot_id
            await self._record_result(winner_id)
            self.stop()
        self._render()
        await interaction.response.edit_message(view=self)
