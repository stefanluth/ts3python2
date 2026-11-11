import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.support.containers import ManagedContainer, start_container, worker_name
from tests.support.integration import Group, configure_server_limits, open_used_connection, open_used_query
from ts3client import TS3Client


@dataclass(frozen=True)
class ServerConfig:
    host: str
    query_port: int
    server_port: int
    password: str


@dataclass
class _ServerSession:
    config: ServerConfig
    container: ManagedContainer | None = None


_server_session: _ServerSession | None = None


def pytest_collection_modifyitems(config, items):
    if os.getenv("TS3_INTEGRATION") == "1" and os.getenv("QUERY_ADMIN_PASSWORD"):
        return

    skip = pytest.mark.skip(reason="set TS3_INTEGRATION=1 and QUERY_ADMIN_PASSWORD to run live tests")
    for item in items:
        if item.get_closest_marker("integration") is not None:
            item.add_marker(skip)


@pytest.hookimpl(trylast=True)
def pytest_collection_finish(session):
    global _server_session

    if _server_session is not None or _is_xdist_controller(session.config):
        return
    if not _integration_enabled(session.config):
        return
    if not any(item.get_closest_marker("integration") for item in session.items):
        return

    _server_session = _start_server(os.environ["QUERY_ADMIN_PASSWORD"])


def pytest_sessionfinish(session, exitstatus):
    global _server_session

    server_session, _server_session = _server_session, None
    if server_session is None or server_session.container is None:
        return

    if session.testsfailed:
        _dump_container_logs(server_session.container)
    server_session.container.stop()


@pytest.fixture(scope="session")
def server():
    if _server_session is None:
        pytest.skip("set TS3_INTEGRATION=1 and QUERY_ADMIN_PASSWORD to run live tests")
    return _server_session.config


@pytest.fixture(scope="session")
def used_query(server):
    connection = open_used_query(server.host, server.query_port, server.server_port, server.password)
    yield connection
    connection.exit()


@pytest.fixture(scope="session")
def server_groups(used_query):
    return tuple(
        Group(int(entry["sgid"]), int(entry.get("type", 1)))
        for entry in used_query.commands.servergrouplist().data.values()
    )


@pytest.fixture(scope="session")
def channel_groups(used_query):
    return tuple(
        Group(int(entry["cgid"]), int(entry.get("type", 1)))
        for entry in used_query.commands.channelgrouplist().data.values()
    )


@pytest.fixture(scope="session")
def regular_server_group_ids(server_groups):
    return tuple(group.id for group in server_groups if group.type == 1)


@pytest.fixture(scope="session")
def query_server_group_ids(server_groups):
    return tuple(group.id for group in server_groups if group.type == 2)


@pytest.fixture(scope="session")
def template_server_group_ids(server_groups):
    return tuple(group.id for group in server_groups if group.type == 0)


@pytest.fixture(scope="session")
def regular_channel_group_ids(channel_groups):
    return tuple(group.id for group in channel_groups if group.type == 1)


@pytest.fixture(scope="session")
def template_channel_group_ids(channel_groups):
    return tuple(group.id for group in channel_groups if group.type == 0)


@pytest.fixture(scope="session")
def bot_client(server):
    client = _open_client(server)
    yield client
    client.disconnect()


@pytest.fixture
def fresh_query(server):
    connection = open_used_query(server.host, server.query_port, server.server_port, server.password)
    yield connection
    connection.exit()


@pytest.fixture
def fresh_client(server):
    client = _open_client(server)
    client.start_polling(0.05)
    yield client
    client.disconnect()


def _integration_enabled(config):
    return (
        os.getenv("TS3_INTEGRATION") == "1"
        and bool(os.getenv("QUERY_ADMIN_PASSWORD"))
        and not config.getvalue("collectonly")
    )


def _is_xdist_controller(config):
    return getattr(config.option, "dist", "no") != "no" and not hasattr(config, "workerinput")


def _start_server(password):
    container = None
    try:
        if _env("TS3_MANAGE_CONTAINER", "0") == "1":
            container = start_container(_env("TS3_TEST_IMAGE", "teamspeak:3.13.9"), password)
            config = ServerConfig(
                host=container.host,
                query_port=container.query_port,
                server_port=int(_env("TS3_SERVER_PORT", "9987")),
                password=password,
            )
        else:
            config = ServerConfig(
                host=_env("TS3_QUERY_HOST", "127.0.0.1"),
                query_port=int(_env("TS3_QUERY_PORT", "10022")),
                server_port=int(_env("TS3_SERVER_PORT", "9987")),
                password=password,
            )

        _wait_for_ssh_port(config.host, config.query_port)
        if _env("TS3_SET_FLOOD_LIMITS", "1") == "1":
            configure_server_limits(config.host, config.query_port, config.password)
        return _ServerSession(config=config, container=container)
    except BaseException:
        if container is not None:
            container.stop()
        raise


def _env(name, default):
    return os.getenv(name, default)


def _dump_container_logs(container):
    try:
        Path(f"ts3-server-{worker_name()}.log").write_text(container.logs(), encoding="utf-8")
    except OSError:
        pass


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


def _connect_client(server):
    client = TS3Client(
        server.host,
        server.query_port,
        "serveradmin",
        server.password,
        timeout=5,
        accept_all_keys=True,
        use_system_host_keys=False,
    )
    try:
        client.query.disable_flood_protection()
    except Exception:
        client.disconnect()
        raise
    return client


def _open_client(server):
    return open_used_connection(
        lambda: _connect_client(server),
        close=lambda client: client.disconnect(),
        server_port=server.server_port,
        description="open the bot query connection",
    )
