import re
from dataclasses import dataclass, field

from classes.event import Event
from classes.message import Message
from utils import parsers


@dataclass
class QueryResponse:
    """A class for representing a query response.

    :param index: The index of the query response match.
    :type index: int
    :param match: The query response match.
    :type match: re.Match[bytes]
    :param response: The query response.
    :type response: bytes
    :param error_id: The error id of the query response.
    :type error_id: int
    :param msg: The error message of the query response.
    :type msg: str
    :param data: The data of the query response.
    :type data: dict
    :param events: The included events in the query response.
    :type events: list[Event]
    :param messages: The included messages in the query response.
    :type messages: list[Message]
    """

    index: int
    match: re.Match[bytes]
    response: bytes
    error_id: int = field(init=False)
    msg: str = field(init=False)
    data: dict = field(init=False)
    events: list[Event] = field(init=False)
    messages: list[Message] = field(init=False)

    def __post_init__(self):
        self.error_id = int(self.match.group("id").decode())
        self.msg = self.match.group("msg").decode().strip()
        data, events, messages = parsers.parse_response(self.response)
        self.data = data
        self.events = events
        self.messages = messages
