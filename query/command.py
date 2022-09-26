from dataclasses import dataclass, field
from typing import Optional

from utils import parsers


@dataclass
class QueryCmd:
    command: str
    values: Optional[list] = field(default_factory=list)
    args: Optional[dict] = field(default_factory=dict)
    encoded: bytes = field(init=False)

    def __post_init__(self):
        cmd = " ".join(
            [
                self.command,
                *self.values,
                *parsers.dict_to_query_parameters(self.args),
            ]
        )

        self.encoded = f"{cmd.strip()}\n".encode()
