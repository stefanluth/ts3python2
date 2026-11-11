import os
import subprocess

import pytest

from tests.support.containers import ManagedContainer, start_container, worker_name


class FakeRunner:
    def __init__(self, port_output="127.0.0.1:49153\n", logs_output="server log\n"):
        self.calls = []
        self.port_output = port_output
        self.logs_output = logs_output

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if command[1] == "port":
            return subprocess.CompletedProcess(command, 0, self.port_output, "")
        if command[1] == "logs":
            return subprocess.CompletedProcess(command, 0, self.logs_output, "")
        return subprocess.CompletedProcess(command, 0, "container-id\n", "")


@pytest.mark.parametrize(
    ("env", "expected"),
    [(None, "local"), ("gw2", "gw2")],
    ids=["missing", "xdist"],
)
def test_worker_name(monkeypatch, env, expected):
    if env is None:
        monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    else:
        monkeypatch.setenv("PYTEST_XDIST_WORKER", env)

    assert worker_name() == expected


def test_start_container_command(monkeypatch):
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw1")
    runner = FakeRunner()

    container = start_container("teamspeak:test", "secret-pass", runner=runner)

    name = f"ts3-test-{os.getpid()}-gw1"
    assert (container.name, container.host, container.query_port) == (name, "127.0.0.1", 49153)
    assert runner.calls[0][0] == [
        "docker",
        "run",
        "-d",
        "--name",
        name,
        "--label",
        "ts3python.test=1",
        "-p",
        "127.0.0.1::10022",
        "-e",
        "TS3SERVER_LICENSE=accept",
        "-e",
        "TS3SERVER_QUERY_PROTOCOLS=ssh",
        "-e",
        "TS3SERVER_QUERY_SSH_PORT=10022",
        "-e",
        "TS3SERVER_SERVERADMIN_PASSWORD=secret-pass",
        "teamspeak:test",
    ]
    assert runner.calls[1][0] == ["docker", "port", name, "10022/tcp"]


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("127.0.0.1:32768\n", 32768),
        ("[::]:49153\n", 49153),
        ("0.0.0.0:61000\n[::]:61000\n", 61000),
    ],
    ids=["ipv4", "ipv6", "multiple-bindings"],
)
def test_start_container_parses_host_port(monkeypatch, output, expected):
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw3")
    runner = FakeRunner(port_output=output)

    assert start_container("teamspeak:test", "password", runner=runner).query_port == expected


def test_start_container_removes_container_when_port_discovery_fails(monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    runner = FakeRunner(port_output="")

    with pytest.raises(RuntimeError, match="could not discover host query port"):
        start_container("teamspeak:test", "password", runner=runner)

    name = f"ts3-test-{os.getpid()}-local"
    assert runner.calls[-1][0] == ["docker", "rm", "-f", name]


def test_logs_returns_docker_log_output():
    runner = FakeRunner(logs_output="line one\nline two\n")
    container = ManagedContainer("ts3-test-1-local", "127.0.0.1", 49153, _runner=runner)

    assert container.logs() == "line one\nline two\n"
    assert runner.calls[0][0] == ["docker", "logs", "ts3-test-1-local"]


def test_stop_is_idempotent():
    runner = FakeRunner()
    container = ManagedContainer("ts3-test-1-gw0", "127.0.0.1", 49153, _runner=runner)

    container.stop()
    container.stop()

    assert [call[0] for call in runner.calls] == [
        ["docker", "rm", "-f", "ts3-test-1-gw0"],
        ["docker", "rm", "-f", "ts3-test-1-gw0"],
    ]


def test_stop_swallows_docker_errors():
    def runner(command, **kwargs):
        raise OSError("docker is unavailable")

    ManagedContainer("ts3-test-1-local", "127.0.0.1", 49153, _runner=runner).stop()
