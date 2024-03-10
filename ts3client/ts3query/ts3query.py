import logging
import socket
import threading
import time
from telnetlib import Telnet

from ..event import Event
from ..message import Message
from ..utils import patterns
from ..utils.logger import create_logger
from .ts3query_command import CommandsWrapper, TS3QueryCommand
from .ts3query_response import TS3QueryResponse


class TS3Query:
    """
    A class for interacting with the TeamSpeak 3 ServerQuery interface.
    If no login and password are provided, the query client will not be logged in.
    You can login with the TS3Query.login() method after the TS3Query has been instantiated.

    :param host: The host of the TeamSpeak 3 server.
    :type host: str
    :param port: The port of the TeamSpeak 3 server.
    :type port: int
    :param login: The login of the TeamSpeak 3 server, defaults to None.
    :type login: str, optional
    :param password: The password of the TeamSpeak 3 server, defaults to None.
    :type password: str, optional
    :param timeout: The timeout of the TeamSpeak 3 server, defaults to 10.
    :type timeout: int, optional
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
        logger: logging.Logger = None,
    ) -> None:
        self.logger = logger or create_logger("TS3Query", "logs/main.log")
        self.logger.info(f"Connecting to {host}:{port}...")

        try:
            self._telnet = Telnet(host, port, timeout)
        except AttributeError as e:
            self.logger.error(e)
            return

        self.timeout = timeout
        self.commands = CommandsWrapper(self)
        self._skip_greeting()

        if not login or not password:
            self.logger.info("No login and/or password provided, not logging in...")
            return

        self.login(login, password)

    def __del__(self) -> None:
        self.exit()

    def connected(self) -> bool:
        sock = self._telnet.get_socket()
        if sock is not None and sock.fileno() != -1:
            try:
                sock.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
            except socket.error:
                return False
        else:
            return False

        return True

    def login(self, login: str, password: str) -> TS3QueryResponse:
        if not self.connected():
            return

        self.logger.info("Logging in...")
        return self.commands.login(login, password)

    def logout(self) -> TS3QueryResponse:
        if not self.connected():
            return

        self.logger.info("Logging out...")
        return self.commands.logout()

    def exit(self) -> None:
        """Exits the server, closes the connection and stops polling."""

        if not self.connected():
            return

        if self._polling_thread and self._polling_thread.is_alive():
            self.stop_polling()

        self.logger.info("Exiting")
        self.commands.quit()
        self.logger.info("Closing connection")
        self._telnet.close()
        self.logger.info("Connection closed")

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
            self._telnet.write(command.encoded)
            response = self._receive()
            self.logger.debug(f"Releasing lock...")

        self.logger.debug(f"Lock released")

        return response

    def _receive(self) -> TS3QueryResponse:
        self.logger.debug("Receiving response...")
        response = self._telnet.expect([patterns.RESPONSE_END_BYTES], self.timeout)
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
            self.commands.version()
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
            self._telnet.read_until(
                b'TS3\n\rWelcome to the TeamSpeak 3 ServerQuery interface, type "help" for a list of '
                b'commands and "help <command>" for information on a specific command.\n\r',
                self.timeout,
            )

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
