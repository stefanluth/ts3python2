import pytest

from tests.support.integration import enable_text_receive, unique_name, wait_until
from ts3client.constants import NotifyRegisterType, TargetMode

pytestmark = pytest.mark.integration


def wait_for_message(query, text):
    return wait_until(
        lambda: next((message for message in query.unread_messages if message.content == text), None),
        timeout=15,
        message=f"did not receive message {text!r}",
    )


def test_send_server_message(bot_client, listener_query):
    enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_SERVER)
    text = unique_name("server-message")

    assert bot_client.send_server_message(text).error_id == 0

    message = wait_for_message(listener_query, text)
    assert message.source == TargetMode.SERVER
    assert message.target == 0
    assert message.invokerid == bot_client.id
    assert message.invokername == bot_client.name
    assert message.invokeruid == bot_client.unique_id


def test_send_channel_message(bot_client, listener_query):
    enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_CHANNEL, channel_id=0)
    text = unique_name("channel-message")

    assert bot_client.send_channel_message(text).error_id == 0

    message = wait_for_message(listener_query, text)
    assert message.source == TargetMode.CHANNEL
    assert message.target == 0


def test_send_private_message(bot_client, listener_query):
    enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_PRIVATE)
    clid = listener_query.commands.whoami().data[0]["client_id"]
    text = unique_name("private-message")

    assert bot_client.send_private_message(clid, text).error_id == 0

    message = wait_for_message(listener_query, text)
    assert message.source == TargetMode.CLIENT
    assert message.target == clid


def test_send_message_supports_explicit_server_target_mode(bot_client, listener_query):
    enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_SERVER)
    text = unique_name("explicit-server-target")

    assert bot_client.send_message(0, TargetMode.SERVER, text).error_id == 0

    message = wait_for_message(listener_query, text)
    assert message.source == TargetMode.SERVER
    assert message.target == 0
    assert message.invokerid == bot_client.id
    assert message.invokername == bot_client.name
    assert message.invokeruid == bot_client.unique_id


def test_send_message_supports_explicit_channel_target_mode(bot_client, listener_query):
    enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_CHANNEL, channel_id=0)
    text = unique_name("explicit-channel-target")

    assert bot_client.send_message(0, TargetMode.CHANNEL, text).error_id == 0

    message = wait_for_message(listener_query, text)
    assert message.source == TargetMode.CHANNEL
    assert message.target == 0


def test_marked_message_leaves_the_unread_list(bot_client, listener_query):
    enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_SERVER)
    text = unique_name("used-message")

    bot_client.send_message(0, TargetMode.SERVER, text)
    message = wait_for_message(listener_query, text)

    assert message in listener_query.messages
    assert message in listener_query.unread_messages

    message.mark_as_used()

    assert message not in listener_query.unread_messages


def test_message_text_round_trips_special_characters(bot_client, listener_query):
    enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_SERVER)
    text = unique_name("special") + " spaces | pipe / slash \\ backslash"

    assert bot_client.send_message(0, TargetMode.SERVER, text).error_id == 0

    assert wait_for_message(listener_query, text).content == text
