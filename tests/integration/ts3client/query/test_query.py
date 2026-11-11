import paramiko
import pytest

from tests.support.integration import channel_create, channel_delete, unique_name
from ts3client.constants import NotifyRegisterType
from ts3client.ts3query import TS3Query

pytestmark = pytest.mark.integration


def test_construct_authenticates_over_ssh(server):
    connection = TS3Query(
        server.host,
        server.query_port,
        "serveradmin",
        server.password,
        timeout=5,
        accept_all_keys=True,
    )
    try:
        assert connection.connected()
    finally:
        connection.exit()


def test_wrong_password_raises_authentication_error(server):
    with pytest.raises(paramiko.AuthenticationException):
        TS3Query(
            server.host,
            server.query_port,
            "serveradmin",
            "wrong_password",
            timeout=5,
            accept_all_keys=True,
        )


def test_use_selects_server(used_query, server):
    response = used_query.commands.serverinfo()
    assert response.error_id == 0, response
    assert response.data[0]["virtualserver_port"] == server.server_port


def test_clientlist_contains_current_query(used_query):
    current = used_query.commands.whoami().data[0]
    response = used_query.commands.clientlist()
    assert response.error_id == 0, response
    clids = [row["clid"] for row in response.data.values()]
    assert current["client_id"] in clids


def test_channel_create_list_delete(used_query):
    name = unique_name("channel")
    cid = channel_create(used_query, name)
    try:
        listing = used_query.commands.channellist()
        assert any(row["cid"] == cid for row in listing.data.values())
    finally:
        channel_delete(used_query, cid)


def test_register_events_after_use(used_query):
    response = used_query.commands.servernotifyregister(event=NotifyRegisterType.SERVER)
    assert response.error_id == 0, response
    used_query.commands.servernotifyunregister()


def test_disable_events(bot_client):
    bot_client.enable_events_and_messages()
    bot_client.disable_events_and_messages()
