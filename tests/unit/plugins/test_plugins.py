from plugins.plugins.afk_mover import AFK_Mover
from plugins.plugins.welcomer import Welcomer
from tests.support.fakes import FakeClient, FakeLogger, FakeStopEvent
from ts3client.event import ClientEnterViewEvent
from ts3client.user import User, UserInfo


def make_plugin(plugin_type, monkeypatch, client, stop):
    monkeypatch.setattr("plugins.plugin.create_logger", lambda *args, **kwargs: FakeLogger())
    return plugin_type(client, stop)


def test_afk_mover_only_moves_clients_over_the_idle_threshold(monkeypatch):
    client = FakeClient()
    client.users = [
        User(clid=1, client_nickname="afk", cid=10),
        User(clid=2, client_nickname="ignored", cid=20),
        User(clid=3, client_nickname="below", cid=30),
        User(clid=4, client_nickname="equal", cid=40),
        User(clid=5, client_nickname="over", cid=50),
    ]
    client.user_infos = {
        1: UserInfo(client_idle_time=90000),
        2: UserInfo(client_idle_time=90000),
        3: UserInfo(client_idle_time=59999),
        4: UserInfo(client_idle_time=60000),
        5: UserInfo(client_idle_time=60001),
    }
    plugin = make_plugin(AFK_Mover, monkeypatch, client, FakeStopEvent(stop_after_waits=1))

    plugin.run(afk_channel_id=10, afk_time=60, check_interval=0, ignore_channels=[20], move_message="go away")

    assert client.moves == [(5, 10)]
    assert client.sent == [(5, "go away")]


class FlakyUsersClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def get_users(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("boom")
        return []


def test_afk_mover_survives_a_failed_check(monkeypatch):
    client = FlakyUsersClient()
    plugin = make_plugin(AFK_Mover, monkeypatch, client, FakeStopEvent(stop_after_waits=2))

    plugin.run(afk_channel_id=10, afk_time=1, check_interval=0)

    assert client.calls == 2


def test_welcomer_skips_query_clients_and_incomplete_events(monkeypatch):
    client = FakeClient()
    query_client = ClientEnterViewEvent(client_type=1, clid=1)
    missing_clid = ClientEnterViewEvent(client_type=0, clid=None)
    voice_client = ClientEnterViewEvent(client_type=0, clid=2, client_nickname="voice")
    client.events = [query_client, missing_clid, voice_client]
    plugin = make_plugin(Welcomer, monkeypatch, client, FakeStopEvent(stop_after_waits=1))

    plugin.run(messages=["hello"])

    assert client.enabled == ["events_and_messages"]
    assert client.sent == [(2, "hello")]
    assert all(event.used for event in client.events)


class FlakyEventsClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.calls = 0

    def get_user_entered_events(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("boom")
        return []


def test_welcomer_survives_a_failed_check(monkeypatch):
    client = FlakyEventsClient()
    plugin = make_plugin(Welcomer, monkeypatch, client, FakeStopEvent(stop_after_waits=2))

    plugin.run(messages=["hello"])

    assert client.calls == 2
