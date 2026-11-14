import random
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from features.games.errors import GameError

TARGET = 21
DEALER_STANDS_ON = 17
FACE_VALUE = 10
ACE_VALUE = 11
ACE_REDUCTION = ACE_VALUE - 1
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
SUITS = ("♠", "♥", "♦", "♣")


class Outcome(Enum):
    PLAYER_WINS = "player"
    DEALER_WINS = "dealer"
    PUSH = "push"


@dataclass(frozen=True)
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        if self.rank == "A":
            return ACE_VALUE
        return int(self.rank) if self.rank.isdigit() else FACE_VALUE

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


def new_deck(rng: random.Random) -> list[Card]:
    deck = [Card(rank, suit) for suit in SUITS for rank in RANKS]
    rng.shuffle(deck)
    return deck


def hand_total(hand: Sequence[Card]) -> int:
    total = sum(card.value for card in hand)
    aces = sum(1 for card in hand if card.rank == "A")
    while total > TARGET and aces:
        total -= ACE_REDUCTION
        aces -= 1
    return total


def is_blackjack(hand: Sequence[Card]) -> bool:
    return len(hand) == 2 and hand_total(hand) == TARGET


class BlackjackGame:
    """One round: cards are drawn from the end of the deck, player and dealer alternating."""

    def __init__(self, deck: list[Card]) -> None:
        self._deck = deck
        self.player_hand: list[Card] = []
        self.dealer_hand: list[Card] = []
        self.outcome: Outcome | None = None
        for hand in (self.player_hand, self.dealer_hand, self.player_hand, self.dealer_hand):
            hand.append(self._deck.pop())
        if is_blackjack(self.player_hand) or is_blackjack(self.dealer_hand):
            self.outcome = self._decide()

    @property
    def is_over(self) -> bool:
        return self.outcome is not None

    @property
    def player_busted(self) -> bool:
        return hand_total(self.player_hand) > TARGET

    @property
    def dealer_busted(self) -> bool:
        return hand_total(self.dealer_hand) > TARGET

    def hit(self) -> None:
        self._ensure_in_progress()
        self.player_hand.append(self._deck.pop())
        if hand_total(self.player_hand) >= TARGET:
            self.stand()

    def stand(self) -> None:
        self._ensure_in_progress()
        if not self.player_busted:
            self._play_dealer()
        self.outcome = self._decide()

    def _ensure_in_progress(self) -> None:
        if self.is_over:
            raise GameError("The game is over.")

    def _play_dealer(self) -> None:
        while hand_total(self.dealer_hand) < DEALER_STANDS_ON:
            self.dealer_hand.append(self._deck.pop())

    def _decide(self) -> Outcome:
        if self.player_busted:
            return Outcome.DEALER_WINS
        if self.dealer_busted:
            return Outcome.PLAYER_WINS
        player_natural = is_blackjack(self.player_hand)
        if player_natural != is_blackjack(self.dealer_hand):
            return Outcome.PLAYER_WINS if player_natural else Outcome.DEALER_WINS
        player, dealer = hand_total(self.player_hand), hand_total(self.dealer_hand)
        if player == dealer:
            return Outcome.PUSH
        return Outcome.PLAYER_WINS if player > dealer else Outcome.DEALER_WINS
