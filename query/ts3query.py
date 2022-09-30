import logging
import threading
from telnetlib import Telnet

from classes.message import Message
from query.command import CommandsWrapper, QueryCmd
from query.response import QueryResponse
from utils import patterns

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("ts3python2.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class TS3Query(Telnet):
    """A class for interacting with the TeamSpeak 3 ServerQuery interface.

    Args:
        host (`str`): The host to connect to.
        port (`int`): The port to connect to.
        login (`str`, optional): The login to use. Defaults to `None`.
        password (`str`, optional): The password to use. Defaults to `None`.
        timeout (`int`, optional): The timeout to use. Defaults to 10.
        logger (`logging.Logger`, optional): The logger to use. Defaults to `None`.

    Returns:
        The TS3Query instance.
    """

    _lock = threading.Lock()

    _messages: list[Message] = []
    _messages_limit: int = 1000
    _messages_thread: threading.Thread = None
    _messages_thread_stop = threading.Event()

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

        try:
            self.exit()
        except EOFError as e:
            logger.debug("Connection already closed")

        super().__del__()

    def exit(self) -> None:
        logger.info("Exiting")
        self.stop_polling_messages()
        self.commands.logout()
        self.commands.quit()

    def send(self, command: QueryCmd) -> QueryResponse:
        with self._lock:
            logger.debug(f"Sending command: {command.command}")
            self.write(command.encoded)
            response = self._receive()

        return response

    def _receive(self) -> QueryResponse:
        response = self.expect([patterns.RESPONSE], self.timeout)
        response = QueryResponse(*response)
        logger.debug(f"Received response: {response.response}")

        if len(self._messages) > self._messages_limit:
            self._messages = self._messages[-self._messages_limit :]

        self._messages.extend(response.messages)

        return response

    def start_polling_messages(self, polling_rate: float = 1) -> None:
        logger.info("Starting polling messages")
        if self._messages_thread and self._messages_thread.is_alive():
            logger.debug("Messages thread is already running")
            return

        logger.debug("Creating messages thread")
        self._messages_thread = threading.Thread(
            target=self._poll_messages,
            args=(self._messages_thread_stop, polling_rate),
        )
        self._messages_thread.start()

    def stop_polling_messages(self) -> None:
        logger.info("Stopping polling messages")

        if not self._messages_thread or not self._messages_thread.is_alive():
            logger.debug("Messages thread is not running")
            return

        if self._messages_thread_stop.is_set():
            logger.debug("Messages thread is already stopped")
            return

        self._messages_thread_stop.set()
        self._messages_thread.join()
        self._messages_thread_stop.clear()
        self._messages_thread = None

    def _poll_messages(self, stop: threading.Event, polling_rate: float) -> None:
        while not stop.isSet():
            self.send(QueryCmd("version"))
            stop.wait(polling_rate)

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
