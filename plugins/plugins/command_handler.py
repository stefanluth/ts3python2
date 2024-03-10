from .. import commands as all_commands
from ..command import Command
from ..plugin import Plugin


class CommandHandler(Plugin):
    def run(self, prefix: str = "!", commands: dict = {}, check_interval: int = 1):
        """
        Handles commands.

        :param prefix: The prefix to use for commands, defaults to "!".
        :type prefix: str
        :param commands: A dictionary of commands to load, defaults to {}.
        :type commands: dict
        :param check_interval: The interval in seconds to check for commands, defaults to 1.
        :type check_interval: int
        """

        if len(commands) == 0:
            self.logger.info("No commands to load.")
            return

        loaded_commands: list[Command] = []
        for command_name, command_config in commands.items():
            if command_name not in all_commands.__all__:
                self.logger.info(f"Command {command_name} not found. Skipping...")
                continue

            self.logger.info(f"Loading command {command_name}...")
            loaded_command: Command = getattr(all_commands, command_name)(self.client, **command_config)
            loaded_commands.append(loaded_command)

        if len(loaded_commands) == 0:
            self.logger.info("No commands loaded.")
            return

        self.logger.info(f"Loaded {len(loaded_commands)} commands...")
        triggers = [command.trigger for command in loaded_commands]

        self.client.enable_message_events()
        self.ready()

        while not self.event.is_set():
            self.logger.debug("Checking for new messages...")
            messages = self.client.get_unread_messages()

            for message in messages:
                self.logger.debug(f"Received message from '{message.invokername}': {message.content}")
                if not message.content.startswith(prefix):
                    self.logger.debug(f"Message does not start with prefix '{prefix}'. Skipping...")
                    continue

                message.mark_as_used()

                trigger = message.content[len(prefix) :].split(" ")[0]

                if trigger not in triggers:
                    self.logger.debug(f"Trigger '{trigger}' not found. Skipping...")
                    continue

                command = loaded_commands[triggers.index(trigger)]

                self.logger.info(f"Running command '{command.name}'...")
                command.run(message)

            self.event.wait(check_interval)
