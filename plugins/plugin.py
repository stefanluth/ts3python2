import threading

from plugins.errors import ImplementationError
from ts3client import TS3Client
from ts3client.utils.logger import create_logger


class Plugin:
    """Base class for all plugins."""

    def __init__(self, client: TS3Client, event: threading.Event):
        self.client = client
        self.event = event
        self.logger = create_logger(self.name, "logs/plugins.log")
        self.logger.info(f"Initializing {self.name}...")
        print(f"Initializing {self.name}...")

    def run(self) -> None:
        raise ImplementationError(self.name, "Plugin does not have a run() method.")

    def stop(self) -> None:
        self.logger.info(f"Stopping {self.name}...")
        self.event.set()

    def ready(self) -> None:
        """Broadcasts that the plugin is ready."""
        self.logger.info(f"{self.name} initialized.")
        print(f"{self.name} initialized.")

    @property
    def name(self):
        return self.__class__.__name__
