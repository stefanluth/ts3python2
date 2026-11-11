from typing import cast

import pytest

import ts3client.ts3client as ts3client_module
from tests.support.fakes import FakeCommands, FakeLogger, FakeQuery, FakeResponse
from ts3client import TS3Client
from ts3client.constants import NotifyRegisterType, TargetMode
from ts3client.event import ClientEnterViewEvent, Event
from ts3client.ts3query import TS3Query
from ts3client.user import User


def test_get_users_returns_users():
    commands = FakeCommands()
    commands.responses["clientlist"] = FakeResponse(
        data={0: {"clid": 1, "client_nickname": "a"}, 1: {"clid": 2, "client_nickname": "b"}}
    )
    client = make_client(commands)

    users = client.get_users()

    assert [user.clid for user in users] == [1, 2]
    assert all(isinstance(user, User) for user in users)


@pytest.mark.parametrize(
    ("method", "command", "error_id"),
    [
        ("find_users", "clientfind", 512),
        ("find_channel", "channelfind", 768),
    ],
)
def test_find_returns_empty_list_when_no_match(method, command, error_id):
    commands = FakeCommands()
    commands.responses[command] = FakeResponse(error_id=error_id, msg="not found")
    client = make_client(commands)

    assert getattr(client, method)("missing") == []


def test_init_connects_only_with_complete_credentials(monkeypatch):
    query = FakeQuery()
    constructed = []

    def fake_query(*args, **kwargs):
        constructed.append((args, kwargs))
        return query

    monkeypatch.setattr(ts3client_module, "TS3Query", fake_query)

    TS3Client("host", 10022, logger=FakeLogger())
    TS3Client(None, None, "user", "pass", logger=FakeLogger())

    assert constructed == []

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

    assert constructed == [
        (
            ("host", 10022),
            {
                "login": "user",
                "password": "pass",
                "timeout": 3,
                "known_hosts": "/tmp/known_hosts",
                "accept_all_keys": True,
                "use_system_host_keys": False,
            },
        )
    ]


@pytest.mark.parametrize(
    ("method", "args", "target_mode", "target"),
    [
        ("send_private_message", (7, "hi"), TargetMode.CLIENT, 7),
        ("send_server_message", ("hi",), TargetMode.SERVER, 0),
        ("send_channel_message", ("hi",), TargetMode.CHANNEL, 0),
    ],
)
def test_send_messages_use_the_right_target_mode(method, args, target_mode, target):
    commands = FakeCommands()
    client = make_client(commands)

    getattr(client, method)(*args)

    assert commands.called("sendtextmessage") == [
        ("sendtextmessage", (), {"targetmode": target_mode, "target": target, "msg": "hi"})
    ]


def test_disconnect_is_idempotent():
    client = make_client()
    query = client.query

    client.disconnect()
    assert query.exit_calls == 1
    assert client._query is None

    with pytest.raises(ConnectionError):
        _ = client.query

    client.disconnect()
    assert query.exit_calls == 1


def test_rename_user_only_allows_the_connected_client():
    commands = FakeCommands()
    commands.responses["whoami"] = FakeResponse(data={0: {"client_id": 7}})
    client = make_client(commands)

    with pytest.raises(NotImplementedError):
        client.rename_user(8, "someone else")
    assert commands.called("clientupdate") == []

    client.rename_user(7, "new name")

    assert commands.called("clientupdate") == [("clientupdate", (), {"client_nickname": "new name"})]


def test_user_entered_events_are_filtered_and_unread():
    client = make_client()
    used_event = ClientEnterViewEvent(clid=1)
    used_event.used = True
    unread_event = ClientEnterViewEvent(clid=2)
    other_event = Event()
    client.query.events = [used_event, unread_event, other_event]

    assert client.get_user_entered_events() == [unread_event]


def test_properties_read_the_current_client_and_server():
    commands = FakeCommands()
    commands.responses["whoami"] = FakeResponse(
        data={
            0: {
                "client_nickname": "bot",
                "client_description": "a bot",
                "client_id": 7,
                "client_unique_identifier": "uid",
                "client_database_id": 9,
            }
        }
    )
    commands.responses["serverinfo"] = FakeResponse(
        data={
            0: {
                "virtualserver_id": 1,
                "virtualserver_unique_identifier": "server-uid",
                "virtualserver_name": "server",
                "virtualserver_port": 9987,
            }
        }
    )
    client = make_client(commands)

    assert client.name == "bot"
    assert client.description == "a bot"
    assert client.id == 7
    assert client.unique_id == "uid"
    assert client.database_id == 9
    assert client.server_id == 1
    assert client.server_unique_id == "server-uid"
    assert client.server_name == "server"
    assert client.server_port == 9987


def test_enable_message_events_registers_all_text_sources():
    commands = FakeCommands()
    client = make_client(commands)

    client.enable_message_events()

    assert client.query.started == [1]
    assert [call[2]["event"] for call in commands.called("servernotifyregister")] == [
        NotifyRegisterType.TEXT_SERVER,
        NotifyRegisterType.TEXT_CHANNEL,
        NotifyRegisterType.TEXT_PRIVATE,
    ]

    client.disable_message_events()

    assert len(commands.called("servernotifyunregister")) == 3


def test_enable_events_and_messages_registers_every_source():
    commands = FakeCommands()
    client = make_client(commands)

    client.enable_events_and_messages()

    registrations = commands.called("servernotifyregister")
    assert client.query.started == [1]
    assert [call[2]["event"] for call in registrations] == [
        NotifyRegisterType.TEXT_SERVER,
        NotifyRegisterType.TEXT_CHANNEL,
        NotifyRegisterType.TEXT_PRIVATE,
        NotifyRegisterType.SERVER,
        NotifyRegisterType.CHANNEL,
    ]
    assert registrations[-1][2]["id"] == 0

    client.disable_events_and_messages()

    assert client.query.stopped == 1
    assert len(commands.called("servernotifyunregister")) == 5


def make_client(commands=None):
    client = object.__new__(TS3Client)
    client.query = cast(TS3Query, FakeQuery(commands))
    client.logger = FakeLogger()
    return client
