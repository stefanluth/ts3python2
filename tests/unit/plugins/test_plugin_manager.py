import pytest

import plugins.plugin_manager as plugin_manager_module
from plugins.errors import ConfigurationError, ImplementationError
from plugins.plugin_manager import PluginManager, validate_config
from tests.support.fakes import FakeClient


class RequiredPlugin:
    def run(self, x: int):
        pass


class WrongTypePlugin:
    def run(self, x: int):
        pass


class GenericListPlugin:
    def run(self, doodles: list[dict] = None):
        pass


class OptionalPlugin:
    def run(self, value: str | None = None):
        pass


class RecordingPlugin:
    instances = []

    def __init__(self, client, event):
        self.client = client
        self.event = event
        RecordingPlugin.instances.append(self)

    def run(self, value: int = 0):
        pass


class FakePlugins:
    __all__ = ["RecordingPlugin"]
    RecordingPlugin = RecordingPlugin


class FakeThread:
    def __init__(self, target=None, kwargs=None):
        self.target = target
        self.kwargs = kwargs
        self.name = None
        self.ident = id(self)
        self.started = False
        self.joined = []

    def start(self):
        self.started = True

    def join(self, timeout=None):
        self.joined.append(timeout)


@pytest.fixture(autouse=True)
def reset_plugin_state():
    RecordingPlugin.instances = []


def make_manager(monkeypatch, config, client=None):
    monkeypatch.setattr(plugin_manager_module, "all_plugins", FakePlugins)
    monkeypatch.setattr(plugin_manager_module, "Thread", FakeThread)
    return PluginManager(client or FakeClient(), config)


def test_run_rejects_an_unknown_plugin(monkeypatch):
    manager = make_manager(monkeypatch, {"Missing": {}})

    with pytest.raises(ImplementationError):
        manager.run()


def test_run_starts_a_thread_with_the_plugin_config(monkeypatch):
    client = FakeClient()
    manager = make_manager(monkeypatch, {"RecordingPlugin": {"value": 2}}, client=client)

    manager.run()

    plugin = RecordingPlugin.instances[0]
    assert plugin.client is client
    thread, stop = next(iter(manager.threads.values()))
    assert thread.started is True
    assert thread.target == plugin.run
    assert thread.kwargs == {"value": 2}
    assert stop.is_set() is False


def test_stop_sets_the_event_and_joins_every_thread(monkeypatch):
    manager = make_manager(monkeypatch, {"RecordingPlugin": {"value": 2}})
    manager.run()
    thread, stop = next(iter(manager.threads.values()))

    manager.stop(timeout=1)

    assert stop.is_set() is True
    assert thread.joined == [1]


def test_missing_required_parameter_raises():
    with pytest.raises(ConfigurationError):
        validate_config(RequiredPlugin(), {})


def test_wrong_type_raises():
    with pytest.raises(ConfigurationError):
        validate_config(WrongTypePlugin(), {"x": "bad"})


def test_generic_list_annotation_does_not_crash():
    validate_config(GenericListPlugin(), {"doodles": []})


def test_optional_annotation_accepts_none():
    validate_config(OptionalPlugin(), {"value": None})


@pytest.mark.bug
def test_unknown_config_key_raises():
    with pytest.raises(ConfigurationError):
        validate_config(RequiredPlugin(), {"x": 1, "typo": 2})
