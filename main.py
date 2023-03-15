import os

from dotenv import load_dotenv

import config
from plugins import PluginManager
from ts3client import TS3Client
from utils.logger import create_logger


def main():
    logger = create_logger("main", "main.log")

    load_dotenv()

    SERVER_IP = os.getenv(config.ENV_VAR_NAME__TS3_SERVER_IP)
    SERVER_PORT = int(os.getenv(config.ENV_VAR_NAME__TS3_SERVER_PORT))
    TELNET_LOGIN = os.getenv(config.ENV_VAR_NAME__TS3_TELNET_LOGIN)
    TELNET_PW = os.getenv(config.ENV_VAR_NAME__TS3_TELNET_PASSWORD)
    TELNET_PORT = int(os.getenv(config.ENV_VAR_NAME__TS3_TELNET_PORT))

    if None in (SERVER_IP, SERVER_PORT, TELNET_LOGIN, TELNET_PW, TELNET_PORT):
        logger.error("Missing credentials.")
        return

    ts3_client = TS3Client()
    ts3_client.connect(SERVER_IP, TELNET_PORT, TELNET_LOGIN, TELNET_PW)
    ts3_client.select_server_by_port(SERVER_PORT)

    plugin_manager = PluginManager(ts3_client, config.PLUGINS_CONFIG)
    plugin_manager.run()


if __name__ == "__main__":
    main()
