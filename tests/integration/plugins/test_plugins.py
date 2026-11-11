import pytest

from plugins.plugin_manager import PluginManager
from tests.support.integration import enable_text_receive, wait_until
from ts3client.constants import NotifyRegisterType, TargetMode

pytestmark = pytest.mark.integration

COMMAND_CONFIG = {
    "CommandHandler": {
        "prefix": "!",
        "check_interval": 1,
        "commands": {"Help": {"trigger": "help", "description": "Send help."}},
    }
}


def start_command_handler(bot_client):
    manager = PluginManager(bot_client, COMMAND_CONFIG)
    manager.run()
    wait_until(
        lambda: any(thread.is_alive() for thread, _ in manager.threads.values()),
        message="command handler did not start",
    )
    return manager


def mark_existing_messages_used(query):
    for message in query.unread_messages:
        message.mark_as_used()


def wait_for_help_reply(listener_query):
    return wait_until(
        lambda: next(
            (message for message in listener_query.unread_messages if "Available commands" in message.content),
            None,
        ),
        timeout=15,
        message="bot did not send the help reply",
    )


def test_plugin_manager_runs_command_handler_end_to_end(bot_client, listener_query):
    manager = start_command_handler(bot_client)
    try:
        enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_PRIVATE)
        mark_existing_messages_used(listener_query)

        listener_query.commands.sendtextmessage(targetmode=TargetMode.SERVER, target=0, msg="!help")

        assert wait_for_help_reply(listener_query)
    finally:
        manager.stop(timeout=5)

    assert all(not thread.is_alive() for thread, _ in manager.threads.values())


def test_command_handler_survives_an_unknown_trigger(bot_client, listener_query):
    manager = start_command_handler(bot_client)
    try:
        enable_text_receive(listener_query, event=NotifyRegisterType.TEXT_PRIVATE)
        mark_existing_messages_used(listener_query)

        listener_query.commands.sendtextmessage(targetmode=TargetMode.SERVER, target=0, msg="!unknown")
        listener_query.commands.sendtextmessage(targetmode=TargetMode.SERVER, target=0, msg="!help")

        assert wait_for_help_reply(listener_query)
    finally:
        manager.stop(timeout=5)
