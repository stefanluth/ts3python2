import pytest

from tests.support.integration import (
    channel_create,
    channel_delete,
    open_used_query,
    unique_name,
    wait_until,
    whoami,
)
from ts3client.constants import EventType, TargetMode

pytestmark = pytest.mark.integration


def test_server_text_message_delivery(bot_client, trigger_query):
    bot_client.enable_message_events()
    text = unique_name("server-message")

    trigger_query.commands.sendtextmessage(targetmode=TargetMode.SERVER, target=0, msg=text)

    wait_until(
        lambda: any(message.content == text for message in bot_client.get_unread_messages()),
        message="bot did not receive server text",
    )


def test_private_text_message_delivery(bot_client, trigger_query):
    bot_client.enable_message_events()
    bot_clid = whoami(bot_client.query)["client_id"]
    text = unique_name("private-message")

    trigger_query.commands.sendtextmessage(targetmode=TargetMode.CLIENT, target=bot_clid, msg=text)

    wait_until(
        lambda: any(message.content == text for message in bot_client.get_unread_messages()),
        message="bot did not receive private text",
    )


def test_channel_text_message_delivery(bot_client, trigger_query, used_query):
    bot_client.enable_message_events()
    bot_clid = whoami(bot_client.query)["client_id"]
    trigger_clid = whoami(trigger_query)["client_id"]
    cid = channel_create(used_query, unique_name("text-channel"))
    try:
        assert used_query.commands.clientmove(clid=bot_clid, cid=cid).error_id == 0
        assert used_query.commands.clientmove(clid=trigger_clid, cid=cid).error_id == 0
        text = unique_name("channel-message")

        trigger_query.commands.sendtextmessage(targetmode=TargetMode.CHANNEL, target=0, msg=text)

        wait_until(
            lambda: any(message.content == text for message in bot_client.get_unread_messages()),
            message="bot did not receive channel text",
        )
    finally:
        channel_delete(used_query, cid)


def test_channel_created_event(bot_client, used_query):
    bot_client.enable_events_and_messages()
    name = unique_name("event-channel")
    cid = channel_create(used_query, name)
    try:
        wait_until(
            lambda: any(
                event.event_type == EventType.CHANNEL_CREATED and getattr(event, "cid", None) == cid
                for event in bot_client.get_events()
            ),
            message="bot did not receive channel created event",
        )
    finally:
        channel_delete(used_query, cid)


def test_channel_deleted_event(bot_client, used_query):
    bot_client.enable_events_and_messages()
    cid = channel_create(used_query, unique_name("deleted-channel"))

    channel_delete(used_query, cid)

    wait_until(
        lambda: any(
            event.event_type == EventType.CHANNEL_DELETED and getattr(event, "cid", None) == cid
            for event in bot_client.get_events()
        ),
        message="bot did not receive channel deleted event",
    )


def test_channel_edited_event(bot_client, used_query):
    bot_client.enable_events_and_messages()
    cid = channel_create(used_query, unique_name("edited-channel"))
    try:
        topic = unique_name("edited-topic")
        assert used_query.commands.channeledit(cid=cid, channel_topic=topic).error_id == 0

        wait_until(
            lambda: any(
                event.event_type == EventType.CHANNEL_EDITED and getattr(event, "cid", None) == cid
                for event in bot_client.get_events()
            ),
            message="bot did not receive channel edited event",
        )
    finally:
        channel_delete(used_query, cid)


def test_channel_moved_event(bot_client, used_query):
    bot_client.enable_events_and_messages()
    parent = channel_create(used_query, unique_name("parent-channel"))
    child = channel_create(used_query, unique_name("child-channel"))
    try:
        assert used_query.commands.channelmove(cid=child, cpid=parent, order=0).error_id == 0

        wait_until(
            lambda: any(
                event.event_type == EventType.CHANNEL_MOVED and getattr(event, "cid", None) == child
                for event in bot_client.get_events()
            ),
            message="bot did not receive channel moved event",
        )
    finally:
        channel_delete(used_query, child)
        channel_delete(used_query, parent)


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


def test_used_event_leaves_the_unread_list(bot_client, used_query):
    bot_client.enable_events_and_messages()
    cid = channel_create(used_query, unique_name("unread-event-channel"))
    try:
        event = wait_until(
            lambda: next(
                (
                    event
                    for event in bot_client.get_unread_events()
                    if event.event_type == EventType.CHANNEL_CREATED and getattr(event, "cid", None) == cid
                ),
                None,
            ),
            message="bot did not receive channel created event",
        )

        assert event in bot_client.get_events()

        event.used = True

        assert event not in bot_client.get_unread_events()
    finally:
        channel_delete(used_query, cid)
