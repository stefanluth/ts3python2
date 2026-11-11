import json
import types

import pytest

import plugins.commands.help as help_module
import plugins.plugins.command_handler as command_handler_module
from plugins.commands.help import Help
from tests.support.integration import (
    drain_messages,
    enable_text_receive,
    running_plugins,
    wait_for_private_message,
    wait_for_private_message_containing,
)
from ts3client.constants import NotifyRegisterType, TargetMode

pytestmark = pytest.mark.integration

WEATHER_PAYLOAD = {
    "location": {"name": "New York"},
    "current": {
        "condition": {"text": "Sunny"},
        "temp_c": 20,
        "feelslike_c": 19,
        "humidity": 50,
        "wind_kph": 10,
        "wind_dir": "N",
    },
}


class FakeHTTPResponse:
    def __init__(self, payload=WEATHER_PAYLOAD):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class RaisingCommand:
    def __init__(self, client, trigger, **kwargs):
        self.client = client
        self.trigger = trigger
        self.name = "RaisingCommand"

    def run(self, message):
        raise RuntimeError("command failed")


def command_config(commands, prefix="!", check_interval=1):
    return {"prefix": prefix, "check_interval": check_interval, "commands": commands}


def run_command_handler(fresh_client, config):
    return running_plugins(fresh_client, {"CommandHandler": config})


def send_command(fresh_query, content):
    fresh_query.commands.sendtextmessage(targetmode=TargetMode.SERVER, target=0, msg=content)


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
        send_command(fresh_query, "!help")

        reply = wait_for_private_message_containing(fresh_query, "Available commands")

    assert "!help - Show help." in reply.content
    assert "!weather - No description available." in reply.content


def test_weather_command_replies_with_the_current_weather(monkeypatch, fresh_client, fresh_query):
    monkeypatch.setattr("urllib.request.urlopen", lambda url, timeout=None: FakeHTTPResponse())
    config = command_config(
        {
            "Weather": {
                "trigger": "weather",
                "api_key": "test-key",
                "description": "Get the weather for a location.",
            }
        }
    )

    with run_command_handler(fresh_client, config):
        enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
        drain_messages(fresh_query)
        send_command(fresh_query, "!weather New York")

        wait_for_private_message(
            fresh_query,
            "Current weather for New York: Sunny, 20°C, feels like 19°C, humidity 50%, wind 10 kph, N.",
        )


def test_weather_command_prompts_for_a_location(monkeypatch, fresh_client, fresh_query):
    monkeypatch.setattr("urllib.request.urlopen", lambda url, timeout=None: FakeHTTPResponse())
    config = command_config(
        {
            "Weather": {
                "trigger": "weather",
                "api_key": "test-key",
                "description": "Get the weather for a location.",
            }
        }
    )

    with run_command_handler(fresh_client, config):
        enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
        drain_messages(fresh_query)
        send_command(fresh_query, "!weather")

        wait_for_private_message(fresh_query, "Please provide a location.")


def test_command_handler_keeps_running_after_a_command_fails(monkeypatch, fresh_client, fresh_query):
    namespace = types.SimpleNamespace(
        __all__=["Help", "RaisingCommand"],
        Help=Help,
        RaisingCommand=RaisingCommand,
    )
    monkeypatch.setattr(command_handler_module, "all_commands", namespace)

    config = command_config(
        {
            "RaisingCommand": {"trigger": "boom"},
            "Help": {"trigger": "help", "description": "Show help."},
        }
    )
    monkeypatch.setattr(help_module, "PLUGINS_CONFIG", {"CommandHandler": config})

    with run_command_handler(fresh_client, config):
        enable_text_receive(fresh_query, event=NotifyRegisterType.TEXT_PRIVATE)
        drain_messages(fresh_query)
        send_command(fresh_query, "!boom")
        send_command(fresh_query, "!help")

        reply = wait_for_private_message_containing(fresh_query, "Available commands")

    assert "!help - Show help." in reply.content
    assert "!boom - No description available." in reply.content
