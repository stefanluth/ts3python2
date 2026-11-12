from datetime import datetime, timezone

import pytest

import plugins.plugins.time_tracker as time_tracker_module
from plugins.commands.tracker import Tracker
from plugins.plugins.time_tracker import TimeTracker
from plugins.time_tracker_store import get_store, reset_stores
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage, FakeStopEvent
from ts3client.user import User, UserInfo

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clean_context(monkeypatch):
    reset_stores()
    monkeypatch.setattr(time_tracker_module, "utcnow", lambda: NOW)
    monkeypatch.setattr("plugins.plugin.create_logger", lambda *args, **kwargs: FakeLogger())
    monkeypatch.setattr("plugins.command.create_logger", lambda *args, **kwargs: FakeLogger())
    yield
    reset_stores()


def make_client():
    client = FakeClient()
    client.id = 1
    client.users = [User(clid=10, client_nickname="Alice", cid=100, client_type=0, client_unique_identifier="uid-1")]
    client.user_infos = {10: UserInfo(client_idle_time=0, client_unique_identifier="uid-1")}
    return client


def use_clock(monkeypatch, *values):
    remaining = list(values)

    def monotonic():
        if len(remaining) > 1:
            return remaining.pop(0)
        return remaining[0]

    monkeypatch.setattr(time_tracker_module, "_monotonic", monotonic)


def make_tracker(client, data_dir):
    tracker = Tracker(client, "tracker", data_dir=data_dir)
    tracker.logger = FakeLogger()
    tracker.store.logger = FakeLogger()
    return tracker


def test_plugin_sample_is_visible_to_command_via_shared_store(tmp_path, monkeypatch):
    client = make_client()
    data_dir = str(tmp_path / "time_tracker")
    use_clock(monkeypatch, 100.0, 160.0)
    plugin = TimeTracker(client, FakeStopEvent(stop_after_waits=2))

    plugin.run(data_dir=data_dir, check_interval=60)

    tracker = make_tracker(client, data_dir)
    tracker.run(FakeMessage("!tracker me", invokeruid="uid-1"))

    assert client.sent[-1][1].find("Total: 1m") >= 0
    assert get_store(data_dir).get("uid-1").total_seconds == 60


def test_command_optout_prevents_subsequent_plugin_samples(tmp_path, monkeypatch):
    client = make_client()
    data_dir = str(tmp_path / "time_tracker")
    tracker = make_tracker(client, data_dir)
    tracker.run(FakeMessage("!tracker optout", invokeruid="uid-1"))

    use_clock(monkeypatch, 100.0, 160.0)
    plugin = TimeTracker(client, FakeStopEvent(stop_after_waits=2))
    plugin.run(data_dir=data_dir, check_interval=60)

    profile = get_store(data_dir).get("uid-1")
    assert profile is not None
    assert profile.do_not_track is True
    assert profile.total_seconds == 0
    assert profile.session_count == 0


def test_command_optin_resumes_later_plugin_samples(tmp_path, monkeypatch):
    client = make_client()
    data_dir = str(tmp_path / "time_tracker")
    tracker = make_tracker(client, data_dir)
    tracker.run(FakeMessage("!tracker optout", invokeruid="uid-1"))
    tracker.run(FakeMessage("!tracker optin", invokeruid="uid-1"))

    use_clock(monkeypatch, 100.0, 160.0)
    plugin = TimeTracker(client, FakeStopEvent(stop_after_waits=2))
    plugin.run(data_dir=data_dir, check_interval=60)

    profile = get_store(data_dir).get("uid-1")
    assert profile is not None
    assert profile.do_not_track is False
    assert profile.total_seconds == 60
