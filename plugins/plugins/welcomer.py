import random

from ts3client import TS3Client

from ..plugin import Plugin


class Welcomer(Plugin):
    def run(self, messages: list[str] = ["Welcome to the server!"]):
        """Send a welcome message to new clients.

        :param messages: The choice of messages to send to new clients.
        :type messages: list[str]
        """
        self.client.enable_events_and_messages()

        while not self.event.is_set():
            self.logger.debug("Checking for new clients...")
            for event in self.client.get_user_entered_events():
                if event.client_type == 1:
                    event.used = True
                    continue
                self.logger.info(f"Sending welcome message to {event.client_nickname}...")
                self.client.send_private_message(event.clid, random.choice(messages))
                event.used = True
            self.event.wait(1)
