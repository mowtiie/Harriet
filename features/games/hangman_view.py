import string
from collections.abc import Mapping
from functools import partial

import discord
from discord import ui

from features.games.errors import GameError
from features.games.game_view import GameView, WinHandler, solo_winner_id
from features.games.hangman import HangmanGame
from features.games.hangman_art import STAGES
from views.style import ACCENT_COLOR, divider

IN_PROGRESS_TEXT = "Pick a letter below."
LETTER_GROUPS = (string.ascii_uppercase[:13], string.ascii_uppercase[13:])


def gallows_text(game: HangmanGame) -> str:
    return f"```\n{STAGES[len(game.misses)]}\n```"


def word_text(game: HangmanGame) -> str:
    return f"`{' '.join(game.masked_letters)}`"


def misses_text(game: HangmanGame) -> str:
    missed = " ".join(game.misses) or "none"
    return f"-# Misses {len(game.misses)}/{game.max_misses}: {missed}"


def status_text(game: HangmanGame, player_name: str, timed_out: bool) -> str:
    if game.is_won:
        return f"**{player_name}** guessed it: **{game.word}**."
    if game.is_lost:
        return f"**{player_name}** ran out of guesses. The word was **{game.word}**."
    if timed_out:
        return f"Timed out. The word was **{game.word}**."
    return IN_PROGRESS_TEXT


class HangmanView(GameView):
    def __init__(
        self,
        game: HangmanGame,
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
        items: list[ui.Item] = [
            ui.TextDisplay(f"# Hangman\n-# {player_name}"),
            divider(),
            ui.TextDisplay(gallows_text(self._game)),
            ui.TextDisplay(word_text(self._game)),
            ui.TextDisplay(misses_text(self._game)),
            divider(),
            ui.TextDisplay(status_text(self._game, player_name, self._timed_out)),
            *self._note_items(),
        ]
        if not (self._game.is_over or self._timed_out):
            items += [divider(), *self._build_selects()]
        self.clear_items()
        self.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))

    def _build_selects(self) -> list[ui.ActionRow]:
        rows = []
        for letters in LETTER_GROUPS:
            options = [
                discord.SelectOption(label=letter)
                for letter in letters
                if letter not in self._game.guessed
            ]
            if options:
                rows.append(ui.ActionRow(self._build_select(letters, options)))
        return rows

    def _build_select(self, letters: str, options: list[discord.SelectOption]) -> ui.Select:
        select = ui.Select(placeholder=f"{letters[0]} to {letters[-1]}", options=options)
        select.callback = partial(self._on_select, select)
        return select

    async def _on_select(self, select: ui.Select, interaction: discord.Interaction) -> None:
        await self._guess(select.values[0], interaction)

    async def _guess(self, letter: str, interaction: discord.Interaction) -> None:
        try:
            self._game.guess(letter)
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
