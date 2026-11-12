import pytest

import plugins.commands.help as help_module
from tests.support.integration import (
    drain_messages,
    enable_text_receive,
    running_plugins,
    send_text,
    wait_for_message,
)
from ts3client.constants import NotifyRegisterType

pytestmark = pytest.mark.integration


def test_help_lists_configured_commands_and_descriptions(monkeypatch, fresh_client, fresh_query):
    config = command_config(
        {
            "Help": {"trigger": "help", "description": "Show help."},
            "Weather": {"trigger": "weather", "api_key": "test-key"},
        }
    )
    monkeypatch.setattr(help_module, "PLUGINS_CONFIG", {"CommandHandler": config})

    with run_command_handler(fresh_client, config):
        enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
        drain_messages(fresh_query)
        send_text(fresh_query, "!help")

        reply = wait_for_message(fresh_query, "Available commands", contains=True)

    assert "!help - Show help." in reply.content
    assert "!weather - No description available." in reply.content


def command_config(commands, prefix="!", check_interval=1):
    return {"prefix": prefix, "check_interval": check_interval, "commands": commands}


def run_command_handler(fresh_client, config):
    return running_plugins(fresh_client, {"CommandHandler": config})
