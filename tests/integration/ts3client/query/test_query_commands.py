import pytest

from tests.support.integration import channel_create, channel_delete, unique_name

pytestmark = pytest.mark.integration


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


def test_uppercase_changeable_properties_are_normalized(used_query):
    cid = channel_create(used_query, unique_name("uppercase"))
    topic = "uppercase | topic"
    try:
        response = used_query.commands.channeledit(cid=cid, CHANNEL_TOPIC=topic)

        assert response.error_id == 0
        assert used_query.commands.channelinfo(cid=cid).data[0]["channel_topic"] == topic
    finally:
        channel_delete(used_query, cid)


def test_instance_template_channel_group_is_accepted(used_query):
    instance = used_query.commands.instanceinfo().data[0]
    group = instance["serverinstance_template_channeldefault_group"]

    response = used_query.commands.instanceedit(serverinstance_template_channeldefault_group=group)

    assert response.error_id == 0
    assert used_query.commands.instanceinfo().data[0]["serverinstance_template_channeldefault_group"] == group
