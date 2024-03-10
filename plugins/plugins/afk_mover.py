from ..plugin import Plugin


class AFK_Mover(Plugin):
    def run(
        self,
        afk_channel_id: int,
        afk_time: int,
        check_interval: int = 1,
        ignore_channels: list = [],
        move_message: str = "You have been moved to the AFK channel.",
    ):
        """
        Moves clients to the AFK channel if they are AFK for a certain amount of time.

        :param client: A TS3Client instance.
        :type client: TS3Client
        :param afk_channel_id: The ID of the AFK channel.
        :type afk_channel_id: int
        :param afk_time: The amount of time in seconds a client has to be idle to be moved to the AFK channel.
        :type afk_time: int
        :param check_interval: The interval in seconds to check for AFK clients, defaults to 1.
        :type check_interval: int
        :param ignore_channels: A list of channel IDs to ignore, defaults to [].
        :type ignore_channels: list[int]
        :param move_message: The message to send to the client when they are moved to the AFK channel, defaults to "You have been moved to the AFK channel.".
        :type move_message: str
        """

        afk_time = afk_time * 1000
        self.ready()

        while not self.event.is_set():
            self.logger.debug("Checking for AFK clients...")
            for user in self.client.get_users():
                if user.cid == afk_channel_id or user.cid in ignore_channels:
                    continue

                user_info = self.client.get_user_info(user.clid)

                if user_info.client_idle_time > afk_time:
                    self.logger.info(f"Moving {user.client_nickname} to AFK channel...")
                    self.client.move_user(user.clid, afk_channel_id)
                    self.client.send_private_message(user.clid, move_message)
            self.logger.debug(f"Sleeping for {check_interval} seconds...")
            self.event.wait(check_interval)
