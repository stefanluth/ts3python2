import pytest

import plugins.plugins.command_handler as command_handler_module
from plugins.plugin_manager import validate_config
from plugins.plugins.command_handler import CommandHandler
from tests.support.fakes import FakeClient, FakeLogger, FakeMessage, FakeStopEvent


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


def test_tick_runs_once_per_loop_for_each_command(monkeypatch):
    client = FakeClient()
    handler = make_handler(monkeypatch, client, FakeStopEvent(stop_after_waits=3))

    handler.run(
        prefix="!",
        commands={
            "RecordingCommand": {"trigger": "help"},
            "SecondRecordingCommand": {"trigger": "other"},
        },
        check_interval=0,
    )

    assert RecordingCommand.tick_calls == 3
    assert SecondRecordingCommand.tick_calls == 3


def test_commands_are_not_stopped_between_loop_iterations(monkeypatch):
    client = FakeClient()
    handler = make_handler(monkeypatch, client, FakeStopEvent(stop_after_waits=3))

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert RecordingCommand.tick_calls == 3
    assert RecordingCommand.stop_calls == 1


def test_tick_exception_is_logged_and_loop_continues(monkeypatch):
    client = FakeClient()
    first = FakeMessage("!help")
    second = FakeMessage("!help")
    client.message_batches = [[first], [second]]
    handler = make_handler(monkeypatch, client, FakeStopEvent(stop_after_waits=2))
    logger = CapturingLogger()
    handler.logger = logger
    RecordingCommand.should_raise_on_tick = True

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert RecordingCommand.calls == [first, second]
    assert logger.exceptions == ["Command 'RecordingCommand' tick failed."] * 2


def test_stop_invokes_each_loaded_command_stop(monkeypatch):
    client = FakeClient()
    handler = make_handler(monkeypatch, client, FakeStopEvent(stop_after_waits=1))

    handler.run(
        prefix="!",
        commands={
            "RecordingCommand": {"trigger": "help"},
            "SecondRecordingCommand": {"trigger": "other"},
        },
        check_interval=0,
    )
    handler.stop()

    assert RecordingCommand.stop_calls == 1
    assert SecondRecordingCommand.stop_calls == 1
    assert handler.event.stopped is True


def test_stop_sets_event_even_when_command_stop_raises(monkeypatch):
    client = FakeClient()
    stop = FakeStopEvent()
    handler = make_handler(monkeypatch, client, stop)
    handler.commands = [RecordingCommand(client, "help")]
    RecordingCommand.should_raise_on_stop = True

    handler.stop()

    assert RecordingCommand.stop_calls == 1
    assert stop.stopped is True


def test_run_stops_commands_when_event_is_set(monkeypatch):
    client = FakeClient()
    handler = make_handler(monkeypatch, client, FakeStopEvent(stop_after_waits=1))

    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0)

    assert RecordingCommand.stop_calls == 1

    handler.stop()

    assert RecordingCommand.stop_calls == 1


def test_fractional_check_interval_is_accepted(monkeypatch):
    client = FakeClient()
    message = FakeMessage("!help")
    client.message_batches = [[message]]
    handler = make_handler(monkeypatch, client, FakeStopEvent(stop_after_waits=1))

    validate_config(handler, {"prefix": "!", "check_interval": 0.2, "commands": {}})
    handler.run(prefix="!", commands={"RecordingCommand": {"trigger": "help"}}, check_interval=0.2)

    assert RecordingCommand.calls == [message]


def make_handler(monkeypatch, client, stop):
    monkeypatch.setattr(command_handler_module, "all_commands", FakeCommandsNamespace)
    handler = CommandHandler(client, stop)
    handler.logger = FakeLogger()
    return handler


@pytest.fixture(autouse=True)
def reset_command_state():
    RecordingCommand.calls = []
    RecordingCommand.should_raise = False
    RecordingCommand.tick_calls = 0
    RecordingCommand.stop_calls = 0
    RecordingCommand.should_raise_on_tick = False
    RecordingCommand.should_raise_on_stop = False
    SecondRecordingCommand.tick_calls = 0
    SecondRecordingCommand.stop_calls = 0


class CapturingLogger(FakeLogger):
    def __init__(self):
        super().__init__()
        self.exceptions = []

    def exception(self, message, *args, **kwargs):
        self.exceptions.append(message)


class RecordingCommand:
    calls = []
    should_raise = False
    tick_calls = 0
    stop_calls = 0
    should_raise_on_tick = False
    should_raise_on_stop = False

    def __init__(self, client, trigger, **kwargs):
        self.client = client
        self.trigger = trigger
        self.name = "RecordingCommand"

    def run(self, message):
        RecordingCommand.calls.append(message)
        if RecordingCommand.should_raise:
            raise RuntimeError("command failed")

    def tick(self):
        RecordingCommand.tick_calls += 1
        if RecordingCommand.should_raise_on_tick:
            raise RuntimeError("tick failed")

    def stop(self):
        RecordingCommand.stop_calls += 1
        if RecordingCommand.should_raise_on_stop:
            raise RuntimeError("stop failed")


class SecondRecordingCommand:
    tick_calls = 0
    stop_calls = 0

    def __init__(self, client, trigger, **kwargs):
        self.client = client
        self.trigger = trigger
        self.name = "SecondRecordingCommand"

    def run(self, message):
        pass

    def tick(self):
        SecondRecordingCommand.tick_calls += 1

    def stop(self):
        SecondRecordingCommand.stop_calls += 1


class FakeCommandsNamespace:
    __all__ = ["RecordingCommand", "SecondRecordingCommand"]
    RecordingCommand = RecordingCommand
    SecondRecordingCommand = SecondRecordingCommand
