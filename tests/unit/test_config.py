import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.py"
CONFIG_ENV = (
    "TS3_SERVER_PORT",
    "TS3_QUERY_PORT",
    "TS3_QUERY_LOGIN",
    "TS3_QUERY_PASSWORD",
    "TS3_SSH_KNOWN_HOSTS",
    "TS3_SSH_ACCEPT_ALL_KEYS",
    "TS3_SSH_USE_SYSTEM_KEYS",
)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, (None, False, True)),
        (
            {
                "TS3_SSH_KNOWN_HOSTS": "/tmp/known_hosts",
                "TS3_SSH_ACCEPT_ALL_KEYS": "true",
                "TS3_SSH_USE_SYSTEM_KEYS": "false",
            },
            ("/tmp/known_hosts", True, False),
        ),
        ({"TS3_SSH_ACCEPT_ALL_KEYS": "", "TS3_SSH_USE_SYSTEM_KEYS": ""}, (None, False, False)),
    ],
    ids=["defaults", "environment", "empty-strings"],
)
def test_ssh_settings_from_environment(monkeypatch, env, expected):
    config = load_config(monkeypatch, **env)

    actual = (config.TS3_SSH_KNOWN_HOSTS, config.TS3_SSH_ACCEPT_ALL_KEYS, config.TS3_SSH_USE_SYSTEM_KEYS)
    assert actual == expected


def load_config(monkeypatch, **env):
    for name in CONFIG_ENV:
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    monkeypatch.setattr("dotenv.load_dotenv", lambda: None)

    spec = importlib.util.spec_from_file_location("config_under_test", CONFIG_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
