from typing import cast

import pytest

import plugins.plugin_manager as plugin_manager_module
from plugins.errors import ConfigurationError, ImplementationError
from plugins.plugin import Plugin
from plugins.plugin_manager import PluginManager, validate_config
from tests.support.fakes import FakeClient
from ts3client import TS3Client


class RequiredPlugin(Plugin):
    def __init__(self):
        pass

    def run(self, x: int):
        pass


class GenericListPlugin(Plugin):
    def __init__(self):
        pass

    def run(self, doodles: list[dict] | None = None):
        pass


class OptionalPlugin(Plugin):
    def __init__(self):
        pass

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


def make_manager(monkeypatch, config, client: FakeClient | None = None):
    monkeypatch.setattr(plugin_manager_module, "all_plugins", FakePlugins)
    monkeypatch.setattr(plugin_manager_module, "Thread", FakeThread)
    return PluginManager(cast(TS3Client, client or FakeClient()), config)


def test_run_rejects_an_unknown_plugin(monkeypatch):
    manager = make_manager(monkeypatch, {"Missing": {}})

    with pytest.raises(ImplementationError):
        manager.run()


def test_run_starts_a_thread_and_stop_settles_it(monkeypatch):
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

    manager.stop(timeout=1)

    assert stop.is_set() is True
    assert thread.joined == [1]


@pytest.mark.parametrize(
    ("plugin_type", "config", "valid"),
    [
        (RequiredPlugin, {}, False),
        (RequiredPlugin, {"x": "bad"}, False),
        pytest.param(RequiredPlugin, {"x": 1, "typo": 2}, False, marks=pytest.mark.bug),
        (GenericListPlugin, {"doodles": []}, True),
        (OptionalPlugin, {"value": None}, True),
    ],
    ids=["missing-required", "wrong-type", "unknown-key", "generic-list", "optional-none"],
)
def test_config_validation(plugin_type, config, valid):
    if valid:
        validate_config(plugin_type(), config)
    else:
        with pytest.raises(ConfigurationError):
            validate_config(plugin_type(), config)
