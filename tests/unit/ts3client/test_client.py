from typing import cast

import pytest

import ts3client.ts3client as ts3client_module
from tests.support.fakes import FakeCommands, FakeLogger, FakeQuery, FakeResponse
from ts3client import TS3Client
from ts3client.constants import TargetMode
from ts3client.ts3query import TS3Query
from ts3client.user import User


def make_client(commands=None):
    client = object.__new__(TS3Client)
    client.query = cast(TS3Query, FakeQuery(commands))
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

    client.disconnect()
    assert query.exit_calls == 1
