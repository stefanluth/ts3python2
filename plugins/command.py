from ts3client import TS3Client
from ts3client.utils.logger import create_logger


class Command:
    """Base class for all commands."""

    def __init__(self, client: TS3Client, trigger: str):
        self.client = client
        self.trigger = trigger
        self.logger = create_logger(self.__class__.__name__, "main.log")

    def run(self):
        self.logger.error("Command.run() not implemented.")
        raise NotImplementedError
