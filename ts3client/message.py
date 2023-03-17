from dataclasses import dataclass, field

from .constants import TargetMode
from .utils.formatters import query_to_string


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
    source: TargetMode = field(init=False)

    def __post_init__(self):
        self.content = query_to_string(self.msg)
        self.source = TargetMode(self.targetmode)

    def mark_as_used(self):
        self.used = True
