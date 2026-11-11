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
from ts3client.ts3query.ts3query_command import TS3QueryCommand
from ts3client.utils import patterns


def make_query(monkeypatch, **kwargs):
    monkeypatch.setattr("ts3client.ts3query.ts3query.SSHTransport", FakeSSHTransport)
    query = TS3Query("host", 1, login="user", password="secret", logger=FakeLogger(), **kwargs)
    query.exit = lambda: None
    return query


def make_message(text="hi"):
    return Message(
        targetmode=TargetMode.SERVER,
        msg=text,
        target=0,
        invokerid=1,
        invokername="user",
        invokeruid="uid",
    )


@pytest.mark.parametrize("login, password", [(None, "secret"), ("user", None), (None, None), ("", "secret")])
def test_missing_credentials_raise_value_error(monkeypatch, login, password):
    monkeypatch.setattr("ts3client.ts3query.ts3query.SSHTransport", FakeSSHTransport)

    with pytest.raises(ValueError):
        TS3Query("host", 1, login=login, password=password, logger=FakeLogger())


def test_constructor_passes_credentials_and_options_to_transport(monkeypatch):
    query = make_query(
        monkeypatch,
        known_hosts="/tmp/known_hosts",
        accept_all_keys=True,
        use_system_host_keys=False,
    )

    transport = query._transport

    assert transport.args == ("host", 1, "user", "secret")
    assert transport.kwargs == {
        "timeout": 10,
        "known_hosts": "/tmp/known_hosts",
        "accept_all_keys": True,
        "use_system_host_keys": False,
    }


def test_constructor_skips_two_greeting_lines(monkeypatch):
    monkeypatch.setattr("ts3client.ts3query.ts3query.SSHTransport", FakeSSHTransport)

    query = TS3Query("host", 1, login="user", password="secret", timeout=4, logger=FakeLogger())

    assert query._transport.read_until_calls == [(b"\n\r", 4), (b"\n\r", 4)]


def test_receive_returns_parsed_response(monkeypatch):
    query = make_query(monkeypatch)
    payload = b"clid=1\n\rerror id=0 msg=ok\n\r"
    match = patterns.RESPONSE_END_BYTES.search(payload)
    query._transport.expect_result = (0, match, payload)

    response = query._receive()

    assert response.data == {0: {"clid": 1}}
    assert response.error_id == 0


def test_receive_uses_transport_expect(monkeypatch):
    query = make_query(monkeypatch)
    payload = b"error id=0 msg=ok\n\r"
    match = patterns.RESPONSE_END_BYTES.search(payload)
    query._transport.expect_result = (0, match, payload)

    query._receive()

    assert query._transport.expect_calls == [([patterns.RESPONSE_END_BYTES], query.timeout)]


def test_send_writes_command_through_transport(monkeypatch):
    query = make_query(monkeypatch)
    query.disable_flood_protection()
    payload = b"version=5.0\n\rerror id=0 msg=ok\n\r"
    match = patterns.RESPONSE_END_BYTES.search(payload)
    query._transport.expect_result = (0, match, payload)

    query.send(TS3QueryCommand("version"))

    assert query._transport.written == [b"version\n"]


def test_exit_sends_quit_and_closes_transport(monkeypatch):
    monkeypatch.setattr("ts3client.ts3query.ts3query.SSHTransport", FakeSSHTransport)
    query = TS3Query("host", 1, login="user", password="secret", logger=FakeLogger())
    commands = FakeCommands()
    query.commands = commands

    query.exit()

    assert commands.called("quit")
    assert query._transport.closed
    assert query._transport.close_calls == 1


def test_exit_closes_transport_when_disconnected(monkeypatch):
    monkeypatch.setattr("ts3client.ts3query.ts3query.SSHTransport", FakeSSHTransport)
    query = TS3Query("host", 1, login="user", password="secret", logger=FakeLogger())
    commands = FakeCommands()
    query.commands = commands
    query._transport.connected_flag = False

    query.exit()

    assert not commands.called("quit")
    assert query._transport.closed


def test_receive_timeout_raises_connection_error(monkeypatch):
    query = make_query(monkeypatch)
    query._transport.expect_result = (-1, None, b"")

    with pytest.raises(ConnectionError):
        query._receive()


def test_receive_eof_raises_connection_error(monkeypatch):
    query = make_query(monkeypatch)
    query._transport.expect_error = EOFError("connection closed")

    with pytest.raises(ConnectionError):
        query._receive()


class FlakyCommands:
    def __init__(self):
        self.calls = 0

    def version(self):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("boom")
        return FakeResponse()


def test_poll_survives_command_exception(monkeypatch):
    query = make_query(monkeypatch)
    commands = FlakyCommands()
    query.commands = commands
    stop = FakeStopEvent(stop_after_waits=2)

    query._poll(stop, 0)

    assert commands.calls == 2


@pytest.mark.bug
def test_polling_stop_event_is_per_instance(monkeypatch):
    first = make_query(monkeypatch)
    second = make_query(monkeypatch)

    assert first._polling_thread_stop is not second._polling_thread_stop


def test_send_when_disconnected_raises(monkeypatch):
    query = make_query(monkeypatch)
    query.connected = lambda: False

    with pytest.raises(ConnectionError):
        query.send(TS3QueryCommand("version"))


@pytest.mark.bug
def test_buffers_are_per_instance(monkeypatch):
    first = make_query(monkeypatch)
    second = make_query(monkeypatch)

    assert first.events is not second.events
    assert first.messages is not second.messages


def test_add_events_trims_to_limit(monkeypatch):
    query = make_query(monkeypatch)
    query._events = []
    query.events_limit = 2
    events = [Event() for _ in range(3)]

    query._add_events(events, query.events_limit)

    assert query.events == events[-2:]


def test_add_messages_trims_to_limit(monkeypatch):
    query = make_query(monkeypatch)
    query._messages = []
    query.messages_limit = 2
    messages = [make_message(str(index)) for index in range(3)]

    query._add_messages(messages, query.messages_limit)

    assert query.messages == messages[-2:]


def test_unread_filters_out_used_messages_and_events(monkeypatch):
    query = make_query(monkeypatch)
    unread_message, used_message = make_message("a"), make_message("b")
    used_message.mark_as_used()
    unread_event, used_event = Event(), Event()
    used_event.used = True
    query._messages = [unread_message, used_message]
    query._events = [unread_event, used_event]

    assert query.unread_messages == [unread_message]
    assert query.unread_events == [unread_event]


def test_remove_used_drops_used_messages_and_events(monkeypatch):
    query = make_query(monkeypatch)
    unread_message, used_message = make_message("a"), make_message("b")
    used_message.mark_as_used()
    unread_event, used_event = Event(), Event()
    used_event.used = True
    query._messages = [unread_message, used_message]
    query._events = [unread_event, used_event]

    query._remove_used_messages()
    query._remove_used_events()

    assert query.messages == [unread_message]
    assert query.events == [unread_event]


def test_buffer_limits_and_flood_timeout_setters(monkeypatch):
    query = make_query(monkeypatch)

    query.messages_limit = 5
    query.events_limit = 6
    query.flood_protection_timeout = 0.1

    assert query.messages_limit == 5
    assert query.events_limit == 6
    assert query.flood_protection_timeout == 0.1
