import re
from dataclasses import dataclass

from classes.message import Message
from utils.patterns import TEXT_MSG


@dataclass
class QueryResponse:
    index: int
    match: re.Match[bytes] | None
    response: bytes
    error_id = property(lambda self: int(self.match.group("id")))
    msg = property(lambda self: self.match.group("msg").decode().strip())
    messages = property(
        lambda self: [
            Message(
                targetmode=int(message.group("targetmode")),
                msg=message.group("msg"),
                target=int(message.group("target")),
                invokerid=int(message.group("invokerid")),
                invokername=message.group("invokername"),
                invokeruid=message.group("invokeruid"),
            )
            for message in TEXT_MSG.finditer(self.response.decode())
        ]
    )
