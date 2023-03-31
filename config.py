import os

from dotenv import load_dotenv

load_dotenv()

TS3_SERVER_IP = os.getenv("TS3_SERVER_IP")
TS3_SERVER_PORT = int(os.getenv("TS3_SERVER_PORT"))
TS3_TELNET_LOGIN = os.getenv("TS3_TELNET_LOGIN")
TS3_TELNET_PASSWORD = os.getenv("TS3_TELNET_PASSWORD")
TS3_TELNET_PORT = int(os.getenv("TS3_TELNET_PORT"))

BOT_CONFIG = {
    "name": "TS3Bot",
}

PLUGINS_CONFIG = {
    "AFK_Mover": {
        "afk_channel_id": 357515,
        "afk_time": 30 * 60,
        "check_interval": 5,
        "ignore_channels": [425000, 357512, 357513, 357514],
    },
    "Welcomer": {
        "message": "Howdy!",
    },
    # Uncomment this to enable the Weather plugin
    # Be sure to add the WEATHERAPI_COM_API_KEY environment variable to your .env file
    # "CommandHandler": {
    #     "prefix": "!",
    #     "check_interval": 1,
    #     "commands": {
    #         "Weather": {
    #             "trigger": "weather",
    #             "api_key": os.getenv("WEATHERAPI_COM_API_KEY"),
    #         },
    #     },
    # },
}
