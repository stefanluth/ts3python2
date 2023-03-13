import os
import time

from dotenv import load_dotenv

import config
from query.definitions import NotifyRegisterType
from query.ts3query import TS3Query
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

    logger.info("Creating TS3Query instance")
    query = TS3Query(SERVER_IP, TELNET_PORT, TELNET_LOGIN, TELNET_PW, timeout=10)

    # Connect to the server
    query.commands.use(port=SERVER_PORT)

    channel_id = query.commands.whoami().data.get("client_channel_id")

    query.commands.servernotifyregister(event=NotifyRegisterType.SERVER)
    query.commands.servernotifyregister(event=NotifyRegisterType.CHANNEL, id=channel_id)
    query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_PRIVATE)
    query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_CHANNEL)
    query.commands.servernotifyregister(event=NotifyRegisterType.TEXT_SERVER)
    # query.start_polling()

    time.sleep(10)
    print("clientlist:", query.commands.clientlist(uid=True).data)

    print(f"Events: {len(query._events)}")
    for event in query._events:
        print(event)

    print(f"Messages: {len(query._messages)}")
    for message in query._messages:
        print(message.content)

    query.exit()


if __name__ == "__main__":
    main()
