import threading
import time

from ts3client.ts3client import TS3Client
from .plugin import Plugin


class Welcomer(Plugin):
    def __init__(self, client: TS3Client, event: threading.Event):
        super().__init__(client, event)
        self.client.enable_events_and_messages()

    def run(self, message: str = "Welcome to the server!"):
        """Send a welcome message to new clients.

        :param message: The message to send to new clients.
        :type message: str
        """

        while not self.event.is_set():
            self.logger.debug("Checking for new clients...")
            for event in self.client.get_client_entered_events():
                self.logger.info(f"Sending welcome message to {event.client_nickname}...")
                self.client.send_private_message(event.clid, message)
                event.used = True
            time.sleep(1)
