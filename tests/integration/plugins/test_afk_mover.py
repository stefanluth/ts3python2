import pytest

from tests.support.integration import (
    channel_create,
    channel_delete,
    register_text_receive,
    running_plugins,
    unique_name,
    wait_until,
    whoami,
)
from ts3client.constants import NotifyRegisterType

pytestmark = pytest.mark.integration


def test_afk_mover_moves_an_idle_client_to_the_afk_channel(bot_client, used_query, fresh_query):
    afk_cid = channel_create(used_query, unique_name("afk-channel"))
    waiting_cid = channel_create(used_query, unique_name("waiting-channel"))
    target_clid = whoami(fresh_query)["client_id"]
    move_message = unique_name("afk-move")
    try:
        assert used_query.commands.clientmove(clid=target_clid, cid=waiting_cid).error_id == 0
        register_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)

        ignore_channels = [channel.cid for channel in bot_client.get_channels() if channel.cid != waiting_cid]

        with running_plugins(
            bot_client,
            {
                "AFK_Mover": {
                    "afk_channel_id": afk_cid,
                    "afk_time": 0,
                    "check_interval": 1,
                    "ignore_channels": ignore_channels,
                    "move_message": move_message,
                }
            },
        ):
            wait_until(
                lambda: used_query.commands.clientinfo(clid=target_clid).data[0]["cid"] == afk_cid,
                timeout=15,
                message="AFK_Mover did not move the idle client",
            )

            def has_move_message():
                fresh_query.commands.version()
                return any(message.content == move_message for message in fresh_query.unread_messages)

            wait_until(
                has_move_message,
                timeout=15,
                interval=0.5,
                message="AFK_Mover did not send the move message",
            )
    finally:
        channel_delete(used_query, afk_cid)
        channel_delete(used_query, waiting_cid)
