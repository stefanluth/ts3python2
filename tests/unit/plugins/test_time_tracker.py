from datetime import datetime, timezone

import pytest

import plugins.plugins.time_tracker as time_tracker_module
from plugins.plugins.time_tracker import TimeTracker
from plugins.time_tracker_store import get_store, reset_stores
from tests.support.fakes import FakeClient, FakeLogger, FakeStopEvent
from ts3client.user import User, UserInfo

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def fixed_context(monkeypatch):
    reset_stores()
    monkeypatch.setattr(time_tracker_module, "utcnow", lambda: NOW)
    monkeypatch.setattr("plugins.plugin.create_logger", lambda *args, **kwargs: FakeLogger())
    yield
    reset_stores()


def make_client(users, user_infos, bot_id=1):
    client = FakeClient()
    client.id = bot_id
    client.users = users
    client.user_infos = user_infos
    return client


def make_plugin(client, stop):
    return TimeTracker(client, stop)


def use_clock(monkeypatch, *values):
    remaining = list(values)

    def monotonic():
        if len(remaining) > 1:
            return remaining.pop(0)
        return remaining[0]

    monkeypatch.setattr(time_tracker_module, "_monotonic", monotonic)


def test_two_samples_accumulate_total_idle_and_afk_time(tmp_path, monkeypatch):
    client = make_client(
        [User(clid=10, client_nickname="Alice", cid=100, client_type=0, client_unique_identifier="uid-1")],
        {10: UserInfo(client_idle_time=330_000)},
    )
    use_clock(monkeypatch, 100.0, 160.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=2))
    data_dir = str(tmp_path / "tracker")

    plugin.run(
        data_dir=data_dir,
        check_interval=60,
        idle_threshold=300,
        afk_channel_ids=[100],
        include_query_clients=False,
    )

    profile = get_store(data_dir).get("uid-1")
    assert profile is not None
    assert profile.total_seconds == 60
    assert profile.idle_seconds == 30
    assert profile.afk_seconds == 60
    assert profile.session_count == 1
    assert profile.last_connected_at == NOW.isoformat()
    assert profile.last_seen_at == NOW.isoformat()


def test_multiple_connections_with_shared_uid_do_not_overwrite_afk_state(tmp_path, monkeypatch):
    client = make_client(
        [
            User(clid=10, client_nickname="Alice Afk", cid=100, client_type=0, client_unique_identifier="shared-uid"),
            User(clid=20, client_nickname="Alice Home", cid=200, client_type=0, client_unique_identifier="shared-uid"),
        ],
        {10: UserInfo(client_idle_time=0), 20: UserInfo(client_idle_time=0)},
    )
    use_clock(monkeypatch, 100.0, 160.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=2))
    data_dir = str(tmp_path / "tracker")

    plugin.run(data_dir=data_dir, check_interval=60, afk_channel_ids=[100])

    profile = get_store(data_dir).get("shared-uid")
    assert profile is not None
    assert profile.total_seconds == 120
    assert profile.afk_seconds == 60
    assert profile.session_count == 2


def test_first_sample_records_a_session_without_crediting_unknown_time(tmp_path, monkeypatch):
    client = make_client(
        [User(clid=10, client_nickname="Alice", cid=100, client_type=0, client_unique_identifier="uid-1")],
        {10: UserInfo(client_idle_time=0)},
    )
    use_clock(monkeypatch, 100.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=1))
    data_dir = str(tmp_path / "tracker")

    plugin.run(data_dir=data_dir, check_interval=60)

    profile = get_store(data_dir).get("uid-1")
    assert profile is not None
    assert profile.total_seconds == 0
    assert profile.session_count == 1


def test_excludes_bot_and_query_clients_by_default(tmp_path, monkeypatch):
    client = make_client(
        [
            User(clid=1, client_nickname="Bot", cid=100, client_type=1, client_unique_identifier="bot"),
            User(clid=2, client_nickname="Query", cid=100, client_type=1, client_unique_identifier="query"),
            User(clid=3, client_nickname="Voice", cid=100, client_type=0, client_unique_identifier="voice"),
        ],
        {1: UserInfo(client_idle_time=0), 2: UserInfo(client_idle_time=0), 3: UserInfo(client_idle_time=0)},
    )
    use_clock(monkeypatch, 100.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=1))
    data_dir = str(tmp_path / "tracker")

    plugin.run(data_dir=data_dir, check_interval=60)

    store = get_store(data_dir)
    assert store.get("bot") is None
    assert store.get("query") is None
    assert store.get("voice") is not None


def test_include_query_clients_tracks_query_clients_but_not_the_bot(tmp_path, monkeypatch):
    client = make_client(
        [
            User(clid=1, client_nickname="Bot", cid=100, client_type=1, client_unique_identifier="bot"),
            User(clid=2, client_nickname="Query", cid=100, client_type=1, client_unique_identifier="query"),
        ],
        {1: UserInfo(client_idle_time=0), 2: UserInfo(client_idle_time=0)},
    )
    use_clock(monkeypatch, 100.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=1))
    data_dir = str(tmp_path / "tracker")

    plugin.run(data_dir=data_dir, check_interval=60, include_query_clients=True)

    store = get_store(data_dir)
    assert store.get("bot") is None
    assert store.get("query") is not None


def test_opt_out_prevents_accumulation(tmp_path, monkeypatch):
    client = make_client(
        [User(clid=10, client_nickname="Alice", cid=100, client_type=0, client_unique_identifier="uid-1")],
        {10: UserInfo(client_idle_time=0)},
    )
    data_dir = str(tmp_path / "tracker")
    store = get_store(data_dir)
    store.get_or_create("uid-1", "Alice", now=NOW)
    store.set_do_not_track("uid-1", True, now=NOW)
    use_clock(monkeypatch, 100.0, 160.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=2))

    plugin.run(data_dir=data_dir, check_interval=60)

    profile = store.get("uid-1")
    assert profile is not None
    assert profile.total_seconds == 0
    assert profile.session_count == 0
    assert profile.do_not_track is True


def test_long_sample_gap_is_capped(tmp_path, monkeypatch):
    client = make_client(
        [User(clid=10, client_nickname="Alice", cid=100, client_type=0, client_unique_identifier="uid-1")],
        {10: UserInfo(client_idle_time=0)},
    )
    use_clock(monkeypatch, 100.0, 1000.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=2))
    data_dir = str(tmp_path / "tracker")

    plugin.run(data_dir=data_dir, check_interval=10)

    profile = get_store(data_dir).get("uid-1")
    assert profile is not None
    assert profile.total_seconds == 30


def test_client_info_failure_still_records_elapsed_total(tmp_path, monkeypatch):
    client = make_client(
        [User(clid=10, client_nickname="Alice", cid=100, client_type=0, client_unique_identifier="uid-1")],
        {},
    )
    use_clock(monkeypatch, 100.0, 160.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=2))
    data_dir = str(tmp_path / "tracker")

    plugin.run(data_dir=data_dir, check_interval=60)

    profile = get_store(data_dir).get("uid-1")
    assert profile is not None
    assert profile.total_seconds == 60
    assert profile.idle_seconds == 0


def test_get_users_failure_is_contained(tmp_path, monkeypatch):
    client = FlakyUsersClient()
    use_clock(monkeypatch, 100.0, 160.0)
    plugin = make_plugin(client, FakeStopEvent(stop_after_waits=2))

    plugin.run(data_dir=str(tmp_path / "tracker"), check_interval=60)

    assert client.calls == 2


def test_stop_event_ends_the_loop(tmp_path, monkeypatch):
    client = make_client([], {})
    use_clock(monkeypatch, 100.0)
    stop = FakeStopEvent(stop_after_waits=1)
    plugin = make_plugin(client, stop)

    plugin.run(data_dir=str(tmp_path / "tracker"), check_interval=60)

    assert stop.stopped is True


class FlakyUsersClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def get_users(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("boom")
        return []
