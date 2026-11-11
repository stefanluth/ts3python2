import pytest

from tests.support.integration import retry
from ts3client.ts3query import TS3Query

pytestmark = pytest.mark.integration


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
    return retry(
        lambda: make_query(server, **kwargs),
        retries=retries,
        description="open an SSH query connection",
    )
