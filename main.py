import logging
import os
import time

from query.definitions import NotifyRegisterType
from query.ts3query import TS3Query

credentials_py_exists = os.path.isfile("credentials.py")


logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)
logger.propagate = False
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("ts3python2.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if credentials_py_exists:
    import credentials

    logger.info("Using credentials from credentials.py")
    SERVER_IP = credentials.SERVER_IP
    SERVER_PORT = credentials.SERVER_PORT
    TELNET_LOGIN = credentials.TELNET_LOGIN
    TELNET_PW = credentials.TELNET_PW
    TELNET_PORT = credentials.TELNET_PORT
else:
    logger.info("Using credentials from environment variables")
    SERVER_IP = os.getenv("TS3_SERVER_IP")
    SERVER_PORT = int(os.getenv("TS3_SERVER_PORT"))
    TELNET_LOGIN = os.getenv("TS3_TELNET_LOGIN")
    TELNET_PW = os.getenv("TS3_TELNET_PORT")
    TELNET_PORT = int(os.getenv("TS3_TELNET_PORT"))


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
    query.commands.servernotifyregister(event=NotifyRegisterType.TEXTPRIVATE)
    query.commands.servernotifyregister(event=NotifyRegisterType.TEXTCHANNEL)
    query.commands.servernotifyregister(event=NotifyRegisterType.TEXTSERVER)

    time.sleep(30)
    for event in query._events:
        print(event)

    for message in query._messages:
        print(message.content)

    query.exit()


if __name__ == "__main__":
    main()
