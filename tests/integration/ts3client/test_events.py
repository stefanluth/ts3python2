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


def create_and_change_description(used_query):
    cid = channel_create(used_query, unique_name("described-channel"))
    assert used_query.commands.channeledit(cid=cid, channel_description=unique_name("description")).error_id == 0
    return cid, [cid]


def create_and_change_password(used_query):
    cid = channel_create(used_query, unique_name("password-channel"))
    assert used_query.commands.channeledit(cid=cid, channel_password="integration-password").error_id == 0
    return cid, [cid]


@pytest.mark.parametrize(
    ("scenario", "event_type"),
    [
        (create_only, EventType.CHANNEL_CREATED),
        (create_and_delete, EventType.CHANNEL_DELETED),
        (create_and_edit, EventType.CHANNEL_EDITED),
        (create_and_move, EventType.CHANNEL_MOVED),
        (create_and_change_description, EventType.CHANNEL_DESCRIPTION_CHANGED),
        (create_and_change_password, EventType.CHANNEL_PASSWORD_CHANGED),
    ],
    ids=["created", "deleted", "edited", "moved", "description-changed", "password-changed"],
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


def test_channel_created_event_reports_parent_and_name(bot_client, used_query):
    bot_client.enable_events_and_messages()
    parent = channel_create(used_query, unique_name("created-parent"))
    name = unique_name("created-details")
    child = channel_create(used_query, name, cpid=parent)
    try:
        event = wait_until(
            lambda: next(
                (
                    event
                    for event in bot_client.get_events()
                    if event.event_type == EventType.CHANNEL_CREATED and getattr(event, "cid", None) == child
                ),
                None,
            ),
            message="bot did not receive channel created event",
        )

        assert event.cpid == parent
        assert event.channel_name == name
    finally:
        channel_delete(used_query, child)
        channel_delete(used_query, parent)


def test_channel_edited_event_reports_topic(bot_client, used_query):
    bot_client.enable_events_and_messages()
    cid = channel_create(used_query, unique_name("edited-topic-channel"))
    topic = unique_name("edited-topic")
    try:
        assert used_query.commands.channeledit(cid=cid, channel_topic=topic).error_id == 0
        event = wait_until(
            lambda: next(
                (
                    event
                    for event in bot_client.get_events()
                    if event.event_type == EventType.CHANNEL_EDITED and getattr(event, "cid", None) == cid
                ),
                None,
            ),
            message="bot did not receive channel edited event",
        )

        assert event.channel_topic == topic
    finally:
        channel_delete(used_query, cid)


def test_server_edited_event_reports_name(bot_client, used_query):
    bot_client.enable_events_and_messages()
    before = used_query.commands.serverinfo().data[0]["virtualserver_name"]
    name = unique_name("server-name")
    try:
        assert used_query.commands.serveredit(virtualserver_name=name).error_id == 0
        event = wait_until(
            lambda: next(
                (
                    event
                    for event in bot_client.get_events()
                    if event.event_type == EventType.SERVER_EDITED
                    and getattr(event, "virtualserver_name", None) == name
                ),
                None,
            ),
            message="bot did not receive server edited event",
        )

        assert event.virtualserver_name == name
    finally:
        used_query.commands.serveredit(virtualserver_name=before)


@pytest.mark.skip(reason="server query clients cannot use privilege keys (error 516)")
def test_token_used_event_reports_token(bot_client, used_query, server, regular_server_group_ids):
    bot_client.enable_events_and_messages()
    group = regular_server_group_ids[0]
    response = used_query.commands.tokenadd(
        tokentype=0,
        tokenid1=group,
        tokenid2=0,
        tokendescription=unique_name("token-event"),
    )
    assert response.error_id == 0, response
    token = response.data[0]["token"]
    query = open_used_query(server.host, server.query_port, server.server_port, server.password)
    try:
        assert query.commands.tokenuse(token=token).error_id == 0
        event = wait_until(
            lambda: next(
                (
                    event
                    for event in bot_client.get_events()
                    if event.event_type == EventType.TOKEN_USED and getattr(event, "token", None) == token
                ),
                None,
            ),
            message="bot did not receive token used event",
        )

        assert event.token == token
    finally:
        query.exit()
        used_query.commands.tokendelete(token=token)
