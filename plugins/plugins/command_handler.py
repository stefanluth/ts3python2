from typing import Any

from .. import commands as all_commands
from ..command import Command
from ..plugin import Plugin


class CommandHandler(Plugin):
    def run(
        self,
        prefix: str = "!",
        commands: dict[str, Any] | None = None,
        check_interval: float | int = 1,
    ):
        """
        Handles commands.

        :param prefix: The prefix to use for commands, defaults to "!".
        :type prefix: str
        :param commands: A dictionary of commands to load, defaults to {}.
        :type commands: dict
        :param check_interval: The interval in seconds to check for commands, defaults to 1.
        :type check_interval: float
        """

        self.commands: list[Command] = []
        self._stopped_commands: list[tuple[Command, Any]] = []

        if commands is None:
            commands = {}

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

        self.commands = loaded_commands

        if len(loaded_commands) == 0:
            self.logger.info("No commands loaded.")
            return

        self.client.enable_message_events()

        self.logger.info(f"Loaded {len(loaded_commands)} commands...")
        triggers = [command.trigger for command in loaded_commands]

        self.ready()

        try:
            while not self.event.is_set():
                for command in loaded_commands:
                    tick = getattr(command, "tick", None)
                    if tick is None:
                        continue
                    try:
                        tick()
                    except Exception:
                        self.logger.exception(f"Command '{command.name}' tick failed.")

                self.logger.debug("Checking for new messages...")
                messages = self.client.get_unread_messages()

                for message in messages:
                    self.logger.debug(f"Received message from '{message.invokername}': {message.content}")
                    message.mark_as_used()

                    if not message.content.startswith(prefix):
                        self.logger.debug(f"Message does not start with prefix '{prefix}'. Skipping...")
                        continue

                    trigger = message.content[len(prefix) :].split(" ")[0]

                    if trigger not in triggers:
                        self.logger.debug(f"Trigger '{trigger}' not found. Skipping...")
                        continue

                    command = loaded_commands[triggers.index(trigger)]

                    self.logger.info(f"Running command '{command.name}'...")
                    try:
                        command.run(message)
                    except Exception:
                        self.logger.exception(f"Command '{command.name}' failed.")

                self.event.wait(check_interval)
        finally:
            self._stop_commands()

    def _stop_commands(self) -> None:
        stopped_commands: list[tuple[Command, Any]] = getattr(self, "_stopped_commands", [])
        self._stopped_commands = stopped_commands

        pending: list[tuple[Command, Any, Any]] = []
        for command in getattr(self, "commands", []):
            command_stop = getattr(command, "stop", None)
            if command_stop is None:
                continue

            stop_function = getattr(command_stop, "__func__", command_stop)
            if any(
                stopped_command is command and stopped_function is stop_function
                for stopped_command, stopped_function in stopped_commands
            ):
                continue

            pending.append((command, command_stop, stop_function))

        if not pending:
            return

        for command, command_stop, stop_function in pending:
            try:
                command_stop()
            except Exception:
                self.logger.exception(f"Command '{command.name}' failed to stop.")
            stopped_commands.append((command, stop_function))

    def stop(self) -> None:
        self._stop_commands()
        super().stop()
