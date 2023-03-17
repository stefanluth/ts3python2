from dataclasses import dataclass
from typing import Optional


@dataclass
class Channel:
    cid: Optional[int] = None
    pid: Optional[int] = None
    channel_order: Optional[int] = None
    channel_name: Optional[str] = None
    total_clients: Optional[int] = None
    channel_needed_subscribe_power: Optional[int] = None
