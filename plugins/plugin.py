import threading

from ts3client import TS3Client
from ts3client.utils.logger import create_logger


class Plugin:
    def __init__(self, client: TS3Client, event: threading.Event):
        self.client = client
        self.event = event
        self.logger = create_logger(self.__class__.__name__, "main.log")

    def run(self) -> None:
        self.logger.error("Plugin.run() not implemented.")
        raise NotImplementedError

    def stop(self) -> None:
        self.event.set()
