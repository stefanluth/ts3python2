import pytest

import ts3client.ts3client as ts3client_module
from tests.support.fakes import FakeCommands, FakeLogger, FakeQuery, FakeResponse
from ts3client import TS3Client
from ts3client.constants import TargetMode
from ts3client.user import User


def make_client(commands=None):
    client = object.__new__(TS3Client)
    client.query = FakeQuery(commands)
    client.logger = FakeLogger()
    return client


def test_get_users_returns_users():
    commands = FakeCommands()
    commands.responses["clientlist"] = FakeResponse(
        data={0: {"clid": 1, "client_nickname": "a"}, 1: {"clid": 2, "client_nickname": "b"}}
    )
    client = make_client(commands)

    users = client.get_users()

    assert [user.clid for user in users] == [1, 2]
    assert all(isinstance(user, User) for user in users)


def test_find_users_returns_empty_list_when_no_match():
    commands = FakeCommands()
    commands.responses["clientfind"] = FakeResponse(error_id=512, msg="invalid clientID")
    client = make_client(commands)

    assert client.find_users("missing") == []


def test_find_channel_returns_empty_list_when_no_match():
    commands = FakeCommands()
    commands.responses["channelfind"] = FakeResponse(error_id=768, msg="invalid channelID")
    client = make_client(commands)

    assert client.find_channel("missing") == []


def test_init_does_not_register_events(monkeypatch):
    query = FakeQuery()
    monkeypatch.setattr(ts3client_module, "TS3Query", lambda *args, **kwargs: query)

    TS3Client("host", 1, "user", "pass", logger=FakeLogger())

    assert query.polling is False
    assert query.commands.called("servernotifyregister") == []
    assert query.login_calls == []


def test_init_passes_credentials_and_ssh_options_to_query(monkeypatch):
    query = FakeQuery()
    captured = {}

    def fake_query(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return query

    monkeypatch.setattr(ts3client_module, "TS3Query", fake_query)

    TS3Client(
        "host",
        10022,
        "user",
        "pass",
        timeout=3,
        logger=FakeLogger(),
        known_hosts="/tmp/known_hosts",
        accept_all_keys=True,
        use_system_host_keys=False,
    )

    assert captured["args"] == ("host", 10022)
    assert captured["kwargs"] == {
        "login": "user",
        "password": "pass",
        "timeout": 3,
        "known_hosts": "/tmp/known_hosts",
        "accept_all_keys": True,
        "use_system_host_keys": False,
    }
    assert query.login_calls == []


def test_init_without_credentials_does_not_connect(monkeypatch):
    constructed = []

    def fake_query(*args, **kwargs):
        constructed.append((args, kwargs))
        return FakeQuery()

    monkeypatch.setattr(ts3client_module, "TS3Query", fake_query)

    client = TS3Client("host", 10022, logger=FakeLogger())

    assert constructed == []
    assert client._query is None


def test_init_without_host_or_port_does_not_connect(monkeypatch):
    constructed = []

    def fake_query(*args, **kwargs):
        constructed.append((args, kwargs))
        return FakeQuery()

    monkeypatch.setattr(ts3client_module, "TS3Query", fake_query)

    client = TS3Client(None, None, "user", "pass", logger=FakeLogger())

    assert constructed == []
    assert client._query is None


def test_send_private_message_targets_a_client():
    commands = FakeCommands()
    client = make_client(commands)

    client.send_private_message(7, "hi")

    assert commands.called("sendtextmessage") == [
        ("sendtextmessage", (), {"targetmode": TargetMode.CLIENT, "target": 7, "msg": "hi"})
    ]


@pytest.mark.parametrize(
    "method, target_mode",
    [("send_server_message", TargetMode.SERVER), ("send_channel_message", TargetMode.CHANNEL)],
)
def test_broadcast_messages_use_the_right_target_mode(method, target_mode):
    commands = FakeCommands()
    client = make_client(commands)

    getattr(client, method)("hi")

    assert commands.called("sendtextmessage") == [
        ("sendtextmessage", (), {"targetmode": target_mode, "target": 0, "msg": "hi"})
    ]


def test_set_name_returns_none_when_name_is_unchanged():
    commands = FakeCommands()
    commands.responses["whoami"] = FakeResponse(data={0: {"client_nickname": "same"}})
    client = make_client(commands)

    assert client.set_name("same") is None
    assert commands.called("clientupdate") == []


def test_set_name_updates_a_changed_nickname():
    commands = FakeCommands()
    commands.responses["whoami"] = FakeResponse(data={0: {"client_nickname": "old"}})
    client = make_client(commands)

    client.set_name("new")

    assert commands.called("clientupdate") == [("clientupdate", (), {"client_nickname": "new"})]


def test_disconnect_is_idempotent():
    client = make_client()
    query = client.query

    client.disconnect()
    assert query.exit_calls == 1
    assert client._query is None

    client.disconnect()
    assert query.exit_calls == 1


@pytest.mark.parametrize("method", ["disable_message_events", "disable_server_events", "disable_channel_events"])
def test_disable_events_does_not_pass_event(method):
    commands = FakeCommands()
    client = make_client(commands)

    getattr(client, method)()

    for call in commands.called("servernotifyunregister"):
        assert call[2] == {}
