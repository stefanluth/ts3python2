import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

LOGGING_LEVEL = logging.DEBUG


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on", "y", "t"}:
        return True

    if normalized in {"0", "false", "no", "off", "n", "f", ""}:
        return False

    return default


TS3_SERVER_IP = os.getenv("TS3_SERVER_IP")
TS3_SERVER_PORT = int(os.getenv("TS3_SERVER_PORT", 9987))
TS3_QUERY_LOGIN = os.getenv("TS3_QUERY_LOGIN")
TS3_QUERY_PASSWORD = os.getenv("TS3_QUERY_PASSWORD")
TS3_QUERY_PORT = int(os.getenv("TS3_QUERY_PORT", 10022))
TS3_SSH_KNOWN_HOSTS = os.getenv("TS3_SSH_KNOWN_HOSTS") or None
TS3_SSH_ACCEPT_ALL_KEYS = _env_bool("TS3_SSH_ACCEPT_ALL_KEYS", False)
TS3_SSH_USE_SYSTEM_KEYS = _env_bool("TS3_SSH_USE_SYSTEM_KEYS", True)

BOT_CONFIG: dict[str, str] = {
    "name": "Bot",
    "description": "Hi there! I'm a bot!",
}

PLUGINS_CONFIG: dict[str, dict[str, Any]] = {
    "AFK_Mover": {
        "afk_channel_id": 357515,
        "afk_time": 30 * 60,
        "check_interval": 5,
        "ignore_channels": [425000, 357512, 357513, 357514],
    },
    "Welcomer": {
        "messages": ["Howdy!", "Hi there!"],
    },
    "CommandHandler": {
        "prefix": "!",
        "check_interval": 1,
        "commands": {
            "Help": {
                "trigger": "help",
                "description": "Send a list of available commands.",
            },
            # # Uncomment this to enable the Weather plugin
            # # Be sure to add the WEATHERAPI_COM_API_KEY environment variable to your .env file
            # "Weather": {
            #     "trigger": "weather",
            #     "api_key": os.getenv("WEATHERAPI_COM_API_KEY"),
            #     "description": "Get the weather for a location.",
            # },
        },
    },
    # # Uncomment this to enable the Doodler plugin
    # # Be sure to adjust the dates and URLs to your needs
    # "Doodler": {
    #     "default": "https://mydomain.com/banner-default.png",
    #     "doodles": [
    #         {
    #             "date": "14-02-2024",
    #             "url": "https://mydomain.com/banner-valentines.png",
    #         },
    #         {
    #             "date": "01-04-2024",
    #             "url": "https://mydomain.com/banner-april-fools.png",
    #         },
    #         {
    #             "date": "31-10-2024",
    #             "url": "https://mydomain.com/banner-halloween.png",
    #         },
    #         {
    #             "startDate": "01-12-2024",
    #             "endDate": "30-12-2024",
    #             "url": "https://mydomain.com/banner-christmas.png",
    #         },
    #         {
    #             "startDate": "01-01-2025",
    #             "endDate": "07-01-2025",
    #             "url": "https://mydomain.com/banner-new-year.png",
    #         },
    #     ],
    # },
}
