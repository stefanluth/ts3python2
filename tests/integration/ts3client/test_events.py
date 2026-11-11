import pytest

from tests.support.integration import (
    channel_create,
    channel_delete,
    open_used_query,
    unique_name,
    wait_until,
    whoami,
)
from ts3client.constants import EventType

pytestmark = pytest.mark.integration


def create_only(used_query):
    cid = channel_create(used_query, unique_name("event-channel"))
    return cid, [cid]


def create_and_delete(used_query):
    cid = channel_create(used_query, unique_name("deleted-channel"))
    channel_delete(used_query, cid)
    return cid, []


def create_and_edit(used_query):
    cid = channel_create(used_query, unique_name("edited-channel"))
    topic = unique_name("edited-topic")
    assert used_query.commands.channeledit(cid=cid, channel_topic=topic).error_id == 0
    return cid, [cid]


def create_and_move(used_query):
    parent = channel_create(used_query, unique_name("parent-channel"))
    child = channel_create(used_query, unique_name("child-channel"))
    assert used_query.commands.channelmove(cid=child, cpid=parent, order=0).error_id == 0
    return child, [child, parent]


@pytest.mark.parametrize(
    ("scenario", "event_type"),
    [
        (create_only, EventType.CHANNEL_CREATED),
        (create_and_delete, EventType.CHANNEL_DELETED),
        (create_and_edit, EventType.CHANNEL_EDITED),
        (create_and_move, EventType.CHANNEL_MOVED),
    ],
    ids=["created", "deleted", "edited", "moved"],
)
def test_channel_events(bot_client, used_query, scenario, event_type):
    bot_client.enable_events_and_messages()
    cid, cleanup = scenario(used_query)
    try:
        wait_until(
            lambda: any(
                event.event_type == event_type and getattr(event, "cid", None) == cid
                for event in bot_client.get_events()
            ),
            message=f"bot did not receive {event_type.name.lower()} event",
        )
    finally:
        for channel_cid in cleanup:
            channel_delete(used_query, channel_cid)


def test_client_moved_event(bot_client, used_query, fresh_query):
    bot_client.enable_events_and_messages()
    clid = whoami(fresh_query)["client_id"]
    cid = channel_create(used_query, unique_name("client-moved-channel"))
    try:
        assert used_query.commands.clientmove(clid=clid, cid=cid).error_id == 0

        wait_until(
            lambda: any(
                event.event_type == EventType.CLIENT_MOVED
                and getattr(event, "clid", None) == clid
                and getattr(event, "ctid", None) == cid
                for event in bot_client.get_events()
            ),
            message="bot did not receive client moved event",
        )
    finally:
        channel_delete(used_query, cid)


def test_client_enter_and_left_view_events(bot_client, server):
    bot_client.enable_events_and_messages()
    query = open_used_query(server.host, server.query_port, server.server_port, server.password)
    try:
        clid = whoami(query)["client_id"]
        wait_until(
            lambda: any(
                event.event_type == EventType.CLIENT_ENTER_VIEW and getattr(event, "clid", None) == clid
                for event in bot_client.get_events()
            ),
            message="bot did not receive client enter view event",
        )

        assert any(event.clid == clid for event in bot_client.get_user_entered_events())
    finally:
        query.exit()

    wait_until(
        lambda: any(
            event.event_type == EventType.CLIENT_LEFT_VIEW and getattr(event, "clid", None) == clid
            for event in bot_client.get_events()
        ),
        message="bot did not receive client left view event",
    )
