import pytest

import tests.support.integration as integration
from tests.support.fakes import FakeCommands, FakeQuery, FakeResponse


def test_configure_server_limits_applies_and_verifies_query_limits(monkeypatch):
    commands = FakeCommands()
    commands.responses["instanceedit"] = FakeResponse()
    commands.responses["instanceinfo"] = FakeResponse(
        data={
            0: {
                "serverinstance_serverquery_max_connections_per_ip": str(integration.QUERY_MAX_CONNECTIONS_PER_IP),
                "serverinstance_pending_connections_per_ip": str(integration.QUERY_PENDING_CONNECTIONS_PER_IP),
            }
        }
    )
    query = FakeQuery(commands)
    constructed = []

    def fake_query(*args, **kwargs):
        constructed.append((args, kwargs))
        return query

    monkeypatch.setattr(integration, "TS3Query", fake_query)

    integration.configure_server_limits("host", 10022, "secret", retries=1)

    assert constructed == [
        (
            ("host", 10022, "serveradmin", "secret"),
            {"timeout": 5, "accept_all_keys": True},
        )
    ]
    edits = commands.called("instanceedit")
    assert len(edits) == 1
    _, _, kwargs = edits[0]
    assert kwargs["serverinstance_serverquery_max_connections_per_ip"] == integration.QUERY_MAX_CONNECTIONS_PER_IP
    assert kwargs["serverinstance_pending_connections_per_ip"] == integration.QUERY_PENDING_CONNECTIONS_PER_IP
    assert commands.called("instanceinfo")
    assert query.exit_calls == 1


def test_configure_server_limits_raises_when_limits_are_not_applied(monkeypatch):
    commands = FakeCommands()
    commands.responses["instanceedit"] = FakeResponse()
    commands.responses["instanceinfo"] = FakeResponse(
        data={
            0: {
                "serverinstance_serverquery_max_connections_per_ip": "5",
                "serverinstance_pending_connections_per_ip": "5",
            }
        }
    )
    query = FakeQuery(commands)
    monkeypatch.setattr(integration, "TS3Query", lambda *args, **kwargs: query)

    with pytest.raises(AssertionError, match="did not apply"):
        integration.configure_server_limits("host", 10022, "secret", retries=1)

    assert query.exit_calls == 1
