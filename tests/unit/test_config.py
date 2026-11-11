import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PORTS_CODE = "import config; print(config.TS3_SERVER_PORT, config.TS3_QUERY_PORT)"
CREDENTIALS_CODE = "import config; print(config.TS3_QUERY_LOGIN, config.TS3_QUERY_PASSWORD)"
SSH_KEYS_CODE = (
    "import config; print(config.TS3_SSH_KNOWN_HOSTS, config.TS3_SSH_ACCEPT_ALL_KEYS, config.TS3_SSH_USE_SYSTEM_KEYS)"
)
BOOL_CODE = "import config; print(config.TS3_SSH_ACCEPT_ALL_KEYS, config.TS3_SSH_USE_SYSTEM_KEYS)"
BOOL_CASES = [
    ("1", True, True),
    ("true", True, True),
    ("TRUE", True, True),
    ("yes", True, True),
    ("on", True, True),
    ("y", True, True),
    ("t", True, True),
    ("0", False, False),
    ("false", False, False),
    ("FALSE", False, False),
    ("no", False, False),
    ("off", False, False),
    ("n", False, False),
    ("f", False, False),
    ("", False, False),
    ("maybe", False, True),
    ("2", False, True),
    ("enabled", False, True),
]


def run_config(code=PORTS_CODE, env_extra=None, remove=()):
    env = dict(os.environ)
    for name in (*remove, *(env_extra or {})):
        env.pop(name, None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_default_ports_are_voice_9987_and_query_10022():
    result = run_config(remove=("TS3_SERVER_PORT", "TS3_QUERY_PORT"))

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "9987 10022"


def test_query_credentials_are_read_from_environment():
    result = run_config(
        CREDENTIALS_CODE,
        env_extra={"TS3_QUERY_LOGIN": "bot_login", "TS3_QUERY_PASSWORD": "bot_password"},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "bot_login bot_password"


def test_ssh_host_key_defaults():
    result = run_config(
        SSH_KEYS_CODE,
        remove=(
            "TS3_SSH_KNOWN_HOSTS",
            "TS3_SSH_ACCEPT_ALL_KEYS",
            "TS3_SSH_USE_SYSTEM_KEYS",
        ),
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "None False True"


def test_ssh_host_key_settings_are_read_from_environment():
    result = run_config(
        SSH_KEYS_CODE,
        env_extra={
            "TS3_SSH_KNOWN_HOSTS": "/tmp/known_hosts",
            "TS3_SSH_ACCEPT_ALL_KEYS": "true",
            "TS3_SSH_USE_SYSTEM_KEYS": "false",
        },
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "/tmp/known_hosts True False"


@pytest.mark.parametrize("value, accept_all, use_system", BOOL_CASES)
def test_ssh_booleans_parse_common_and_unknown_strings(value, accept_all, use_system):
    result = run_config(
        BOOL_CODE,
        env_extra={"TS3_SSH_ACCEPT_ALL_KEYS": value, "TS3_SSH_USE_SYSTEM_KEYS": value},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"{accept_all} {use_system}"
