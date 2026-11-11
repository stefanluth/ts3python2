import signal

import config
from plugins import PluginManager
from ts3client import TS3Client
from ts3client.utils.logger import create_logger, log_path

logger = create_logger("main", log_path("main.log"))


def main():
    def sigint_handler(sig, frame):
        logger.info("Stopping...")
        print("\nStopping...")
        plugin_manager.stop()
        ts3_client.disconnect()
        logger.info("Stopped.")

    SERVER_IP = config.TS3_SERVER_IP
    SERVER_PORT = config.TS3_SERVER_PORT
    QUERY_LOGIN = config.TS3_QUERY_LOGIN
    QUERY_PASSWORD = config.TS3_QUERY_PASSWORD
    QUERY_PORT = config.TS3_QUERY_PORT

    if None in (SERVER_IP, SERVER_PORT, QUERY_LOGIN, QUERY_PASSWORD, QUERY_PORT):
        raise ValueError("One or more credentials values are missing.")

    print("Connecting to server...")
    ts3_client = TS3Client(
        SERVER_IP,
        QUERY_PORT,
        QUERY_LOGIN,
        QUERY_PASSWORD,
        known_hosts=config.TS3_SSH_KNOWN_HOSTS,
        accept_all_keys=config.TS3_SSH_ACCEPT_ALL_KEYS,
        use_system_host_keys=config.TS3_SSH_USE_SYSTEM_KEYS,
    )
    ts3_client.select_server_by_port(SERVER_PORT)
    print("Connected.")

    if config.BOT_CONFIG.get("name") is not None:
        print(f"Setting bot name: {config.BOT_CONFIG['name']}")
        ts3_client.set_name(config.BOT_CONFIG["name"])
    if config.BOT_CONFIG.get("description") is not None:
        print(f"Setting bot description: {config.BOT_CONFIG['description']}")
        ts3_client.set_description(config.BOT_CONFIG["description"])

    print("Starting plugins...")
    plugin_manager = PluginManager(ts3_client, config.PLUGINS_CONFIG)
    plugin_manager.run()

    signal.signal(signal.SIGINT, sigint_handler)
    print("Press Ctrl+C to exit")

    ts3_client.keep_alive()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        raise e
