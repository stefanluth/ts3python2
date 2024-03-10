from plugins.errors import ImplementationError
from ts3client import TS3Client
from ts3client.utils.logger import create_logger


class Command:
    """Base class for all commands."""

    def __init__(self, client: TS3Client, trigger: str, *args, **kwargs):
        self.client = client
        self.trigger = trigger
        self.logger = create_logger(self.__class__.__name__, "logs/main.log")

    def run(self):
        raise ImplementationError(self.__class__.__name__, "Command does not have a run() method.")

    def ready(self) -> None:
        """Broadcasts that the command is ready."""
        self.logger.info(f"{self.name} initialized.")
        print(f"{self.name} initialized.")

    @property
    def name(self):
        return self.__class__.__name__
