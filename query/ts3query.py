import threading
from telnetlib import Telnet

from classes.event import Event
from classes.message import Message
from query.command import CommandsWrapper, QueryCommand
from query.response import QueryResponse
from utils import patterns
from utils.logger import get_logger

logger = get_logger("main")


class TS3Query(Telnet):
    """A class for interacting with the TeamSpeak 3 ServerQuery interface.

    :param host: The host of the TeamSpeak 3 server.
    :type host: str
    :param port: The port of the TeamSpeak 3 server.
    :type port: int
    :param login: The login of the TeamSpeak 3 server.
    :type login: str
    :param password: The password of the TeamSpeak 3 server.
    :type password: str
    :param timeout: The timeout of the TeamSpeak 3 server.
    :type timeout: int
    """

    _lock = threading.Lock()

    _exited = True

    _events: list[Event] = []
    _events_limit: int = 1000
    _messages: list[Message] = []
    _messages_limit: int = 1000
    _polling_thread: threading.Thread = None
    _polling_thread_stop = threading.Event()

    def __init__(
        self,
        host: str,
        port: int,
        login: str = None,
        password: str = None,
        timeout=10,
    ) -> None:
        logger.name = f"{self.__class__.__name__}"
        logger.info(f"Connecting to {host}:{port}")
        try:
            super().__init__(host, port, timeout)
            self._exited = False
        except AttributeError as e:
            logger.error(e)
            logger.error("Invalid host and/or port")
            return
        logger.name = f"{self.__class__.__name__}({host}:{port})"

        self.timeout = timeout
        self.commands = CommandsWrapper(self)

        self._skip_greeting()

        if login and password:
            logger.info("Logging in")
            self.commands.login(login, password)
        else:
            logger.info("No login and/or password provided")

    def __del__(self) -> None:
        logger.info("Deleting instance")
        self.exit()
        super().__del__()

    def exit(self) -> None:
        """Exits the server, closes the connection and stops polling."""

        if self._polling_thread and self._polling_thread.is_alive():
            self.stop_polling()

        if not self._exited:
            logger.info("Exiting")
            self.commands.quit()
            self.close()
            self._exited = True

    def send(self, command: QueryCommand) -> QueryResponse:
        """Sends a command to the server.

        :param command: The command to send
        :type command: QueryCommand
        :return: The response from the server
        :rtype: QueryResponse
        """
        logger.debug(f"Aquiring lock...")
        with self._lock:
            logger.debug(f"Lock aquired")
            logger.debug(f"Sending command: {command.command}")
            self.write(command.encoded)
            response = self._receive()

        return response

    def _receive(self) -> QueryResponse:
        logger.debug("Receiving response...")
        response = self.expect([patterns.RESPONSE_END_BYTES], self.timeout)
        response = QueryResponse(*response)
        logger.debug(f"Received response: {response.response}")

        self._add_events(response.events, self._events_limit)
        self._add_messages(response.messages, self._messages_limit)

        logger.debug(f"Received data: {response.data}")

        return response

    def _add_events(self, events: list[Event], limit: int):
        logger.debug(f"Adding events: {events}")
        self._events.extend(events)

        if len(self._events) > limit:
            logger.debug("Events limit reached, trimming events")
            self._events = self._events[-limit:]

    def _add_messages(self, messages: list[Message], limit: int):
        logger.debug(f"Adding messages: {messages}")
        self._messages.extend(messages)

        if len(self._messages) > limit:
            logger.debug("Messages limit reached, trimming messages")
            self._messages = self._messages[-limit:]

    def start_polling(self, polling_rate: float = 1) -> None:
        """Starts polling the server for events and messages.

        :param polling_rate: The rate at which to poll the server, defaults to 1
        :type polling_rate: float, optional
        """
        logger.debug("Starting polling...")
        if self._polling_thread and self._polling_thread.is_alive():
            logger.debug("Polling thread is already running")
            return

        logger.debug("Creating polling thread")
        self._polling_thread = threading.Thread(
            target=self._poll,
            args=(self._polling_thread_stop, polling_rate),
        )
        logger.info("Starting polling thread")
        self._polling_thread.start()

    def stop_polling(self) -> None:
        """Stops polling the server for events and messages."""
        logger.debug("Stopping polling...")

        if not self._polling_thread or not self._polling_thread.is_alive():
            logger.debug("Polling thread is not running")
            return

        if self._polling_thread_stop.is_set():
            logger.debug("Polling thread is already stopped")
            return

        logger.info("Stopping polling thread")
        self._polling_thread_stop.set()
        self._polling_thread.join()
        self._polling_thread_stop.clear()
        self._polling_thread = None

    def _poll(self, stop: threading.Event, polling_rate: float) -> None:
        logger.debug("Polling...")
        while not stop.isSet():
            self.commands.version()
            stop.wait(polling_rate)
        logger.debug("Polling stopped")

    def set_messages_limit(self, limit: int) -> None:
        logger.info(f"Setting messages limit to {limit}")
        self._messages_limit = limit

    @property
    def messages_limit(self) -> int:
        return self._messages_limit

    @property
    def messages(self) -> list[Message]:
        return self._messages

    @property
    def unread_messages(self) -> list[Message]:
        return [message for message in self._messages if not message.used]

    def _skip_greeting(self) -> None:
        logger.debug("Skipping greeting")
        self.read_until(
            b'TS3\n\rWelcome to the TeamSpeak 3 ServerQuery interface, type "help" for a list of '
            b'commands and "help <command>" for information on a specific command.\n\r',
            self.timeout,
        )
