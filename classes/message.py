from dataclasses import dataclass, field
from enum import Enum

from utils.formatters import query_to_string


class MessageSource(Enum):
    PRIVATE = 1
    CHANNEL = 2
    SERVER = 3


@dataclass
class Message:
    targetmode: int
    msg: str
    target: int
    invokerid: int
    invokername: str
    invokeruid: str
    used: bool = field(default=False, init=False)
    content: str = field(init=False)
    source = property(lambda self: MessageSource(self.targetmode))

    def __post_init__(self):
        self.content = query_to_string(self.msg)

    def mark_as_used(self):
        self.used = True
