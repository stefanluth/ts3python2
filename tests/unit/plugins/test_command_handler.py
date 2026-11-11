import pytest

import plugins.plugins.command_handler as command_handler_module
from plugins.plugins.command_handler import CommandHandler
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage, FakeStopEvent


class RecordingCommand:
    calls = []
    should_raise = False

    def __init__(self, client, trigger, **kwargs):
        self.client = client
        self.trigger = trigger
        self.name = "RecordingCommand"

    def run(self, message):
        RecordingCommand.calls.append(message)
        if RecordingCommand.should_raise:
            raise RuntimeError("command failed")


class FakeCommandsNamespace:
    __all__ = ["RecordingCommand"]
    RecordingCommand = RecordingCommand


@pytest.fixture(autouse=True)
def reset_command_state():
    RecordingCommand.calls = []
    RecordingCommand.should_raise = False


def make_handler(monkeypatch, client, stop):
    monkeypatch.setattr(command_handler_module, "all_commands", FakeCommandsNamespace)
    handler = CommandHandler(client, stop)
    handler.logger = FakeLogger()
    return handler


def test_registers_message_events(monkeypatch):
    client = FakeClient()
    handler = make_handler(monkeypatch, client, FakeStopEvent())

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert client.enabled == ["message"]


def test_matching_message_runs_the_command_and_marks_it_used(monkeypatch):
    client = FakeClient()
    message = FakeMessage("!help")
    client.message_batches = [[message]]
    handler = make_handler(monkeypatch, client, FakeStopEvent())

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert RecordingCommand.calls == [message]
    assert message.used is True


def test_unknown_trigger_does_not_run_a_command(monkeypatch):
    client = FakeClient()
    message = FakeMessage("!nope")
    client.message_batches = [[message]]
    handler = make_handler(monkeypatch, client, FakeStopEvent())

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert RecordingCommand.calls == []


def test_unknown_command_name_returns_without_enabling_events(monkeypatch):
    client = FakeClient()
    handler = make_handler(monkeypatch, client, FakeStopEvent())

    handler.run(prefix="!", commands={"NotACommand": {"trigger": "help"}}, check_interval=0)

    assert client.enabled == []


def test_empty_commands_returns_without_enabling_events(monkeypatch):
    client = FakeClient()
    handler = make_handler(monkeypatch, client, FakeStopEvent())

    handler.run(prefix="!", commands={}, check_interval=0)

    assert client.enabled == []


@pytest.mark.bug
def test_non_prefix_message_is_marked_used(monkeypatch):
    client = FakeClient()
    message = FakeMessage("hello")
    client.message_batches = [[message]]
    handler = make_handler(monkeypatch, client, FakeStopEvent())

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert message.used is True


@pytest.mark.bug
def test_command_exception_does_not_kill_loop(monkeypatch):
    client = FakeClient()
    first = FakeMessage("!help")
    second = FakeMessage("!help")
    client.message_batches = [[first], [second]]
    handler = make_handler(monkeypatch, client, FakeStopEvent(stop_after_waits=2))
    RecordingCommand.should_raise = True

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert RecordingCommand.calls == [first, second]
