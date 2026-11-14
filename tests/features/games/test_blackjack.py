"""Tests for blackjack rules and the view."""

import random
import unittest

from features.games.blackjack import (
    RANKS,
    SUITS,
    BlackjackGame,
    Card,
    Outcome,
    hand_total,
    is_blackjack,
    new_deck,
)
from features.games.blackjack_view import (
    BlackjackView,
    dealer_hand_text,
    status_text,
    winner_id_of,
)
from features.games.errors import GameError
from tests.features.games.test_game_views import RecordingHandler, make_interaction, notes_in

PLAYER, DEALER = 1, 2
NAMES = {PLAYER: "Alice", DEALER: "Harriet"}


def hand(*ranks: str) -> list[Card]:
    return [Card(rank, "♠") for rank in ranks]


def game_with(*ranks: str) -> BlackjackGame:
    """Deal in order: player, dealer, player, dealer, then every later draw."""
    return BlackjackGame(list(reversed(hand(*ranks))))


def make_view(*ranks: str, on_finish=None) -> BlackjackView:
    return BlackjackView(
        game_with(*ranks),
        NAMES,
        player_id=PLAYER,
        dealer_id=DEALER,
        timeout_seconds=60,
        on_finish=on_finish,
    )


class HandTotalTests(unittest.TestCase):
    def test_face_cards_are_ten_and_number_cards_are_face_value(self) -> None:
        self.assertEqual(hand_total(hand("K", "7")), 17)
        self.assertEqual(hand_total(hand("2", "3", "9")), 14)

    def test_an_ace_counts_eleven_until_that_would_bust(self) -> None:
        self.assertEqual(hand_total(hand("A", "6")), 17)
        self.assertEqual(hand_total(hand("A", "6", "9")), 16)

    def test_several_aces_are_reduced_one_at_a_time(self) -> None:
        self.assertEqual(hand_total(hand("A", "A")), 12)
        self.assertEqual(hand_total(hand("A", "A", "9")), 21)

    def test_blackjack_is_exactly_two_cards(self) -> None:
        self.assertTrue(is_blackjack(hand("A", "K")))
        self.assertFalse(is_blackjack(hand("7", "7", "7")))

    def test_new_deck_has_every_card_once(self) -> None:
        deck = new_deck(random.Random(0))
        self.assertEqual(len(deck), len(RANKS) * len(SUITS))
        self.assertEqual(len(set(deck)), len(deck))


class BlackjackGameTests(unittest.TestCase):
    def test_cards_are_dealt_alternately(self) -> None:
        game = game_with("2", "3", "4", "5", "9")
        self.assertEqual([card.rank for card in game.player_hand], ["2", "4"])
        self.assertEqual([card.rank for card in game.dealer_hand], ["3", "5"])
        self.assertFalse(game.is_over)

    def test_hit_draws_a_card(self) -> None:
        game = game_with("2", "3", "4", "5", "6")
        game.hit()
        self.assertEqual([card.rank for card in game.player_hand], ["2", "4", "6"])

    def test_busting_loses_and_the_dealer_does_not_draw(self) -> None:
        game = game_with("10", "6", "6", "5", "K", "9")
        game.hit()
        self.assertTrue(game.player_busted)
        self.assertIs(game.outcome, Outcome.DEALER_WINS)
        self.assertEqual(len(game.dealer_hand), 2)

    def test_reaching_21_stands_automatically(self) -> None:
        game = game_with("10", "9", "5", "8", "6", "9")
        game.hit()
        self.assertTrue(game.is_over)
        self.assertIs(game.outcome, Outcome.PLAYER_WINS)

    def test_dealer_draws_to_seventeen_and_stands_on_it(self) -> None:
        game = game_with("10", "5", "6", "2", "K")
        game.stand()
        self.assertEqual(hand_total(game.dealer_hand), 17)
        self.assertEqual(len(game.dealer_hand), 3)
        self.assertIs(game.outcome, Outcome.DEALER_WINS)

    def test_dealer_stands_on_a_hard_seventeen_without_drawing(self) -> None:
        game = game_with("10", "10", "8", "7", "K")
        game.stand()
        self.assertEqual(len(game.dealer_hand), 2)
        self.assertIs(game.outcome, Outcome.PLAYER_WINS)

    def test_dealer_bust_means_the_player_wins(self) -> None:
        game = game_with("10", "10", "2", "6", "K")
        game.stand()
        self.assertTrue(game.dealer_busted)
        self.assertIs(game.outcome, Outcome.PLAYER_WINS)

    def test_equal_totals_push(self) -> None:
        game = game_with("10", "10", "8", "8")
        game.stand()
        self.assertIs(game.outcome, Outcome.PUSH)

    def test_player_natural_wins_immediately(self) -> None:
        game = game_with("A", "9", "K", "7")
        self.assertIs(game.outcome, Outcome.PLAYER_WINS)

    def test_dealer_natural_wins_immediately(self) -> None:
        game = game_with("9", "A", "7", "K")
        self.assertIs(game.outcome, Outcome.DEALER_WINS)

    def test_two_naturals_push(self) -> None:
        game = game_with("A", "A", "K", "K")
        self.assertIs(game.outcome, Outcome.PUSH)

    def test_natural_beats_a_three_card_21(self) -> None:
        game = game_with("A", "7", "K", "7", "7")
        self.assertIs(game.outcome, Outcome.PLAYER_WINS)

    def test_no_moves_after_the_game_is_over(self) -> None:
        game = game_with("A", "9", "K", "7")
        with self.assertRaises(GameError):
            game.hit()
        with self.assertRaises(GameError):
            game.stand()


class DisplayTests(unittest.TestCase):
    def test_dealer_hides_the_second_card_until_revealed(self) -> None:
        cards = hand("K", "7")
        hidden = dealer_hand_text("Harriet", cards, revealed=False)
        shown = dealer_hand_text("Harriet", cards, revealed=True)
        self.assertEqual(hidden, "**Harriet** · ?\n`K♠` `??`")
        self.assertEqual(shown, "**Harriet** · 17\n`K♠` `7♠`")

    def test_status_text_names_the_winner_and_the_reason(self) -> None:
        def status(game: BlackjackGame, timed_out: bool = False) -> str:
            return status_text(game, "Alice", "Harriet", timed_out)

        in_progress = game_with("10", "5", "9", "6")
        self.assertEqual(status(in_progress), "Hit or stand?")
        self.assertIn("Timed out", status(in_progress, timed_out=True))
        bust = game_with("10", "6", "6", "5", "K")
        bust.hit()
        self.assertEqual(status(bust), "Bust. **Harriet** wins.")
        push = game_with("10", "10", "8", "8")
        push.stand()
        self.assertEqual(status(push), "Push. Nobody wins.")

    def test_winner_id_maps_the_outcome(self) -> None:
        win = game_with("A", "9", "K", "7")
        loss = game_with("9", "A", "7", "K")
        push = game_with("A", "A", "K", "K")
        self.assertEqual(winner_id_of(win, PLAYER, DEALER), PLAYER)
        self.assertEqual(winner_id_of(loss, PLAYER, DEALER), DEALER)
        self.assertIsNone(winner_id_of(push, PLAYER, DEALER))


class BlackjackViewTests(unittest.IsolatedAsyncioTestCase):
    async def test_hit_updates_the_message(self) -> None:
        view = make_view("2", "3", "4", "5", "6")
        interaction = make_interaction(PLAYER)
        await view._on_hit(interaction)
        self.assertEqual(len(view._game.player_hand), 3)
        interaction.response.edit_message.assert_awaited_once()
        self.assertFalse(view.is_finished())

    async def test_stand_finishes_the_game_and_reports_the_winner(self) -> None:
        handler = RecordingHandler()
        view = make_view("10", "10", "8", "7", on_finish=handler)
        await view._on_stand(make_interaction(PLAYER))
        self.assertEqual(handler.winners, [PLAYER])
        self.assertTrue(view.is_finished())
        self.assertIn("-# +50 XP", notes_in(view))

    async def test_dealer_win_is_reported_as_the_dealer(self) -> None:
        handler = RecordingHandler(note=None)
        view = make_view("10", "10", "7", "9", on_finish=handler)
        await view._on_stand(make_interaction(PLAYER))
        self.assertEqual(handler.winners, [DEALER])

    async def test_push_reports_no_winner(self) -> None:
        handler = RecordingHandler(note=None)
        view = make_view("10", "10", "8", "8", on_finish=handler)
        await view._on_stand(make_interaction(PLAYER))
        self.assertEqual(handler.winners, [None])

    async def test_an_opening_natural_is_settled_before_any_press(self) -> None:
        handler = RecordingHandler()
        view = make_view("A", "9", "K", "7", on_finish=handler)
        await view.settle_opening_hand()
        self.assertEqual(handler.winners, [PLAYER])
        self.assertTrue(view.is_finished())
        self.assertIn("-# +50 XP", notes_in(view))

    async def test_settling_an_unfinished_game_reports_nothing(self) -> None:
        handler = RecordingHandler()
        view = make_view("10", "5", "9", "6", on_finish=handler)
        await view.settle_opening_hand()
        self.assertEqual(handler.winners, [])
        self.assertFalse(view.is_finished())

    async def test_only_the_player_may_press(self) -> None:
        view = make_view("10", "5", "9", "6")
        self.assertTrue(await view.interaction_check(make_interaction(PLAYER)))
        self.assertFalse(await view.interaction_check(make_interaction(DEALER)))

    async def test_pressing_after_the_game_is_over_is_refused_privately(self) -> None:
        view = make_view("A", "9", "K", "7")
        interaction = make_interaction(PLAYER)
        await view._on_hit(interaction)
        self.assertTrue(interaction.response.send_message.await_args.kwargs["ephemeral"])


if __name__ == "__main__":
    unittest.main()
