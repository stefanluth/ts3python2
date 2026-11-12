from datetime import datetime, timezone

import pytest

from plugins.commands.tracker import DEFAULT_METRIC, TOP_SCOPE, Tracker
from plugins.errors import ConfigurationError
from plugins.time_tracker_store import get_store, reset_stores
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage
from ts3client.user import UserInfo

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clean_stores():
    reset_stores()
    yield
    reset_stores()


def make_tracker(tmp_path, client=None, **kwargs):
    client = client if client is not None else FakeClient()
    tracker = Tracker(client, "tracker", data_dir=str(tmp_path / "time_tracker"), **kwargs)
    tracker.logger = FakeLogger()
    tracker.store.logger = FakeLogger()
    return tracker


def run(tracker, content, **kwargs):
    message = FakeMessage(content, **kwargs)
    tracker.run(message)
    return message


def seed(tmp_path, uid="uid-1", name="Alice", total=3600, idle=600, afk=300):
    store = get_store(str(tmp_path / "time_tracker"))
    store.record_interval(uid, name, elapsed=total, idle_elapsed=idle, afk_elapsed=afk, new_session=True, now=NOW)
    return store


def last_text(client):
    return client.sent[-1][1]


def test_me_is_private_and_shows_stats(tmp_path):
    seed(tmp_path)
    tracker = make_tracker(tmp_path)

    run(tracker, "!tracker me")

    assert tracker.client.sent[0][0] == 1
    text = last_text(tracker.client)
    assert "Time tracking for Alice:" in text
    assert "Total: 1h" in text
    assert "Idle: 10m" in text
    assert "AFK: 5m" in text
    assert "Sessions: 1" in text
    assert "Rank: #1" in text
    assert "Tracking: enabled" in text
    assert "Last seen:" in text


def test_top_is_a_server_message_and_defaults_to_total(tmp_path):
    seed(tmp_path, "uid-alice", "Alice", total=100, idle=10, afk=5)
    seed(tmp_path, "uid-bob", "Bob", total=200, idle=20, afk=1)
    tracker = make_tracker(tmp_path)

    run(tracker, "!tracker top")
    assert tracker.client.server_sent[-1].startswith("Top tracked time (total):")
    total_text = tracker.client.server_sent[-1]
    assert total_text.index("Bob") < total_text.index("Alice")

    run(tracker, "!tracker top idle")
    assert "(idle)" in tracker.client.server_sent[-1]

    run(tracker, "!tracker top afk")
    assert "(afk)" in tracker.client.server_sent[-1]
    assert tracker.client.sent == []


def test_optout_and_optin_change_tracking_state(tmp_path):
    store = seed(tmp_path)
    tracker = make_tracker(tmp_path)

    run(tracker, "!tracker optout")
    assert store.get("uid-1").do_not_track is True
    assert "disabled" in last_text(tracker.client)

    run(tracker, "!tracker top")
    assert tracker.client.server_sent[-1] == "No tracked total time yet."

    run(tracker, "!tracker optin")
    assert store.get("uid-1").do_not_track is False
    assert "enabled" in last_text(tracker.client)


def test_help_aliases_and_unknown_subcommands(tmp_path):
    tracker = make_tracker(tmp_path)

    run(tracker, "!tracker ?")
    assert "Tracker commands:" in last_text(tracker.client)

    run(tracker, "!tracker stats")
    assert last_text(tracker.client) == "No tracking data yet."

    run(tracker, "!tracker unknown")
    assert "Tracker commands:" in last_text(tracker.client)


def test_leaderboard_size_configuration_is_validated(tmp_path):
    for value in (0, -1, True, "10"):
        with pytest.raises(ConfigurationError, match="leaderboard_size"):
            make_tracker(tmp_path, leaderboard_size=value)

    tracker = make_tracker(tmp_path, leaderboard_size=3)
    assert tracker.leaderboard_size == 3
    assert DEFAULT_METRIC == "total"
    assert TOP_SCOPE == "server"


def test_no_data_and_invoker_uid_fallback(tmp_path):
    tracker = make_tracker(tmp_path)

    run(tracker, "!tracker me")
    assert last_text(tracker.client) == "No tracking data yet."

    seed(tmp_path, "fallback-uid", "Fallback", total=60, idle=0, afk=0)
    tracker.client.user_infos[1] = UserInfo(client_unique_identifier="fallback-uid")
    run(tracker, "!tracker me", invokeruid="")

    assert "Time tracking for Fallback:" in last_text(tracker.client)


def test_invoker_uid_falls_back_to_clid_when_user_info_fails(tmp_path):
    seed(tmp_path, "clid:1", "Unknown", total=60, idle=0, afk=0)
    tracker = make_tracker(tmp_path)

    run(tracker, "!tracker me", invokeruid="")

    assert "Time tracking for Unknown:" in last_text(tracker.client)


def test_top_rejects_an_unknown_metric(tmp_path):
    tracker = make_tracker(tmp_path)

    run(tracker, "!tracker top steps")

    assert last_text(tracker.client) == "Unknown metric: steps."


def test_opted_out_profile_is_hidden_from_its_own_rank(tmp_path):
    store = seed(tmp_path)
    store.set_do_not_track("uid-1", True, now=NOW)
    tracker = make_tracker(tmp_path)

    run(tracker, "!tracker me")

    text = last_text(tracker.client)
    assert "Rank: hidden (opted out)" in text
    assert "Tracking: disabled" in text
