import random

import pytest

from plugins.casino_games import (
    BlackjackSession,
    GameError,
    SlotsConfig,
    default_slots_config,
    double,
    hand_value,
    hit,
    is_blackjack,
    parse_roulette_selection,
    roulette_color,
    spin_roulette,
    spin_slots,
    stand,
    start_blackjack,
)
from tests.support.fakes import FixedRouletteRng, SequenceRng, StackedRng


def make_blackjack_session(player, dealer, deck=(), bet=10, doubled=False, done=False, outcome=None, payout=0):
    return BlackjackSession(
        deck=list(deck),
        player=list(player),
        dealer=list(dealer),
        bet=bet,
        doubled=doubled,
        done=done,
        outcome=outcome,
        payout=payout,
    )


def blackjack_payload():
    return {
        "deck": ["2C"],
        "player": ["10H", "9D"],
        "dealer": ["10H", "8D"],
        "bet": 10,
        "doubled": False,
        "done": False,
        "outcome": None,
        "payout": 0,
    }


@pytest.mark.parametrize(
    "text, kind, value, multiplier",
    [
        ("0", "straight", 0, 36),
        ("17", "straight", 17, 36),
        ("36", "straight", 36, 36),
        ("red", "red", None, 2),
        ("BLACK", "black", None, 2),
        ("odd", "odd", None, 2),
        ("even", "even", None, 2),
        ("low", "low", None, 2),
        ("high", "high", None, 2),
        ("dozen1", "dozen", 1, 3),
        ("dozen2", "dozen", 2, 3),
        ("DoZeN3", "dozen", 3, 3),
        ("column1", "column", 1, 3),
        ("column2", "column", 2, 3),
        ("COLUMN3", "column", 3, 3),
        ("  Red  ", "red", None, 2),
    ],
)
def test_roulette_parse_accepts_every_selection_form(text, kind, value, multiplier):
    selection = parse_roulette_selection(text)

    assert selection.kind == kind
    assert selection.value == value
    assert selection.return_multiplier == multiplier
    assert selection.label


@pytest.mark.parametrize(
    "text",
    ["", "37", "-1", "1.5", "green", "dozen0", "dozen4", "column0", "column4", "banana", "00"],
)
def test_roulette_parse_rejects_invalid_selections(text):
    with pytest.raises(GameError):
        parse_roulette_selection(text)


@pytest.mark.parametrize(
    "number, color",
    [(0, "green"), (1, "red"), (2, "black"), (17, "black"), (36, "red"), (34, "red"), (33, "black")],
)
def test_roulette_color_matches_the_wheel(number, color):
    assert roulette_color(number) == color


@pytest.mark.parametrize("number", [-1, 37, True, 1.5, "1"])
def test_roulette_color_rejects_invalid_numbers(number):
    with pytest.raises(GameError):
        roulette_color(number)


def test_roulette_zero_is_green_and_loses_even_money_dozen_and_column():
    losing = [
        "red",
        "black",
        "odd",
        "even",
        "low",
        "high",
        "dozen1",
        "dozen2",
        "dozen3",
        "column1",
        "column2",
        "column3",
    ]

    for text in losing:
        result = spin_roulette(10, parse_roulette_selection(text), rng=FixedRouletteRng(0))
        assert result.number == 0
        assert result.color == "green"
        assert result.won is False
        assert result.payout == 0

    straight = spin_roulette(10, parse_roulette_selection("0"), rng=FixedRouletteRng(0))
    assert straight.won is True
    assert straight.payout == 360


@pytest.mark.parametrize(
    "text, number, payout",
    [
        ("19", 19, 360),
        ("red", 19, 20),
        ("odd", 19, 20),
        ("high", 19, 20),
        ("dozen2", 19, 30),
        ("column1", 19, 30),
        ("12", 12, 360),
        ("even", 12, 20),
        ("low", 12, 20),
        ("dozen1", 12, 30),
        ("column3", 12, 30),
        ("2", 2, 360),
        ("black", 2, 20),
        ("even", 2, 20),
        ("low", 2, 20),
        ("dozen1", 2, 30),
        ("column2", 2, 30),
    ],
)
def test_roulette_straight_even_money_dozen_and_column_payouts(text, number, payout):
    result = spin_roulette(10, parse_roulette_selection(text), rng=FixedRouletteRng(number))

    assert result.number == number
    assert result.won is True
    assert result.payout == payout
    assert result.label == result.selection.label


@pytest.mark.parametrize(
    "text, number",
    [("red", 2), ("black", 1), ("odd", 2), ("even", 1), ("high", 18), ("dozen1", 13), ("column1", 2), ("5", 17)],
)
def test_roulette_losing_selections_pay_nothing(text, number):
    result = spin_roulette(10, parse_roulette_selection(text), rng=FixedRouletteRng(number))

    assert result.won is False
    assert result.payout == 0


@pytest.mark.parametrize("bet", [0, -1, True, 1.5, "10"])
def test_roulette_rejects_invalid_bets(bet):
    with pytest.raises(GameError):
        spin_roulette(bet, parse_roulette_selection("red"), rng=FixedRouletteRng(1))


def test_slots_default_config_matches_the_expected_paytable():
    config = default_slots_config()

    assert config.symbols == ("cherry", "lemon", "bell", "bar", "seven")
    assert config.weights == (30, 25, 20, 15, 10)
    assert config.triple_payouts == {"cherry": 4, "lemon": 5, "bell": 10, "bar": 20, "seven": 50}
    assert config.two_cherry_payout == 2


@pytest.mark.parametrize(
    "reels, multiplier",
    [
        (("seven", "seven", "seven"), 50),
        (("bar", "bar", "bar"), 20),
        (("bell", "bell", "bell"), 10),
        (("lemon", "lemon", "lemon"), 5),
        (("cherry", "cherry", "cherry"), 4),
        (("cherry", "cherry", "lemon"), 2),
        (("cherry", "lemon", "cherry"), 2),
        (("lemon", "cherry", "cherry"), 2),
        (("cherry", "lemon", "lemon"), 0),
        (("cherry", "lemon", "bell"), 0),
        (("lemon", "bell", "bar"), 0),
        (("seven", "seven", "bar"), 0),
    ],
)
def test_slots_deterministic_reels_and_paytable_branches(reels, multiplier):
    config = default_slots_config()

    result = spin_slots(10, config, rng=SequenceRng([reels]))

    assert result.reels == reels
    assert result.multiplier == multiplier
    assert result.payout == 10 * multiplier
    assert result.label == " | ".join(reels)


@pytest.mark.parametrize(
    "config",
    [
        SlotsConfig(("a", "b"), (1,), {"a": 1, "b": 1}, 2),
        SlotsConfig((), (), {}, 2),
        SlotsConfig(("a", "a"), (1, 1), {"a": 1}, 2),
        SlotsConfig(("a", "b"), (1, 0), {"a": 1, "b": 1}, 2),
        SlotsConfig(("a", "b"), (1, -1), {"a": 1, "b": 1}, 2),
        SlotsConfig(("a", "b"), (1, True), {"a": 1, "b": 1}, 2),
        SlotsConfig(("a", "b"), (1, 1), {"a": 1}, 2),
        SlotsConfig(("a", "b"), (1, 1), {"a": 1, "b": -1}, 2),
        SlotsConfig(("a", "b"), (1, 1), {"a": 1, "b": 1}, -1),
        SlotsConfig(("a", ""), (1, 1), {"a": 1, "": 1}, 2),
    ],
)
def test_slots_rejects_invalid_configurations(config):
    with pytest.raises(GameError):
        spin_slots(10, config, rng=SequenceRng([("a", "b", "a")]))


@pytest.mark.parametrize("bet", [0, -1, True, 1.5, "10"])
def test_slots_rejects_invalid_bets(bet):
    with pytest.raises(GameError):
        spin_slots(bet, default_slots_config(), rng=SequenceRng([("cherry", "lemon", "bell")]))


@pytest.mark.parametrize(
    "cards, total, soft",
    [
        (["AS"], 11, True),
        (["AS", "6H"], 17, True),
        (["AS", "6H", "10C"], 17, False),
        (["AS", "AH"], 12, True),
        (["AS", "AH", "9C"], 21, True),
        (["10H", "KD"], 20, False),
        (["JS", "QD", "2C"], 22, False),
        (["2S", "3H", "4D"], 9, False),
    ],
)
def test_blackjack_hand_value_counts_soft_and_hard_aces(cards, total, soft):
    assert hand_value(cards) == (total, soft)


@pytest.mark.parametrize("cards", [["ZZ"], ["1S"], ["10X"], ["H"], [""], "AS"])
def test_blackjack_hand_value_rejects_invalid_cards(cards):
    with pytest.raises(GameError):
        hand_value(cards)


@pytest.mark.parametrize(
    "cards, expected",
    [
        (["AS", "KH"], True),
        (["10H", "AD"], True),
        (["AS", "9S"], False),
        (["10H", "9D"], False),
        (["AS", "5H", "5D"], False),
        (["AS", "AH"], False),
    ],
)
def test_blackjack_is_blackjack_detects_natural_hands(cards, expected):
    assert is_blackjack(cards) is expected


def test_blackjack_player_natural_settles_immediately():
    session = start_blackjack(10, rng=StackedRng(["AS", "9H", "KH", "7C"]))

    assert session.player == ["AS", "KH"]
    assert session.dealer == ["9H", "7C"]
    assert session.done is True
    assert session.outcome == "blackjack"
    assert session.payout == 25


def test_blackjack_both_naturals_push():
    session = start_blackjack(10, rng=StackedRng(["AS", "AH", "KH", "KD"]))

    assert session.done is True
    assert session.outcome == "push"
    assert session.payout == 10


def test_blackjack_dealer_natural_loses_immediately():
    session = start_blackjack(10, rng=StackedRng(["10H", "AS", "9D", "KH"]))

    assert session.done is True
    assert session.outcome == "loss"
    assert session.payout == 0


def test_blackjack_natural_uses_the_configured_payout():
    session = start_blackjack(10, blackjack_payout=2.0, rng=StackedRng(["AS", "9H", "KH", "7C"]))

    assert session.outcome == "blackjack"
    assert session.payout == 30


@pytest.mark.parametrize(
    "overrides",
    [
        {"bet": 0},
        {"bet": -1},
        {"bet": True},
        {"decks": 0},
        {"decks": -2},
        {"decks": True},
        {"blackjack_payout": 0},
        {"blackjack_payout": -1},
        {"blackjack_payout": True},
    ],
)
def test_blackjack_start_rejects_invalid_parameters(overrides):
    values = {"bet": 10}
    values.update(overrides)

    with pytest.raises(GameError):
        start_blackjack(**values, rng=random.Random(1))


def test_blackjack_hit_busts_and_settles_the_loss():
    session = make_blackjack_session(["10H", "9D"], ["7C", "8D"], deck=["KS"])

    result = hit(session)

    assert result is session
    assert session.player == ["10H", "9D", "KS"]
    assert session.done is True
    assert session.outcome == "bust"
    assert session.payout == 0


def test_blackjack_hit_keeps_a_safe_hand_active():
    session = make_blackjack_session(["5H", "6D"], ["10H", "7D"], deck=["3C"])

    hit(session)

    assert session.player[-1] == "3C"
    assert session.done is False
    assert session.outcome is None
    assert session.payout == 0


@pytest.mark.parametrize(
    "player, dealer, outcome, payout",
    [
        (["10H", "9D"], ["10H", "8D"], "win", 20),
        (["10H", "9D"], ["10H", "9D"], "push", 10),
        (["10H", "8D"], ["10H", "9D"], "loss", 0),
        (["10H", "8D"], ["10H", "6D", "KD"], "win", 20),
    ],
)
def test_blackjack_stand_settles_win_push_loss_and_dealer_bust(player, dealer, outcome, payout):
    session = make_blackjack_session(player, dealer)

    stand(session)

    assert session.done is True
    assert session.outcome == outcome
    assert session.payout == payout


def test_blackjack_dealer_draws_until_seventeen():
    session = make_blackjack_session(["10H", "9D"], ["10H", "5D"], deck=["3C"])

    stand(session)

    assert session.dealer == ["10H", "5D", "3C"]
    assert session.outcome == "win"
    assert session.payout == 20


def test_blackjack_dealer_hits_soft_seventeen_only_when_configured():
    standing = make_blackjack_session(["10H", "8D"], ["AS", "6H"], deck=["2C"])
    stand(standing)
    assert standing.dealer == ["AS", "6H"]
    assert standing.outcome == "win"

    hitting = make_blackjack_session(["10H", "8D"], ["AS", "6H"], deck=["2C"])
    stand(hitting, dealer_hits_soft_17=True)
    assert hitting.dealer == ["AS", "6H", "2C"]
    assert hitting.outcome == "loss"


def test_blackjack_dealer_never_hits_hard_seventeen():
    session = make_blackjack_session(["10H", "8D"], ["10H", "7D"], deck=["2C"])

    stand(session, dealer_hits_soft_17=True)

    assert session.dealer == ["10H", "7D"]
    assert session.outcome == "win"


def test_blackjack_double_doubles_bet_draws_once_and_wins():
    session = make_blackjack_session(["5H", "6D"], ["10H", "7D"], deck=["10C"])

    result = double(session)

    assert result is session
    assert session.bet == 20
    assert session.doubled is True
    assert session.player == ["5H", "6D", "10C"]
    assert session.outcome == "win"
    assert session.payout == 40


def test_blackjack_double_push_pays_the_doubled_bet():
    session = make_blackjack_session(["5H", "5D"], ["10H", "9D"], deck=["9C"])

    double(session)

    assert session.bet == 20
    assert session.outcome == "push"
    assert session.payout == 20


def test_blackjack_double_bust_loses_the_doubled_bet():
    session = make_blackjack_session(["10H", "6D"], ["10H", "7D"], deck=["KD"])

    double(session)

    assert session.bet == 20
    assert session.doubled is True
    assert session.outcome == "bust"
    assert session.payout == 0


def test_blackjack_double_rejects_hands_with_more_than_two_cards():
    session = make_blackjack_session(["2H", "3D", "4C"], ["10H", "7D"], deck=["5S"])

    with pytest.raises(GameError):
        double(session)

    assert session.bet == 10
    assert session.doubled is False


def test_blackjack_double_rejects_an_already_doubled_hand():
    session = make_blackjack_session(["5H", "6D"], ["10H", "7D"], deck=["10C"], doubled=True)

    with pytest.raises(GameError):
        double(session)


def test_blackjack_hit_stand_and_double_reject_a_finished_hand():
    session = make_blackjack_session(
        ["10H", "9D"],
        ["10H", "8D"],
        done=True,
        outcome="win",
        payout=20,
    )

    with pytest.raises(GameError):
        hit(session)
    with pytest.raises(GameError):
        stand(session)
    with pytest.raises(GameError):
        double(session)


def test_blackjack_from_dict_round_trips_active_and_finished_sessions():
    active = start_blackjack(10, rng=random.Random(5))
    assert BlackjackSession.from_dict(active.to_dict()) == active

    finished = make_blackjack_session(["10H", "9D"], ["10H", "8D"], done=True, outcome="win", payout=20)
    assert BlackjackSession.from_dict(finished.to_dict()) == finished


@pytest.mark.parametrize(
    "patch",
    [
        {"deck": "not a list"},
        {"player": ["ZZ"]},
        {"dealer": ["10X"]},
        {"bet": 0},
        {"bet": "10"},
        {"bet": True},
        {"doubled": "no"},
        {"done": "no"},
        {"outcome": "won"},
        {"outcome": "win"},
        {"payout": -1},
        {"payout": "10"},
        {"done": True, "outcome": None},
    ],
)
def test_blackjack_from_dict_rejects_malformed_sessions(patch):
    data = blackjack_payload()
    data.update(patch)

    with pytest.raises(GameError):
        BlackjackSession.from_dict(data)


def test_blackjack_from_dict_rejects_non_mappings_and_missing_fields():
    with pytest.raises(GameError):
        BlackjackSession.from_dict([])

    payload = blackjack_payload()
    for key in list(payload):
        data = dict(payload)
        del data[key]
        with pytest.raises(GameError):
            BlackjackSession.from_dict(data)
