import pytest

from tests.support.integration import channel_create, channel_delete, unique_name

pytestmark = pytest.mark.integration


def test_set_name_and_descriptions(bot_client, fresh_client):
    name = unique_name("client")

    assert fresh_client.set_name(name).error_id == 0
    assert fresh_client.name == name
    assert fresh_client.set_name(name) is None

    renamed = unique_name("renamed")
    assert fresh_client.rename_user(fresh_client.id, renamed).error_id == 0
    assert fresh_client.name == renamed

    own_description = unique_name("description")
    assert fresh_client.set_description(own_description).error_id == 0
    assert fresh_client.get_user_info(fresh_client.id).client_description == own_description

    info = bot_client.get_user_info(fresh_client.id)
    assert info.client_nickname == fresh_client.name

    other_description = unique_name("user-description")
    assert bot_client.set_user_description(fresh_client.id, other_description).error_id == 0
    assert bot_client.get_user_info(fresh_client.id).client_description == other_description


def test_find_users_finds_a_connected_client(bot_client, fresh_client):
    found = bot_client.find_users(fresh_client.name)

    assert {user.clid for user in found} == {fresh_client.id}


def test_move_user_to_created_channel(bot_client, used_query, fresh_client):
    name = unique_name("move-channel")
    cid = channel_create(used_query, name)
    try:
        assert bot_client.move_user(fresh_client.id, cid).error_id == 0

        assert bot_client.get_user_info(fresh_client.id).cid == cid
        channel = next(channel for channel in bot_client.get_channels() if channel.cid == cid)
        assert channel.channel_name == name
        assert bot_client.get_channel_info(cid).channel_name == name
    finally:
        channel_delete(used_query, cid)


def test_find_channel_returns_all_matches(bot_client):
    prefix = unique_name("find")
    first = channel_create(bot_client.query, f"{prefix}-a")
    second = channel_create(bot_client.query, f"{prefix}-b")
    try:
        result = bot_client.find_channel(prefix)

        assert {channel.cid for channel in result} == {first, second}
    finally:
        channel_delete(bot_client.query, first)
        channel_delete(bot_client.query, second)
