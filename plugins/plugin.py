import threading

from ts3client import TS3Client

from utils.logger import create_logger


class Plugin:
    def __init__(self, client: TS3Client, event: threading.Event):
        self.client = client
        self.event = event
        self.logger = create_logger(self.__class__.__name__, "main.log")

    def run(self) -> None:
        print("This method should be overridden by the plugin.")

    def stop(self) -> None:
        self.event.set()
