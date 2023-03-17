import signal

import config
from plugins import PluginManager
from ts3client import TS3Client
from ts3client.utils.logger import create_logger


def main():
    logger = create_logger("main", "main.log")

    SERVER_IP = config.TS3_SERVER_IP
    SERVER_PORT = config.TS3_SERVER_PORT
    TELNET_LOGIN = config.TS3_TELNET_LOGIN
    TELNET_PW = config.TS3_TELNET_PASSWORD
    TELNET_PORT = config.TS3_TELNET_PORT

    if None in (SERVER_IP, SERVER_PORT, TELNET_LOGIN, TELNET_PW, TELNET_PORT):
        logger.error("Missing credentials.")
        return

    ts3_client = TS3Client(SERVER_IP, TELNET_PORT, TELNET_LOGIN, TELNET_PW)
    ts3_client.select_server_by_port(SERVER_PORT)

    plugin_manager = PluginManager(ts3_client, config.PLUGINS_CONFIG)
    plugin_manager.run()

    def sigint_handler(sig, frame):
        logger.info("Stopping...")
        print("\nStopping...")
        plugin_manager.stop()
        ts3_client.disconnect()
        logger.info("Stopped.")

    signal.signal(signal.SIGINT, sigint_handler)
    print("Press Ctrl+C to exit")


if __name__ == "__main__":
    main()
