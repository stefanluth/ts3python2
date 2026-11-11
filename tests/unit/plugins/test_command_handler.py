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


@pytest.mark.parametrize(
    ("commands", "expected_enabled"),
    [
        ({"RecordingCommand": {"trigger": "help"}}, ["message"]),
        ({"NotACommand": {"trigger": "help"}}, []),
    ],
    ids=["known-command", "unknown-command"],
)
def test_registers_message_events_only_for_loaded_commands(monkeypatch, commands, expected_enabled):
    client = FakeClient()
    handler = make_handler(monkeypatch, client, FakeStopEvent())

    handler.run(prefix="!", commands=commands, check_interval=0)

    assert client.enabled == expected_enabled


@pytest.mark.parametrize(
    ("content", "expects_run"),
    [
        ("!help", True),
        ("!nope", False),
        pytest.param("hello", False, marks=pytest.mark.bug),
    ],
    ids=["matching-trigger", "unknown-trigger", "non-prefix"],
)
def test_messages_are_used_and_run_only_on_a_known_trigger(monkeypatch, content, expects_run):
    client = FakeClient()
    message = FakeMessage(content)
    client.message_batches = [[message]]
    handler = make_handler(monkeypatch, client, FakeStopEvent())

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert RecordingCommand.calls == ([message] if expects_run else [])
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
