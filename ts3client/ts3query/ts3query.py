import logging
import threading
import time

from ..event import Event
from ..message import Message
from ..utils import patterns
from ..utils.logger import create_logger
from .transport import SSHTransport
from .ts3query_command import CommandsWrapper, TS3QueryCommand
from .ts3query_response import TS3QueryResponse


class TS3Query:
    """
    A class for interacting with the TeamSpeak 3 ServerQuery interface over SSH.
    The SSH login and password are required and are used when the connection is
    established; there is no separate login command.

    :param host: The host of the TeamSpeak 3 server.
    :type host: str
    :param port: The SSH query port of the TeamSpeak 3 server.
    :type port: int
    :param login: The SSH login of the TeamSpeak 3 server, defaults to None.
    :type login: str, optional
    :param password: The SSH password of the TeamSpeak 3 server, defaults to None.
    :type password: str, optional
    :param timeout: The timeout of the TeamSpeak 3 server, defaults to 10.
    :type timeout: int, optional
    :param known_hosts: Path to a known_hosts file, defaults to None.
    :type known_hosts: str, optional
    :param accept_all_keys: Accept unknown SSH host keys, defaults to False.
    :type accept_all_keys: bool, optional
    :param use_system_host_keys: Load the system SSH known hosts, defaults to True.
    :type use_system_host_keys: bool, optional
    :param logger: The logger to use, defaults to None.
    :type logger: logging.Logger, optional
    """

    _lock = threading.RLock()

    _flood_protection: bool = True
    _flood_protection_timeout: float = 0.5
    _events: list[Event] = []
    _events_limit: int = 1000
    _messages: list[Message] = []
    _messages_limit: int = 1000
    _polling_thread: threading.Thread | None = None
    _polling_thread_stop = threading.Event()

    def __init__(
        self,
        host: str,
        port: int,
        login: str = None,
        password: str = None,
        timeout=10,
        known_hosts: str = None,
        accept_all_keys: bool = False,
        use_system_host_keys: bool = True,
        logger: logging.Logger = None,
    ) -> None:
        self.logger = logger or create_logger("TS3Query", "logs/main.log")
        self._transport = None
        self._exiting = False

        if not login or not password:
            raise ValueError("SSH login and password are required")

        self.logger.info(f"Connecting to {host}:{port}...")
        self.timeout = timeout
        self._transport = SSHTransport(
            host,
            port,
            login,
            password,
            timeout=timeout,
            known_hosts=known_hosts,
            accept_all_keys=accept_all_keys,
            use_system_host_keys=use_system_host_keys,
        )

        self.commands = CommandsWrapper(self)
        self._skip_greeting()

    def __del__(self) -> None:
        self.exit()

    def connected(self) -> bool:
        transport = getattr(self, "_transport", None)
        return bool(transport and transport.connected())

    def exit(self) -> None:
        """Exits the server, closes the connection and stops polling."""
        transport = getattr(self, "_transport", None)
        if transport is None:
            return

        if not getattr(self, "_exiting", False):
            self._exiting = True

            try:
                if self._polling_thread and self._polling_thread.is_alive():
                    self.stop_polling()
            except Exception:
                self.logger.exception("Failed to stop polling")

            if transport.connected():
                self.logger.info("Exiting")
                try:
                    self.commands.quit()
                except Exception:
                    self.logger.exception("Failed to send quit")

        self.logger.info("Closing connection")
        try:
            transport.close()
            self.logger.info("Connection closed")
        except Exception:
            self.logger.exception("Failed to close connection")

    def send(self, command: TS3QueryCommand) -> TS3QueryResponse:
        """
        Sends a command to the server.

        :param command: The command to send
        :type command: QueryCommand
        :return: The response from the server
        :rtype: QueryResponse
        """
        if not self.connected():
            return

        self.logger.debug(f"Aquiring lock...")
        with self._lock:
            if self._flood_protection:
                time.sleep(self._flood_protection_timeout)

            self.logger.debug(f"Lock aquired")
            self.logger.debug(f"Sending command: {command.command}")
            self._transport.write(command.encoded)
            response = self._receive()
            self.logger.debug(f"Releasing lock...")

        self.logger.debug(f"Lock released")

        return response

    def _receive(self) -> TS3QueryResponse:
        self.logger.debug("Receiving response...")
        response = self._transport.expect([patterns.RESPONSE_END_BYTES], self.timeout)
        self.logger.debug(f"Received response: {response}")

        response = TS3QueryResponse(*response)
        self.logger.debug(f"Parsed response: {response}")

        self._remove_used_events()
        self._add_events(response.events, self._events_limit)
        self._remove_used_messages()
        self._add_messages(response.messages, self._messages_limit)

        return response

    def keep_alive(self) -> None:
        """Waits for the polling thread to stop."""
        if self._polling_thread and self._polling_thread.is_alive():
            self.logger.debug("Waiting for polling thread to stop")
            self._polling_thread.join()
            self.logger.debug("Polling thread stopped")

    def start_polling(self, polling_rate: float = 1) -> None:
        """
        Starts polling the server for events and messages.

        :param polling_rate: The rate at which to poll the server, defaults to 1
        :type polling_rate: float, optional
        """
        self.logger.debug("Starting polling...")
        if self._polling_thread and self._polling_thread.is_alive():
            self.logger.debug("Polling thread is already running")
            return

        self.logger.debug("Creating polling thread")
        self._polling_thread = threading.Thread(
            target=self._poll,
            args=(self._polling_thread_stop, polling_rate),
            daemon=True,
        )
        self.logger.info("Starting polling thread")
        self._polling_thread.start()

    def stop_polling(self) -> None:
        """Stops polling the server for events and messages."""
        self.logger.debug("Stopping polling...")

        if not self._polling_thread or not self._polling_thread.is_alive():
            self.logger.debug("Polling thread is not running")
            return

        if self._polling_thread_stop.is_set():
            self.logger.debug("Polling thread is already stopped")
            return

        self.logger.info("Stopping polling thread")
        self._polling_thread_stop.set()
        self._polling_thread.join()
        self._polling_thread_stop.clear()
        self._polling_thread = None

    def _poll(self, stop: threading.Event, polling_rate: float) -> None:
        self.logger.debug("Polling...")
        while not stop.is_set():
            try:
                self.commands.version()
            except Exception:
                self.logger.exception("Polling command failed")
            stop.wait(polling_rate)
        self.logger.debug("Polling stopped")

    def enable_flood_protection(self) -> None:
        self.logger.info("Enabling flood protection")
        self._flood_protection = True

    def disable_flood_protection(self) -> None:
        self.logger.info("Disabling flood protection")
        self._flood_protection = False

    def _add_events(self, events: list[Event], limit: int):
        self.logger.debug(f"Adding events: {events}")
        self._events.extend(events)

        if len(self._events) > limit:
            self.logger.debug("Events limit reached, trimming events")
            self._events = self._events[-limit:]

    def _add_messages(self, messages: list[Message], limit: int):
        self.logger.debug(f"Adding messages: {messages}")
        self._messages.extend(messages)

        if len(self._messages) > limit:
            self.logger.debug("Messages limit reached, trimming messages")
            self._messages = self._messages[-limit:]

    def _remove_used_messages(self):
        self.logger.debug("Removing used messages")
        self._messages = [message for message in self._messages if not message.used]

    def _remove_used_events(self):
        self.logger.debug("Removing used events")
        self._events = [event for event in self._events if not event.used]

    def _skip_greeting(self) -> None:
        if not self.connected():
            return

        with self._lock:
            self.logger.debug("Skipping greeting")
            self._transport.read_until(b"\n\r", self.timeout)
            self._transport.read_until(b"\n\r", self.timeout)

    @property
    def flood_protection(self) -> bool:
        return self._flood_protection

    @property
    def flood_protection_timeout(self) -> float:
        return self._flood_protection_timeout

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def unread_messages(self) -> list[Message]:
        return [message for message in self._messages if not message.used]

    @property
    def messages_limit(self) -> int:
        return self._messages_limit

    @property
    def events(self) -> list[Event]:
        return self._events

    @property
    def unread_events(self) -> list[Event]:
        return [event for event in self._events if not event.used]

    @property
    def events_limit(self) -> int:
        return self._events_limit

    @flood_protection_timeout.setter
    def flood_protection_timeout(self, rate: float) -> None:
        self.logger.info(f"Setting flood protection rate to {rate}")
        self._flood_protection_timeout = rate

    @messages_limit.setter
    def messages_limit(self, limit: int) -> None:
        self.logger.info(f"Setting messages limit to {limit}")
        self._messages_limit = limit

    @events_limit.setter
    def events_limit(self, limit: int) -> None:
        self.logger.info(f"Setting events limit to {limit}")
        self._events_limit = limit
