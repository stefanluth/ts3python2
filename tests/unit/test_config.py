import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.py"
CONFIG_ENV = (
    "TS3_SERVER_PORT",
    "TS3_QUERY_PORT",
    "TS3_QUERY_LOGIN",
    "TS3_QUERY_PASSWORD",
    "TS3_SSH_KNOWN_HOSTS",
    "TS3_SSH_ACCEPT_ALL_KEYS",
    "TS3_SSH_USE_SYSTEM_KEYS",
)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, (None, False, True)),
        (
            {
                "TS3_SSH_KNOWN_HOSTS": "/tmp/known_hosts",
                "TS3_SSH_ACCEPT_ALL_KEYS": "true",
                "TS3_SSH_USE_SYSTEM_KEYS": "false",
            },
            ("/tmp/known_hosts", True, False),
        ),
        ({"TS3_SSH_ACCEPT_ALL_KEYS": "", "TS3_SSH_USE_SYSTEM_KEYS": ""}, (None, False, False)),
    ],
    ids=["defaults", "environment", "empty-strings"],
)
def test_ssh_settings_from_environment(monkeypatch, env, expected):
    config = load_config(monkeypatch, **env)

    actual = (config.TS3_SSH_KNOWN_HOSTS, config.TS3_SSH_ACCEPT_ALL_KEYS, config.TS3_SSH_USE_SYSTEM_KEYS)
    assert actual == expected


def test_poll_command_config(monkeypatch):
    config = load_config(monkeypatch)

    poll = config.PLUGINS_CONFIG["CommandHandler"]["commands"]["Poll"]

    assert poll["trigger"] == "poll"
    assert poll["polls_dir"] == "polls"
    assert poll["notify_users"] is True
    assert poll["notify_query_clients"] is False
    assert set(poll) == {
        "trigger",
        "description",
        "polls_dir",
        "max_options",
        "max_question_length",
        "default_duration",
        "notify_users",
        "notify_query_clients",
        "prefix",
    }


def test_casino_command_config(monkeypatch):
    config = load_config(monkeypatch)

    casino = config.PLUGINS_CONFIG["CommandHandler"]["commands"]["Casino"]

    assert casino["trigger"] == "casino"
    assert casino["data_dir"] == "casino"
    assert casino["starting_balance"] == 500
    assert casino["daily_reward"] == 100
    assert casino["min_bet"] == 1
    assert casino["max_bet"] == 10000
    assert casino["blackjack_payout"] == 1.5
    assert set(casino) == {
        "trigger",
        "description",
        "data_dir",
        "currency_name",
        "currency_symbol",
        "starting_balance",
        "daily_reward",
        "daily_cooldown",
        "min_bet",
        "max_bet",
        "leaderboard_size",
        "blackjack_payout",
        "blackjack_decks",
        "dealer_hits_soft_17",
        "slots_symbols",
        "slots_weights",
        "slots_payouts",
        "slots_two_cherry_payout",
    }


def test_time_tracker_plugin_config(monkeypatch):
    config = load_config(monkeypatch)

    tracker = config.PLUGINS_CONFIG["TimeTracker"]

    assert tracker["data_dir"] == "time_tracker"
    assert tracker["check_interval"] == 60
    assert tracker["idle_threshold"] == 900
    assert tracker["afk_channel_ids"] == []
    assert tracker["include_query_clients"] is False
    assert set(tracker) == {
        "data_dir",
        "check_interval",
        "idle_threshold",
        "afk_channel_ids",
        "include_query_clients",
    }


def test_tracker_command_config(monkeypatch):
    config = load_config(monkeypatch)

    tracker = config.PLUGINS_CONFIG["CommandHandler"]["commands"]["Tracker"]

    assert tracker["trigger"] == "tracker"
    assert tracker["data_dir"] == "time_tracker"
    assert tracker["leaderboard_size"] == 10
    assert "top_scope" not in tracker
    assert "default_metric" not in tracker
    assert set(tracker) == {
        "trigger",
        "description",
        "data_dir",
        "leaderboard_size",
    }


def load_config(monkeypatch, **env):
    for name in CONFIG_ENV:
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    monkeypatch.setattr("dotenv.load_dotenv", lambda: None)

    spec = importlib.util.spec_from_file_location("config_under_test", CONFIG_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
