from datetime import datetime, timezone

import pytest

import plugins.casino_store as casino_store_module
from plugins.commands.casino import Casino
from plugins.errors import ConfigurationError
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage, FixedRouletteRng, SequenceRng, StackedRng

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def fixed_time(monkeypatch):
    monkeypatch.setattr(casino_store_module, "utcnow", lambda: NOW)


def make_casino(tmp_path, client=None, **kwargs):
    client = client if client is not None else FakeClient()
    casino = Casino(client, "casino", data_dir=str(tmp_path / "casino"), **kwargs)
    casino.logger = FakeLogger()
    casino.store.logger = FakeLogger()
    return casino


def run(casino, content, **kwargs):
    message = FakeMessage(content, **kwargs)
    casino.run(message)
    return message


def last_text(client):
    return client.sent[-1][1]


def assert_private(client, clid=1):
    assert client.sent
    assert all(target == clid for target, _ in client.sent)
    assert client.server_sent == []
    assert client.channel_sent == []
    assert client.messages_sent == []


def test_help_aliases_and_unknown_subcommands_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client)

    run(casino, "!casino help")
    assert "Casino commands:" in last_text(client)
    assert "!casino balance" in last_text(client)

    run(casino, "!casino ?")
    assert "Casino commands:" in last_text(client)

    run(casino, "!casino")
    assert "Casino commands:" in last_text(client)

    run(casino, "!casino nope")
    assert "Casino commands:" in last_text(client)

    run(casino, "?casino help")
    assert "?casino balance" in last_text(client)

    assert_private(client)


def test_balance_daily_and_profile_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client)

    run(casino, "!casino balance")
    assert last_text(client) == "Balance: 500 chips"

    run(casino, "!casino bal")
    assert last_text(client) == "Balance: 500 chips"

    run(casino, "!casino daily")
    assert "Daily reward: 100 chips" in last_text(client)
    assert "Balance: 600 chips" in last_text(client)

    run(casino, "!casino daily")
    assert "Try again in" in last_text(client)

    run(casino, "!casino profile")
    text = last_text(client)
    assert "Profile: user" in text
    assert "Balance: 600 chips" in text
    assert "Rank: 1" in text
    assert "Games: 0" in text
    assert "Wins: 0" in text
    assert "Losses: 0" in text
    assert "Pushes: 0" in text
    assert "Total wagered: 0 chips" in text
    assert "Biggest win: 0 chips" in text

    assert_private(client)


def test_leaderboard_and_count_validation_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, leaderboard_size=3)
    casino.store.get_or_create("uid-2", "Bob")
    casino.store.settle_round("uid-2", game="roulette", wager=10, payout=20)

    run(casino, "!casino leaderboard")
    text = last_text(client)
    assert "Leaderboard:" in text
    assert "1. Bob - 510 chips" in text
    assert "2. user - 500 chips" in text

    run(casino, "!casino lb 1")
    text = last_text(client)
    assert "1. Bob - 510 chips" in text
    assert "user - 500 chips" not in text

    run(casino, "!casino top 99")
    text = last_text(client)
    assert "Bob" in text
    assert "user" in text

    for count in ("0", "-1", "abc"):
        run(casino, f"!casino leaderboard {count}")
        assert "positive integer" in last_text(client)

    assert_private(client)


def test_empty_leaderboard_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client)

    casino._leaderboard(FakeMessage("!casino leaderboard"), [])

    assert last_text(client) == "No players yet."
    assert_private(client)


def test_roulette_win_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=FixedRouletteRng(19))

    run(casino, "!casino roulette 10 red")
    text = last_text(client)
    assert "Roulette: 19 red" in text
    assert "Bet: 10 chips on red" in text
    assert "Result: win" in text
    assert "Net: +10 chips" in text
    assert "Balance: 510 chips" in text
    assert casino.store.balance("uid-1") == 510
    assert casino.store.get("uid-1").games_played == 1

    assert_private(client)


def test_roulette_loss_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=FixedRouletteRng(2))

    run(casino, "!casino rl 10 red")
    text = last_text(client)
    assert "Roulette: 2 black" in text
    assert "Result: loss" in text
    assert "Net: -10 chips" in text
    assert "Balance: 490 chips" in text

    assert_private(client)


def test_slots_win_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=SequenceRng([("cherry", "cherry", "cherry")]))

    run(casino, "!casino slots 10")
    text = last_text(client)
    assert "Slots: cherry | cherry | cherry" in text
    assert "Result: win (x4)" in text
    assert "Net: +30 chips" in text
    assert "Balance: 530 chips" in text
    assert casino.store.balance("uid-1") == 530

    assert_private(client)


def test_slots_loss_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=SequenceRng([("cherry", "lemon", "bell")]))

    run(casino, "!casino slot 10")
    text = last_text(client)
    assert "Slots: cherry | lemon | bell" in text
    assert "Result: loss (x0)" in text
    assert "Net: -10 chips" in text
    assert "Balance: 490 chips" in text

    assert_private(client)


def test_custom_slots_config_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(
        tmp_path,
        client,
        rng=SequenceRng([("a", "a", "a")]),
        slots_symbols=("a", "b"),
        slots_weights=(1, 1),
        slots_payouts={"a": 10, "b": 0},
        slots_two_cherry_payout=1,
    )

    run(casino, "!casino slots 5")
    text = last_text(client)
    assert "Slots: a | a | a" in text
    assert "Result: win (x10)" in text
    assert "Net: +45 chips" in text
    assert "Balance: 545 chips" in text

    assert_private(client)


def test_blackjack_start_and_hit_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=StackedRng(["10H", "7C", "9D", "8H", "2S"]))

    run(casino, "!casino blackjack 10")
    text = last_text(client)
    assert "Your hand: 10H 9D (19)" in text
    assert "Dealer shows: 7C" in text
    assert "Bet: 10 chips" in text
    assert "Balance: 490 chips" in text
    assert "!casino hit" in text
    assert casino.store.blackjack("uid-1") is not None

    run(casino, "!casino h")
    text = last_text(client)
    assert "Your hand: 10H 9D 2S (21)" in text
    assert "Dealer shows: 7C" in text
    assert "Balance: 490 chips" in text
    assert casino.store.blackjack("uid-1") is not None

    assert_private(client)


def test_blackjack_no_bet_shows_active_hand_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=StackedRng(["10H", "7C", "9D", "8H", "2S"]))

    run(casino, "!casino blackjack 10")
    run(casino, "!casino blackjack")
    text = last_text(client)
    assert "Your hand: 10H 9D (19)" in text
    assert "Dealer shows: 7C" in text
    assert "!casino stand" in text

    assert_private(client)


def test_blackjack_stand_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=StackedRng(["10H", "10D", "9D", "8H"]))

    run(casino, "!casino bj 10")
    run(casino, "!casino s")
    text = last_text(client)
    assert "Your hand: 10H 9D (19)" in text
    assert "Dealer hand: 10D 8H (18)" in text
    assert "Result: win" in text
    assert "Payout: 20 chips" in text
    assert "Net: +10 chips" in text
    assert "Balance: 510 chips" in text
    assert casino.store.blackjack("uid-1") is None

    assert_private(client)


def test_blackjack_natural_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=StackedRng(["AS", "9H", "KH", "7C"]))

    run(casino, "!casino blackjack 10")
    text = last_text(client)
    assert "Result: blackjack" in text
    assert "Your hand: AS KH (21)" in text
    assert "Dealer hand: 9H 7C (16)" in text
    assert "Payout: 25 chips" in text
    assert "Net: +15 chips" in text
    assert "Balance: 515 chips" in text
    assert casino.store.blackjack("uid-1") is None

    assert_private(client)


def test_blackjack_hit_bust_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=StackedRng(["10H", "7C", "9D", "8H", "KS"]))

    run(casino, "!casino blackjack 10")
    run(casino, "!casino hit")
    text = last_text(client)
    assert "Your hand: 10H 9D KS (29)" in text
    assert "Result: bust" in text
    assert "Payout: 0 chips" in text
    assert "Net: -10 chips" in text
    assert "Balance: 490 chips" in text
    assert casino.store.blackjack("uid-1") is None

    assert_private(client)


def test_blackjack_double_flow_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=StackedRng(["5H", "10H", "6D", "7D", "10C"]))

    run(casino, "!casino blackjack 10")
    assert casino.store.balance("uid-1") == 490

    run(casino, "!casino d")
    text = last_text(client)
    assert "Your hand: 5H 6D 10C (21)" in text
    assert "Dealer hand: 10H 7D (17)" in text
    assert "Result: win" in text
    assert "Payout: 40 chips" in text
    assert "Net: +20 chips" in text
    assert "Balance: 520 chips" in text
    assert casino.store.blackjack("uid-1") is None
    assert casino.store.get("uid-1").total_wagered == 20

    assert_private(client)


def test_blackjack_double_rejected_when_balance_low_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(
        tmp_path,
        client,
        starting_balance=15,
        rng=StackedRng(["5H", "10H", "6D", "7D", "10C"]),
    )

    run(casino, "!casino blackjack 10")
    run(casino, "!casino double")
    assert "Not enough balance to double." in last_text(client)
    assert casino.store.balance("uid-1") == 5
    assert casino.store.blackjack("uid-1") is not None

    assert_private(client)


def test_blackjack_actions_without_hand_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client)

    for content in ("!casino hit", "!casino stand", "!casino double"):
        run(casino, content)
        assert last_text(client) == "No active blackjack hand."

    run(casino, "!casino blackjack")
    assert last_text(client) == "Use: !casino blackjack <bet>."

    assert_private(client)


def test_blackjack_second_game_rejected_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=StackedRng(["10H", "7C", "9D", "8H", "2S"]))

    run(casino, "!casino blackjack 10")
    run(casino, "!casino bj 20")
    assert "Finish your current hand" in last_text(client)
    assert casino.store.balance("uid-1") == 490
    assert casino.store.blackjack("uid-1") is not None

    assert_private(client)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("!casino roulette 0 red", "Bet must be between 1 and 10000."),
        ("!casino roulette -5 red", "Bet must be a positive integer."),
        ("!casino roulette abc red", "Bet must be a positive integer."),
        ("!casino roulette 1.5 red", "Bet must be a positive integer."),
        ("!casino slots 20000", "Bet must be between 1 and 10000."),
    ],
)
def test_invalid_bets_reply_privately(tmp_path, content, message):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=FixedRouletteRng(19))

    run(casino, content)

    assert message in last_text(client)
    assert casino.store.balance("uid-1") == 500
    assert casino.store.get("uid-1").games_played == 0
    assert_private(client)


def test_insufficient_balance_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, starting_balance=5, rng=SequenceRng([("cherry", "cherry", "cherry")]))

    run(casino, "!casino slots 10")
    assert "Not enough balance." in last_text(client)
    assert casino.store.balance("uid-1") == 5

    assert_private(client)


def test_unknown_roulette_selection_reply_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=FixedRouletteRng(19))

    run(casino, "!casino roulette 10 banana")
    assert "Unknown roulette selection" in last_text(client)
    assert casino.store.balance("uid-1") == 500

    assert_private(client)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, "Balance: 500 chips"),
        ({"currency_name": "coins"}, "Balance: 500 coins"),
        ({"currency_name": "coins", "currency_symbol": "$"}, "Balance: $500"),
    ],
)
def test_currency_formatting_reply_privately(tmp_path, kwargs, expected):
    client = FakeClient()
    casino = make_casino(tmp_path, client, **kwargs)

    run(casino, "!casino balance")

    assert last_text(client) == expected
    assert_private(client)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_bet": 0},
        {"min_bet": 10, "max_bet": 5},
        {"starting_balance": -1},
        {"daily_reward": -1},
        {"daily_cooldown": -1},
        {"leaderboard_size": 0},
        {"blackjack_payout": 0},
        {"blackjack_decks": 0},
        {"dealer_hits_soft_17": "yes"},
        {"slots_symbols": "ab"},
        {"slots_symbols": ()},
        {"slots_symbols": ("a", "a"), "slots_weights": (1, 1), "slots_payouts": {"a": 1}},
        {"slots_symbols": ("a", "b"), "slots_weights": (1,)},
        {"slots_symbols": ("a", "b"), "slots_weights": (1, 1), "slots_payouts": {"a": 1}},
        {"slots_symbols": ("a", "b"), "slots_weights": (1, 0), "slots_payouts": {"a": 1, "b": 1}},
        {"slots_symbols": ("a", ""), "slots_weights": (1, 1), "slots_payouts": {"a": 1, "": 1}},
        {"slots_weights": (1, 1)},
        {"slots_payouts": {"cherry": -1}},
        {"slots_two_cherry_payout": -1},
    ],
)
def test_config_validation_rejects_nonsense(tmp_path, kwargs):
    with pytest.raises(ConfigurationError):
        Casino(FakeClient(), "casino", data_dir=str(tmp_path / "casino"), **kwargs)


def test_unexpected_failure_replies_privately(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client, rng=FixedRouletteRng(19))

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    casino.store.settle_round = fail

    run(casino, "!casino roulette 10 red")

    assert last_text(client) == "Casino command failed."
    assert_private(client)


def test_reply_send_failure_is_swallowed(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client)

    def fail(*args, **kwargs):
        raise RuntimeError("send failed")

    client.send_private_message = fail

    casino.run(FakeMessage("!casino balance"))


def test_missing_invoker_uid_falls_back_to_user_info(tmp_path):
    client = FakeClient()
    casino = make_casino(tmp_path, client)
    message = FakeMessage("!casino balance", invokeruid=None)
    message.invokeruid = None
    client.user_infos[1] = type("Info", (), {"client_unique_identifier": "resolved-uid"})()

    casino.run(message)

    assert last_text(client) == "Balance: 500 chips"
    assert casino.store.get("resolved-uid") is not None
    assert_private(client)
