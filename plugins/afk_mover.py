import threading
import time

from ts3client import TS3Client
from utils.logger import create_logger

from .plugin import Plugin

logger = create_logger("AFK_Mover", "main.log")


class AFK_Mover(Plugin):
    def __init__(self, client: TS3Client, stop: threading.Event):
        super().__init__(client, stop)

    def run(
        self,
        afk_channel_id: int,
        afk_time: int,
        check_interval: int = 1,
        ignore_channels: list[int] = [],
        move_message: str = "You have been moved to the AFK channel.",
    ):
        """Moves clients to the AFK channel if they are AFK for a certain amount of time.

        :param client: A TS3Client instance.
        :type client: TS3Client
        :param afk_channel_id: The ID of the AFK channel.
        :type afk_channel_id: int
        :param afk_time: The amount of time in seconds a client has to be AFK to be moved to the AFK channel.
        :type afk_time: int
        :param check_interval: The interval in seconds to check for AFK clients, defaults to 1.
        :type check_interval: int
        :param ignore_channels: A list of channel IDs to ignore, defaults to [].
        :type ignore_channels: list[int]
        """

        afk_time = afk_time * 1000

        while not self.event.is_set():
            for client in self.client.get_clients():
                client_info = self.client.get_client_info(client.get("clid"))

                if client_info.get("cid") == afk_channel_id or client_info.get("cid") in ignore_channels:
                    continue

                if client_info.get("client_idle_time") > afk_time:
                    logger.info(f"Moving {client_info.get('client_nickname')} to AFK channel...")
                    self.client.move_client(client.get("clid"), afk_channel_id)
                    self.client.send_private_message(client.get("clid"), move_message)
            logger.debug(f"Sleeping for {check_interval} seconds...")
            time.sleep(check_interval)
