from collections.abc import Callable, Mapping, Sequence

import discord
from discord import ui

from features.games.blackjack import BlackjackGame, Card, Outcome, hand_total
from features.games.errors import GameError
from features.games.game_view import GameView, WinHandler
from views.style import ACCENT_COLOR, divider

HIDDEN_CARD = "??"
IN_PROGRESS_TEXT = "Hit or stand?"
TIMED_OUT_TEXT = "Timed out before the game finished."
PUSH_TEXT = "Push. Nobody wins."


def format_cards(cards: Sequence[Card]) -> str:
    return " ".join(f"`{card}`" for card in cards)


def player_hand_text(name: str, hand: Sequence[Card]) -> str:
    return f"**{name}** · {hand_total(hand)}\n{format_cards(hand)}"


def dealer_hand_text(name: str, hand: Sequence[Card], revealed: bool) -> str:
    if revealed:
        return player_hand_text(name, hand)
    return f"**{name}** · ?\n{format_cards(hand[:1])} `{HIDDEN_CARD}`"


def status_text(
    game: BlackjackGame, player_name: str, dealer_name: str, timed_out: bool
) -> str:
    if game.outcome is None:
        return TIMED_OUT_TEXT if timed_out else IN_PROGRESS_TEXT
    if game.outcome is Outcome.PUSH:
        return PUSH_TEXT
    winner = player_name if game.outcome is Outcome.PLAYER_WINS else dealer_name
    result = f"**{winner}** wins."
    if game.player_busted:
        return f"Bust. {result}"
    if game.dealer_busted:
        return f"Dealer busts. {result}"
    return result


def winner_id_of(game: BlackjackGame, player_id: int, dealer_id: int) -> int | None:
    if game.outcome is Outcome.PLAYER_WINS:
        return player_id
    return dealer_id if game.outcome is Outcome.DEALER_WINS else None


class BlackjackView(GameView):
    def __init__(
        self,
        game: BlackjackGame,
        names: Mapping[int, str],
        *,
        player_id: int,
        dealer_id: int,
        timeout_seconds: float,
        on_finish: WinHandler | None = None,
    ) -> None:
        super().__init__((player_id,), timeout_seconds, on_finish)
        self._game = game
        self._names = names
        self._player_id = player_id
        self._dealer_id = dealer_id
        self._render()

    def _render(self) -> None:
        game = self._game
        player_name, dealer_name = self._names[self._player_id], self._names[self._dealer_id]
        items: list[ui.Item] = [
            ui.TextDisplay(f"# Blackjack\n-# {player_name} vs {dealer_name}"),
            divider(),
            ui.TextDisplay(dealer_hand_text(dealer_name, game.dealer_hand, game.is_over)),
            ui.TextDisplay(player_hand_text(player_name, game.player_hand)),
            divider(),
            ui.TextDisplay(status_text(self._game, player_name, dealer_name, self._timed_out)),
            *self._note_items(),
        ]
        if not (self._game.is_over or self._timed_out):
            items += [divider(), ui.ActionRow(*self._build_buttons())]
        self.clear_items()
        self.add_item(ui.Container(*items, accent_colour=ACCENT_COLOR))

    async def settle_opening_hand(self) -> None:
        """Record the result when a natural blackjack ended the game before any move."""
        await self._finish_if_over()
        self._render()

    async def _finish_if_over(self) -> None:
        if not self._game.is_over:
            return
        await self._record_result(winner_id_of(self._game, self._player_id, self._dealer_id))
        self.stop()

    def _build_buttons(self) -> list[ui.Button]:
        hit = ui.Button(label="Hit", style=discord.ButtonStyle.primary)
        hit.callback = self._on_hit
        stand = ui.Button(label="Stand", style=discord.ButtonStyle.secondary)
        stand.callback = self._on_stand
        return [hit, stand]

    async def _on_hit(self, interaction: discord.Interaction) -> None:
        await self._act(self._game.hit, interaction)

    async def _on_stand(self, interaction: discord.Interaction) -> None:
        await self._act(self._game.stand, interaction)

    async def _act(
        self, action: Callable[[], None], interaction: discord.Interaction
    ) -> None:
        try:
            action()
        except GameError as error:
            await interaction.response.send_message(str(error), ephemeral=True)
            return
        await self._finish_if_over()
        self._render()
        await interaction.response.edit_message(view=self)
