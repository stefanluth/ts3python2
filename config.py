ENV_VAR_NAME__TS3_SERVER_IP = "TS3_SERVER_IP"
ENV_VAR_NAME__TS3_SERVER_PORT = "TS3_SERVER_PORT"
ENV_VAR_NAME__TS3_TELNET_LOGIN = "TS3_TELNET_LOGIN"
ENV_VAR_NAME__TS3_TELNET_PASSWORD = "TS3_TELNET_PASSWORD"
ENV_VAR_NAME__TS3_TELNET_PORT = "TS3_TELNET_PORT"

BOT_CONFIG = {
    "name": "TS3Bot",
}

PLUGINS_CONFIG = {
    "afk_mover": {
        "afk_channel_id": 357515,
        "afk_time": 30 * 60,
        "check_interval": 5,
        "ignore_channels": [425000, 357512, 357513, 357514],
    },
}
