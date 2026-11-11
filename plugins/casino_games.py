from __future__ import annotations

import math
import random
from dataclasses import dataclass
from numbers import Real

RED_NUMBERS = frozenset({1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36})

_EVEN_MONEY_KINDS = frozenset({"red", "black", "odd", "even", "low", "high"})
_DOZEN_LABELS = {"dozen1": 1, "dozen2": 2, "dozen3": 3}
_COLUMN_LABELS = {"column1": 1, "column2": 2, "column3": 3}

RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
SUITS = ("S", "H", "D", "C")
_RANK_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
    "A": 1,
}
_BLACKJACK_OUTCOMES = frozenset({"blackjack", "win", "push", "loss", "bust"})


class GameError(Exception):
    """A game rule or input error that can be shown to the user."""


@dataclass
class RouletteSelection:
    kind: str
    value: int | None
    label: str
    return_multiplier: int


@dataclass
class RouletteResult:
    number: int
    color: str
    selection: RouletteSelection
    won: bool
    payout: int
    label: str


@dataclass
class SlotsConfig:
    symbols: tuple[str, ...]
    weights: tuple[int, ...]
    triple_payouts: dict[str, int]
    two_cherry_payout: int


@dataclass
class SlotsResult:
    reels: tuple[str, str, str]
    multiplier: int
    payout: int
    label: str


@dataclass
class BlackjackSession:
    deck: list[str]
    player: list[str]
    dealer: list[str]
    bet: int
    doubled: bool = False
    done: bool = False
    outcome: str | None = None
    payout: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "deck": list(self.deck),
            "player": list(self.player),
            "dealer": list(self.dealer),
            "bet": self.bet,
            "doubled": self.doubled,
            "done": self.done,
            "outcome": self.outcome,
            "payout": self.payout,
        }

    @classmethod
    def from_dict(cls, data: object) -> BlackjackSession:
        if not isinstance(data, dict):
            raise GameError("Blackjack session must be an object.")
        required = {"deck", "player", "dealer", "bet", "doubled", "done", "outcome", "payout"}
        if not required <= set(data):
            raise GameError("Blackjack session is missing fields.")
        deck = _validated_cards(data.get("deck"), "deck")
        player = _validated_cards(data.get("player"), "player")
        dealer = _validated_cards(data.get("dealer"), "dealer")
        bet = data.get("bet")
        if isinstance(bet, bool) or not isinstance(bet, int) or bet <= 0:
            raise GameError("Bet must be a positive integer.")
        doubled = data.get("doubled")
        if not isinstance(doubled, bool):
            raise GameError("Doubled flag must be a boolean.")
        done = data.get("done")
        if not isinstance(done, bool):
            raise GameError("Done flag must be a boolean.")
        outcome = data.get("outcome")
        if outcome is not None and (not isinstance(outcome, str) or outcome not in _BLACKJACK_OUTCOMES):
            raise GameError("Invalid blackjack outcome.")
        payout = data.get("payout")
        if isinstance(payout, bool) or not isinstance(payout, int) or payout < 0:
            raise GameError("Payout must be a non-negative integer.")
        if done:
            if outcome is None:
                raise GameError("A finished hand needs an outcome.")
        elif outcome is not None or payout != 0:
            raise GameError("An active hand cannot have an outcome or payout.")
        return cls(
            deck=deck,
            player=player,
            dealer=dealer,
            bet=bet,
            doubled=doubled,
            done=done,
            outcome=outcome,
            payout=payout,
        )


def parse_roulette_selection(text: str) -> RouletteSelection:
    if not isinstance(text, str):
        raise GameError("Roulette selection must be text.")
    token = text.strip().lower()
    if token.isdigit():
        number = int(token)
        if token == str(number) and 0 <= number <= 36:
            return RouletteSelection("straight", number, str(number), 36)
        raise GameError("Roulette numbers run from 0 to 36.")
    if token in _EVEN_MONEY_KINDS:
        return RouletteSelection(token, None, token, 2)
    if token in _DOZEN_LABELS:
        return RouletteSelection("dozen", _DOZEN_LABELS[token], token, 3)
    if token in _COLUMN_LABELS:
        return RouletteSelection("column", _COLUMN_LABELS[token], token, 3)
    raise GameError(f"Unknown roulette selection: {text!r}.")


def roulette_color(number: int) -> str:
    if isinstance(number, bool) or not isinstance(number, int) or not 0 <= number <= 36:
        raise GameError("Roulette numbers run from 0 to 36.")
    if number == 0:
        return "green"
    if number in RED_NUMBERS:
        return "red"
    return "black"


def spin_roulette(
    bet: int,
    selection: RouletteSelection,
    rng: random.Random | None = None,
) -> RouletteResult:
    _validate_bet(bet)
    if not isinstance(selection, RouletteSelection):
        raise GameError("Invalid roulette selection.")
    engine = rng if rng is not None else random.SystemRandom()
    number = engine.randrange(37)
    color = roulette_color(number)
    won = _roulette_won(number, color, selection)
    payout = bet * selection.return_multiplier if won else 0
    return RouletteResult(
        number=number,
        color=color,
        selection=selection,
        won=won,
        payout=payout,
        label=selection.label,
    )


def default_slots_config() -> SlotsConfig:
    return SlotsConfig(
        symbols=("cherry", "lemon", "bell", "bar", "seven"),
        weights=(30, 25, 20, 15, 10),
        triple_payouts={"cherry": 4, "lemon": 5, "bell": 10, "bar": 20, "seven": 50},
        two_cherry_payout=2,
    )


def spin_slots(
    bet: int,
    config: SlotsConfig,
    rng: random.Random | None = None,
) -> SlotsResult:
    _validate_bet(bet)
    _validate_slots_config(config)
    engine = rng if rng is not None else random.SystemRandom()
    drawn = engine.choices(config.symbols, weights=config.weights, k=3)
    reels: tuple[str, str, str] = (drawn[0], drawn[1], drawn[2])
    if reels[0] == reels[1] == reels[2]:
        multiplier = config.triple_payouts[reels[0]]
    elif reels.count("cherry") == 2:
        multiplier = config.two_cherry_payout
    else:
        multiplier = 0
    payout = bet * multiplier
    return SlotsResult(
        reels=reels,
        multiplier=multiplier,
        payout=payout,
        label=" | ".join(reels),
    )


def hand_value(cards: list[str]) -> tuple[int, bool]:
    if not isinstance(cards, list):
        raise GameError("A hand must be a list of cards.")
    total = 0
    aces = 0
    for card in cards:
        rank = _card_rank(card)
        if rank == "A":
            aces += 1
        total += _RANK_VALUES[rank]
    soft = aces > 0 and total + 10 <= 21
    if soft:
        total += 10
    return total, soft


def is_blackjack(cards: list[str]) -> bool:
    if not isinstance(cards, list):
        raise GameError("A hand must be a list of cards.")
    if len(cards) != 2:
        return False
    total, _ = hand_value(cards)
    return total == 21


def start_blackjack(
    bet: int,
    decks: int = 1,
    dealer_hits_soft_17: bool = False,
    blackjack_payout: float = 1.5,
    rng: random.Random | None = None,
) -> BlackjackSession:
    _validate_bet(bet)
    _validate_decks(decks)
    _validate_blackjack_payout(blackjack_payout)
    engine = rng if rng is not None else random.SystemRandom()
    deck = _build_deck(decks)
    engine.shuffle(deck)
    player = [_draw(deck)]
    dealer = [_draw(deck)]
    player.append(_draw(deck))
    dealer.append(_draw(deck))
    session = BlackjackSession(deck=deck, player=player, dealer=dealer, bet=bet)
    player_blackjack = is_blackjack(player)
    dealer_blackjack = is_blackjack(dealer)
    if player_blackjack and dealer_blackjack:
        _settle(session, "push", bet)
    elif player_blackjack:
        _settle(session, "blackjack", bet + math.floor(bet * blackjack_payout))
    elif dealer_blackjack:
        _settle(session, "loss", 0)
    return session


def hit(session: BlackjackSession, dealer_hits_soft_17: bool = False) -> BlackjackSession:
    _require_active(session)
    session.player.append(_draw(session.deck))
    total, _ = hand_value(session.player)
    if total > 21:
        _settle(session, "bust", 0)
    return session


def stand(
    session: BlackjackSession,
    dealer_hits_soft_17: bool = False,
    blackjack_payout: float = 1.5,
) -> BlackjackSession:
    _require_active(session)
    _validate_blackjack_payout(blackjack_payout)
    _play_dealer(session, dealer_hits_soft_17)
    _settle_showdown(session)
    return session


def double(
    session: BlackjackSession,
    dealer_hits_soft_17: bool = False,
    blackjack_payout: float = 1.5,
) -> BlackjackSession:
    _require_active(session)
    if session.doubled:
        raise GameError("This hand has already been doubled.")
    if len(session.player) != 2:
        raise GameError("Double is only allowed on the first two cards.")
    _validate_blackjack_payout(blackjack_payout)
    card = _draw(session.deck)
    session.bet *= 2
    session.doubled = True
    session.player.append(card)
    total, _ = hand_value(session.player)
    if total > 21:
        _settle(session, "bust", 0)
        return session
    _play_dealer(session, dealer_hits_soft_17)
    _settle_showdown(session)
    return session


def _roulette_won(number: int, color: str, selection: RouletteSelection) -> bool:
    kind = selection.kind
    if kind == "straight":
        return selection.value == number
    if kind == "red":
        return color == "red"
    if kind == "black":
        return color == "black"
    if kind == "odd":
        return number != 0 and number % 2 == 1
    if kind == "even":
        return number != 0 and number % 2 == 0
    if kind == "low":
        return 1 <= number <= 18
    if kind == "high":
        return 19 <= number <= 36
    if kind == "dozen" and selection.value is not None:
        low = (selection.value - 1) * 12 + 1
        return low <= number <= low + 11
    if kind == "column" and selection.value is not None:
        return number != 0 and number % 3 == selection.value % 3
    raise GameError("Invalid roulette selection.")


def _validate_bet(bet: int) -> None:
    if isinstance(bet, bool) or not isinstance(bet, int) or bet <= 0:
        raise GameError("Bet must be a positive integer.")


def _validate_decks(decks: int) -> None:
    if isinstance(decks, bool) or not isinstance(decks, int) or decks < 1:
        raise GameError("Decks must be a positive integer.")


def _validate_blackjack_payout(blackjack_payout: float) -> None:
    if isinstance(blackjack_payout, bool) or not isinstance(blackjack_payout, Real) or not blackjack_payout > 0:
        raise GameError("Blackjack payout must be positive.")


def _validate_slots_config(config: SlotsConfig) -> None:
    if not isinstance(config, SlotsConfig):
        raise GameError("Invalid slots configuration.")
    if not config.symbols:
        raise GameError("Slots need at least one symbol.")
    if any(not isinstance(symbol, str) or not symbol for symbol in config.symbols):
        raise GameError("Slots symbols must be non-empty text.")
    if len(set(config.symbols)) != len(config.symbols):
        raise GameError("Slots symbols must be unique.")
    if len(config.symbols) != len(config.weights):
        raise GameError("Slots symbols and weights must have the same length.")
    for weight in config.weights:
        if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
            raise GameError("Slots weights must be positive integers.")
    if not isinstance(config.triple_payouts, dict):
        raise GameError("Slots triple payouts must be a mapping.")
    for symbol in config.symbols:
        payout = config.triple_payouts.get(symbol)
        if isinstance(payout, bool) or not isinstance(payout, int) or payout < 0:
            raise GameError("Slots triple payouts must be non-negative integers for every symbol.")
    if isinstance(config.two_cherry_payout, bool) or not isinstance(config.two_cherry_payout, int):
        raise GameError("Slots two-cherry payout must be a non-negative integer.")
    if config.two_cherry_payout < 0:
        raise GameError("Slots two-cherry payout must be a non-negative integer.")


def _card_rank(card: str) -> str:
    if not isinstance(card, str) or len(card) not in (2, 3):
        raise GameError(f"Invalid card: {card!r}.")
    rank = card[:-1]
    suit = card[-1]
    if rank not in _RANK_VALUES or suit not in SUITS:
        raise GameError(f"Invalid card: {card!r}.")
    return rank


def _validated_cards(data: object, field: str) -> list[str]:
    if not isinstance(data, list):
        raise GameError(f"Blackjack {field} must be a list of cards.")
    for card in data:
        _card_rank(card)
    return list(data)


def _build_deck(decks: int) -> list[str]:
    return [rank + suit for _ in range(decks) for suit in SUITS for rank in RANKS]


def _draw(deck: list[str]) -> str:
    if not deck:
        raise GameError("The deck is empty.")
    return deck.pop()


def _require_active(session: BlackjackSession) -> None:
    if not isinstance(session, BlackjackSession):
        raise GameError("Invalid blackjack session.")
    if session.done:
        raise GameError("This hand is already finished.")


def _play_dealer(session: BlackjackSession, dealer_hits_soft_17: bool) -> None:
    while True:
        total, soft = hand_value(session.dealer)
        if total > 21:
            return
        if total < 17 or (total == 17 and soft and dealer_hits_soft_17):
            session.dealer.append(_draw(session.deck))
            continue
        return


def _settle_showdown(session: BlackjackSession) -> None:
    player_total, _ = hand_value(session.player)
    dealer_total, _ = hand_value(session.dealer)
    if dealer_total > 21 or player_total > dealer_total:
        _settle(session, "win", session.bet * 2)
    elif player_total == dealer_total:
        _settle(session, "push", session.bet)
    else:
        _settle(session, "loss", 0)


def _settle(session: BlackjackSession, outcome: str, payout: int) -> None:
    session.done = True
    session.outcome = outcome
    session.payout = payout
