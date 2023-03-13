import logging
import os
import time

from dotenv import load_dotenv

from query.definitions import NotifyRegisterType
from query.ts3query import TS3Query


def main():
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
    logger = logging.getLogger("main")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.FileHandler("ts3python2.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    load_dotenv()
    SERVER_IP = os.getenv("TS3_SERVER_IP")
    SERVER_PORT = int(os.getenv("TS3_SERVER_PORT"))
    TELNET_LOGIN = os.getenv("TS3_TELNET_LOGIN")
    TELNET_PW = os.getenv("TS3_TELNET_PASSWORD")
    TELNET_PORT = int(os.getenv("TS3_TELNET_PORT"))
    main()
