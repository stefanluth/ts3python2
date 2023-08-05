from config import PLUGINS_CONFIG
from ts3client import TS3Client
from ts3client.message import Message

from ..command import Command


class Help(Command):
    """Send a list of available commands."""

    def __init__(self, client: TS3Client, trigger: str, *args, **kwargs):
        super().__init__(client, trigger)

    def run(self, message: Message):
        """Send a list of available commands."""
        self.logger.info(f"User {message.invokername} triggered the help command.")

        prefix = PLUGINS_CONFIG["CommandHandler"]["prefix"]
        commands = PLUGINS_CONFIG["CommandHandler"]["commands"]

        commands_help = []
        for c in commands:
            description = "No description available."
            if "description" in commands[c]:
                description = commands[c]["description"]
            commands_help.append(f"{prefix}{commands[c]['trigger']} - {description}")

        help_text = "\nAvailable commands:\n\n" + "\n".join(commands_help)
        self.client.send_private_message(message.invokerid, help_text)
