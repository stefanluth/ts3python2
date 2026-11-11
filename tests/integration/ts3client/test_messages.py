import pytest

from tests.support.integration import enable_text_receive, unique_name, wait_for_message
from ts3client.constants import NotifyRegisterType, TargetMode

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("kind", "event", "channel_id", "source"),
    [
        ("server", NotifyRegisterType.TEXT_SERVER, None, TargetMode.SERVER),
        ("channel", NotifyRegisterType.TEXT_CHANNEL, 0, TargetMode.CHANNEL),
        ("private", NotifyRegisterType.TEXT_PRIVATE, None, TargetMode.CLIENT),
    ],
    ids=["server", "channel", "private"],
)
def test_send_message(bot_client, fresh_query, kind, event, channel_id, source):
    enable_text_receive(fresh_query, event=event, channel_id=channel_id)
    text = unique_name(f"{kind}-message")

    assert send_message(bot_client, fresh_query, kind, text).error_id == 0

    message = wait_for_message(fresh_query, text)
    assert message.source == source
    assert message.target == expected_target(fresh_query, kind)
    assert message.invokerid == bot_client.id
    assert message.invokername == bot_client.name
    assert message.invokeruid == bot_client.unique_id


def send_message(client, query, kind, text):
    if kind == "server":
        return client.send_server_message(text)
    if kind == "channel":
        return client.send_channel_message(text)
    return client.send_private_message(query.commands.whoami().data[0]["client_id"], text)


def expected_target(query, kind):
    if kind == "private":
        return query.commands.whoami().data[0]["client_id"]
    return 0
