import time
from ts3client import TS3Client
from utils.logger import get_logger

logger = get_logger("main")


def afk_mover(ts3_client: TS3Client, afk_channel_id: int, afk_time: int, check_interval: int = 1):
    """Moves clients to the AFK channel if they are AFK for a certain amount of time.

    :param client: A TS3Client instance.
    :type client: TS3Client
    :param afk_channel_id: The ID of the AFK channel.
    :type afk_channel_id: int
    :param afk_time: The amount of time in seconds a client has to be AFK to be moved to the AFK channel.
    :type afk_time: int
    """

    afk_time = afk_time * 1000

    while True:
        for client in ts3_client.get_clients():
            client_info = ts3_client.get_client_info(client.get("clid"))

            if client_info.get("cid") == afk_channel_id:
                continue

            if client_info.get("client_idle_time") > afk_time:
                logger.info(f"Moving {client_info.get('client_nickname')} to AFK channel...")
                ts3_client.move_client(client.get("clid"), afk_channel_id)

        time.sleep(check_interval)