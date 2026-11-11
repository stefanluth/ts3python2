import time

import paramiko
import pytest

from ts3client.ts3query import TS3Query

pytestmark = pytest.mark.integration


def make_query(server, **kwargs):
    return TS3Query(
        server.host,
        server.query_port,
        "serveradmin",
        server.password,
        timeout=5,
        **kwargs,
    )


def open_ssh_query(server, retries=3, **kwargs):
    last_error = None
    for attempt in range(retries):
        try:
            return make_query(server, **kwargs)
        except (paramiko.SSHException, EOFError, ConnectionError, OSError) as error:
            last_error = error
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise AssertionError(f"could not open an SSH query connection: {last_error}")


def test_known_hosts_is_saved_and_reused(server, tmp_path):
    known_hosts = tmp_path / "known_hosts"

    first = open_ssh_query(
        server,
        accept_all_keys=True,
        use_system_host_keys=False,
        known_hosts=str(known_hosts),
    )
    try:
        assert first.connected()
    finally:
        first.exit()

    assert known_hosts.exists()
    assert known_hosts.read_text().strip()

    second = open_ssh_query(
        server,
        accept_all_keys=False,
        use_system_host_keys=False,
        known_hosts=str(known_hosts),
    )
    try:
        assert second.connected()
    finally:
        second.exit()


def test_connected_reflects_exit(server):
    query = open_ssh_query(server, accept_all_keys=True, use_system_host_keys=False)

    assert query.connected()

    query.exit()

    assert not query.connected()


def test_reconnect_after_exit(server):
    first = open_ssh_query(server, accept_all_keys=True, use_system_host_keys=False)
    first.exit()

    second = open_ssh_query(server, accept_all_keys=True, use_system_host_keys=False)
    try:
        assert second.connected()
    finally:
        second.exit()


def test_unknown_host_key_is_rejected(server, tmp_path):
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text("")

    with pytest.raises(paramiko.SSHException):
        make_query(
            server,
            accept_all_keys=False,
            use_system_host_keys=False,
            known_hosts=str(known_hosts),
        )
