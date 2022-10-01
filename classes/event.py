from dataclasses import dataclass, field


class Event:
    """
    Represents a TeamSpeak event.
    """

    pass


@dataclass
class ChannelCreatedEvent(Event):
    channel_topic: str = field(default_factory=str)
    cid: int = field(default_factory=int)
    invokerid: int = field(default_factory=int)
    invokername: str = field(default_factory=str)
    invokeruid: str = field(default_factory=str)
    reasonid: int = field(default_factory=int)


@dataclass
class ClientMovedEvent(Event):
    clid: int = field(default_factory=int)
    ctid: int = field(default_factory=int)
    invokerid: int = field(default_factory=int)
    invokername: str = field(default_factory=str)
    invokeruid: str = field(default_factory=str)
    reasonid: int = field(default_factory=int)
