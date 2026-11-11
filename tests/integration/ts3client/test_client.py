import pytest

from tests.support.integration import channel_create, channel_delete, unique_name
from ts3client.ts3client_response import TS3ClientResponse

pytestmark = pytest.mark.integration


def test_whoami_returns_client(bot_client):
    data = bot_client.whoami()

    assert data.get("client_id") is not None
    assert data.get("client_nickname")


def test_get_users_contains_bot(bot_client):
    current = bot_client.whoami()["client_id"]

    users = bot_client.get_users()

    assert any(user.clid == current for user in users)


def test_client_identity_properties_match_whoami(bot_client):
    current = bot_client.whoami()

    assert bot_client.name == current["client_nickname"]
    assert bot_client.id == current["client_id"]
    assert bot_client.unique_id == current["client_unique_identifier"]
    assert bot_client.database_id == current["client_database_id"]


def test_server_properties_match_the_selected_server(bot_client, server):
    assert bot_client.server_id
    assert bot_client.server_unique_id
    assert bot_client.server_name
    assert bot_client.server_port == server.server_port


def test_set_name_and_description(fresh_client):
    name = unique_name("client")
    description = unique_name("description")

    assert fresh_client.set_name(name).error_id == 0
    assert fresh_client.name == name
    assert fresh_client.set_name(name) is None
    assert fresh_client.set_description(description).error_id == 0
    assert fresh_client.get_user_info(fresh_client.id).client_description == description


def test_get_user_info_and_set_user_description(bot_client, fresh_client):
    info = bot_client.get_user_info(fresh_client.id)

    assert info.client_nickname == fresh_client.name

    description = unique_name("user-description")
    assert bot_client.set_user_description(fresh_client.id, description).error_id == 0

    assert bot_client.get_user_info(fresh_client.id).client_description == description


def test_find_users_finds_a_connected_client(bot_client, fresh_client):
    found = bot_client.find_users(fresh_client.name)

    assert any(user.clid == fresh_client.id for user in found)


@pytest.mark.bug
def test_rename_user(fresh_client):
    name = unique_name("renamed")

    assert fresh_client.rename_user(fresh_client.id, name).error_id == 0
    assert fresh_client.name == name


def test_move_user_to_created_channel(bot_client, used_query, fresh_client):
    name = unique_name("move-channel")
    cid = channel_create(used_query, name)
    try:
        assert bot_client.move_user(fresh_client.id, cid).error_id == 0

        assert bot_client.get_user_info(fresh_client.id).cid == cid
        channel = next(channel for channel in bot_client.get_channels() if channel.cid == cid)
        assert channel.channel_name == name
    finally:
        channel_delete(used_query, cid)


def test_get_channel_info(bot_client, used_query):
    name = unique_name("channel-info")
    cid = channel_create(used_query, name)
    try:
        info = bot_client.get_channel_info(cid)

        assert info.channel_name == name
    finally:
        channel_delete(used_query, cid)


def test_select_server_by_port(fresh_client, server):
    fresh_client.select_server_by_port(server.server_port)

    assert fresh_client.server_port == server.server_port


def test_select_server_by_id(fresh_client, used_query, server):
    sid = used_query.commands.serveridgetbyport(virtualserver_port=server.server_port).data[0]["server_id"]

    fresh_client.select_server(sid)

    assert fresh_client.server_port == server.server_port


def test_find_channel_returns_all_matches(bot_client):
    prefix = unique_name("find")
    first = channel_create(bot_client.query, f"{prefix}-a")
    second = channel_create(bot_client.query, f"{prefix}-b")
    try:
        result = bot_client.find_channel(prefix)

        assert isinstance(result, list)
        assert {channel.cid for channel in result} == {first, second}
    finally:
        channel_delete(bot_client.query, first)
        channel_delete(bot_client.query, second)


def test_bindinglist_default(used_query):
    response = used_query.commands.bindinglist()

    assert response.error_id == 0


@pytest.mark.bug
def test_empty_response_exposes_msg(used_query):
    response = TS3ClientResponse(used_query.commands.clientupdate(client_nickname=unique_name("query")))

    assert response.get("msg") == "ok"
