from collections.abc import Awaitable, Callable, Mapping

import discord
from discord import ui

from features.games.errors import GameError
from features.games.game_view import GameView, WinHandler, solo_winner_id
from features.games.number_guess import (
    MAX_NUMBER,
    MIN_NUMBER,
    NumberGuessGame,
    parse_guess,
)
from views.style import ACCENT_COLOR, divider

SubmitHandler = Callable[[str, discord.Interaction], Awaitable[None]]


def attempts_text(game: NumberGuessGame) -> str:
    if not game.attempts:
        return "-# No guesses yet."
    return "\n".join(f"`{attempt.number}` {attempt.hint.value}" for attempt in game.attempts)


def guesses_phrase(count: int) -> str:
    return f"{count} guess" if count == 1 else f"{count} guesses"


def status_text(game: NumberGuessGame, player_name: str, timed_out: bool) -> str:
    if game.is_won:
        guesses = guesses_phrase(len(game.attempts))
        return f"**{player_name}** got it: **{game.secret}**, in {guesses}."
    if game.is_lost:
        return f"Out of guesses. The number was **{game.secret}**."
    if timed_out:
        return f"Timed out. The number was **{game.secret}**."
    return (
        f"It's between **{game.lowest_possible}** and **{game.highest_possible}**. "
        f"{guesses_phrase(game.guesses_left)} left."
    )


class GuessModal(ui.Modal, title="Your guess"):
    def __init__(self, on_guess: SubmitHandler) -> None:
        super().__init__()
        self._on_guess = on_guess
        self._input = ui.TextInput(
            placeholder=f"{MIN_NUMBER} to {MAX_NUMBER}",
            min_length=1,
            max_length=len(str(MAX_NUMBER)),
        )
        self.add_item(ui.Label(text="Number", component=self._input))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self._on_guess(self._input.value, interaction)


class NumberGuessView(GameView):
    def __init__(
        self,
        game: NumberGuessGame,
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
            ui.TextDisplay(f"# Guess the number\n-# {player_name} · {MIN_NUMBER} to {MAX_NUMBER}"),
            divider(),
            ui.TextDisplay(attempts_text(self._game)),
            divider(),
            ui.TextDisplay(status_text(self._game, player_name, self._timed_out)),
            *self._note_items(),
        ]
        if not (self._game.is_over or self._timed_out):
            items += [divider(), ui.ActionRow(self._build_button())]
        self.clear_items()
        self.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))

    def _build_button(self) -> ui.Button:
        button = ui.Button(label="Guess", style=discord.ButtonStyle.primary)
        button.callback = self._on_press
        return button

    async def _on_press(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(GuessModal(self.submit_guess))

    async def submit_guess(self, text: str, interaction: discord.Interaction) -> None:
        try:
            self._game.guess(parse_guess(text))
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
