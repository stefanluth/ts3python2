import threading

from plugins.errors import ImplementationError
from ts3client import TS3Client
from ts3client.utils.logger import create_logger


class Plugin:
    """Base class for all plugins."""

    def __init__(self, client: TS3Client, event: threading.Event):
        self.client = client
        self.event = event
        self.logger = create_logger(self.__class__.__name__, "logs/plugins.log")

    def run(self) -> None:
        raise ImplementationError(self.__class__.__name__, "Plugin does not have a run() method.")

    def stop(self) -> None:
        self.event.set()
