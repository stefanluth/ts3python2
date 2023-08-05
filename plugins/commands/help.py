from config import PLUGINS_CONFIG
from ts3client import TS3Client
from ts3client.message import Message

from ..command import Command


class Help(Command):
    """Send a list of available commands."""

    def __init__(self, client: TS3Client, trigger: str):
        super().__init__(client, trigger)

    def run(self, message: Message):
        """Send a list of available commands."""
        self.logger.info(f"User {message.invokername} triggered the help command.")

        commands = PLUGINS_CONFIG["CommandHandler"]["commands"]
        commands = [f"!{c['trigger']}" for c in list(PLUGINS_CONFIG["CommandHandler"]["commands"].values())]

        self.client.send_private_message(message.invokerid, "Available commands:")
        self.client.send_private_message(message.invokerid, "\n".join(commands))
