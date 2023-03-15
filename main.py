import os
import time

from dotenv import load_dotenv

import config
from client import TS3Client
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

    client = TS3Client()
    client.connect(SERVER_IP, TELNET_PORT, TELNET_LOGIN, TELNET_PW)
    # client.login(TELNET_LOGIN, TELNET_PW)
    client.select_server_by_port(SERVER_PORT)
    client.set_name(config.BOT_CONFIG.get("name"))

    print(client.get_clients())


if __name__ == "__main__":
    main()
