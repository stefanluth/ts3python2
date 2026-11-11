import pytest

from tests.support.integration import channel_create, channel_delete, unique_name
from ts3client.errors import TS3Error
from ts3client.ts3client_response import TS3ClientResponse

pytestmark = pytest.mark.integration


def test_help_returns_command_text(used_query):
    response = used_query.commands.help()

    assert response.error_id == 0
    assert "help" in response.data["help"].lower()


def test_version_returns_server_version(used_query):
    response = used_query.commands.version()

    assert response.error_id == 0
    assert response.data[0]["version"]
    assert response.data[0]["platform"]


def test_hostinfo_and_instanceinfo(used_query):
    host = used_query.commands.hostinfo()
    instance = used_query.commands.instanceinfo()

    assert host.error_id == 0
    assert host.data[0]
    assert instance.error_id == 0
    assert instance.data[0]


def test_serverlist_contains_the_selected_server(used_query, server):
    response = used_query.commands.serverlist()

    assert response.error_id == 0
    assert any(row.get("virtualserver_port") == server.server_port for row in response.data.values())


def test_serveridgetbyport_matches_the_selected_server(used_query, server):
    response = used_query.commands.serveridgetbyport(virtualserver_port=server.server_port)

    assert response.error_id == 0
    assert response.data[0]["server_id"]


def test_serverrequestconnectioninfo(used_query):
    response = used_query.commands.serverrequestconnectioninfo()

    assert response.error_id == 0
    assert response.data[0]


def test_clientinfo_matches_whoami(used_query):
    current = used_query.commands.whoami().data[0]

    info = used_query.commands.clientinfo(clid=current["client_id"])

    assert info.error_id == 0
    assert info.data[0]["client_nickname"] == current["client_nickname"]


def test_clientdblist_and_clientdbinfo_agree(used_query):
    dblist = used_query.commands.clientdblist()

    assert dblist.error_id == 0
    assert dblist.data

    first = dblist.data[0]
    db_info = used_query.commands.clientdbinfo(cldbid=first["cldbid"])

    assert db_info.error_id == 0
    assert db_info.data[0]["client_nickname"] == first["client_nickname"]


def test_servergroupsbyclientid_returns_groups(used_query):
    current = used_query.commands.whoami().data[0]

    response = used_query.commands.servergroupsbyclientid(cldbid=current["client_database_id"])

    assert response.error_id == 0
    assert response.data


def test_channelgrouplist_returns_groups(used_query):
    response = used_query.commands.channelgrouplist()

    assert response.error_id == 0
    assert response.data


def test_permissionlist_and_permidgetbyname(used_query):
    permissions = used_query.commands.permissionlist()

    assert permissions.error_id == 0
    assert permissions.data

    first = permissions.data[0]
    response = used_query.commands.permidgetbyname(permsid=first["permname"])

    assert response.error_id == 0
    assert response.data[0]["permid"] == first["permid"]


def test_invalid_client_raises_ts3_error(used_query):
    with pytest.raises(TS3Error) as error:
        TS3ClientResponse(used_query.commands.clientinfo(clid=999999999))

    assert error.value.id != 0


def test_invalid_channel_raises_ts3_error(used_query):
    with pytest.raises(TS3Error) as error:
        TS3ClientResponse(used_query.commands.channelinfo(cid=999999999))

    assert error.value.id != 0


def test_channel_topic_round_trips_escaped_characters(used_query):
    name = unique_name("escape")
    topic = "spaces and | pipe / slash \\ backslash"
    cid = channel_create(used_query, name)
    try:
        response = used_query.commands.channeledit(cid=cid, channel_topic=topic)
        info = used_query.commands.channelinfo(cid=cid)

        assert response.error_id == 0
        assert info.data[0]["channel_topic"] == topic
    finally:
        channel_delete(used_query, cid)
