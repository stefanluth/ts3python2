from datetime import datetime, timezone

import pytest

import config
import plugins.casino_store as casino_store_module
import plugins.commands.casino as casino_module
from plugins.casino_games import BlackjackSession, RouletteResult, SlotsResult
from plugins.plugins.command_handler import CommandHandler
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage, FakeStopEvent

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


def fixed_spin_roulette(bet, selection, rng=None):
    return RouletteResult(
        number=19,
        color="red",
        selection=selection,
        won=True,
        payout=bet * 2,
        label=selection.label,
    )


def fixed_spin_slots(bet, config, rng=None):
    reels = ("cherry", "cherry", "cherry")
    return SlotsResult(reels=reels, multiplier=4, payout=bet * 4, label=" | ".join(reels))


def fixed_start_blackjack(bet, decks=1, dealer_hits_soft_17=False, blackjack_payout=1.5, rng=None):
    return BlackjackSession(
        deck=["2S", "KS"],
        player=["10H", "9D"],
        dealer=["7C", "8H"],
        bet=bet,
    )


@pytest.fixture(autouse=True)
def deterministic_casino(monkeypatch):
    monkeypatch.setattr(casino_store_module, "utcnow", lambda: NOW)
    monkeypatch.setattr(casino_module, "spin_roulette", fixed_spin_roulette)
    monkeypatch.setattr(casino_module, "spin_slots", fixed_spin_slots)
    monkeypatch.setattr(casino_module, "start_blackjack", fixed_start_blackjack)


def make_config(data_dir):
    casino = dict(config.PLUGINS_CONFIG["CommandHandler"]["commands"]["Casino"])
    casino["data_dir"] = str(data_dir)
    return {"Casino": casino}


def run_batches(client, batches, data_dir):
    client.message_batches = list(batches)
    handler = CommandHandler(client, FakeStopEvent(stop_after_waits=len(batches)))
    handler.logger = FakeLogger()
    handler.run(prefix="!", commands=make_config(data_dir), check_interval=0)
    return handler


def test_casino_lifecycle_through_command_handler(tmp_path):
    client = FakeClient()
    batches = [
        [FakeMessage("!casino balance")],
        [FakeMessage("!casino daily")],
        [FakeMessage("!casino roulette 10 red")],
        [FakeMessage("!casino slots 10")],
        [FakeMessage("!casino blackjack 10")],
        [FakeMessage("!casino hit")],
        [FakeMessage("!casino leaderboard")],
    ]

    handler = run_batches(client, batches, tmp_path / "casino")

    assert "message" in client.enabled
    assert all(target == 1 for target, _ in client.sent)
    assert client.server_sent == []
    assert client.channel_sent == []
    assert client.messages_sent == []

    texts = [text for _, text in client.sent]
    assert len(texts) == 7
    assert texts[0] == "Balance: 500 chips"
    assert "Daily reward: 100 chips" in texts[1]
    assert "Balance: 600 chips" in texts[1]
    assert "Result: win" in texts[2]
    assert "Balance: 610 chips" in texts[2]
    assert "Result: win (x4)" in texts[3]
    assert "Balance: 640 chips" in texts[3]
    assert "Blackjack:" in texts[4]
    assert "Your hand:" in texts[4]
    assert "Balance: 630 chips" in texts[4]
    assert "Result: bust" in texts[5]
    assert "Balance: 630 chips" in texts[5]
    assert "Leaderboard:" in texts[6]
    assert "user" in texts[6]
    assert handler.commands[0].store.blackjack("uid-1") is None


def test_casino_restart_persists_balance_and_active_hand(tmp_path):
    data_dir = tmp_path / "casino"
    first_client = FakeClient()
    first_batches = [
        [FakeMessage("!casino daily")],
        [FakeMessage("!casino roulette 10 red")],
        [FakeMessage("!casino blackjack 10")],
    ]
    run_batches(first_client, first_batches, data_dir)

    second_client = FakeClient()
    second_batches = [
        [FakeMessage("!casino balance")],
        [FakeMessage("!casino blackjack")],
    ]
    handler = run_batches(second_client, second_batches, data_dir)

    assert "message" in second_client.enabled
    assert all(target == 1 for target, _ in second_client.sent)
    assert second_client.server_sent == []
    assert second_client.channel_sent == []
    assert second_client.messages_sent == []

    texts = [text for _, text in second_client.sent]
    assert len(texts) == 2
    assert texts[0] == "Balance: 600 chips"
    assert "Blackjack:" in texts[1]
    assert "Your hand:" in texts[1]
    assert "Balance: 600 chips" in texts[1]

    casino_command = handler.commands[0]
    assert casino_command.store.blackjack("uid-1") is not None
    assert casino_command.store.balance("uid-1") == 600
