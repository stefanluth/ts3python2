from typing import cast

import pytest

from tests.support.fakes import (
    FakeCommands,
    FakeLogger,
    FakeResponse,
    FakeSSHTransport,
    FakeStopEvent,
)
from ts3client.constants import TargetMode
from ts3client.event import Event
from ts3client.message import Message
from ts3client.ts3query import TS3Query
from ts3client.ts3query.ts3query_command import CommandsWrapper, TS3QueryCommand
from ts3client.utils import patterns


@pytest.mark.parametrize("login, password", [(None, "secret"), ("user", None)])
def test_missing_credentials_raise_value_error(login, password):
    with pytest.raises(ValueError):
        TS3Query("host", 1, login=login, password=password, logger=FakeLogger())


@pytest.mark.parametrize("failure", [None, "timeout", "eof"])
def test_receive_parses_or_raises(monkeypatch, failure):
    query = make_query(monkeypatch)

    if failure is None:
        payload = b"clid=1\n\rerror id=0 msg=ok\n\r"
        match = patterns.RESPONSE_END_BYTES.search(payload)
        query._transport.expect_result = (0, match, payload)

        response = query._receive()

        assert response.data == {0: {"clid": 1}}
        assert response.error_id == 0
        return

    if failure == "timeout":
        query._transport.expect_result = (-1, None, b"")
    else:
        query._transport.expect_error = EOFError("connection closed")

    with pytest.raises(ConnectionError):
        query._receive()


@pytest.mark.parametrize(
    ("connected", "expected_written"),
    [(True, [b"version\n"]), (False, [])],
    ids=["connected-writes", "disconnected-raises"],
)
def test_send_writes_only_when_connected(monkeypatch, connected, expected_written):
    query = make_query(monkeypatch)
    query.disable_flood_protection()
    payload = b"version=5.0\n\rerror id=0 msg=ok\n\r"
    match = patterns.RESPONSE_END_BYTES.search(payload)
    query._transport.expect_result = (0, match, payload)

    if connected:
        query.send(TS3QueryCommand("version"))
    else:
        query.connected = lambda: False
        with pytest.raises(ConnectionError):
            query.send(TS3QueryCommand("version"))

    assert query._transport.written == expected_written


@pytest.mark.parametrize(("connected", "sends_quit"), [(True, True), (False, False)])
def test_exit_closes_transport_and_sends_quit_only_when_connected(monkeypatch, connected, sends_quit):
    monkeypatch.setattr("ts3client.ts3query.ts3query.SSHTransport", FakeSSHTransport)
    query = TS3Query("host", 1, login="user", password="secret", logger=FakeLogger())
    commands = FakeCommands()
    query.commands = cast(CommandsWrapper, commands)
    transport = transport_of(query)
    transport.connected_flag = connected

    query.exit()

    assert bool(commands.called("quit")) is sends_quit
    assert transport.closed
    assert transport.close_calls == 1


def test_poll_survives_command_exception(monkeypatch):
    query = make_query(monkeypatch)
    commands = FlakyCommands()
    query.commands = commands
    stop = FakeStopEvent(stop_after_waits=2)

    query._poll(stop, 0)

    assert commands.calls == 2


@pytest.mark.bug
def test_state_is_per_instance(monkeypatch):
    first = make_query(monkeypatch)
    second = make_query(monkeypatch)

    assert first._polling_thread_stop is not second._polling_thread_stop
    assert first.events is not second.events
    assert first.messages is not second.messages

    assert first.flood_protection is True
    first.disable_flood_protection()
    first.flood_protection_timeout = 0.1
    assert first.flood_protection is False
    assert first.flood_protection_timeout == 0.1
    assert second.flood_protection is True
    assert second.flood_protection_timeout == 0.5


@pytest.mark.parametrize(
    ("attribute", "limit_attribute", "add_method", "make_items"),
    [
        ("events", "events_limit", "_add_events", lambda: [Event() for _ in range(3)]),
        ("messages", "messages_limit", "_add_messages", lambda: [make_message(str(index)) for index in range(3)]),
    ],
)
def test_add_items_trims_to_limit(monkeypatch, attribute, limit_attribute, add_method, make_items):
    query = make_query(monkeypatch)
    setattr(query, f"_{attribute}", [])
    setattr(query, limit_attribute, 2)
    items = make_items()

    getattr(query, add_method)(items, 2)

    assert getattr(query, attribute) == items[-2:]


def test_used_items_are_excluded_from_unread_and_removed(monkeypatch):
    query = make_query(monkeypatch)
    unread_message, used_message = make_message("a"), make_message("b")
    used_message.mark_as_used()
    unread_event, used_event = Event(), Event()
    used_event.used = True
    query._messages = [unread_message, used_message]
    query._events = [unread_event, used_event]

    assert query.unread_messages == [unread_message]
    assert query.unread_events == [unread_event]

    query._remove_used_messages()
    query._remove_used_events()

    assert query.messages == [unread_message]
    assert query.events == [unread_event]


def test_start_polling_is_idempotent_and_stop_clears_the_thread(monkeypatch):
    query = make_query(monkeypatch)

    query.stop_polling()
    assert query._polling_thread is None

    query.start_polling(0.01)
    thread = query._polling_thread
    query.start_polling(0.01)

    assert query._polling_thread is thread

    query.stop_polling()

    assert query._polling_thread is None
    assert thread is not None
    assert thread.is_alive() is False


def make_query(monkeypatch, **kwargs):
    monkeypatch.setattr("ts3client.ts3query.ts3query.SSHTransport", FakeSSHTransport)
    query = TS3Query("host", 1, login="user", password="secret", logger=FakeLogger(), **kwargs)
    query.exit = lambda: None
    return query


def transport_of(query: TS3Query) -> FakeSSHTransport:
    transport = query._transport
    assert isinstance(transport, FakeSSHTransport)
    return transport


def make_message(text="hi"):
    return Message(
        targetmode=TargetMode.SERVER.value,
        msg=text,
        target=0,
        invokerid=1,
        invokername="user",
        invokeruid="uid",
    )


class FlakyCommands:
    def __init__(self):
        self.calls = 0

    def version(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("boom")
        return FakeResponse()
