import os
import socket
import time
from dataclasses import dataclass

import paramiko
import pytest

from tests.support.integration import configure_server_flood, open_used_query
from ts3client import TS3Client


@dataclass(frozen=True)
class ServerConfig:
    host: str
    query_port: int
    server_port: int
    password: str


def _env(name, default):
    return os.getenv(name, default)


def _wait_for_ssh_port(host, port, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            pass
        time.sleep(0.5)
    raise AssertionError(f"TS3 SSH query port {host}:{port} did not become reachable")


def pytest_collection_modifyitems(config, items):
    if os.getenv("TS3_INTEGRATION") == "1" and os.getenv("QUERY_ADMIN_PASSWORD"):
        return

    skip = pytest.mark.skip(reason="set TS3_INTEGRATION=1 and QUERY_ADMIN_PASSWORD to run live tests")
    for item in items:
        if item.get_closest_marker("integration") is not None:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def server():
    password = os.getenv("QUERY_ADMIN_PASSWORD")
    if os.getenv("TS3_INTEGRATION") != "1" or not password:
        pytest.skip("set TS3_INTEGRATION=1 and QUERY_ADMIN_PASSWORD to run live tests")

    config = ServerConfig(
        host=_env("TS3_QUERY_HOST", "127.0.0.1"),
        query_port=int(_env("TS3_QUERY_PORT", "10022")),
        server_port=int(_env("TS3_SERVER_PORT", "9987")),
        password=password,
    )
    _wait_for_ssh_port(config.host, config.query_port)
    if _env("TS3_SET_FLOOD_LIMITS", "1") == "1":
        configure_server_flood(config.host, config.query_port, config.password)
    return config


@pytest.fixture(scope="session")
def used_query(server):
    connection = open_used_query(server.host, server.query_port, server.server_port, server.password)
    yield connection
    connection.exit()


def _open_client(server):
    last_error = None
    for attempt in range(3):
        client = None
        try:
            client = TS3Client(
                server.host,
                server.query_port,
                "serveradmin",
                server.password,
                timeout=5,
                accept_all_keys=True,
                use_system_host_keys=False,
            )
            client.query.disable_flood_protection()
            response = client.query.commands.use(port=server.server_port)
            if response.error_id == 0:
                return client
            last_error = response
        except paramiko.AuthenticationException:
            raise
        except (EOFError, ConnectionError, OSError, paramiko.SSHException) as error:
            last_error = error

        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass
        time.sleep(1.5 * (attempt + 1))

    raise AssertionError(f"could not open the bot query connection: {last_error}")


@pytest.fixture(scope="session")
def bot_client(server):
    client = _open_client(server)
    yield client
    client.disconnect()


@pytest.fixture(scope="session")
def trigger_query(server):
    connection = open_used_query(server.host, server.query_port, server.server_port, server.password)
    yield connection
    connection.exit()


@pytest.fixture
def fresh_query(server):
    connection = open_used_query(server.host, server.query_port, server.server_port, server.password)
    yield connection
    connection.exit()


@pytest.fixture
def listener_query(fresh_query):
    return fresh_query


@pytest.fixture
def fresh_client(server):
    client = _open_client(server)
    yield client
    client.disconnect()
