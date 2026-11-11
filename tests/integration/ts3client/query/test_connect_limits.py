from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.support.integration import (
    QUERY_MAX_CONNECTIONS_PER_IP,
    QUERY_PENDING_CONNECTIONS_PER_IP,
    open_used_query,
)

pytestmark = pytest.mark.integration

CONCURRENT_CONNECTIONS = 8


def test_server_query_connection_limits_are_configured(used_query):
    info = used_query.commands.instanceinfo().data[0]

    assert int(info["serverinstance_serverquery_max_connections_per_ip"]) >= QUERY_MAX_CONNECTIONS_PER_IP
    assert int(info["serverinstance_pending_connections_per_ip"]) == QUERY_PENDING_CONNECTIONS_PER_IP


def test_server_allows_many_concurrent_query_connections(server):
    opened = []

    def connect():
        connection = open_used_query(server.host, server.query_port, server.server_port, server.password)
        opened.append(connection)
        return connection

    with ThreadPoolExecutor(max_workers=CONCURRENT_CONNECTIONS) as executor:
        futures = [executor.submit(connect) for _ in range(CONCURRENT_CONNECTIONS)]
        try:
            connections = [future.result() for future in futures]

            assert len(connections) == CONCURRENT_CONNECTIONS
            assert all(connection.connected() for connection in connections)
        finally:
            for connection in opened:
                connection.exit()
