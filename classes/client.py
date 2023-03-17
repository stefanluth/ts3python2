from dataclasses import dataclass
from typing import Optional


@dataclass
class Client:
    clid: int
    client_nickname: str
    cid: Optional[int] = None
    client_type: Optional[int] = None
    client_database_id: Optional[int] = None
    client_unique_identifier: Optional[str] = None
