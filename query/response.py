import re
from dataclasses import dataclass
from typing import Optional

from utils import parsers
from utils.patterns import EVENT, MESSAGE, RESPONSE_END


@dataclass
class QueryResponse:
    index: int
    match: re.Match[bytes]
    response: bytes
    error_id = property(lambda self: int(self.match.group("id")))
    msg = property(lambda self: self.match.group("msg").decode().strip())

    data = property(lambda self: parsers.parse_response_match(self.response))

    events = property(
        lambda self: [
            parsers.parse_event_match(match)
            for match in EVENT.finditer(self.response.decode())
        ]
    )

    messages = property(
        lambda self: [
            parsers.parse_message_match(match)
            for match in MESSAGE.finditer(self.response.decode())
        ]
    )
