import hashlib
import json
import time

import pytest

from plugins.casino_store import CasinoStore
from tests.support.integration import (
    drain_messages,
    enable_text_receive,
    running_plugins,
    wait_for_message,
    wait_until,
    whoami,
)
from ts3client.constants import NotifyRegisterType, TargetMode

pytestmark = pytest.mark.integration

CASINO_REPLY_MARKERS = (
    "Casino commands:",
    "Balance:",
    "Daily reward:",
    "Profile:",
    "Leaderboard:",
    "Roulette:",
    "Slots:",
    "Blackjack",
    "Use: !casino",
    "Bet must be",
    "Not enough balance",
    "No active blackjack hand",
)


def casino_config(data_dir, **overrides):
    casino = {
        "trigger": "casino",
        "description": "Casino",
        "data_dir": str(data_dir),
        "currency_name": "chips",
        "currency_symbol": "",
        "starting_balance": 500,
        "daily_reward": 100,
        "daily_cooldown": 86400,
        "min_bet": 1,
        "max_bet": 10000,
        "leaderboard_size": 10,
        "blackjack_payout": 1.5,
        "blackjack_decks": 1,
        "dealer_hits_soft_17": False,
        "slots_symbols": ["cherry", "lemon", "bell", "bar", "seven"],
        "slots_weights": [30, 25, 20, 15, 10],
        "slots_payouts": {"cherry": 4, "lemon": 5, "bell": 10, "bar": 20, "seven": 50},
        "slots_two_cherry_payout": 2,
    }
    casino.update(overrides)
    return {"prefix": "!", "check_interval": 0.2, "commands": {"Casino": casino}}


def player_file(data_dir, uid):
    digest = hashlib.sha256(uid.encode("utf-8")).hexdigest()
    return data_dir / "players" / f"{digest}.json"


def send_text(query, text):
    query.commands.sendtextmessage(targetmode=TargetMode.SERVER, target=0, msg=text)


def wait_for_casino_ready(query, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        send_text(query, "!casino help")
        try:
            return wait_for_message(query, "Casino commands:", contains=True, timeout=0.5)
        except AssertionError:
            continue
    raise AssertionError("bot did not become ready to receive casino commands")


def wait_for_private(query, text, timeout=20):
    def find():
        return next(
            (
                message
                for message in query.unread_messages
                if message.source == TargetMode.CLIENT and text in message.content
            ),
            None,
        )

    message = wait_until(find, timeout=timeout, message=f"did not receive a private message containing {text!r}")
    message.mark_as_used()
    return message


def wait_for_private_any(query, texts, timeout=20):
    def find():
        return next(
            (
                message
                for message in query.unread_messages
                if message.source == TargetMode.CLIENT and any(text in message.content for text in texts)
            ),
            None,
        )

    message = wait_until(
        find,
        timeout=timeout,
        message=f"did not receive a private message containing any of {texts!r}",
    )
    message.mark_as_used()
    return message


def assert_no_server_replies(query):
    replies = [
        message
        for message in query.unread_messages
        if message.source == TargetMode.SERVER and any(marker in message.content for marker in CASINO_REPLY_MARKERS)
    ]
    assert replies == [], [message.content for message in replies]


def balance_line(message):
    for line in message.content.splitlines():
        if line.startswith("Balance: "):
            return line
    raise AssertionError(f"reply did not contain a balance line: {message.content!r}")


def assert_daily_cooldown(message):
    assert "Daily reward is not ready yet" in message.content
    assert "Try again in" in message.content


def test_casino_lifecycle(server, fresh_client, fresh_query, tmp_path):
    enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
    enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_SERVER)
    drain_messages(fresh_query)
    data_dir = tmp_path / "casino"
    config = {"CommandHandler": casino_config(data_dir)}

    with running_plugins(fresh_client, config):
        wait_for_casino_ready(fresh_query)
        drain_messages(fresh_query)
        identity = whoami(fresh_query)
        uid = identity["client_unique_identifier"]
        name = identity["client_nickname"]

        send_text(fresh_query, "!casino balance")
        balance = wait_for_private(fresh_query, "Balance: 500 chips")
        assert "Balance: 500 chips" in balance.content

        send_text(fresh_query, "!casino daily")
        daily = wait_for_private(fresh_query, "Daily reward: 100 chips")
        assert "Balance: 600 chips" in daily.content

        send_text(fresh_query, "!casino daily")
        cooldown = wait_for_private(fresh_query, "Try again in")
        assert_daily_cooldown(cooldown)

        send_text(fresh_query, "!casino balance")
        assert "Balance: 600 chips" in wait_for_private(fresh_query, "Balance: 600 chips").content

        send_text(fresh_query, "!casino leaderboard")
        leaderboard = wait_for_private(fresh_query, "Leaderboard:")
        assert name in leaderboard.content
        assert "600 chips" in leaderboard.content

        send_text(fresh_query, "!casino roulette 10 red")
        roulette = wait_for_private(fresh_query, "Roulette:")
        assert "Balance:" in roulette.content

        send_text(fresh_query, "!casino slots 10")
        slots = wait_for_private(fresh_query, "Slots:")
        assert "Balance:" in slots.content

        send_text(fresh_query, "!casino blackjack 10")
        blackjack = wait_for_private_any(fresh_query, ("Blackjack:", "Blackjack result:"))
        assert "Your hand:" in blackjack.content
        if "Blackjack result:" not in blackjack.content:
            send_text(fresh_query, "!casino hit")
            hit_reply = wait_for_private_any(fresh_query, ("Blackjack result:", "Blackjack:"))
            assert "Your hand:" in hit_reply.content
            if "Blackjack result:" not in hit_reply.content:
                send_text(fresh_query, "!casino stand")
                result = wait_for_private(fresh_query, "Blackjack result:")
                assert "Your hand:" in result.content

        assert_no_server_replies(fresh_query)

    data = json.loads(player_file(data_dir, uid).read_text())
    assert data["schema_version"] == 1
    assert data["uid"] == uid
    assert data["balance"] == data["ledger_total"]
    assert data["games_played"] == 3
    assert data["wins"] + data["losses"] + data["pushes"] == data["games_played"]
    reasons = {entry["reason"] for entry in data["transactions"]}
    assert {
        "daily",
        "roulette wager",
        "roulette payout",
        "slots wager",
        "slots payout",
        "blackjack wager",
        "blackjack payout",
    } <= reasons
    assert data["blackjack"] is None


def test_casino_leaderboard_includes_persisted_players(server, fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "casino"
    seeded_uid = "seeded-casino-player"
    seeded_name = "Seeded Player"
    seeded = CasinoStore(data_dir)
    seeded.get_or_create(seeded_uid, seeded_name)
    seeded.claim_daily(seeded_uid)

    enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
    drain_messages(fresh_query)
    config = {"CommandHandler": casino_config(data_dir)}

    with running_plugins(fresh_client, config):
        wait_for_casino_ready(fresh_query)
        drain_messages(fresh_query)
        identity = whoami(fresh_query)
        live_uid = identity["client_unique_identifier"]
        live_name = identity["client_nickname"]

        send_text(fresh_query, "!casino balance")
        assert "Balance: 500 chips" in wait_for_private(fresh_query, "Balance: 500 chips").content

        send_text(fresh_query, "!casino leaderboard")
        leaderboard = wait_for_private(fresh_query, "Leaderboard:")
        lines = leaderboard.content.splitlines()
        assert any(line.startswith("1. ") and seeded_name in line and "600 chips" in line for line in lines)
        assert any(line.startswith("2. ") and live_name in line and "500 chips" in line for line in lines)

    live_data = json.loads(player_file(data_dir, live_uid).read_text())
    seeded_data = json.loads(player_file(data_dir, seeded_uid).read_text())
    assert live_data["balance"] == 500
    assert seeded_data["balance"] == 600


def test_casino_rejects_invalid_actions_without_balance_change(server, fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "casino"
    enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
    drain_messages(fresh_query)
    config = {"CommandHandler": casino_config(data_dir)}

    with running_plugins(fresh_client, config):
        wait_for_casino_ready(fresh_query)
        drain_messages(fresh_query)
        uid = whoami(fresh_query)["client_unique_identifier"]

        send_text(fresh_query, "!casino balance")
        assert "Balance: 500 chips" in wait_for_private(fresh_query, "Balance: 500 chips").content

        cases = (
            ("!casino roulette 0 red", "Bet must be between 1 and 10000."),
            ("!casino roulette 10 banana", "Unknown roulette selection"),
            ("!casino slots 10001", "Bet must be between 1 and 10000."),
            ("!casino slots 10000", "Not enough balance."),
            ("!casino hit", "No active blackjack hand."),
            ("!casino blackjack 0", "Bet must be between 1 and 10000."),
            ("!casino leaderboard 0", "Leaderboard count must be a positive integer."),
        )
        for command, expected in cases:
            send_text(fresh_query, command)
            reply = wait_for_private(fresh_query, expected)
            assert expected in reply.content

        send_text(fresh_query, "!casino balance")
        assert "Balance: 500 chips" in wait_for_private(fresh_query, "Balance: 500 chips").content

    data = json.loads(player_file(data_dir, uid).read_text())
    assert data["balance"] == 500
    assert data["ledger_total"] == 500
    assert data["games_played"] == 0
    assert data["blackjack"] is None
    assert [entry["reason"] for entry in data["transactions"]] == ["starting_balance"]


def test_casino_survives_plugin_restart(server, fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "casino"
    enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
    drain_messages(fresh_query)
    config = {"CommandHandler": casino_config(data_dir)}

    with running_plugins(fresh_client, config):
        wait_for_casino_ready(fresh_query)
        drain_messages(fresh_query)
        identity = whoami(fresh_query)
        uid = identity["client_unique_identifier"]
        name = identity["client_nickname"]

        send_text(fresh_query, "!casino daily")
        wait_for_private(fresh_query, "Daily reward: 100 chips")

        send_text(fresh_query, "!casino blackjack 10")
        blackjack = wait_for_private_any(fresh_query, ("Blackjack:", "Blackjack result:"))
        captured_balance = balance_line(blackjack)
        hand_active = "Blackjack result:" not in blackjack.content

    first_data = json.loads(player_file(data_dir, uid).read_text())
    assert first_data["balance"] == first_data["ledger_total"]
    assert f"Balance: {first_data['balance']:,} chips" == captured_balance
    if hand_active:
        assert first_data["blackjack"] is not None
    else:
        assert first_data["blackjack"] is None

    with running_plugins(fresh_client, config):
        wait_for_casino_ready(fresh_query)
        drain_messages(fresh_query)

        send_text(fresh_query, "!casino daily")
        cooldown = wait_for_private(fresh_query, "Try again in")
        assert_daily_cooldown(cooldown)

        send_text(fresh_query, "!casino balance")
        assert balance_line(wait_for_private(fresh_query, "Balance:")) == captured_balance

        send_text(fresh_query, "!casino leaderboard")
        leaderboard = wait_for_private(fresh_query, "Leaderboard:")
        assert name in leaderboard.content

        if hand_active:
            send_text(fresh_query, "!casino blackjack")
            resumed = wait_for_private(fresh_query, "Blackjack:")
            assert "Your hand:" in resumed.content
            send_text(fresh_query, "!casino stand")
            result = wait_for_private(fresh_query, "Blackjack result:")
            assert "Your hand:" in result.content
        else:
            usage = wait_for_private(fresh_query, "Use: !casino blackjack <bet>.")
            assert "Blackjack result:" not in usage.content

    final_data = json.loads(player_file(data_dir, uid).read_text())
    assert final_data["balance"] == final_data["ledger_total"]
    assert final_data["blackjack"] is None


def test_casino_custom_config(server, fresh_client, fresh_query, tmp_path):
    data_dir = tmp_path / "casino"
    enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
    drain_messages(fresh_query)
    config = {
        "CommandHandler": casino_config(
            data_dir,
            currency_symbol="$",
            starting_balance=25,
            daily_reward=5,
            slots_symbols=["a", "b"],
            slots_weights=[1, 1],
            slots_payouts={"a": 10, "b": 0},
            slots_two_cherry_payout=1,
        )
    }

    with running_plugins(fresh_client, config):
        wait_for_casino_ready(fresh_query)
        drain_messages(fresh_query)

        send_text(fresh_query, "!casino balance")
        assert "Balance: $25" in wait_for_private(fresh_query, "Balance: $25").content

        send_text(fresh_query, "!casino daily")
        daily = wait_for_private(fresh_query, "Daily reward: $5")
        assert "Balance: $30" in daily.content

        send_text(fresh_query, "!casino slots 1")
        slots = wait_for_private(fresh_query, "Slots:")
        assert "Balance: $" in slots.content
